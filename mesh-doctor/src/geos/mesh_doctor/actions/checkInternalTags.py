# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Check that tagged 2D elements are internal (have exactly 2 volume neighbors)."""

from dataclasses import dataclass
from typing import Optional, Dict, List, Union
import vtk
from tqdm import tqdm
import numpy as np

from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid, writeMesh, VtkOutput


@dataclass( frozen=True )
class Options:
    """Options for the internal tags check.

    Attributes:
        tagValues: List of tag values to check
        tagArrayName: Name of the cell data array containing tags
        outputCsv: Optional path to output CSV file with problematic elements
        nullTagValue: Optional tag value to assign to faulty cells (e.g., 9999)
        fixedVtkOutput: Optional VtkOutput for mesh with faulty cells retagged
        verbose: Enable detailed connectivity diagnostics for problematic cells
        boundaryDistance: Optional safety distance from mesh boundary. Cells within this
                         distance will be untagged (set to nullTagValue)
        boundaryMode: Which boundaries to check: 'all', 'bottom', 'top'
    """
    tagValues: tuple[ int, ...]
    tagArrayName: str
    outputCsv: Optional[ str ]
    nullTagValue: Optional[ int ]
    fixedVtkOutput: Optional[ VtkOutput ]
    verbose: bool = False
    boundaryDistance: Optional[ float ] = None
    boundaryMode: str = 'all'


@dataclass( frozen=True )
class Result:
    """Result of the internal tags check.

    Attributes:
        info: Summary information about the check
        passed: Whether all checked elements have exactly 2 neighbors
    """
    info: str
    passed: bool


@dataclass( frozen=True )
class ElementInfo:
    """Information about a tagged element.

    Attributes:
        cellId: Cell ID in the mesh
        tag: Tag value
        numNeighbors: Number of volume neighbors
        neighbors: List of neighbor cell IDs
        distanceToBoundary: Distance to the nearest boundary (if computed)
    """
    cellId: int
    tag: int
    numNeighbors: int
    neighbors: list[ int ]
    distanceToBoundary: Optional[ float ] = None


def __getVolumeNeighbors( mesh: vtk.vtkUnstructuredGrid, cellId: int, volumeCells: set[ int ],
                          surfaceCellTypes: list[ int ] ) -> list[ int ]:
    """Find all volume neighbors of a 2D cell.

    Args:
        mesh: The unstructured grid
        cellId: ID of the 2D cell
        volumeCells: Set of volume cell IDs
        surfaceCellTypes: List of surface cell type IDs

    Returns:
        List of volume cell IDs that share all points with the 2D cell
    """
    surfaceCell = mesh.GetCell( cellId )

    # Get all points of the surface cell
    surfacePoints = set()
    for i in range( surfaceCell.GetNumberOfPoints() ):
        surfacePoints.add( surfaceCell.GetPointId( i ) )

    # Get cells connected to the first point
    firstPoint = surfaceCell.GetPointId( 0 )
    neighborCells = vtk.vtkIdList()
    mesh.GetPointCells( firstPoint, neighborCells )

    # Find volume cells that contain all surface points
    volumeNeighbors = []
    for i in range( neighborCells.GetNumberOfIds() ):
        neighborId = neighborCells.GetId( i )

        # Skip if not a volume cell
        if neighborId not in volumeCells:
            continue

        # Get points of the volume cell
        volumeCell = mesh.GetCell( neighborId )
        volumePoints = set()
        for j in range( volumeCell.GetNumberOfPoints() ):
            volumePoints.add( volumeCell.GetPointId( j ) )

        # Check if all surface points are in the volume cell
        if surfacePoints.issubset( volumePoints ):
            volumeNeighbors.append( neighborId )

    return volumeNeighbors


