# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import networkx
from numpy import empty, ones, zeros
from tqdm import tqdm
from typing import Collection, Iterable, Mapping, Optional, Sequence, TypeAlias
from vtk import vtkDataArray
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkCell, vtkCellArray, vtkPolygon, vtkUnstructuredGrid, VTK_POLYGON,
                                            VTK_POLYHEDRON )
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.util.vtkConstants import VTK_ID_TYPE
from geos.mesh_doctor.actions.vtkPolyhedron import FaceStream
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh.utils.arrayHelpers import hasArray
from geos.mesh.utils.genericHelpers import toVtkIdList, vtkIter

IDMapping: TypeAlias = Mapping[ int, int ]
CellsPointsCoords: TypeAlias = dict[ int, list[ tuple[ float ] ] ]
Coordinates3D: TypeAlias = tuple[ float, float, float ]


class FracturePolicy( Enum ):
    FIELD = 0
    INTERNAL_SURFACES = 1


@dataclass( frozen=True )
class Options:
    policy: FracturePolicy
    field: str
    fieldValuesCombined: frozenset[ int ]
    fieldValuesPerFracture: list[ frozenset[ int ] ]
    meshVtkOutput: VtkOutput
    allFracturesVtkOutput: list[ VtkOutput ]


@dataclass( frozen=True )
class Result:
    info: str


@dataclass( frozen=True )
class FractureInfo:
    nodeToCells: Mapping[ int, Iterable[ int ] ]  # For each Fracture_ node, gives all the cells that use this node.
    faceNodes: Iterable[ Collection[ int ] ]  # For each fracture face, returns the nodes of this face
    faceCellId: Iterable[ int ]  # For each fracture face, returns the corresponding id of the cell in the mesh


def buildNodeToCells( mesh: vtkUnstructuredGrid,
                      faceNodes: Iterable[ Iterable[ int ] ] ) -> Mapping[ int, Iterable[ int ] ]:
    """Builds the mapping from each fracture node to the cells that use this node.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        faceNodes (Iterable[ Iterable[ int ] ]): The nodes of each face of the fracture.

    Returns:
        Mapping[ int, Iterable[ int ] ]: A mapping from each fracture node to the cells that use this node.
    """
    # TODO normally, just a list and not a set should be enough.
    nodeToCells: dict[ int, set[ int ] ] = defaultdict( set )

    fractureNodes: set[ int ] = set()
    for fns in faceNodes:
        for n in fns:
            fractureNodes.add( n )

    for cellId in tqdm( range( mesh.GetNumberOfCells() ), desc="Computing the node to cells mapping" ):
        cellPoints: frozenset[ int ] = frozenset( vtkIter( mesh.GetCell( cellId ).GetPointIds() ) )
        intersection: Iterable[ int ] = cellPoints & fractureNodes
        for node in intersection:
            nodeToCells[ node ].add( cellId )

    return nodeToCells


