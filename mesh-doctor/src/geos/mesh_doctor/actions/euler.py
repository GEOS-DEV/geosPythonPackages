# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Compute Euler characteristic for mesh files (3D solid and/or 2D surface)."""

from __future__ import annotations
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import numpy as np
import vtk
from tqdm import tqdm
from vtk.util.numpy_support import vtk_to_numpy

from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid

# --- Options & Result types ---------------------------------------------------


@dataclass( frozen=True )
class Options:
    """Options for Euler characteristic computation.

    Attributes:
        mode: "solid"   -> analyze 3D cells only (chi = V - E + F - C).
              "surface" -> analyze 2D cells only (chi = V - E + F),
                           always per connected component.
              "all"     -> both, in one report; missing dimension is silently
                           skipped.
        tagArray: Cell-data array used to group surface cells (e.g.
                  "FaultMask"). If None, all 2D cells are analyzed as one
                  group. Ignored in `solid` mode.
        tagValue: If set together with `tagArray`, only that value is
                  analyzed. If None and `tagArray` is set, all distinct
                  non-zero values present in the array are screened.
    """
    mode: str = "solid"
    tagArray: Optional[ str ] = None
    tagValue: Optional[ float ] = None


@dataclass( frozen=True )
class SurfaceComponent:
    """Per-component topology for a 2D surface."""
    componentId: int
    numCells: int
    numVertices: int
    numEdges: int
    numFaces: int
    eulerCharacteristic: int
    numBoundaryEdges: int
    numNonManifoldEdges: int
    interpretation: str
    nonManifoldEdgeEndpoints: tuple[ tuple[ int, int ], ...] = field( default_factory=tuple )


@dataclass( frozen=True )
class SurfaceGroup:
    """Surface analysis for one tag value, or the whole 2D mesh if no tag."""
    tagArray: Optional[ str ]
    tagValue: Optional[ float ]
    numCells: int
    numVertices: int
    numEdges: int
    numFaces: int
    eulerCharacteristic: int
    numBoundaryEdges: int
    numNonManifoldEdges: int
    components: tuple[ SurfaceComponent, ...]


@dataclass( frozen=True )
class Result:
    """Result of Euler characteristic computation.

    The `solid*` fields are populated when `mode in {"solid","all"}` and the
    input mesh has 3D cells. The `surface*` fields are populated when
    `mode in {"surface","all"}` and the input mesh has 2D cells.
    """
    mode: str
    # cell breakdown of the input
    num3dCells: int
    num2dCells: int
    numOtherCells: int
    # solid
    solidComputed: bool = False
    numVertices: int = 0
    numEdges: int = 0
    numFaces: int = 0
    numCells: int = 0
    solidEulerCharacteristic: int = 0
    numBoundaryEdges: int = 0
    numNonManifoldEdges: int = 0
    numConnectedComponents: int = 0
    # surface
    surfaceComputed: bool = False
    surfaceGroups: tuple[ SurfaceGroup, ...] = field( default_factory=tuple )


# --- Cell-classification helpers ---------------------------------------------


def __classifyCells( mesh: vtk.vtkUnstructuredGrid ) -> tuple[ list[ int ], list[ int ], int ]:
    """Classify cells by topological dimension.

    Returns:
        (cell3dIds, cell2dIds, nOther)
    """
    cell3dIds: list[ int ] = []
    cell2dIds: list[ int ] = []
    nOther = 0
    for i in tqdm( range( mesh.GetNumberOfCells() ), desc="Scanning cells" ):
        d = mesh.GetCell( i ).GetCellDimension()
        if d == 3:
            cell3dIds.append( i )
        elif d == 2:
            cell2dIds.append( i )
        else:
            nOther += 1
    return cell3dIds, cell2dIds, nOther


def __extractCells( mesh: vtk.vtkUnstructuredGrid, cellIds: list[ int ] ) -> vtk.vtkUnstructuredGrid:
    """Return a new unstructured grid containing only the listed cells."""
    idList = vtk.vtkIdList()
    for c in cellIds:
        idList.InsertNextId( c )
    ext = vtk.vtkExtractCells()
    ext.SetInputData( mesh )
    ext.SetCellList( idList )
    ext.Update()
    return ext.GetOutput()