def __extractVolumeMeshBoundary( mesh: vtk.vtkUnstructuredGrid, volumeCells: set[ int ] ) -> vtk.vtkPolyData:
    """Extract the outer boundary (skin) of the 3D volume mesh.

    This finds all faces of 3D volume elements that have no neighbor, which form
    the outer boundary of the mesh domain.

    Args:
        mesh: The unstructured grid
        volumeCells: Set of volume cell IDs

    Returns:
        PolyData containing the boundary surface of the volume mesh
    """
    setupLogger.info( "Extracting outer boundary of 3D volume mesh..." )

    # Create a mesh containing only volume cells
    volumeMesh = vtk.vtkUnstructuredGrid()
    volumeMesh.SetPoints( mesh.GetPoints() )

    # Build a mapping from original cell IDs to volume mesh cell IDs
    for cellId in tqdm( volumeCells, desc="Building volume mesh" ):
        cell = mesh.GetCell( cellId )
        volumeMesh.InsertNextCell( cell.GetCellType(), cell.GetPointIds() )

    setupLogger.info( f"Volume mesh has {volumeMesh.GetNumberOfCells()} cells" )

    # Use VTK's geometry filter to extract the outer surface
    # This finds all faces that are only connected to one cell (external faces)
    geometryFilter = vtk.vtkGeometryFilter()
    geometryFilter.SetInputData( volumeMesh )
    geometryFilter.Update()

    boundarySurface = geometryFilter.GetOutput()
    setupLogger.info( f"Extracted boundary surface with {boundarySurface.GetNumberOfCells()} faces" )

    return boundarySurface


def __classifyBoundarySurfaceByLocation( boundarySurface: vtk.vtkPolyData ) -> Dict[ str, vtk.vtkPolyData ]:
    """Classify boundary surface faces by their location using Z-range based approach.

    This approach works well for uneven surfaces (topography):
    - Bottom: faces in the lower 5% of Z-range
    - Top: faces in the upper 5% of Z-range

    Args:
        boundarySurface: PolyData containing the boundary surface

    Returns:
        Dictionary with keys 'bottom', 'top' containing PolyData surfaces
    """
    bounds = boundarySurface.GetBounds()
    zMin = bounds[ 4 ]
    zMax = bounds[ 5 ]
    zRange = zMax - zMin

    # In order to capture uneven surfaces:
    # Define "bottom zone" as lowest 5% of Z-range
    # Define "top zone" as highest 5% of Z-range
    zonePercentage = 0.05

    bottomZoneHeight = zRange * zonePercentage
    topZoneHeight = zRange * zonePercentage

    bottomThreshold = zMin + bottomZoneHeight
    topThreshold = zMax - topZoneHeight

    setupLogger.info( f"Classifying {boundarySurface.GetNumberOfCells()} boundary faces by Z-coordinate:" )
    setupLogger.info( f"  Boundary surface Z-range: [{zMin:.3f}, {zMax:.3f}] (total: {zRange:.3f})" )
    setupLogger.info(
        f"  Bottom zone ({zonePercentage*100:.0f}% of range = {bottomZoneHeight:.3f}m): Z ≤ {bottomThreshold:.3f}" )
    setupLogger.info(
        f"  Top zone ({zonePercentage*100:.0f}% of range = {topZoneHeight:.3f}m): Z ≥ {topThreshold:.3f}" )

    # Create separate surfaces for bottom and top
    bottomSurface = vtk.vtkPolyData()
    bottomSurface.SetPoints( boundarySurface.GetPoints() )
    bottomCells = vtk.vtkCellArray()

    topSurface = vtk.vtkPolyData()
    topSurface.SetPoints( boundarySurface.GetPoints() )
    topCells = vtk.vtkCellArray()

    counters = { 'bottom': 0, 'top': 0, 'both': 0, 'neither': 0 }
    bottomZValues = []
    topZValues = []

    nCells = boundarySurface.GetNumberOfCells()
    for i in range( nCells ):
        cell = boundarySurface.GetCell( i )

        # Get min/max Z of all points in the cell
        minZ = float( 'inf' )
        maxZ = float( '-inf' )
        centerZ = 0.0

        nPoints = cell.GetNumberOfPoints()
        for j in range( nPoints ):
            pointId = cell.GetPointId( j )
            point = boundarySurface.GetPoint( pointId )
            z = point[ 2 ]
            minZ = min( minZ, z )
            maxZ = max( maxZ, z )
            centerZ += z
        centerZ /= nPoints

        # Classify based on Z-coordinate zones
        # A face is in the bottom zone if its minimum Z is in the bottom zone
        # A face is in the top zone if its maximum Z is in the top zone
        isBottom = minZ <= bottomThreshold
        isTop = maxZ >= topThreshold

        if isBottom and isTop:
            counters[ 'both' ] += 1
        elif isBottom:
            counters[ 'bottom' ] += 1
        elif isTop:
            counters[ 'top' ] += 1
        else:
            counters[ 'neither' ] += 1

        if isBottom:
            bottomCells.InsertNextCell( cell )
            bottomZValues.append( centerZ )

        if isTop:
            topCells.InsertNextCell( cell )
            topZValues.append( centerZ )

    bottomSurface.SetPolys( bottomCells )
    topSurface.SetPolys( topCells )

    setupLogger.info( "Classification results:" )
    setupLogger.info( f"  Bottom faces: {counters['bottom']}" )
    if bottomZValues:
        bottomZValues.sort()
        setupLogger.info( f"    Z range: [{bottomZValues[0]:.3f}, {bottomZValues[-1]:.3f}]" )

    setupLogger.info( f"  Top faces: {counters['top']}" )
    if topZValues:
        topZValues.sort()
        setupLogger.info( f"    Z range: [{topZValues[0]:.3f}, {topZValues[-1]:.3f}]" )

    setupLogger.info( f"  Both (spanning zones): {counters['both']}" )
    setupLogger.info( f"  Neither (middle region): {counters['neither']}" )

    return { 'bottom': bottomSurface, 'top': topSurface }