def __buildFractureInfoFromFields( mesh: vtkUnstructuredGrid, f: Sequence[ int ],
                                   fieldValues: frozenset[ int ] ) -> FractureInfo:
    """Build the fracture info from field values.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        f (Sequence[ int ]): The field values for each cell.
        fieldValues (frozenset[ int ]): The set of field values to consider.

    Returns:
        FractureInfo: The fracture information.
    """
    cellsToFaces: dict[ int, list[ int ] ] = defaultdict( list )
    # For each face of each cell, we search for the unique neighbor cell (if it exists).
    # Then, if the 2 values of the two cells match the field requirements,
    # we store the cell and its local face index: this is indeed part of the surface that we'll need to be split.
    cell: vtkCell
    for cellId in tqdm( range( mesh.GetNumberOfCells() ), desc="Computing the cell to faces mapping" ):
        # No need to consider a cell if its field value is not in the target range.
        if f[ cellId ] not in fieldValues:
            continue
        cell = mesh.GetCell( cellId )
        for i in range( cell.GetNumberOfFaces() ):
            neighborCellIds = vtkIdList()
            mesh.GetCellNeighbors( cellId, cell.GetFace( i ).GetPointIds(), neighborCellIds )
            assert neighborCellIds.GetNumberOfIds() < 2
            for j in range( neighborCellIds.GetNumberOfIds() ):  # It's 0 or 1...
                neighborCellId = neighborCellIds.GetId( j )
                if f[ neighborCellId ] != f[ cellId ] and f[ neighborCellId ] in fieldValues:
                    # TODO add this (cellIds, faceId) information to the fractureInfo?
                    cellsToFaces[ cellId ].append( i )
    faceNodes: list[ Collection[ int ] ] = []
    faceNodesHashes: set[ frozenset[ int ] ] = set()  # A temporary not to add multiple times the same face.
    for cellId, facesIds in tqdm( cellsToFaces.items(), desc="Extracting the faces of the fractures" ):
        cell = mesh.GetCell( cellId )
        for faceId in facesIds:
            fn: Collection[ int ] = tuple( vtkIter( cell.GetFace( faceId ).GetPointIds() ) )
            fnh = frozenset( fn )
            if fnh not in faceNodesHashes:
                faceNodesHashes.add( fnh )
                faceNodes.append( fn )
    nodeToCells: Mapping[ int, Iterable[ int ] ] = buildNodeToCells( mesh, faceNodes )
    faceCellId: list = []  # no cell of the mesh corresponds to that face when fracture policy is 'field'

    return FractureInfo( nodeToCells=nodeToCells, faceNodes=faceNodes, faceCellId=faceCellId )


def __buildFractureInfoFromInternalSurfaces( mesh: vtkUnstructuredGrid, f: Sequence[ int ],
                                             fieldValues: frozenset[ int ] ) -> FractureInfo:
    """Build the fracture info from internal surfaces defined by the field values.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        f (Sequence[ int ]): The field values for each cell.
        fieldValues (frozenset[ int ]): The set of field values to consider.

    Returns:
        FractureInfo: The fracture information.
    """
    nodeToCells: dict[ int, list[ int ] ] = defaultdict( list )
    faceNodes: list[ Collection[ int ] ] = []
    faceCellId: list[ int ] = []
    for cellId in tqdm( range( mesh.GetNumberOfCells() ), desc="Computing the face to nodes mapping" ):
        cell = mesh.GetCell( cellId )
        if cell.GetCellDimension() == 2 and f[ cellId ] in fieldValues:
            nodes = []
            for v in range( cell.GetNumberOfPoints() ):
                pointId: int = cell.GetPointId( v )
                nodeToCells[ pointId ] = []
                nodes.append( pointId )
            faceNodes.append( tuple( nodes ) )
            faceCellId.append( cellId )

    for cellId in tqdm( range( mesh.GetNumberOfCells() ), desc="Computing the node to cells mapping" ):
        cell = mesh.GetCell( cellId )
        if cell.GetCellDimension() == 3:
            for v in range( cell.GetNumberOfPoints() ):
                if cell.GetPointId( v ) in nodeToCells:
                    nodeToCells[ cell.GetPointId( v ) ].append( cellId )

    return FractureInfo( nodeToCells=nodeToCells, faceNodes=faceNodes, faceCellId=faceCellId )


def buildFractureInfo( mesh: vtkUnstructuredGrid,
                       options: Options,
                       combinedFractures: bool,
                       fractureId: int = 0 ) -> FractureInfo:
    """For a given mesh and options, builds the fracture information.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        options (Options): Options for processing.
        combinedFractures (bool): If True, considers all fractures together. Else, only the fracture with id.
        fractureId (int, optional): The fracture id to consider if combinedFractures is False. Defaults to 0.

    Raises:
        ValueError: If the field does not exist in the mesh.

    Returns:
        FractureInfo: The fracture information.
    """
    field = options.field
    fieldValues = options.fieldValuesCombined if combinedFractures else options.fieldValuesPerFracture[ fractureId ]
    cellData = mesh.GetCellData()
    if cellData.HasArray( field ):
        f = vtk_to_numpy( cellData.GetArray( field ) )
    else:
        raise ValueError( f"Cell field {field} does not exist in mesh, nothing done" )

    if options.policy == FracturePolicy.FIELD:
        return __buildFractureInfoFromFields( mesh, f, fieldValues )
    elif options.policy == FracturePolicy.INTERNAL_SURFACES:
        return __buildFractureInfoFromInternalSurfaces( mesh, f, fieldValues )


