# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Cure the one-sided fault issue on a split (post-fracture-generation) mesh.

Node splitting duplicates the fault nodes so that both sides can move independently, but it
writes a single surface polygon per fault location, remapped onto whichever 3D neighbour was
enumerated first. The resulting fault surface is a patchwork: adjacent faces sit on different
collocated node copies. GEOS derives its seal node set from that surface, so the open
matrix/fracture taps end up on mixed sides and fluid crosses the fault even though most faces
look sealed.

This action rewrites every tagged fault face onto ONE consistent side per fault value, so that:
  - the seal node set holds only that side's node copies (cross-fault flow is blocked, and the
    fracture stays anchored to one matrix side so the flow solve converges);
  - every fault face remains a real 3D-cell face (the orphan2d action still passes);
  - fault junctions (nodes with 3 or 4 collocated copies) are handled by locating the coincident
    reference-side 3D face geometrically, not through a two-way twin relationship.

Collocated (split) nodes are detected by coordinate coincidence, so no separate fault or
faceBlock file is needed. Two cell arrays are added for display and QC:
  - "faultSide": +1 on the reference side, -1 on a residual degeneracy (typically a fault-fault
    intersection line, where no single side exists), 0 on non-fault cells.
  - "onHole": 1 on faces bordering a residual hole (a boundary loop other than the fault
    perimeter), 0 elsewhere. A fully cured fault has onHole all 0.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable

import numpy as np
from numpy.typing import NDArray

import vtk
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkStaticPointLocator, VTK_TRIANGLE, VTK_POLYGON,
                                            VTK_QUAD )
from vtkmodules.util.numpy_support import numpy_to_vtk, numpy_to_vtkIdTypeArray, vtk_to_numpy

from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh_doctor.parsing.cliParsing import setupLogger

FAULT_SIDE_ARRAY: str = "faultSide"
ON_HOLE_ARRAY: str = "onHole"

__CELL_TYPES_2D: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON )
__IS_FAULT_FACE_ARRAY: str = "__cureOneSidedIsFaultFace"
__ORIGINAL_CELL_ARRAY: str = "__cureOneSidedOriginalCell"


@dataclass( frozen=True )
class Options:
    """Options for the cureOneSided action.

    Attributes:
        outputFile: VTK output file configuration for the cured mesh.
        tagArray: Name of the cell-data array tagging the fault faces.
        tagValues: Fault values to cure. Empty means every distinct non-zero value of tagArray
            carried by a 2D cell.
        tolerance: Distance below which two nodes are considered collocated.
    """
    outputFile: VtkOutput
    tagArray: str
    tagValues: tuple[ int, ...]
    tolerance: float


@dataclass( frozen=True )
class FaultResult:
    """Per-fault-value outcome of the cure.

    Attributes:
        tagValue: The fault value this entry describes.
        numFaces: Number of 2D cells carrying this value.
        numMovedFaces: Faces rewritten onto the reference side.
        numAlreadyCorrectFaces: Faces that already sat on the reference side.
        numDegenerateFaces: Faces left as-is because no reference-side 3D face exists.
        numSkippedFaces: Faces with no orientable normal or no 3D owner cell (orphan faces).
        numHoleBorderFaces: Faces bordering a residual hole of this fault surface.
    """
    tagValue: int
    numFaces: int
    numMovedFaces: int
    numAlreadyCorrectFaces: int
    numDegenerateFaces: int
    numSkippedFaces: int
    numHoleBorderFaces: int


@dataclass( frozen=True )
class Result:
    """Result of the cureOneSided action.

    Attributes:
        faults: Per-fault-value outcomes, ordered by fault value.
        numFaultFaces: Total number of tagged 2D fault faces.
        numMovedFaces: Total number of faces rewritten onto the reference side.
        numDegenerateFaces: Total number of faces left on their original side.
        numSkippedFaces: Total number of faces that could not be processed.
        numHoleBorderFaces: Total number of faces bordering a residual hole.
    """
    faults: tuple[ FaultResult, ...]
    numFaultFaces: int
    numMovedFaces: int
    numDegenerateFaces: int
    numSkippedFaces: int
    numHoleBorderFaces: int