def __filterByTagValue( mesh: vtk.vtkUnstructuredGrid, tagArray: str, tagValue: float ) -> vtk.vtkUnstructuredGrid:
    """Keep only cells whose `tagArray` equals `tagValue`."""
    th = vtk.vtkThreshold()
    th.SetInputData( mesh )
    th.SetInputArrayToProcess( 0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, tagArray )
    th.SetLowerThreshold( float( tagValue ) )
    th.SetUpperThreshold( float( tagValue ) )
    th.SetThresholdFunction( vtk.vtkThreshold.THRESHOLD_BETWEEN )
    th.Update()
    return th.GetOutput()


# --- Solid path --------------------------------------------------------------


def __countConnectedComponents( mesh: vtk.vtkUnstructuredGrid ) -> int:
    """Count disconnected regions (cells connected via shared points)."""
    cf = vtk.vtkConnectivityFilter()
    cf.SetInputData( mesh )
    cf.SetExtractionModeToAllRegions()
    cf.SetRegionIdAssignmentMode( vtk.vtkConnectivityFilter.CELL_COUNT_DESCENDING )
    cf.ColorRegionsOn()
    cf.Update()
    return cf.GetNumberOfExtractedRegions()


def __countUniqueEdgesAndFaces( mesh: vtk.vtkUnstructuredGrid ) -> tuple[ int, int ]:
    """Count unique edges and faces in a 3D mesh."""
    setupLogger.info( "Counting unique edges and faces in 3D mesh..." )
    edgeList: list[ tuple[ int, int ] ] = []
    faceSet: set[ tuple[ int, ...] ] = set()
    for i in tqdm( range( mesh.GetNumberOfCells() ), desc="Processing cells", mininterval=1.0 ):
        cell = mesh.GetCell( i )
        for k in range( cell.GetNumberOfEdges() ):
            e = cell.GetEdge( k )
            p0 = e.GetPointId( 0 )
            p1 = e.GetPointId( 1 )
            edgeList.append( ( min( p0, p1 ), max( p0, p1 ) ) )
        for k in range( cell.GetNumberOfFaces() ):
            f = cell.GetFace( k )
            faceSet.add( tuple( sorted( f.GetPointId( j ) for j in range( f.GetNumberOfPoints() ) ) ) )
    edges = np.unique( np.asarray( edgeList, dtype=np.int64 ), axis=0 )
    return len( edges ), len( faceSet )


def __surfaceQualityOfSolidBoundary( mesh3d: vtk.vtkUnstructuredGrid ) -> tuple[ int, int ]:
    """Count boundary and non-manifold edges on the boundary of a 3D mesh."""
    surfaceFilter = vtk.vtkDataSetSurfaceFilter()
    surfaceFilter.SetInputData( mesh3d )
    surfaceFilter.Update()
    surf = surfaceFilter.GetOutput()
    fb = vtk.vtkFeatureEdges()
    fb.SetInputData( surf )
    fb.BoundaryEdgesOn()
    fb.ManifoldEdgesOff()
    fb.NonManifoldEdgesOff()
    fb.FeatureEdgesOff()
    fb.Update()
    boundary = fb.GetOutput().GetNumberOfCells()
    fn = vtk.vtkFeatureEdges()
    fn.SetInputData( surf )
    fn.BoundaryEdgesOff()
    fn.ManifoldEdgesOff()
    fn.NonManifoldEdgesOn()
    fn.FeatureEdgesOff()
    fn.Update()
    nonManifold = fn.GetOutput().GetNumberOfCells()
    return boundary, nonManifold


# --- Surface path -------------------------------------------------------------


def __interpretSurface( chi: int, boundaryEdges: int, nonManifoldEdges: int ) -> str:
    """Short topology label for a surface component."""
    if nonManifoldEdges > 0:
        return f"non-manifold ({nonManifoldEdges} edge(s))"
    if boundaryEdges == 0:
        if chi == 2:
            return "closed sphere"
        if chi == 0:
            return "torus (closed, genus 1)"
        if chi < 0 and chi % 2 == 0:
            return f"closed surface (genus {( 2 - chi ) // 2})"
        return f"closed (chi={chi}, unusual)"
    if chi == 1:
        return "disk"
    if chi == 0:
        return "annulus / cylinder"
    if chi < 0:
        return f"surface with multiple boundaries / holes (chi={chi})"
    return f"open (chi={chi}, unusual)"