def buildCellToCellGraph( mesh: vtkUnstructuredGrid, fracture: FractureInfo ) -> networkx.Graph:
    """Connects all the cells that touch the fracture by at least one node.

    Two cells are connected when they share at least a face which is not a face of the fracture.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        fracture (FractureInfo): The fracture info.

    Returns:
        networkx.Graph: The graph: each node of this graph is the index of the cell.
    There's an edge between two nodes of the graph if the cells share a face.
    """
    # Faces are identified by their nodes. But the order of those nodes may vary while referring to the same face.
    # Therefore we compute some kinds of hashes of those face to easily detect if a face is part of the fracture.
    tmp: list[ frozenset[ int ] ] = []
    for fn in fracture.faceNodes:
        tmp.append( frozenset( fn ) )
    faceHashes: frozenset[ frozenset[ int ] ] = frozenset( tmp )

    # We extract the list of the cells that touch the fracture by at least one node.
    cells: set[ int ] = set()
    for cellIds in fracture.nodeToCells.values():
        for cellId in cellIds:
            cells.add( cellId )

    # Using the last precomputed containers, we're now building the dict which connects
    # every face (hash) of the fracture to the cells that touch the face...
    faceToCells: dict[ frozenset[ int ], list[ int ] ] = defaultdict( list )
    for cellId in tqdm( cells, desc="Computing the cell to cell graph" ):
        cell: vtkCell = mesh.GetCell( cellId )
        for faceId in range( cell.GetNumberOfFaces() ):
            faceHash: frozenset[ int ] = frozenset( vtkIter( cell.GetFace( faceId ).GetPointIds() ) )
            if faceHash not in faceHashes:
                faceToCells[ faceHash ].append( cellId )

    # ... eventually, when a face touches two cells, this means that those two cells share the same face
    # and should be connected in the final cell to cell graph.
    cellToCell = networkx.Graph()
    cellToCell.add_nodes_from( cells )
    cellToCell.add_edges_from( filter( lambda cs: len( cs ) == 2, faceToCells.values() ) )

    return cellToCell


def _identifySplit( numPoints: int, cellToCell: networkx.Graph,
                    nodeToCells: Mapping[ int, Iterable[ int ] ] ) -> Mapping[ int, IDMapping ]:
    """For each cell, compute the node indices replacements.

    Args:
        numPoints (int): The number of points in the whole mesh (not the fracture).
        cellToCell (networkx.Graph): The cell to cell graph (connection through common faces).
        nodeToCells (Mapping[ int, Iterable[ int ] ]): Maps the nodes of the fracture to the cells relying on this node.

    Returns:
        Mapping[ int, IDMapping ]: For each cell (first key), returns a mapping from the current index
                                and the new index that should replace the current index.
    Note that the current index and the new index can be identical: no replacement should be done then.
    """

    class NewIndex:
        """Returns the next available index.

        Note that the first time an index is met, the index itself is returned:
        we do not want to change an index if we do not have to.
        """

        def __init__( self, numNodes: int ) -> None:
            self.__currentLastIndex = numNodes - 1
            self.__seen: set[ int ] = set()

        def __call__( self, index: int ) -> int:
            if index in self.__seen:
                self.__currentLastIndex += 1
                return self.__currentLastIndex
            else:
                self.__seen.add( index )
                return index

    buildNewIndex = NewIndex( numPoints )
    result: dict[ int, dict[ int, int ] ] = defaultdict( dict )
    # Iteration over `sorted` nodes to have a predictable result for tests.
    for node, cells in tqdm( sorted( nodeToCells.items() ), desc="Identifying the node splits" ):
        for connectedCells in networkx.connected_components( cellToCell.subgraph( cells ) ):
            # Each group of connect cells need around `node` must consider the same `node`.
            # Separate groups must have different (duplicated) nodes.
            newIndex: int = buildNewIndex( node )
            for cell in connectedCells:
                result[ cell ][ node ] = newIndex
    return result