def __getBoundarySurfaceForMode( classified: Dict[ str, vtk.vtkPolyData ], mode: str ) -> vtk.vtkPolyData:
    """Get boundary surface matching the specified mode.

    Args:
        classified: Dictionary of classified boundary surfaces
        mode: Which boundaries to include ('all', 'bottom', 'top')

    Returns:
        PolyData surface matching the mode
    """
    if mode == 'bottom':
        return classified[ 'bottom' ]
    elif mode == 'top':
        return classified[ 'top' ]
    elif mode == 'all':
        # Combine top and bottom
        appendFilter = vtk.vtkAppendPolyData()
        appendFilter.AddInputData( classified[ 'bottom' ] )
        appendFilter.AddInputData( classified[ 'top' ] )
        appendFilter.Update()
        return appendFilter.GetOutput()
    else:
        # Return empty surface for invalid mode
        return vtk.vtkPolyData()


def __buildSurfaceLocator( surface: vtk.vtkPolyData ) -> Optional[ vtk.vtkCellLocator ]:
    """Build a spatial locator for a surface to speed up distance queries.

    Args:
        surface: PolyData surface

    Returns:
        VTK cell locator for the surface, or None if surface is empty
    """
    if surface.GetNumberOfCells() == 0:
        setupLogger.warning( "Surface has no cells to build locator from" )
        return None

    setupLogger.info( f"Building spatial locator for surface with {surface.GetNumberOfCells()} faces..." )

    # Build locator
    locator = vtk.vtkCellLocator()
    locator.SetDataSet( surface )
    locator.BuildLocator()

    return locator


def __computeDistanceToSurface( mesh: vtk.vtkUnstructuredGrid, cellId: int, locator: vtk.vtkCellLocator ) -> float:
    """Compute the minimum distance from a cell to a surface using a spatial locator.

    Args:
        mesh: The unstructured grid
        cellId: ID of the cell to measure from
        locator: VTK cell locator for the surface

    Returns:
        Minimum distance to surface
    """
    # Get center of the cell
    cell = mesh.GetCell( cellId )
    cellCenter = [ 0.0, 0.0, 0.0 ]

    # Compute cell center as average of all points
    nPoints = cell.GetNumberOfPoints()
    for i in range( nPoints ):
        pointId = cell.GetPointId( i )
        point = mesh.GetPoint( pointId )
        for j in range( 3 ):
            cellCenter[ j ] += point[ j ]

    for j in range( 3 ):
        cellCenter[ j ] /= nPoints

    # Find closest point on surface
    closestPoint = [ 0.0, 0.0, 0.0 ]
    cellIdVtk = vtk.reference( 0 )
    subId = vtk.reference( 0 )
    dist2 = vtk.reference( 0.0 )

    locator.FindClosestPoint( cellCenter, closestPoint, cellIdVtk, subId, dist2 )

    return np.sqrt( dist2.get() )