class _UnionFind:
    """Minimal union-find over point ids, used to group boundary edges into loops."""

    def __init__( self ) -> None:
        """Create an empty union-find structure."""
        self.m_parent: dict[ int, int ] = {}

    def find( self, a: int ) -> int:
        """Return the representative of the set containing ``a``.

        Args:
            a: The element to look up. It is inserted if unknown.

        Returns:
            The representative element of ``a``'s set.
        """
        self.m_parent.setdefault( a, a )
        while self.m_parent[ a ] != a:
            self.m_parent[ a ] = self.m_parent[ self.m_parent[ a ] ]
            a = self.m_parent[ a ]
        return a

    def union( self, a: int, b: int ) -> None:
        """Merge the sets containing ``a`` and ``b``.

        Args:
            a: First element.
            b: Second element.
        """
        rootA, rootB = self.find( a ), self.find( b )
        if rootA != rootB:
            self.m_parent[ rootA ] = rootB


def _toIdList( idList: vtkIdList, pointIds: NDArray[ np.int64 ] ) -> vtkIdList:
    """Fill a vtkIdList with the given point ids and return it.

    Args:
        idList: The list to reset and fill (reused across calls to avoid churn).
        pointIds: The point ids to insert.

    Returns:
        The filled list.
    """
    idList.Reset()
    for pointId in pointIds:
        idList.InsertNextId( int( pointId ) )
    return idList


def buildCollocatedGroups( mesh: vtkUnstructuredGrid, pointIds: Iterable[ int ],
                           tolerance: float ) -> tuple[ NDArray[ np.int64 ], dict[ int, list[ int ] ] ]:
    """Group the given points with every mesh point collocated with them.

    Two points closer than ``tolerance`` belong to the same group, i.e. they are two copies of a
    single geometric node created by the fault split. Only the groups reachable from ``pointIds``
    are built, which is all the cure needs and much cheaper than grouping the whole mesh.

    Args:
        mesh: The mesh whose points are grouped.
        pointIds: The points to group, typically the corners of the fault faces.
        tolerance: Distance below which two points are considered collocated.

    Returns:
        A ``representative`` array mapping each point id to the lowest id of its group (to itself
        for a point outside of any built group), and a mapping from that representative id to every
        point id of the group.
    """
    coordinates: NDArray[ np.float64 ] = vtk_to_numpy( mesh.GetPoints().GetData() )
    locator = vtkStaticPointLocator()
    locator.SetDataSet( mesh )
    locator.BuildLocator()

    # Union-find rather than one bucket per query, so that a chain of near-coincident copies whose
    # ends are further apart than the tolerance still ends up in a single group.
    unionFind = _UnionFind()
    neighbors = vtkIdList()
    queried: set[ int ] = set()
    for pointId in pointIds:
        if pointId in queried:
            continue
        queried.add( pointId )
        locator.FindPointsWithinRadius( tolerance, coordinates[ pointId ], neighbors )
        unionFind.find( pointId )
        for k in range( neighbors.GetNumberOfIds() ):
            unionFind.union( pointId, neighbors.GetId( k ) )

    representative: NDArray[ np.int64 ] = np.arange( mesh.GetNumberOfPoints(), dtype=np.int64 )
    members: dict[ int, list[ int ] ] = defaultdict( list )
    for pointId in unionFind.m_parent:
        members[ unionFind.find( pointId ) ].append( pointId )
    groups: dict[ int, list[ int ] ] = {}
    for group in members.values():
        group.sort()
        root = group[ 0 ]
        representative[ group ] = root
        groups[ root ] = group
    return representative, groups