def __copyFieldsSplitMesh( oldMesh: vtkUnstructuredGrid, splitMesh: vtkUnstructuredGrid,
                           addedPointsWithOldId: list[ tuple[ int, int ] ] ) -> None:
    """Copies the fields from the old mesh to the new one. Point data will be duplicated for collocated nodes.

    Args:
        oldMesh (vtkUnstructuredGrid): The mesh before the split.
        splitMesh (vtkUnstructuredGrid): The mesh after the split. Will receive the fields in place.
        addedPointsWithOldId (list[ tuple[ int, int ] ]): List of tuples (newId, oldId) for each duplicated point.
    """
    # Copying the cell data. The cells are the same, just their nodes support have changed.
    inputCellData = oldMesh.GetCellData()
    for i in range( inputCellData.GetNumberOfArrays() ):
        inputArray: vtkDataArray = inputCellData.GetArray( i )
        setupLogger.info( f"Copying cell field \"{inputArray.GetName()}\"." )
        tmp = inputArray.NewInstance()
        tmp.DeepCopy( inputArray )
        splitMesh.GetCellData().AddArray( inputArray )

    # Copying field data. This data is a priori not related to geometry.
    inputFieldData = oldMesh.GetFieldData()
    for i in range( inputFieldData.GetNumberOfArrays() ):
        inputArray = inputFieldData.GetArray( i )
        setupLogger.info( f"Copying field data \"{inputArray.GetName()}\"." )
        tmp = inputArray.NewInstance()
        tmp.DeepCopy( inputArray )
        splitMesh.GetFieldData().AddArray( inputArray )

    # Copying copy data. Need to take into account the new points.
    inputPointData = oldMesh.GetPointData()
    newNumberPoints: int = splitMesh.GetNumberOfPoints()
    for i in range( inputPointData.GetNumberOfArrays() ):
        oldPointsArray = vtk_to_numpy( inputPointData.GetArray( i ) )
        name: str = inputPointData.GetArrayName( i )
        setupLogger.info( f"Copying point data \"{name}\"." )
        oldNrows: int = oldPointsArray.shape[ 0 ]
        oldNcols: int = 1 if len( oldPointsArray.shape ) == 1 else oldPointsArray.shape[ 1 ]
        # Reshape oldPointsArray if it is 1-dimensional
        if len( oldPointsArray.shape ) == 1:
            oldPointsArray = oldPointsArray.reshape( ( oldNrows, 1 ) )
        newPointsArray = empty( ( newNumberPoints, oldNcols ), dtype=oldPointsArray.dtype )
        newPointsArray[ :oldNrows, : ] = oldPointsArray
        for newAndOldId in addedPointsWithOldId:
            newPointsArray[ newAndOldId[ 0 ], : ] = oldPointsArray[ newAndOldId[ 1 ], : ]
        # Reshape the VTK array to match the original dimensions
        if oldNcols > 1:
            vtkArray = numpy_to_vtk( newPointsArray.flatten() )
            vtkArray.SetNumberOfComponents( oldNcols )
            vtkArray.SetNumberOfTuples( newNumberPoints )
        else:
            vtkArray = numpy_to_vtk( newPointsArray )
        vtkArray.SetName( name )
        splitMesh.GetPointData().AddArray( vtkArray )