def __diagnose1NeighborCell( mesh: vtk.vtkUnstructuredGrid, elem: ElementInfo, volumeCells: set[ int ] ) -> None:
    """Diagnose a cell with only 1 neighbor by showing face-by-face neighbors.

    Args:
        mesh: The unstructured grid
        elem: The problematic element info (must have exactly 1 neighbor)
        volumeCells: Set of all volume cell IDs
    """
    if elem.numNeighbors != 1:
        return

    # Get the 2D surface cell we're trying to match
    surfaceCell = mesh.GetCell( elem.cellId )
    surfacePointIds = surfaceCell.GetPointIds()
    surfaceNodes = [ surfacePointIds.GetId( i ) for i in range( surfacePointIds.GetNumberOfIds() ) ]

    neighborCellId = elem.neighbors[ 0 ]
    volumeCell = mesh.GetCell( neighborCellId )
    cellTypeName = volumeCell.GetClassName()
    numFaces = volumeCell.GetNumberOfFaces()

    distInfo = f", distance to boundary: {elem.distanceToBoundary:.3f}" if elem.distanceToBoundary is not None else ""
    setupLogger.warning( f"  Cell {elem.cellId} (tag={elem.tag}) has only 1 neighbor: cell {neighborCellId}{distInfo}" )
    setupLogger.warning( f"    2D element nodes: {surfaceNodes}" )
    setupLogger.warning( f"    Cell type: {cellTypeName} ({numFaces} faces)" )
    setupLogger.warning( "    Face-by-face neighbors:" )

    # For each face of the volume cell, find the neighbor
    for faceIdx in range( numFaces ):
        face = volumeCell.GetFace( faceIdx )
        facePointIds = face.GetPointIds()

        # Find neighboring cells that share this face
        neighborCells = vtk.vtkIdList()
        mesh.GetCellNeighbors( neighborCellId, facePointIds, neighborCells )

        # Filter to only volume cells
        volumeNeighbors = []
        for i in range( neighborCells.GetNumberOfIds() ):
            nId = neighborCells.GetId( i )
            if nId in volumeCells and nId != neighborCellId:
                volumeNeighbors.append( nId )

        if volumeNeighbors:
            setupLogger.warning( f"      Face {faceIdx}: {volumeNeighbors}" )
        else:
            setupLogger.warning( f"      Face {faceIdx}: <boundary or no 3D neighbor>" )


