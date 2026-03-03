# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Compute Euler Characteristic for mesh files (3D elements only)."""

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
    """Result of Euler characteristic computation.

    Attributes:
        numVertices: Number of surface vertices (V)
        numEdges: Number of surface edges (E)
        numFaces: Number of surface faces (F)
        eulerCharacteristic: Euler characteristic (X = V - E + F)
        num3dCells: Number of 3D volumetric cells in input
        num2dCells: Number of 2D surface cells in input (ignored)
        numOtherCells: Number of other cells in input
        numBoundaryEdges: Number of boundary edges
        numNonManifoldEdges: Number of non-manifold edges
        numConnectedComponents: Number of disconnected mesh regions
    """
    numVertices: int
    numEdges: int
    numFaces: int
    eulerCharacteristic: int
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
    setupLogger.info( "Checking for disconnected components..." )

    connectivity = vtk.vtkConnectivityFilter()
    connectivity.SetInputData( mesh )
    connectivity.SetExtractionModeToAllRegions()
    connectivity.ColorRegionsOn()
    connectivity.Update()

    numRegions = connectivity.GetNumberOfExtractedRegions()

    setupLogger.info( f"Found {numRegions} disconnected component(s)" )

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
        setupLogger.warning( "Computing Euler characteristic from all cells..." )
        return mesh, n3d, n2d, nOther, False

    if n2d > 0:
        setupLogger.info( f"Filtering out {n2d} 2D boundary cells..." )
        setupLogger.info( f"Using only {n3d} volumetric elements for surface extraction" )

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


def __extractSurface( mesh: vtk.vtkUnstructuredGrid ) -> vtk.vtkPolyData:
    """Extract surface from unstructured grid (3D elements only).

    Args:
        mesh: Input unstructured grid (3D elements)

    Returns:
        Surface as polydata
    """
    setupLogger.info( "Extracting surface from 3D elements..." )
    surfaceFilter = vtk.vtkDataSetSurfaceFilter()
    surfaceFilter.SetInputData( mesh )
    surfaceFilter.Update()
    return surfaceFilter.GetOutput()


def __countUniqueEdges( surface: vtk.vtkPolyData ) -> int:
    """Count unique edges in the surface mesh.

    Args:
        surface: Surface mesh

    Returns:
        Number of unique edges
    """
    setupLogger.info( "Counting unique edges..." )

    # Use VTK's edge extraction (faster than manual iteration)
    edgeExtractor = vtk.vtkExtractEdges()
    edgeExtractor.SetInputData( surface )
    edgeExtractor.Update()

    return edgeExtractor.GetOutput().GetNumberOfCells()


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
    """Compute Euler characteristic for a mesh.

    Only considers 3D volumetric elements. Extracts surface and computes V - E + F.

    Args:
        mesh: Input unstructured grid
        options: Computation options

    Returns:
        Result with Euler characteristic and topology information
    """
    setupLogger.info( "Starting Euler characteristic computation..." )
    setupLogger.info( f"Input mesh: {mesh.GetNumberOfPoints()} points, {mesh.GetNumberOfCells()} cells" )

    # Filter to 3D elements only
    mesh3d, n3d, n2d, nOther, has3d = __filter3dElements( mesh )

    # Count connected components BEFORE extracting surface
    numComponents = __countConnectedComponents( mesh3d )

    # Extract surface from 3D elements
    surface = __extractSurface( mesh3d )

    # Get counts
    V = surface.GetNumberOfPoints()
    F = surface.GetNumberOfCells()
    E = __countUniqueEdges( surface )

    setupLogger.info( "Surface topology:" )
    setupLogger.info( f"  Vertices (V): {V:,}" )
    setupLogger.info( f"  Edges    (E): {E:,}" )
    setupLogger.info( f"  Faces    (F): {F:,}" )

    # Calculate Euler characteristic
    euler = V - E + F

    setupLogger.info( f"Euler characteristic (X = V - E + F): {euler}" )
    setupLogger.info( f"Connected components: {numComponents}" )

    # Interpret result with component information
    if numComponents == 1:
        # Single component - standard topology interpretation
        if euler == 2:
            setupLogger.info( "Topology: Single closed surface (sphere-like) - VALID for simulation!" )
        elif euler == 0:
            setupLogger.warning( "Topology: Torus-like (genus 1)" )
            setupLogger.warning( "  Expected X = 2 for standard simulation mesh" )
        elif euler == 1:
            setupLogger.warning( "Topology: Disk-like (open surface)" )
            setupLogger.warning( "  Mesh is not closed! Expected X = 2" )
        elif euler < 0:
            genus = ( 2 - euler ) // 2
            setupLogger.warning( f"Topology: Complex surface with handles (genus g = {genus})" )
            setupLogger.warning( "  Expected X = 2 for standard simulation mesh" )
        else:
            setupLogger.warning( f"Topology: Unexpected (X = {euler})" )
    else:
        # Multiple components detected
        expectedEuler = 2 * numComponents  # If all components are sphere-like

        setupLogger.error( f"Topology: Mesh has {numComponents} DISCONNECTED COMPONENTS!" )
        setupLogger.error( f"  Euler characteristic: {euler}" )
        setupLogger.error( f"  Expected for {numComponents} spheres: X = {expectedEuler}" )

        if numComponents > 1:
            # Internal cavities = additional components beyond the outer surface
            numCavities = numComponents - 1
            setupLogger.error( f"  Likely {numCavities} internal void(s)/cavity(ies)" )

        if euler == expectedEuler:
            setupLogger.error( "  All components are sphere-like (X=2 each)" )
        elif euler < expectedEuler:
            setupLogger.error( "  Some components have genus > 0 (holes/handles)" )
        else:
            setupLogger.error( "  Unusual topology - verify mesh integrity" )

        setupLogger.error( "  This mesh is NOT suitable for simulation without fixing!" )
        setupLogger.error( "  Expected: single closed volume (X = 2, components = 1)" )

    # Check mesh quality
    boundaryEdges, nonManifoldEdges = __checkMeshQuality( surface )

    setupLogger.info( "Mesh quality:" )
    setupLogger.info( f"  Boundary edges:     {boundaryEdges:,}" )
    setupLogger.info( f"  Non-manifold edges: {nonManifoldEdges:,}" )

    if boundaryEdges == 0 and nonManifoldEdges == 0:
        if euler == 2 and numComponents == 1:
            setupLogger.info( "  Perfect closed manifold mesh - READY for simulation!" )
        else:
            setupLogger.warning( "  Perfect manifold but topology issues - verify before simulation" )
    elif boundaryEdges > 0:
        setupLogger.warning( "  Open surface detected (has boundaries)" )
    if nonManifoldEdges > 0:
        setupLogger.error( "  Non-manifold edges detected (mesh has issues!)" )

    return Result( numVertices=V,
                   numEdges=E,
                   numFaces=F,
                   eulerCharacteristic=euler,
                   num3dCells=n3d,
                   num2dCells=n2d,
                   numOtherCells=nOther,
                   numBoundaryEdges=boundaryEdges,
                   numNonManifoldEdges=nonManifoldEdges,
                   numConnectedComponents=numComponents )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Compute Euler characteristic for a VTU file.

    Args:
        vtuInputFile: Path to input VTU file
        options: Computation options

    Returns:
        Result with Euler characteristic and topology information
    """
    mesh = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