def __copyFieldsFractureMesh( oldMesh: vtkUnstructuredGrid, fractureMesh: vtkUnstructuredGrid, faceCellId: list[ int ],
                              node3dToNode2d: IDMapping ) -> None:
    """Copies the fields from the old mesh to the new fracture when using internalSurfaces policy.

    Args:
        oldMesh (vtkUnstructuredGrid): The mesh before the split.
        fractureMesh (vtkUnstructuredGrid): The fracture mesh generated from the fractureInfo.
        faceCellId (list[ int ]): The list of cell IDs that define the fracture faces.
        node3dToNode2d (IDMapping): A mapping from 3D node IDs to 2D node IDs.
    """
    # No copy of field data will be done with the fracture mesh because may lose its relevance compared to the splitted.
    # Copying the cell data. The interesting cells are the ones stored in faceCellId.
    newNumberCells: int = fractureMesh.GetNumberOfCells()
    inputCellData = oldMesh.GetCellData()
    for i in range( inputCellData.GetNumberOfArrays() ):
        oldCellsArray = vtk_to_numpy( inputCellData.GetArray( i ) )
        oldNrows: int = oldCellsArray.shape[ 0 ]
        if len( oldCellsArray.shape ) == 1:
            oldCellsArray = oldCellsArray.reshape( ( oldNrows, 1 ) )
        name: str = inputCellData.GetArrayName( i )
        setupLogger.info( f"Copying cell data \"{name}\"." )
        newArray = oldCellsArray[ faceCellId, : ]
        # Reshape the VTK array to match the original dimensions
        oldNcols: int = 1 if len( oldCellsArray.shape ) == 1 else oldCellsArray.shape[ 1 ]
        if oldNcols > 1:
            vtkArray = numpy_to_vtk( newArray.flatten() )
            vtkArray.SetNumberOfComponents( oldNcols )
            vtkArray.SetNumberOfTuples( newNumberCells )
        else:
            vtkArray = numpy_to_vtk( newArray )
        vtkArray.SetName( name )
        fractureMesh.GetCellData().AddArray( vtkArray )

    newNumberPoints: int = fractureMesh.GetNumberOfPoints()
    inputPointData = oldMesh.GetPointData()
    for i in range( inputPointData.GetNumberOfArrays() ):
        oldPointsArray = vtk_to_numpy( inputPointData.GetArray( i ) )
        oldNrows = oldPointsArray.shape[ 0 ]
        if len( oldPointsArray.shape ) == 1:
            oldPointsArray = oldPointsArray.reshape( ( oldNrows, 1 ) )
        name = inputPointData.GetArrayName( i )
        setupLogger.info( f"Copying point data \"{name}\"." )
        newArray = oldPointsArray[ list( node3dToNode2d.keys() ), : ]
        oldNcols = 1 if len( oldPointsArray.shape ) == 1 else oldPointsArray.shape[ 1 ]
        if oldNcols > 1:
            vtkArray = numpy_to_vtk( newArray.flatten() )
            vtkArray.SetNumberOfComponents( oldNcols )
            vtkArray.SetNumberOfTuples( newNumberPoints )
        else:
            vtkArray = numpy_to_vtk( newArray )
        vtkArray.SetName( name )
        fractureMesh.GetPointData().AddArray( vtkArray )