def checkInternalTags( mesh: vtk.vtkUnstructuredGrid, options: Options ) -> Result:
    """Check that all 2D elements with specified tags have exactly 2 volume neighbors.

    Args:
        mesh: Input unstructured grid
        options: Check options

    Returns:
        Result with summary information

    Raises:
        ValueError: If tag array not found or other validation errors
    """
    setupLogger.info( f"Mesh: {mesh.GetNumberOfPoints()} points, {mesh.GetNumberOfCells()} cells" )

    # Validate options
    validModes = { 'all', 'bottom', 'top' }
    if options.boundaryMode not in validModes:
        raise ValueError( f"Invalid boundaryMode '{options.boundaryMode}'. Must be one of {validModes}" )

    # Get tags array
    cellData = mesh.GetCellData()
    if not cellData.HasArray( options.tagArrayName ):
        availableArrays = [ cellData.GetArrayName( i ) for i in range( cellData.GetNumberOfArrays() ) ]
        raise ValueError( f"Tag array '{options.tagArrayName}' not found. "
                          f"Available cell data arrays: {availableArrays}" )

    tags = cellData.GetArray( options.tagArrayName )

    # Convert tag array to int if needed
    if not isinstance( tags, vtk.vtkIntArray ):
        setupLogger.info( f"Converting tag array '{options.tagArrayName}' to integer type..." )
        intTagsArray = vtk.vtkIntArray()
        intTagsArray.SetName( tags.GetName() )
        intTagsArray.SetNumberOfComponents( tags.GetNumberOfComponents() )
        for i in range( tags.GetNumberOfTuples() ):
            intTagsArray.InsertNextValue( int( tags.GetValue( i ) ) )
        mesh.GetCellData().RemoveArray( options.tagArrayName )
        mesh.GetCellData().AddArray( intTagsArray )
        tags = intTagsArray

    # Define cell types
    SURFACE_CELL_TYPES = [ vtk.VTK_TRIANGLE, vtk.VTK_QUAD, vtk.VTK_POLYGON, vtk.VTK_PIXEL ]
    VOLUME_CELL_TYPES = [ vtk.VTK_TETRA, vtk.VTK_HEXAHEDRON, vtk.VTK_WEDGE, vtk.VTK_PYRAMID, vtk.VTK_VOXEL ]

    # Build connectivity
    setupLogger.info( "Building cell connectivity..." )
    mesh.BuildLinks()

    # Find volume cells and build tag mapping for 2D cells in one pass
    nCells = mesh.GetNumberOfCells()
    volumeCells = set()
    tagToCells: Dict[ int, List[ int ] ] = {}  # Map tag values to list of 2D cell IDs

    for cellId in tqdm( range( nCells ), desc="Building cell mappings" ):
        cellType = mesh.GetCellType( cellId )

        # Collect volume cells
        if cellType in VOLUME_CELL_TYPES:
            volumeCells.add( cellId )

        # Collect 2D cells by tag (only for tags we're interested in)
        if cellType in SURFACE_CELL_TYPES:
            currentTag = tags.GetValue( cellId )
            if currentTag in options.tagValues:
                if currentTag not in tagToCells:
                    tagToCells[ currentTag ] = []
                tagToCells[ currentTag ].append( cellId )

    setupLogger.info( f"Found {len(volumeCells)} volume cells" )

    # =============================================================================
    # Optional safety margin check
    # Extract 3D volume mesh boundary and check distance to it
    # =============================================================================

    boundaryLocator = None
    cellsNearBoundary = set()

    if options.boundaryDistance is not None:
        if options.boundaryDistance <= 0:
            raise ValueError( f"boundaryDistance must be positive, got {options.boundaryDistance}" )

        setupLogger.info( f"{'='*60}" )
        setupLogger.info( "BOUNDARY PROXIMITY CHECK" )
        setupLogger.info( f"  Distance threshold: {options.boundaryDistance}" )
        setupLogger.info( f"  Boundary mode: {options.boundaryMode}" )
        setupLogger.info( f"{'='*60}" )

        # Extract the outer boundary of the 3D volume mesh
        boundarySurface = __extractVolumeMeshBoundary( mesh, volumeCells )

        if boundarySurface.GetNumberOfCells() == 0:
            setupLogger.warning( "No boundary surface extracted from volume mesh. Skipping boundary distance check." )
        else:
            # Classify boundary surface by location
            classifiedSurfaces = __classifyBoundarySurfaceByLocation( boundarySurface )

            # Get the surface for the requested mode
            targetSurface = __getBoundarySurfaceForMode( classifiedSurfaces, options.boundaryMode )

            if targetSurface.GetNumberOfCells() == 0:
                setupLogger.warning(
                    f"No boundary surface faces found for mode '{options.boundaryMode}'. Skipping boundary distance check."
                )
            else:
                setupLogger.info(
                    f"Using {targetSurface.GetNumberOfCells()} boundary faces for mode '{options.boundaryMode}'" )

                # Build locator for the target surface
                boundaryLocator = __buildSurfaceLocator( targetSurface )

                if boundaryLocator is None:
                    setupLogger.warning( "Failed to build boundary locator. Skipping boundary distance check." )
                else:
                    # Get all tagged cells
                    allTaggedCells = []
                    for tagValue in options.tagValues:
                        allTaggedCells.extend( tagToCells.get( tagValue, [] ) )

                    setupLogger.info( f"Checking {len(allTaggedCells)} tagged cells..." )

                    # Compute distances for all tagged cells
                    descText = f"Computing distances to {options.boundaryMode} boundary"
                    for cellId in tqdm( allTaggedCells, desc=descText ):
                        distance = __computeDistanceToSurface( mesh, cellId, boundaryLocator )

                        if distance <= options.boundaryDistance:
                            cellsNearBoundary.add( cellId )

                    setupLogger.info(
                        f"Found {len(cellsNearBoundary)} cells within {options.boundaryDistance} of boundary ({options.boundaryMode})"
                    )

        if cellsNearBoundary and options.nullTagValue is not None:
            setupLogger.info( f"These cells will be untagged (set to {options.nullTagValue})" )
        elif cellsNearBoundary and options.nullTagValue is None:
            setupLogger.warning( "Cells near boundary found, but no nullTagValue specified for untagging" )

    # =============================================================================
    # Check that tagged cells have exactly 2 volume neighbors
    # This is the primary validation: cells with != 2 neighbors are on boundary
    # =============================================================================

    # Store results by tag
    tagResults = {}
    allBadElements = []
    allBoundaryElements = []
    cellsNearBoundaryByTag = {}  # Track boundary cells per tag

    # Process each tag value
    for tagValue in options.tagValues:
        setupLogger.info( f"{'='*60}" )
        setupLogger.info( f"Checking tag = {tagValue}" )
        setupLogger.info( f"{'='*60}" )

        elementsByNeighbors: Dict[ Union[ int, str ], List[ ElementInfo ] ] = { 0: [], 1: [], 2: [], 'other': [] }

        # Get cells with this tag (pre-filtered)
        cellsWithTag = tagToCells.get( tagValue, [] )
        setupLogger.info( f"Found {len(cellsWithTag)} cells with tag {tagValue}" )

        # Track cells near boundary for this specific tag
        cellsNearBoundaryThisTag = set()

        # Process only the cells with this specific tag
        for cellId in tqdm( cellsWithTag, desc=f"Processing tag {tagValue}" ):
            # Count volume neighbors
            volumeNeighbors = __getVolumeNeighbors( mesh, cellId, volumeCells, SURFACE_CELL_TYPES )
            numNeighbors = len( volumeNeighbors )

            # Compute distance to boundary if needed (only in verbose mode for performance)
            distToBoundary = None
            if options.verbose and options.boundaryDistance is not None and boundaryLocator is not None:
                distToBoundary = __computeDistanceToSurface( mesh, cellId, boundaryLocator )

            elemInfo = ElementInfo( cellId=cellId,
                                    tag=tagValue,
                                    numNeighbors=numNeighbors,
                                    neighbors=volumeNeighbors,
                                    distanceToBoundary=distToBoundary )

            # Categorize by neighbor count
            if numNeighbors in { 0, 1, 2 }:
                elementsByNeighbors[ numNeighbors ].append( elemInfo )
            else:
                elementsByNeighbors[ 'other' ].append( elemInfo )

            # Track cells near boundary
            if cellId in cellsNearBoundary:
                allBoundaryElements.append( elemInfo )
                cellsNearBoundaryThisTag.add( cellId )

        # Store boundary cells for this tag
        cellsNearBoundaryByTag[ tagValue ] = cellsNearBoundaryThisTag

        # Calculate totals
        total = sum( len( v ) for v in elementsByNeighbors.values() )
        nearBoundary = len( cellsNearBoundaryThisTag )

        # Print summary for this tag
        setupLogger.info( f"Summary for tag = {tagValue}:" )
        setupLogger.info( f"  Total 2D cells: {total}" )
        setupLogger.info( f"  With 0 neighbors: {len(elementsByNeighbors[0])} cells" )
        setupLogger.info( f"  With 1 neighbor:  {len(elementsByNeighbors[1])} cells" )
        setupLogger.info( f"  With 2 neighbors: {len(elementsByNeighbors[2])} cells" )
        setupLogger.info( f"  With 3+ neighbors: {len(elementsByNeighbors['other'])} cells" )

        if options.boundaryDistance is not None:
            setupLogger.info(
                f"  Near boundary ({options.boundaryMode}, d ≤ {options.boundaryDistance}): {nearBoundary} cells" )
            if nearBoundary > 0:
                percentage = 100.0 * nearBoundary / total if total > 0 else 0.0
                setupLogger.info( f"    -> {percentage:.1f}% of tag {tagValue} cells will be untagged" )

        # Collect bad elements (excluding those near boundary that will be untagged)
        for elem in elementsByNeighbors[ 0 ]:
            if elem.cellId not in cellsNearBoundary:
                allBadElements.append( elem )
        for elem in elementsByNeighbors[ 1 ]:
            if elem.cellId not in cellsNearBoundary:
                allBadElements.append( elem )
        for elem in elementsByNeighbors[ 'other' ]:
            if elem.cellId not in cellsNearBoundary:
                allBadElements.append( elem )

        tagResults[ tagValue ] = elementsByNeighbors

    # Print overall summary
    setupLogger.info( f"{'='*60}" )
    setupLogger.info( "OVERALL SUMMARY" )
    setupLogger.info( f"{'='*60}" )

    totalBad = len( allBadElements )
    totalNearBoundary = len( { elem.cellId for elem in allBoundaryElements } )
    totalChecked = sum( sum( len( v ) for v in neighbors.values() ) for neighbors in tagResults.values() )

    setupLogger.info( f"Tags checked: {list(options.tagValues)}" )
    setupLogger.info( f"Total 2D cells checked: {totalChecked}" )
    setupLogger.info( f"Cells with exactly 2 neighbors: {totalChecked - totalBad - totalNearBoundary}" )
    setupLogger.info( f"Cells with other than 2 neighbors: {totalBad}" )

    if options.boundaryDistance is not None:
        setupLogger.info(
            f"Cells near boundary ({options.boundaryMode}, d ≤ {options.boundaryDistance}): {totalNearBoundary}" )
        setupLogger.info( "Breakdown by tag:" )
        for tagValue in sorted( options.tagValues ):
            numNear = len( cellsNearBoundaryByTag.get( tagValue, set() ) )
            totalForTag = sum( len( v ) for v in tagResults[ tagValue ].values() )
            percentage = 100.0 * numNear / totalForTag if totalForTag > 0 else 0.0
            setupLogger.info( f"  Tag {tagValue}: {numNear}/{totalForTag} cells ({percentage:.1f}%) will be untagged" )

    if totalBad > 0:
        setupLogger.warning( f"Found {totalBad} problematic cells across all tags (excluding boundary cells)!" )
        # Group bad elements by tag for reporting
        badByTag = {}
        for elem in allBadElements:
            if elem.tag not in badByTag:
                badByTag[ elem.tag ] = 0
            badByTag[ elem.tag ] += 1
        for tag, count in sorted( badByTag.items() ):
            setupLogger.warning( f"   Tag {tag}: {count} problematic cells" )

        # Diagnose cells with only 1 neighbor (only in verbose mode)
        if options.verbose:
            oneNeighborCells = [ elem for elem in allBadElements if elem.numNeighbors == 1 ]
            if oneNeighborCells:
                setupLogger.warning( f"{'='*60}" )
                setupLogger.warning( "CONNECTIVITY ANALYSIS FOR 1-NEIGHBOR CELLS" )
                setupLogger.warning( f"{'='*60}" )

                for elem in oneNeighborCells:
                    __diagnose1NeighborCell( mesh, elem, volumeCells )
    else:
        setupLogger.info( "All cells have exactly 2 neighbors (excluding boundary cells)!" )


    # Write to CSV if requested
    if options.outputCsv and ( allBadElements or allBoundaryElements ):
        setupLogger.info( f"Writing problematic elements to: {options.outputCsv}" )
        with open( options.outputCsv, 'w' ) as f:
            f.write( "cell_id,tag,num_neighbors,neighbor_1,neighbor_2,reason,distance_to_boundary\n" )

            # Write bad elements
            for elem in allBadElements:
                neighbor1 = elem.neighbors[ 0 ] if len( elem.neighbors ) > 0 else -1
                neighbor2 = elem.neighbors[ 1 ] if len( elem.neighbors ) > 1 else -1
                distStr = f"{elem.distanceToBoundary:.6f}" if elem.distanceToBoundary is not None else ""
                f.write(
                    f"{elem.cellId},{elem.tag},{elem.numNeighbors},{neighbor1},{neighbor2},bad_connectivity,{distStr}\n"
                )

            # Write boundary elements
            for elem in allBoundaryElements:
                neighbor1 = elem.neighbors[ 0 ] if len( elem.neighbors ) > 0 else -1
                neighbor2 = elem.neighbors[ 1 ] if len( elem.neighbors ) > 1 else -1
                # Compute distance if not already available
                dist = elem.distanceToBoundary
                if dist is None and boundaryLocator is not None:
                    dist = __computeDistanceToSurface( mesh, elem.cellId, boundaryLocator )
                distStr = f"{dist:.6f}" if dist is not None else ""
                f.write(
                    f"{elem.cellId},{elem.tag},{elem.numNeighbors},{neighbor1},{neighbor2},near_boundary,{distStr}\n" )

        totalWritten = len( allBadElements ) + len( { elem.cellId for elem in allBoundaryElements } )
        setupLogger.info(
            f"Written {totalWritten} rows ({len(allBadElements)} bad connectivity, {len({elem.cellId for elem in allBoundaryElements})} near boundary)"
        )
    elif options.outputCsv and not allBadElements and not allBoundaryElements:
        setupLogger.info( "No problematic elements to write (all cells have 2 neighbors and none near boundary)" )

    # Retag faulty cells and write fixed mesh if requested
    cellsToRetag: set[ int ] = set()

    # Add bad connectivity cells
    if allBadElements:
        cellsToRetag.update( elem.cellId for elem in allBadElements )

    # Add boundary proximity cells
    if options.boundaryDistance is not None and cellsNearBoundary:
        cellsToRetag.update( cellsNearBoundary )

    if options.fixedVtkOutput and options.nullTagValue is not None and cellsToRetag:
        setupLogger.info( f"Retagging {len(cellsToRetag)} cells to tag {options.nullTagValue}..." )

        # Breakdown by reason
        numBadConnectivity = len( allBadElements )
        numNearBoundary = len( cellsNearBoundary )
        badCellIds = { elem.cellId for elem in allBadElements }
        numOverlap = len( badCellIds & cellsNearBoundary )

        setupLogger.info( f"  - Bad connectivity: {numBadConnectivity} cells" )
        if options.boundaryDistance is not None:
            setupLogger.info( f"  - Near boundary ({options.boundaryMode}): {numNearBoundary} cells" )
            setupLogger.info( f"    (overlap with bad connectivity: {numOverlap})" )

        # Get the tags array
        tagsArray = mesh.GetCellData().GetArray( options.tagArrayName )

        # Retag the problematic cells
        numRetagged = 0
        for cellId in cellsToRetag:
            tagsArray.SetValue( cellId, options.nullTagValue )
            numRetagged += 1

        setupLogger.info( f"Retagged {numRetagged} cells" )

        # Write the modified mesh (tag array already in int format)
        writeMesh( mesh, options.fixedVtkOutput )
        setupLogger.info( f"Written fixed mesh to: {options.fixedVtkOutput.output}" )
    elif options.fixedVtkOutput and not cellsToRetag:
        setupLogger.info( "No cells to retag (all cells have 2 neighbors and none near boundary)" )
    elif options.fixedVtkOutput and options.nullTagValue is None:
        setupLogger.warning( "Cannot write fixed mesh: --nullTagValue not provided (e.g., add --nullTagValue 9999)" )

    # Create result message
    totalProblematic = len( cellsToRetag )
    if totalProblematic > 0:
        reasons = []
        if totalBad > 0:
            reasons.append( f"{totalBad} with bad connectivity" )
        if totalNearBoundary > 0:
            reasons.append( f"{totalNearBoundary} near boundary ({options.boundaryMode})" )

        resultMsg = f"FAILED: Found {totalProblematic} problematic elements out of {totalChecked} checked ({', '.join(reasons)})"
        passed = False
    else:
        resultMsg = f"PASSED: All {totalChecked} tagged elements are internal (have exactly 2 volume neighbors)"
        if options.boundaryDistance is not None:
            resultMsg += f" and none are within {options.boundaryDistance} of boundary ({options.boundaryMode})"
        passed = True

    return Result( info=resultMsg, passed=passed )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Main action to check that tagged elements are internal.

    Args:
        vtuInputFile: Path to input VTU file
        options: Check options

    Returns:
        Result with summary information
    """
    mesh = readUnstructuredGrid( vtuInputFile )
    return checkInternalTags( mesh, options )
