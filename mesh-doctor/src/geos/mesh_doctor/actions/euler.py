# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Compute Solid Euler Characteristic for mesh files (3D elements only)."""

from dataclasses import dataclass
import vtk
from tqdm import tqdm

from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    """Options for Euler characteristic computation."""
    pass


@dataclass( frozen=True )
class Result:
    """Result of solid Euler characteristic computation.

    Attributes:
        numVertices: Number of vertices (V) in 3D mesh
        numEdges: Number of unique edges (E) in 3D mesh
        numFaces: Number of unique faces (F) in 3D mesh
        numCells: Number of 3D cells (C)
        solidEulerCharacteristic: Solid Euler characteristic (chi = V - E + F - C)
        num3dCells: Number of 3D volumetric cells in input
        num2dCells: Number of 2D surface cells in input (ignored)
        numOtherCells: Number of other cells in input
        numBoundaryEdges: Number of boundary edges on surface
        numNonManifoldEdges: Number of non-manifold edges on surface
        numConnectedComponents: Number of disconnected 3D mesh regions
    """
    numVertices: int
    numEdges: int
    numFaces: int
    numCells: int
    solidEulerCharacteristic: int
    num3dCells: int
    num2dCells: int
    numOtherCells: int
    numBoundaryEdges: int
    numNonManifoldEdges: int
    numConnectedComponents: int


def __countConnectedComponents( mesh: vtk.vtkUnstructuredGrid ) -> int:
    """Count number of disconnected mesh components.

    Args:
        mesh: Input unstructured grid

    Returns:
        Number of disconnected regions
    """
    setupLogger.info( "Checking for disconnected 3D components..." )

    connectivity = vtk.vtkConnectivityFilter()
    connectivity.SetInputData( mesh )
    connectivity.SetExtractionModeToAllRegions()
    connectivity.ColorRegionsOn()
    connectivity.Update()

    numRegions = connectivity.GetNumberOfExtractedRegions()

    setupLogger.info( f"Found {numRegions} disconnected 3D component(s)" )

    return numRegions


def __filter3dElements( mesh: vtk.vtkUnstructuredGrid ) -> tuple[ vtk.vtkUnstructuredGrid, int, int, int, bool ]:
    """Filter only 3D volumetric elements from unstructured grid.

    Removes 2D faces, 1D edges, and 0D vertices.

    Args:
        mesh: Input unstructured grid

    Returns:
        Tuple of (filtered_mesh, n_3d, n_2d, n_other, has_3d)
    """
    # Classify cells by dimension
    cell3dIds = []
    n3d = 0
    n2d = 0
    nOther = 0

    setupLogger.info( "Classifying cell types..." )
    for i in tqdm( range( mesh.GetNumberOfCells() ), desc="Scanning cells" ):
        cell = mesh.GetCell( i )
        cellDim = cell.GetCellDimension()

        if cellDim == 3:
            cell3dIds.append( i )
            n3d += 1
        elif cellDim == 2:
            n2d += 1
        else:
            nOther += 1

    setupLogger.info( "Cell type breakdown:" )
    setupLogger.info( f"  3D volumetric cells: {n3d}" )
    setupLogger.info( f"  2D surface cells:    {n2d}" )
    setupLogger.info( f"  Other cells:         {nOther}" )

    # Check if we have 3D cells
    has3d = n3d > 0

    if not has3d:
        setupLogger.warning( "No 3D volumetric elements found!" )
        setupLogger.warning( "This appears to be a pure surface mesh." )
        setupLogger.warning( "Cannot compute solid Euler characteristic." )
        return mesh, n3d, n2d, nOther, False

    if n2d > 0:
        setupLogger.info( f"Filtering out {n2d} 2D boundary cells..." )
        setupLogger.info( f"Using only {n3d} volumetric elements" )

    # Extract only 3D cells using vtkExtractCells
    idList = vtk.vtkIdList()
    for cellId in cell3dIds:
        idList.InsertNextId( cellId )

    extractor = vtk.vtkExtractCells()
    extractor.SetInputData( mesh )
    extractor.SetCellList( idList )
    extractor.Update()

    filteredMesh = extractor.GetOutput()

    return filteredMesh, n3d, n2d, nOther, has3d