def __performSplit( oldMesh: vtkUnstructuredGrid, cellToNodeMapping: Mapping[ int, IDMapping ] ) -> vtkUnstructuredGrid:
    """Split the main 3d mesh based on the node duplication information contained in @p cellToNodeMapping.

    Args:
        oldMesh (vtkUnstructuredGrid): The main 3d mesh.
        cellToNodeMapping (Mapping[ int, IDMapping ]): For each cell,
        gives the nodes that must be duplicated and their new index.

    Returns:
        vtkUnstructuredGrid: The main 3d mesh split at the fracture location.
    """
    addedPoints: set[ int ] = set()
    addedPointsWithOldId: list[ tuple[ int, int ] ] = []
    for nodeMapping in cellToNodeMapping.values():
        for i, o in nodeMapping.items():
            if i != o:
                addedPoints.add( o )
                addedPointsWithOldId.append( ( o, i ) )
    numNewPoints: int = oldMesh.GetNumberOfPoints() + len( addedPoints )

    # Creating the new points for the new mesh.
    oldPoints: vtkPoints = oldMesh.GetPoints()
    newPoints = vtkPoints()
    newPoints.SetDataType( oldPoints.GetDataType() )  # Preserve precision from input mesh
    newPoints.SetNumberOfPoints( numNewPoints )
    collocatedNodes = ones( numNewPoints, dtype=int ) * -1
    # Copying old points into the new container.
    for p in range( oldPoints.GetNumberOfPoints() ):
        newPoints.SetPoint( p, oldPoints.GetPoint( p ) )
        collocatedNodes[ p ] = p
    # Creating the new collocated/duplicated points based on the old points positions.
    for nodeMappingDup in cellToNodeMapping.values():
        for i, o in nodeMappingDup.items():
            if i != o:
                newPoints.SetPoint( o, oldPoints.GetPoint( i ) )
                collocatedNodes[ o ] = i
    collocatedNodes.flags.writeable = False

    # For each 2D cell, find its adjacent 3D cell and copy the node mapping
    setupLogger.info( "Building 2D cell mappings from adjacent 3D cells..." )
    cell2dToMapping: dict[ int, dict[ int, int ] ] = {}

    for c in tqdm( range( oldMesh.GetNumberOfCells() ), desc="Matching 2D to 3D cells" ):
        cell2d: vtkCell = oldMesh.GetCell( c )
        if cell2d.GetCellDimension() != 2:
            continue

        # Get the point IDs of this 2D cell
        pointIds = cell2d.GetPointIds()

        # Find a 3D cell neighbor
        neighborIds = vtkIdList()
        oldMesh.GetCellNeighbors( c, pointIds, neighborIds )

        # Use the first 3D neighbor's mapping
        for i in range( neighborIds.GetNumberOfIds() ):
            neighborId = neighborIds.GetId( i )
            neighborCell = oldMesh.GetCell( neighborId )

            if neighborCell.GetCellDimension() == 3 and neighborId in cellToNodeMapping:
                # This 3D cell has a mapping - use it for the 2D cell
                # Get the 2D cell's point IDs
                cell2dPointIds = set( vtkIter( pointIds ) )

                # Only copy mappings for nodes that belong to the 2D cell
                neighborMapping = cellToNodeMapping[ neighborId ]
                cell2dToMapping[ c ] = {
                    node: newNode
                    for node, newNode in neighborMapping.items() if node in cell2dPointIds
                }
                break

    setupLogger.info( f"Found mappings for {len(cell2dToMapping)} 2D cells" )

    # Merge 2D mappings into main mapping
    combinedMapping = dict( cellToNodeMapping )
    combinedMapping.update( cell2dToMapping )

    # We are creating a new mesh.
    # The cells will be the same, except that their nodes may be duplicated or renumbered nodes.
    # In vtk, the polyhedron and the standard cells are managed differently.
    # Also, it looks like the internal representation is being modified
    # (see https://gitlab.kitware.com/vtk/vtk/-/merge_requests/9812)
    # so we'll try nothing fancy for the moment.
    # Maybe in the future using a `DeepCopy` of the vtkCellArray can be considered?
    # The cell point ids could be modified in place then.
    newMesh = oldMesh.NewInstance()
    newMesh.SetPoints( newPoints )
    newMesh.Allocate( oldMesh.GetNumberOfCells() )

    for c in tqdm( range( oldMesh.GetNumberOfCells() ), desc="Performing the mesh split" ):
        cellNodeMapping: IDMapping = combinedMapping.get( c, {} )
        cell: vtkCell = oldMesh.GetCell( c )
        cellType: int = cell.GetCellType()
        # For polyhedron, we'll manipulate the face stream directly.
        if cellType == VTK_POLYHEDRON:
            faceStream = vtkIdList()
            oldMesh.GetFaceStream( c, faceStream )
            newFaceNodes: list[ list[ int ] ] = []
            for faceNodes in FaceStream.buildFromVtkIdList( faceStream ).faceNodes:
                newPointIds = []
                for currentPointId in faceNodes:
                    newPointId: int = cellNodeMapping.get( currentPointId, currentPointId )
                    newPointIds.append( newPointId )
                newFaceNodes.append( newPointIds )
            newMesh.InsertNextCell( cellType, toVtkIdList( FaceStream( newFaceNodes ).dump() ) )
        else:
            # For the standard cells, we extract the point ids of the cell directly.
            # Then the values will be (potentially) overwritten in place, before being sent back into the cell.
            cellPointIds: vtkIdList = cell.GetPointIds()
            for i in range( cellPointIds.GetNumberOfIds() ):
                currentPtId: int = cellPointIds.GetId( i )
                newPtId: int = cellNodeMapping.get( currentPtId, currentPtId )
                cellPointIds.SetId( i, newPtId )
            newMesh.InsertNextCell( cellType, cellPointIds )

    __copyFieldsSplitMesh( oldMesh, newMesh, addedPointsWithOldId )

    return newMesh