def computeFaceNormals( mesh: vtkUnstructuredGrid, tagArray: str, tagValue: int ) -> dict[ int, NDArray[ np.float64 ] ]:
    """Compute a consistently oriented normal for every 2D face carrying a single fault value.

    Orientation is propagated per fault value, so that a junction between two faults does not force
    the two surfaces to share an orientation.

    Args:
        mesh: The mesh holding the fault faces.
        tagArray: Name of the cell-data array tagging the fault faces.
        tagValue: The fault value to orient.

    Returns:
        A mapping from cell id to unit normal, restricted to the faces of that fault value. Faces
        that the geometry extraction dropped are absent.
    """
    tags = vtk_to_numpy( mesh.GetCellData().GetArray( tagArray ) ).astype( int )
    cellTypes = vtk_to_numpy( mesh.GetCellTypesArray() )
    isFaultFace = ( ( tags == tagValue ) & np.isin( cellTypes, __CELL_TYPES_2D ) ).astype( np.int8 )
    if isFaultFace.sum() == 0:
        return {}

    faultFaceArray = numpy_to_vtk( isFaultFace, deep=True )
    faultFaceArray.SetName( __IS_FAULT_FACE_ARRAY )
    mesh.GetCellData().AddArray( faultFaceArray )
    originalCellArray = numpy_to_vtk( np.arange( mesh.GetNumberOfCells(), dtype=np.int64 ), deep=True )
    originalCellArray.SetName( __ORIGINAL_CELL_ARRAY )
    mesh.GetCellData().AddArray( originalCellArray )
    try:
        threshold = vtk.vtkThreshold()
        threshold.SetInputData( mesh )
        threshold.SetInputArrayToProcess( 0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, __IS_FAULT_FACE_ARRAY )
        threshold.SetLowerThreshold( 0.5 )
        threshold.SetUpperThreshold( 1.5 )
        threshold.SetThresholdFunction( vtk.vtkThreshold.THRESHOLD_BETWEEN )
        threshold.Update()

        geometry = vtk.vtkGeometryFilter()
        geometry.SetInputData( threshold.GetOutput() )
        geometry.Update()

        normalsFilter = vtk.vtkPolyDataNormals()
        normalsFilter.SetInputData( geometry.GetOutput() )
        normalsFilter.SetConsistency( True )
        normalsFilter.SetAutoOrientNormals( False )
        normalsFilter.SetComputeCellNormals( True )
        normalsFilter.SetComputePointNormals( False )
        normalsFilter.SetSplitting( False )
        normalsFilter.Update()
        oriented = normalsFilter.GetOutput()
    finally:
        mesh.GetCellData().RemoveArray( __IS_FAULT_FACE_ARRAY )
        mesh.GetCellData().RemoveArray( __ORIGINAL_CELL_ARRAY )

    normals = vtk_to_numpy( oriented.GetCellData().GetNormals() )
    originalCells = vtk_to_numpy( oriented.GetCellData().GetArray( __ORIGINAL_CELL_ARRAY ) ).astype( np.int64 )
    return { int( originalCells[ i ] ): normals[ i ] for i in range( len( originalCells ) ) }