def __countUniqueEdgesAndFaces( mesh: vtk.vtkUnstructuredGrid ) -> tuple[ int, int ]:
    """Count unique edges and faces in 3D mesh (NumPy optimized).

    Args:
        mesh: 3D unstructured grid

    Returns:
        Tuple of (num_edges, num_faces)
    """
    setupLogger.info( "Counting unique edges and faces in 3D mesh..." )

    try:
        import numpy as np
        use_numpy = True
    except ImportError:
        use_numpy = False

    numCells = mesh.GetNumberOfCells()

    if use_numpy:
        # Use numpy for faster operations
        edge_list = []
        face_list = []

        for i in tqdm( range( numCells ), desc="Processing cells", mininterval=1.0 ):

            cell = mesh.GetCell( i )

            # Edges
            numEdges = cell.GetNumberOfEdges()
            for edge_idx in range( numEdges ):
                edge = cell.GetEdge( edge_idx )
                p0 = edge.GetPointId( 0 )
                p1 = edge.GetPointId( 1 )
                edge_list.append( ( min( p0, p1 ), max( p0, p1 ) ) )

            # Faces
            numFaces = cell.GetNumberOfFaces()
            for face_idx in range( numFaces ):
                face = cell.GetFace( face_idx )
                num_pts = face.GetNumberOfPoints()
                point_ids = tuple( sorted( [ face.GetPointId( j ) for j in range( num_pts ) ] ) )
                face_list.append( point_ids )

        # Use numpy unique for deduplication (faster than set)
        setupLogger.info( "  Deduplicating edges and faces..." )

        # For edges: convert to array and use unique
        edge_array = np.array( edge_list, dtype=np.int64 )
        unique_edges = np.unique( edge_array, axis=0 )
        num_edges = len( unique_edges )

        # For faces: use set (numpy doesn't handle variable-length well)
        num_faces = len( set( face_list ) )

    else:
        # Fallback to optimized set-based approach
        edge_set = set()
        face_set = set()

        for i in tqdm( range( numCells ), desc="Processing cells", mininterval=0.5 ):
            cell = mesh.GetCell( i )

            numEdges = cell.GetNumberOfEdges()
            for edge_idx in range( numEdges ):
                edge = cell.GetEdge( edge_idx )
                p0 = edge.GetPointId( 0 )
                p1 = edge.GetPointId( 1 )
                edge_set.add( ( min( p0, p1 ), max( p0, p1 ) ) )

            numFaces = cell.GetNumberOfFaces()
            for face_idx in range( numFaces ):
                face = cell.GetFace( face_idx )
                num_pts = face.GetNumberOfPoints()
                face_set.add( tuple( sorted( [ face.GetPointId( j ) for j in range( num_pts ) ] ) ) )

        num_edges = len( edge_set )
        num_faces = len( face_set )

    setupLogger.info( f"  Unique edges: {num_edges:,}" )
    setupLogger.info( f"  Unique faces: {num_faces:,}" )

    return num_edges, num_faces


def __extractSurface( mesh: vtk.vtkUnstructuredGrid ) -> vtk.vtkPolyData:
    """Extract surface from unstructured grid (3D elements only).

    Args:
        mesh: Input unstructured grid (3D elements)

    Returns:
        Surface as polydata
    """
    setupLogger.info( "Extracting boundary surface from 3D elements..." )
    surfaceFilter = vtk.vtkDataSetSurfaceFilter()
    surfaceFilter.SetInputData( mesh )
    surfaceFilter.Update()
    return surfaceFilter.GetOutput()


def __checkMeshQuality( surface: vtk.vtkPolyData ) -> tuple[ int, int ]:
    """Check for boundary edges and non-manifold features.

    Args:
        surface: Surface mesh

    Returns:
        Tuple of (boundary_edges, non_manifold_edges)
    """
    setupLogger.info( "Checking mesh quality..." )

    # Count boundary edges
    featureEdgesBoundary = vtk.vtkFeatureEdges()
    featureEdgesBoundary.SetInputData( surface )
    featureEdgesBoundary.BoundaryEdgesOn()
    featureEdgesBoundary.ManifoldEdgesOff()
    featureEdgesBoundary.NonManifoldEdgesOff()
    featureEdgesBoundary.FeatureEdgesOff()
    featureEdgesBoundary.Update()
    boundaryEdges = featureEdgesBoundary.GetOutput().GetNumberOfCells()

    # Count non-manifold edges
    featureEdgesNm = vtk.vtkFeatureEdges()
    featureEdgesNm.SetInputData( surface )
    featureEdgesNm.BoundaryEdgesOff()
    featureEdgesNm.ManifoldEdgesOff()
    featureEdgesNm.NonManifoldEdgesOn()
    featureEdgesNm.FeatureEdgesOff()
    featureEdgesNm.Update()
    nonManifoldEdges = featureEdgesNm.GetOutput().GetNumberOfCells()

    return boundaryEdges, nonManifoldEdges


