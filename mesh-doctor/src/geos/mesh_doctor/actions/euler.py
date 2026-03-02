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
        eulerCharacteristic: Euler characteristic (χ = V - E + F)
        num3dCells: Number of 3D volumetric cells in input
        num2dCells: Number of 2D surface cells in input (ignored)
        numOtherCells: Number of other cells in input
        numBoundaryEdges: Number of boundary edges
        numNonManifoldEdges: Number of non-manifold edges
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


def __filter3dElements( mesh: vtk.vtkUnstructuredGrid ) -> tuple[ vtk.vtkUnstructuredGrid, int, int, int, bool ]:
    """Filter only 3D volumetric elements from unstructured grid.
    
    Removes 2D faces, 1D edges, and 0D vertices.
    
    Args:
        mesh: Input unstructured grid
        
    Returns:
        Tuple of (filtered_mesh, n_3d, n_2d, n_other, has_3d)
    """
    # Cell types that are 3D volumes
    volumeTypes = [
        vtk.VTK_TETRA,  # 10
        vtk.VTK_HEXAHEDRON,  # 12
        vtk.VTK_WEDGE,  # 13
        vtk.VTK_PYRAMID,  # 14
        vtk.VTK_VOXEL,  # 11
        vtk.VTK_PENTAGONAL_PRISM,  # 15
        vtk.VTK_HEXAGONAL_PRISM,  # 16
        vtk.VTK_QUADRATIC_TETRA,  # 24
        vtk.VTK_QUADRATIC_HEXAHEDRON,  # 25
        vtk.VTK_QUADRATIC_WEDGE,  # 26
        vtk.VTK_QUADRATIC_PYRAMID,  # 27
    ]

    surfaceTypes = [
        vtk.VTK_TRIANGLE, vtk.VTK_QUAD, vtk.VTK_POLYGON, vtk.VTK_QUADRATIC_TRIANGLE, vtk.VTK_QUADRATIC_QUAD
    ]

    # Count cell types
    n3d = 0
    n2d = 0
    nOther = 0

    setupLogger.info( "Classifying cell types..." )
    for i in tqdm( range( mesh.GetNumberOfCells() ), desc="Scanning cells" ):
        cellType = mesh.GetCellType( i )

        if cellType in volumeTypes:
            n3d += 1
        elif cellType in surfaceTypes:
            n2d += 1
        else:
            nOther += 1

    setupLogger.info( f"Cell type breakdown:" )
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

    # Add cell type array for filtering
    cellTypes = vtk.vtkIntArray()
    cellTypes.SetName( "CellType" )
    cellTypes.SetNumberOfTuples( mesh.GetNumberOfCells() )

    for i in range( mesh.GetNumberOfCells() ):
        cellTypes.SetValue( i, mesh.GetCellType( i ) )

    mesh.GetCellData().AddArray( cellTypes )

    # Threshold filter to extract only 3D cells
    threshold = vtk.vtkThreshold()
    threshold.SetInputData( mesh )
    threshold.SetInputArrayToProcess( 0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, "CellType" )
    threshold.SetThresholdFunction( vtk.vtkThreshold.THRESHOLD_BETWEEN )
    threshold.SetLowerThreshold( 10 )  # Minimum 3D cell type
    threshold.SetUpperThreshold( 100 )  # Maximum reasonable cell type
    threshold.Update()

    filteredMesh = threshold.GetOutput()

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
    edges = set()
    nFaces = surface.GetNumberOfCells()

    for i in tqdm( range( nFaces ), desc="Processing faces" ):
        cell = surface.GetCell( i )
        nEdges = cell.GetNumberOfEdges()
        for j in range( nEdges ):
            edge = cell.GetEdge( j )
            pt1 = edge.GetPointId( 0 )
            pt2 = edge.GetPointId( 1 )
            edges.add( tuple( sorted( [ pt1, pt2 ] ) ) )

    return len( edges )


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

    # Extract surface from 3D elements
    surface = __extractSurface( mesh3d )

    # Get counts
    V = surface.GetNumberOfPoints()
    F = surface.GetNumberOfCells()
    E = __countUniqueEdges( surface )

    setupLogger.info( f"Surface topology:" )
    setupLogger.info( f"  Vertices (V): {V:,}" )
    setupLogger.info( f"  Edges    (E): {E:,}" )
    setupLogger.info( f"  Faces    (F): {F:,}" )

    # Calculate Euler characteristic
    euler = V - E + F

    setupLogger.info( f"Euler characteristic (χ = V - E + F): {euler}" )

    # Interpret result
    if euler == 2:
        setupLogger.info( "Topology: Closed surface (sphere-like)" )
    elif euler == 0:
        setupLogger.info( "Topology: Torus-like or open cylinder" )
    elif euler == 1:
        setupLogger.info( "Topology: Disk-like (open surface)" )
    else:
        genus = ( 2 - euler ) / 2
        setupLogger.info( f"Topology: Complex (genus g ≈ {genus:.1f})" )

    # Check mesh quality
    boundaryEdges, nonManifoldEdges = __checkMeshQuality( surface )

    setupLogger.info( f"Mesh quality:" )
    setupLogger.info( f"  Boundary edges:     {boundaryEdges:,}" )
    setupLogger.info( f"  Non-manifold edges: {nonManifoldEdges:,}" )

    if boundaryEdges == 0 and nonManifoldEdges == 0:
        setupLogger.info( "  Perfect closed manifold mesh!" )
    elif boundaryEdges > 0:
        setupLogger.warning( "  Open surface detected (has boundaries)" )
    if nonManifoldEdges > 0:
        setupLogger.warning( "  Non-manifold edges detected (mesh has issues!)" )

    return Result( numVertices=V,
                   numEdges=E,
                   numFaces=F,
                   eulerCharacteristic=euler,
                   num3dCells=n3d,
                   num2dCells=n2d,
                   numOtherCells=nOther,
                   numBoundaryEdges=boundaryEdges,
                   numNonManifoldEdges=nonManifoldEdges )


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