def markHoleBorderFaces( numCells: int, facesByValue: dict[ int, list[ int ] ], offsets: NDArray[ np.int64 ],
                         connectivity: NDArray[ np.int64 ] ) -> NDArray[ np.int8 ]:
    """Flag the faces that border a residual hole of their fault surface.

    A hole is any boundary-edge loop of a fault other than its outer perimeter. Boundary edges are
    computed from the cured raw connectivity, so coincident collocated points stay distinct and the
    seams are not welded shut.

    Args:
        numCells: Total number of cells in the mesh.
        facesByValue: Fault value to the list of its 2D cell ids.
        offsets: Cell connectivity offsets of the (cured) mesh.
        connectivity: Cell connectivity of the (cured) mesh.

    Returns:
        A per-cell flag, 1 on the faces bordering a residual hole and 0 elsewhere.
    """
    onHole: NDArray[ np.int8 ] = np.zeros( numCells, dtype=np.int8 )
    for faces in facesByValue.values():
        edgeUseCount: dict[ tuple[ int, int ], int ] = defaultdict( int )
        edgeOwner: dict[ tuple[ int, int ], int ] = {}
        for cellId in faces:
            start, end = int( offsets[ cellId ] ), int( offsets[ cellId + 1 ] )
            facePoints = [ int( pointId ) for pointId in connectivity[ start:end ] ]
            numFacePoints = len( facePoints )
            for k in range( numFacePoints ):
                a, b = facePoints[ k ], facePoints[ ( k + 1 ) % numFacePoints ]
                edge = ( a, b ) if a < b else ( b, a )
                edgeUseCount[ edge ] += 1
                edgeOwner[ edge ] = cellId
        boundaryEdges = [ edge for edge, count in edgeUseCount.items() if count == 1 ]
        if not boundaryEdges:
            continue

        unionFind = _UnionFind()
        for a, b in boundaryEdges:
            unionFind.union( a, b )
        loops: dict[ int, list[ tuple[ int, int ] ] ] = defaultdict( list )
        for edge in boundaryEdges:
            loops[ unionFind.find( edge[ 0 ] ) ].append( edge )
        # The longest boundary loop is the fault perimeter; any other loop is a hole.
        perimeter = max( loops, key=lambda root: len( loops[ root ] ) )
        for root, edges in loops.items():
            if root == perimeter:
                continue
            for edge in edges:
                onHole[ edgeOwner[ edge ] ] = 1
    return onHole