def meshAction( mesh: vtk.vtkUnstructuredGrid, options: Options ) -> Result:
    """Compute solid Euler characteristic for a mesh.

    Only considers 3D volumetric elements. Computes chi_solid = V - E + F - C.

    Args:
        mesh: Input unstructured grid
        options: Computation options

    Returns:
        Result with solid Euler characteristic and topology information
    """
    setupLogger.info( "Starting solid Euler characteristic computation..." )
    setupLogger.info( f"Input mesh: {mesh.GetNumberOfPoints()} points, {mesh.GetNumberOfCells()} cells" )

    # Filter to 3D elements only
    mesh3d, n3d, n2d, nOther, has3d = __filter3dElements( mesh )

    if not has3d:
        raise RuntimeError( "Cannot compute solid Euler - no 3D cells found" )

    # Count connected components
    numComponents = __countConnectedComponents( mesh3d )

    # Get basic counts
    V = mesh3d.GetNumberOfPoints()
    C = mesh3d.GetNumberOfCells()

    # Count unique edges and faces in 3D mesh
    E, F = __countUniqueEdgesAndFaces( mesh3d )

    setupLogger.info( "Solid mesh topology:" )
    setupLogger.info( f"  Vertices (V): {V:,}" )
    setupLogger.info( f"  Edges    (E): {E:,}" )
    setupLogger.info( f"  Faces    (F): {F:,}" )
    setupLogger.info( f"  Cells    (C): {C:,}" )

    # Calculate solid Euler characteristic
    solidEuler = V - E + F - C

    setupLogger.info( f"Solid Euler characteristic (chi = V - E + F - C): {solidEuler}" )

    # Interpret result
    setupLogger.info( "Topology interpretation:" )
    setupLogger.info( f"  3D connected components: {numComponents}" )

    if numComponents == 1:
        if solidEuler == 1:
            setupLogger.info( "  chi = 1: Contractible (solid ball topology)" )
            setupLogger.info( "  VALID simple 3D region for simulation" )
        elif solidEuler == 0:
            setupLogger.warning( "  chi = 0: Solid torus (has through-hole)" )
            setupLogger.warning( "  Verify this matches your domain geometry" )
        elif solidEuler == 2:
            setupLogger.warning( "  chi = 2: Hollow shell or internal cavity topology" )
            setupLogger.warning( "  Expected chi = 1 for simple solid ball" )
            setupLogger.warning( "  This suggests internal void or nested structure" )
            setupLogger.warning( "  3D cells ARE connected (verified above) - verify intended" )
        else:
            setupLogger.warning( f"  chi = {solidEuler}: Unusual topology" )
            setupLogger.warning( "  Verify mesh integrity" )
    else:
        setupLogger.error( f"  Mesh has {numComponents} disconnected 3D components!" )
        setupLogger.error( "  This is NOT suitable for simulation without fixing" )

    # Check mesh quality
    surface = __extractSurface( mesh3d )
    boundaryEdges, nonManifoldEdges = __checkMeshQuality( surface )

    setupLogger.info( "Mesh quality:" )
    setupLogger.info( f"  Boundary edges:     {boundaryEdges:,}" )
    setupLogger.info( f"  Non-manifold edges: {nonManifoldEdges:,}" )

    # Final validation
    if numComponents == 1 and boundaryEdges == 0 and nonManifoldEdges == 0:
        if solidEuler == 1:
            setupLogger.info( "  Perfect: single connected volume, simple topology - READY!" )
        else:
            setupLogger.warning( f"  Connected volume but chi = {solidEuler}" )
            setupLogger.warning( "  Verify internal features are intended" )
    elif numComponents > 1:
        setupLogger.error( "  Multiple disconnected regions - INVALID!" )
    elif boundaryEdges > 0:
        setupLogger.error( "  Open surface detected - INVALID!" )
    elif nonManifoldEdges > 0:
        setupLogger.error( "  Non-manifold geometry detected - INVALID!" )

    return Result( numVertices=V,
                   numEdges=E,
                   numFaces=F,
                   numCells=C,
                   solidEulerCharacteristic=solidEuler,
                   num3dCells=n3d,
                   num2dCells=n2d,
                   numOtherCells=nOther,
                   numBoundaryEdges=boundaryEdges,
                   numNonManifoldEdges=nonManifoldEdges,
                   numConnectedComponents=numComponents )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Compute solid Euler characteristic for a VTU file.

    Args:
        vtuInputFile: Path to input VTU file
        options: Computation options

    Returns:
        Result with solid Euler characteristic and topology information
    """
    mesh = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