def __surfaceComponentsFromColored( colored: vtk.vtkUnstructuredGrid ) -> list[ SurfaceComponent ]:
    """Compute (V, E, F, chi, boundary, non-manifold) per RegionId of a colored 2D mesh."""
    rid = vtk_to_numpy( colored.GetCellData().GetArray( "RegionId" ) ).astype( np.int64 )
    cells = colored.GetCells()
    # GetConnectivityArray / GetOffsetsArray require VTK 9+
    conn = vtk_to_numpy( cells.GetConnectivityArray() ).astype( np.int64, copy=False )
    off = vtk_to_numpy( cells.GetOffsetsArray() ).astype( np.int64, copy=False )

    components: list[ SurfaceComponent ] = []
    sizes = sorted( Counter( rid.tolist() ).items(), key=lambda kv: -kv[ 1 ] )
    for regionId, _nCells in sizes:
        sel = np.flatnonzero( rid == regionId )
        verts: set[ int ] = set()
        edgeCount: dict[ tuple[ int, int ], int ] = {}
        for cid in sel:
            pts = conn[ off[ cid ]:off[ cid + 1 ] ]
            K = len( pts )
            for v in pts:
                verts.add( int( v ) )
            for i in range( K ):
                a, b = int( pts[ i ] ), int( pts[ ( i + 1 ) % K ] )
                ek = ( a, b ) if a < b else ( b, a )
                edgeCount[ ek ] = edgeCount.get( ek, 0 ) + 1
        V = len( verts )
        E = len( edgeCount )
        F = int( len( sel ) )
        bE = sum( 1 for c in edgeCount.values() if c == 1 )
        nmEdges = tuple( ek for ek, c in edgeCount.items() if c > 2 )
        nm = len( nmEdges )
        chi = V - E + F
        components.append(
            SurfaceComponent( componentId=int( regionId ),
                              numCells=F,
                              numVertices=V,
                              numEdges=E,
                              numFaces=F,
                              eulerCharacteristic=chi,
                              numBoundaryEdges=bE,
                              numNonManifoldEdges=nm,
                              interpretation=__interpretSurface( chi, bE, nm ),
                              nonManifoldEdgeEndpoints=nmEdges ) )
    return components


def __runSurfaceGroup( mesh2d: vtk.vtkUnstructuredGrid, tagArray: Optional[ str ],
                       tagValue: Optional[ float ] ) -> SurfaceGroup:
    """Filter (optionally) and per-component analyze one surface group."""
    if tagValue is not None and tagArray is not None:  # noqa: SIM108
        sub = __filterByTagValue( mesh2d, tagArray, tagValue )
    else:
        sub = mesh2d
    nCells = sub.GetNumberOfCells()
    if nCells == 0:
        return SurfaceGroup( tagArray=tagArray,
                             tagValue=tagValue,
                             numCells=0,
                             numVertices=0,
                             numEdges=0,
                             numFaces=0,
                             eulerCharacteristic=0,
                             numBoundaryEdges=0,
                             numNonManifoldEdges=0,
                             components=() )
    cf = vtk.vtkConnectivityFilter()
    cf.SetInputData( sub )
    cf.SetExtractionModeToAllRegions()
    cf.ColorRegionsOn()
    cf.Update()
    components = __surfaceComponentsFromColored( cf.GetOutput() )
    V = sum( c.numVertices for c in components )
    E = sum( c.numEdges for c in components )
    F = sum( c.numFaces for c in components )
    bE = sum( c.numBoundaryEdges for c in components )
    nm = sum( c.numNonManifoldEdges for c in components )
    return SurfaceGroup( tagArray=tagArray,
                         tagValue=tagValue,
                         numCells=nCells,
                         numVertices=V,
                         numEdges=E,
                         numFaces=F,
                         eulerCharacteristic=V - E + F,
                         numBoundaryEdges=bE,
                         numNonManifoldEdges=nm,
                         components=tuple( components ) )