def __generateFractureMesh( oldMesh: vtkUnstructuredGrid, fractureInfo: FractureInfo,
                            cellToNodeMapping: Mapping[ int, IDMapping ] ) -> vtkUnstructuredGrid:
    """Generates the mesh of the fracture.

    Args:
        oldMesh (vtkUnstructuredGrid): The main 3d mesh.
        fractureInfo (FractureInfo): The fracture description.
        cellToNodeMapping (Mapping[ int, IDMapping ]): For each cell, gives the nodes that must be duplicated
                                                       and their new index.

    Returns:
        vtkUnstructuredGrid: The fracture mesh.
    """
    setupLogger.info( "Generating the meshes" )

    meshPoints: vtkPoints = oldMesh.GetPoints()
    isNodeDuplicated = zeros( meshPoints.GetNumberOfPoints(), dtype=bool )  # defaults to False
    for nodeMapping in cellToNodeMapping.values():
        for i, o in nodeMapping.items():
            if not isNodeDuplicated[ i ]:
                isNodeDuplicated[ i ] = i != o

    # Some elements can have all their nodes not duplicated.
    # In this case, it's mandatory not get rid of this element because the neighboring 3d elements won't follow.
    faceNodes: list[ Collection[ int ] ] = []
    discardedFaceNodes: set[ Iterable[ int ] ] = set()
    if fractureInfo.faceCellId != []:  # The fracture policy is 'internalSurfaces'
        faceCellId: list[ int ] = []
        for ns, fId in zip( fractureInfo.faceNodes, fractureInfo.faceCellId ):
            if any( map( isNodeDuplicated.__getitem__, ns ) ):
                faceNodes.append( ns )
                faceCellId.append( fId )
            else:
                discardedFaceNodes.add( ns )
    else:  # The fracture policy is 'field'
        for ns in fractureInfo.faceNodes:
            if any( map( isNodeDuplicated.__getitem__, ns ) ):
                faceNodes.append( ns )
            else:
                discardedFaceNodes.add( ns )

    if discardedFaceNodes:
        msg: str = "(" + '), ('.join( ", ".join( map( str, dfns ) ) for dfns in discardedFaceNodes ) + ")"
        setupLogger.info( f"The faces made of nodes [{msg}] were/was discarded"
                          " from the fracture mesh because none of their/its nodes were duplicated." )

    fractureNodesTmp = ones( meshPoints.GetNumberOfPoints(), dtype=int ) * -1
    for ns in faceNodes:
        for n in ns:
            fractureNodesTmp[ n ] = n
    fractureNodes: Collection[ int ] = tuple( filter( lambda n: n > -1, fractureNodesTmp ) )
    numPoints: int = len( fractureNodes )
    points = vtkPoints()
    points.SetDataType( meshPoints.GetDataType() )  # Preserve precision from input mesh
    points.SetNumberOfPoints( numPoints )
    node3dToNode2d: dict[ int, int ] = {}  # Building the node mapping, from 3d mesh nodes to 2d fracture nodes.
    for i, n in enumerate( fractureNodes ):
        coords: Coordinates3D = meshPoints.GetPoint( n )
        points.SetPoint( i, coords )
        node3dToNode2d[ n ] = i

    # The polygons are constructed in the same order as the faces defined in the fractureInfo. Therefore,
    # fractureInfo.faceCellId can be used to link old cells to fracture cells for copy with internalSurfaces.
    polygons = vtkCellArray()
    for ns in faceNodes:
        polygon = vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds( len( ns ) )
        for i, n in enumerate( ns ):
            polygon.GetPointIds().SetId( i, node3dToNode2d[ n ] )
        polygons.InsertNextCell( polygon )

    buckets: dict[ int, set[ int ] ] = defaultdict( set )
    for nodeMappingBucket in cellToNodeMapping.values():
        for i, o in nodeMappingBucket.items():
            k: Optional[ int ] = node3dToNode2d.get( min( i, o ) )
            if k is not None:
                buckets[ k ].update( ( i, o ) )

    assert set( buckets.keys() ) == set( range( numPoints ) )
    maxCollocatedNodes: int = max( map( len, buckets.values() ) ) if buckets.values() else 0
    collocatedNodes = ones( ( numPoints, maxCollocatedNodes ), dtype=int ) * -1
    for i, bucket in buckets.items():
        for j, val in enumerate( bucket ):
            collocatedNodes[ i, j ] = val
    array = numpy_to_vtk( collocatedNodes, array_type=VTK_ID_TYPE )
    array.SetName( "collocated_nodes" )  # Following the hardcoded naming convention used in GEOS for now:
    # src/coreComponents/mesh/generators/CollocatedNodes.cpp:  string const COLLOCATED_NODES = "collocated_nodes";

    fractureMesh = vtkUnstructuredGrid()  # We could be using vtkPolyData, but it's not supported by GEOS for now.
    fractureMesh.SetPoints( points )
    if polygons.GetNumberOfCells() > 0:
        fractureMesh.SetCells( [ VTK_POLYGON ] * polygons.GetNumberOfCells(), polygons )
    fractureMesh.GetPointData().AddArray( array )

    # The copy of fields from the old mesh to the fracture is only available when using the internalSurfaces policy
    # because the FractureInfo is linked to 2D elements from the oldMesh
    if fractureInfo.faceCellId != []:
        __copyFieldsFractureMesh( oldMesh, fractureMesh, faceCellId, node3dToNode2d )

    return fractureMesh