def _findTagValues( mesh: vtkUnstructuredGrid, tagArray: str, tagValues: tuple[ int, ...] ) -> list[ int ]:
    """Return the fault values to cure, defaulting to every non-zero value carried by a 2D cell.

    Args:
        mesh: The mesh to inspect.
        tagArray: Name of the cell-data array tagging the fault faces.
        tagValues: The requested values, possibly empty.

    Returns:
        The sorted list of fault values to process.
    """
    if tagValues:
        return sorted( set( tagValues ) )
    tags = vtk_to_numpy( mesh.GetCellData().GetArray( tagArray ) ).astype( int )
    cellTypes = vtk_to_numpy( mesh.GetCellTypesArray() )
    found = np.unique( tags[ np.isin( cellTypes, __CELL_TYPES_2D ) ] )
    return [ int( value ) for value in found if value != 0 ]


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Rewrite every wrong-side fault face onto the coincident reference-side 3D cell face.

    The mesh is modified in place: the fault face connectivity is rewritten and the "faultSide" and
    "onHole" cell arrays are added.

    Args:
        mesh: The post-split domain mesh to cure.
        options: The cure options.

    Returns:
        The per-fault and overall statistics of the cure.

    Raises:
        ValueError: If ``options.tagArray`` is not a cell-data array of the mesh.
    """
    if mesh.GetCellData().GetArray( options.tagArray ) is None:
        raise ValueError( f"Cell array \"{options.tagArray}\" is not in the mesh." )
    values: list[ int ] = _findTagValues( mesh, options.tagArray, options.tagValues )
    if not values:
        setupLogger.warning( f"No non-zero value of \"{options.tagArray}\" is carried by a 2D cell." )

    mesh.BuildLinks()
    numCells: int = mesh.GetNumberOfCells()
    points: NDArray[ np.float64 ] = vtk_to_numpy( mesh.GetPoints().GetData() )
    tags = vtk_to_numpy( mesh.GetCellData().GetArray( options.tagArray ) ).astype( int )
    cellTypes = vtk_to_numpy( mesh.GetCellTypesArray() )
    is2d = np.isin( cellTypes, __CELL_TYPES_2D )
    offsets: NDArray[ np.int64 ] = vtk_to_numpy( mesh.GetCells().GetOffsetsArray() ).astype( np.int64 )
    connectivity: NDArray[ np.int64 ] = vtk_to_numpy( mesh.GetCells().GetConnectivityArray() ).astype( np.int64 ).copy()

    facesByValue: dict[ int, list[ int ] ] = {
        tagValue: [ int( cellId ) for cellId in np.where( ( tags == tagValue ) & is2d )[ 0 ] ]
        for tagValue in values
    }
    faultPointIds: set[ int ] = set()
    for faces in facesByValue.values():
        for cellId in faces:
            faultPointIds.update(
                int( pointId ) for pointId in connectivity[ int( offsets[ cellId ] ):int( offsets[ cellId + 1 ] ) ] )
    setupLogger.info( f"Grouping the {len( faultPointIds )} fault nodes collocated within {options.tolerance}." )
    representative, collocatedGroups = buildCollocatedGroups( mesh, sorted( faultPointIds ), options.tolerance )

    faceIds, neighborIds, cellPointIds, pointCellIds = vtkIdList(), vtkIdList(), vtkIdList(), vtkIdList()

    def centroid( cellId: int ) -> NDArray[ np.float64 ]:
        mesh.GetCellPoints( cellId, cellPointIds )
        return points[ [ cellPointIds.GetId( k ) for k in range( cellPointIds.GetNumberOfIds() ) ] ].mean( axis=0 )

    faultSide: NDArray[ np.int8 ] = np.zeros( numCells, dtype=np.int8 )
    perValueCounts: dict[ int, list[ int ] ] = {}
    for tagValue in values:
        normals = computeFaceNormals( mesh, options.tagArray, tagValue )
        faces = facesByValue[ tagValue ]
        numMoved, numAlreadyCorrect, numDegenerate, numSkipped = 0, 0, 0, 0
        setupLogger.info( f"Curing {len( faces )} faces of \"{options.tagArray}\" == {tagValue}." )
        for cellId in faces:
            normal = normals.get( cellId )
            if normal is None:
                numSkipped += 1
                continue
            start, end = int( offsets[ cellId ] ), int( offsets[ cellId + 1 ] )
            facePointIds = connectivity[ start:end ]
            faceCentroid = points[ facePointIds ].mean( axis=0 )

            mesh.GetCellNeighbors( cellId, _toIdList( faceIds, facePointIds ), neighborIds )
            owner = -1
            for j in range( neighborIds.GetNumberOfIds() ):
                neighborId = neighborIds.GetId( j )
                if mesh.GetCell( neighborId ).GetCellDimension() == 3:
                    owner = neighborId
                    break
            if owner < 0:
                numSkipped += 1
                continue
            if np.dot( centroid( owner ) - faceCentroid, normal ) > 0:  # Already on the reference side.
                faultSide[ cellId ] = 1
                numAlreadyCorrect += 1
                continue

            # Look for the real 3D-cell face coincident with this one on the +normal side. Scanning
            # every collocated copy of every corner also resolves fault junctions, where a node has
            # 3 or 4 copies and no two-way twin exists.
            target = frozenset( int( representative[ pointId ] ) for pointId in facePointIds )
            candidates: set[ int ] = set()
            for pointId in facePointIds:
                for collocatedId in collocatedGroups[ int( representative[ pointId ] ) ]:
                    mesh.GetPointCells( collocatedId, pointCellIds )
                    for j in range( pointCellIds.GetNumberOfIds() ):
                        candidates.add( pointCellIds.GetId( j ) )

            referenceFace: list[ int ] | None = None
            for candidateId in candidates:
                if candidateId == owner:
                    continue
                candidate = mesh.GetCell( candidateId )
                if candidate.GetCellDimension() != 3:
                    continue
                if np.dot( centroid( candidateId ) - faceCentroid, normal ) <= 0:
                    continue
                for faceIndex in range( candidate.GetNumberOfFaces() ):
                    candidatePointIds = candidate.GetFace( faceIndex ).GetPointIds()
                    numCandidatePoints = candidatePointIds.GetNumberOfIds()
                    if numCandidatePoints != ( end - start ):
                        continue
                    candidateIds = [ candidatePointIds.GetId( k ) for k in range( numCandidatePoints ) ]
                    if frozenset( int( representative[ pointId ] ) for pointId in candidateIds ) == target:
                        referenceFace = candidateIds
                        break
                if referenceFace is not None:
                    break

            if referenceFace is None:
                # No single side exists here, typically along a fault-fault intersection line.
                faultSide[ cellId ] = -1
                numDegenerate += 1
            else:
                connectivity[ start:end ] = np.array( referenceFace, dtype=np.int64 )
                faultSide[ cellId ] = 1
                numMoved += 1
        perValueCounts[ tagValue ] = [ numMoved, numAlreadyCorrect, numDegenerate, numSkipped ]

    onHole = markHoleBorderFaces( numCells, facesByValue, offsets, connectivity )

    cells = vtk.vtkCellArray()
    cells.SetData( numpy_to_vtkIdTypeArray( np.ascontiguousarray( offsets ), deep=True ),
                   numpy_to_vtkIdTypeArray( np.ascontiguousarray( connectivity ), deep=True ) )
    mesh.SetCells( numpy_to_vtk( np.ascontiguousarray( cellTypes ), deep=True, array_type=vtk.VTK_UNSIGNED_CHAR ),
                   cells )

    faultSideArray = numpy_to_vtk( faultSide, deep=True )
    faultSideArray.SetName( FAULT_SIDE_ARRAY )
    mesh.GetCellData().AddArray( faultSideArray )
    onHoleArray = numpy_to_vtk( onHole, deep=True )
    onHoleArray.SetName( ON_HOLE_ARRAY )
    mesh.GetCellData().AddArray( onHoleArray )
    for data, arrayName in ( ( mesh.GetPointData(), "GLOBAL_IDS_POINTS" ), ( mesh.GetCellData(), "GLOBAL_IDS_CELLS" ) ):
        if data.GetArray( arrayName ) is not None:
            data.SetGlobalIds( data.GetArray( arrayName ) )

    faults: list[ FaultResult ] = []
    for tagValue in values:
        numMoved, numAlreadyCorrect, numDegenerate, numSkipped = perValueCounts[ tagValue ]
        faces = facesByValue[ tagValue ]
        faults.append(
            FaultResult( tagValue=tagValue,
                         numFaces=len( faces ),
                         numMovedFaces=numMoved,
                         numAlreadyCorrectFaces=numAlreadyCorrect,
                         numDegenerateFaces=numDegenerate,
                         numSkippedFaces=numSkipped,
                         numHoleBorderFaces=int( onHole[ faces ].sum() ) if faces else 0 ) )

    return Result( faults=tuple( faults ),
                   numFaultFaces=sum( fault.numFaces for fault in faults ),
                   numMovedFaces=sum( fault.numMovedFaces for fault in faults ),
                   numDegenerateFaces=sum( fault.numDegenerateFaces for fault in faults ),
                   numSkippedFaces=sum( fault.numSkippedFaces for fault in faults ),
                   numHoleBorderFaces=sum( fault.numHoleBorderFaces for fault in faults ) )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Read a split VTU mesh, cure its one-sided fault issue and write the result.

    Args:
        vtuInputFile: Path to the post-split domain VTU mesh.
        options: The cure options.

    Returns:
        The per-fault and overall statistics of the cure.
    """
    setupLogger.info( f"Reading mesh from \"{vtuInputFile}\"." )
    mesh = readUnstructuredGrid( vtuInputFile )
    result = meshAction( mesh, options )
    setupLogger.info( f"Writing cured mesh to \"{options.outputFile.output}\"." )
    writeMesh( mesh, options.outputFile )
    return result
