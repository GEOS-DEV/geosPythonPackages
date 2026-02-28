# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Check that tagged 2D elements are internal (have exactly 2 volume neighbors)."""

from dataclasses import dataclass
from typing import Optional, Dict, List, Any, Union
import vtk
from tqdm import tqdm

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
    """
    tagValues: tuple[ int, ...]
    tagArrayName: str
    outputCsv: Optional[ str ]
    nullTagValue: Optional[ int ]
    fixedVtkOutput: Optional[ VtkOutput ]
    verbose: bool = False


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
    """
    cellId: int
    tag: int
    numNeighbors: int
    neighbors: list[ int ]


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

    setupLogger.warning( f"  Cell {elem.cellId} (tag={elem.tag}) has only 1 neighbor: cell {neighborCellId}" )
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

    # Store results by tag
    tagResults = {}
    allBadElements = []

    # Process each tag value
    for tagValue in options.tagValues:
        setupLogger.info( f"{'='*60}" )
        setupLogger.info( f"Checking tag = {tagValue}" )
        setupLogger.info( f"{'='*60}" )

        elementsByNeighbors: Dict[Union[int, str], List[ElementInfo]] = { 0: [], 1: [], 2: [], 'other': [] }

        # Get cells with this tag (pre-filtered)
        cellsWithTag = tagToCells.get( tagValue, [] )
        setupLogger.info( f"Found {len(cellsWithTag)} cells with tag {tagValue}" )

        # Process only the cells with this specific tag
        for cellId in tqdm( cellsWithTag, desc=f"Processing tag {tagValue}" ):
            # Count volume neighbors
            volumeNeighbors = __getVolumeNeighbors( mesh, cellId, volumeCells, SURFACE_CELL_TYPES )
            numNeighbors = len( volumeNeighbors )

            elemInfo = ElementInfo( cellId=cellId, tag=tagValue, numNeighbors=numNeighbors, neighbors=volumeNeighbors )

            # Categorize by neighbor count
            if numNeighbors in { 0, 1, 2 }:
                elementsByNeighbors[ numNeighbors ].append( elemInfo )
            else:
                elementsByNeighbors[ 'other' ].append( elemInfo )

        # Calculate totals
        total = sum( len( v ) for v in elementsByNeighbors.values() )

        # Print summary for this tag
        setupLogger.info( f"Summary for tag = {tagValue}:" )
        setupLogger.info( f"  Total 2D cells: {total}" )
        setupLogger.info( f"  With 0 neighbors: {len(elementsByNeighbors[0])} cells" )
        setupLogger.info( f"  With 1 neighbor:  {len(elementsByNeighbors[1])} cells" )
        setupLogger.info( f"  With 2 neighbors: {len(elementsByNeighbors[2])} cells" )
        setupLogger.info( f"  With 3+ neighbors: {len(elementsByNeighbors['other'])} cells" )

        # Collect bad elements
        allBadElements.extend( elementsByNeighbors[ 0 ] )
        allBadElements.extend( elementsByNeighbors[ 1 ] )
        allBadElements.extend( elementsByNeighbors[ 'other' ] )

        tagResults[ tagValue ] = elementsByNeighbors

    # Print overall summary
    setupLogger.info( f"{'='*60}" )
    setupLogger.info( "OVERALL SUMMARY" )
    setupLogger.info( f"{'='*60}" )

    totalBad = len( allBadElements )
    totalChecked = sum( sum( len( v ) for v in neighbors.values() ) for neighbors in tagResults.values() )

    setupLogger.info( f"Tags checked: {list(options.tagValues)}" )
    setupLogger.info( f"Total 2D cells checked: {totalChecked}" )
    setupLogger.info( f"Cells with exactly 2 neighbors: {totalChecked - totalBad}" )
    setupLogger.info( f"Cells with other than 2 neighbors: {totalBad}" )

    if totalBad > 0:
        setupLogger.warning( f"Found {totalBad} problematic cells across all tags!" )
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
        setupLogger.info( "All cells have exactly 2 neighbors!" )

    # Write to CSV if requested
    if options.outputCsv and allBadElements:
        setupLogger.info( f"Writing bad elements to: {options.outputCsv}" )
        with open( options.outputCsv, 'w' ) as f:
            f.write( "cell_id,tag,num_neighbors,neighbor_1,neighbor_2\n" )
            for elem in allBadElements:
                neighbor1 = elem.neighbors[ 0 ] if len( elem.neighbors ) > 0 else -1
                neighbor2 = elem.neighbors[ 1 ] if len( elem.neighbors ) > 1 else -1
                f.write( f"{elem.cellId},{elem.tag},{elem.numNeighbors},{neighbor1},{neighbor2}\n" )
        setupLogger.info( f"Written {len(allBadElements)} rows" )
    elif options.outputCsv and not allBadElements:
        setupLogger.info( "No bad elements to write (all cells have 2 neighbors)" )

    # Retag faulty cells and write fixed mesh if requested
    if options.fixedVtkOutput and options.nullTagValue is not None and allBadElements:
        setupLogger.info( f"Retagging {len(allBadElements)} faulty cells to tag {options.nullTagValue}..." )

        # Get the tags array
        tagsArray = mesh.GetCellData().GetArray( options.tagArrayName )

        # Create set of bad cell IDs for fast lookup
        badCellIds = { elem.cellId for elem in allBadElements }

        # Retag the problematic cells
        numRetagged = 0
        for cellId in badCellIds:
            tagsArray.SetValue( cellId, options.nullTagValue )
            numRetagged += 1

        setupLogger.info( f"Retagged {numRetagged} cells" )

        # Write the modified mesh (tag array already in int format)
        writeMesh( mesh, options.fixedVtkOutput )
        setupLogger.info( f"Written fixed mesh to: {options.fixedVtkOutput.output}" )
    elif options.fixedVtkOutput and not allBadElements:
        setupLogger.info( "No faulty cells to retag (all cells have 2 neighbors)" )
    elif options.fixedVtkOutput and options.nullTagValue is None:
        setupLogger.warning( "Cannot write fixed mesh: --nullTagValue not provided (e.g., add --nullTagValue 9999)" )

    # Create result message
    if totalBad > 0:
        resultMsg = f"FAILED: Found {totalBad} non-internal elements out of {totalChecked} checked"
        passed = False
    else:
        resultMsg = f"PASSED: All {totalChecked} tagged elements are internal (have exactly 2 volume neighbors)"
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