def __splitMeshOnFractures( mesh: vtkUnstructuredGrid,
                            options: Options ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    """Splits the input mesh based on the fracture information contained in options.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to be split.
        options (Options): The options for processing.

    Returns:
        tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]: The output mesh and a list of fracture meshes.
    """
    allFractureInfos: list[ FractureInfo ] = []
    for fractureId in range( len( options.fieldValuesPerFracture ) ):
        fractureInfo: FractureInfo = buildFractureInfo( mesh, options, False, fractureId )
        allFractureInfos.append( fractureInfo )
    combinedFractures: FractureInfo = buildFractureInfo( mesh, options, True )
    cellToCell: networkx.Graph = buildCellToCellGraph( mesh, combinedFractures )
    cellToNodeMapping: Mapping[ int, IDMapping ] = _identifySplit( mesh.GetNumberOfPoints(), cellToCell,
                                                                   combinedFractures.nodeToCells )
    outputMesh: vtkUnstructuredGrid = __performSplit( mesh, cellToNodeMapping )
    fractureMeshes: list[ vtkUnstructuredGrid ] = []
    for fractureInfoSeparated in allFractureInfos:
        fractureMesh: vtkUnstructuredGrid = __generateFractureMesh( mesh, fractureInfoSeparated, cellToNodeMapping )
        fractureMeshes.append( fractureMesh )
    return ( outputMesh, fractureMeshes )


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the generation of fractures on a vtkUnstructuredGrid if options given to do so.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to generate fractures on.
        options (Options): The options for processing.

    Returns:
        Result: The result of the fracture generation.
    """
    outputMesh, fractureMeshes = __splitMeshOnFractures( mesh, options )
    writeMesh( outputMesh, options.meshVtkOutput )
    for i, fractureMesh in enumerate( fractureMeshes ):
        writeMesh( fractureMesh, options.allFracturesVtkOutput[ i ] )
    # TODO provide statistics about what was actually performed (size of the fracture, number of split nodes...).
    return Result( info="OK" )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtkUnstructuredGrid and generates fractures based on the provided options.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the global ids addition.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    # Mesh cannot contain global ids before splitting.
    if hasArray( mesh, [ "GLOBAL_IDS_POINTS", "GLOBAL_IDS_CELLS" ] ):
        errMsg: str = ( "The mesh cannot contain global ids for neither cells nor points. The correct procedure " +
                        " is to split the mesh and then generate global ids for new split meshes." )
        setupLogger.error( errMsg )
        raise ValueError( errMsg )
    return meshAction( mesh, options )