def __discoverTagValues( mesh: vtk.vtkUnstructuredGrid, tagArray: str, skipZero: bool = True ) -> list[ float ]:
    """Return the sorted distinct values of `tagArray`, optionally skipping 0."""
    arr = mesh.GetCellData().GetArray( tagArray )
    if arr is None:
        setupLogger.warning( f"Tag array '{tagArray}' not found on input mesh." )
        return []
    values = vtk_to_numpy( arr )
    unique = sorted( { float( v ) for v in np.asarray( values ).ravel() } )
    if skipZero:
        unique = [ v for v in unique if v != 0.0 ]
    return unique


# --- Top-level dispatch ------------------------------------------------------


def __solidAction( mesh3d: vtk.vtkUnstructuredGrid ) -> dict:
    """Run the existing solid analysis and return the resulting fields."""
    nComponents = __countConnectedComponents( mesh3d )
    V = mesh3d.GetNumberOfPoints()
    C = mesh3d.GetNumberOfCells()
    E, F = __countUniqueEdgesAndFaces( mesh3d )
    chi = V - E + F - C
    boundary, nonManifold = __surfaceQualityOfSolidBoundary( mesh3d )
    return {
        "numVertices": V,
        "numEdges": E,
        "numFaces": F,
        "numCells": C,
        "solidEulerCharacteristic": chi,
        "numBoundaryEdges": boundary,
        "numNonManifoldEdges": nonManifold,
        "numConnectedComponents": nComponents,
    }


def __surfaceAction( mesh2d: vtk.vtkUnstructuredGrid, options: Options ) -> list[ SurfaceGroup ]:
    """Run the surface analysis. Returns one or more SurfaceGroups."""
    if options.tagArray is None:
        return [ __runSurfaceGroup( mesh2d, None, None ) ]
    if options.tagValue is not None:
        return [ __runSurfaceGroup( mesh2d, options.tagArray, options.tagValue ) ]
    # discover all distinct non-zero values and screen them
    values = __discoverTagValues( mesh2d, options.tagArray, skipZero=True )
    return [ __runSurfaceGroup( mesh2d, options.tagArray, v ) for v in values ]


def meshAction( mesh: vtk.vtkUnstructuredGrid, options: Options ) -> Result:
    """Compute Euler characteristic for a mesh.

    Args:
        mesh: Input unstructured grid
        options: Configuration options

    Returns:
        Result with the requested topology information.
    """
    setupLogger.info( "Starting Euler characteristic computation..." )
    setupLogger.info( f"Input mesh: {mesh.GetNumberOfPoints():,} points, "
                      f"{mesh.GetNumberOfCells():,} cells, mode={options.mode}" )

    cell3dIds, cell2dIds, nOther = __classifyCells( mesh )
    n3d = len( cell3dIds )
    n2d = len( cell2dIds )
    setupLogger.info( f"Cell breakdown: 3D={n3d:,}, 2D={n2d:,}, other={nOther:,}" )

    wantSolid = options.mode in { "solid", "all" }
    wantSurface = options.mode in { "surface", "all" }
    if options.mode == "solid" and n3d == 0:
        raise RuntimeError( "Cannot compute solid Euler characteristic, no 3D cells." )
    if options.mode == "surface" and n2d == 0:
        raise RuntimeError( "Cannot compute surface Euler characteristic, no 2D cells." )

    solidFields: dict = {}
    solidComputed = False
    if wantSolid and n3d > 0:
        mesh3d = __extractCells( mesh, cell3dIds )
        solidFields = __solidAction( mesh3d )
        solidComputed = True
    elif wantSolid:
        setupLogger.info( "No 3D cells in input, skipping solid analysis." )

    surfaceGroups: list[ SurfaceGroup ] = []
    surfaceComputed = False
    if wantSurface and n2d > 0:
        mesh2d = __extractCells( mesh, cell2dIds )
        surfaceGroups = __surfaceAction( mesh2d, options )
        surfaceComputed = True
    elif wantSurface:
        setupLogger.info( "No 2D cells in input, skipping surface analysis." )

    return Result( mode=options.mode,
                   num3dCells=n3d,
                   num2dCells=n2d,
                   numOtherCells=nOther,
                   solidComputed=solidComputed,
                   **solidFields,
                   surfaceComputed=surfaceComputed,
                   surfaceGroups=tuple( surfaceGroups ) )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Compute Euler characteristic for a VTU file."""
    return meshAction( readUnstructuredGrid( vtuInputFile ), options )
