# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Bertrand Denel
from dataclasses import dataclass
from typing import Optional
import vtk
from tqdm import tqdm
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid, writeMesh, VtkOutput


@dataclass( frozen=True )
class Options:
    orphanVtkOutput: Optional[ VtkOutput ]
    cleanVtkOutput: Optional[ VtkOutput ]


@dataclass( frozen=True )
class Result:
    total2dCells: int
    total3dCells: int
    matched2dCells: int
    orphaned2dCells: int
    orphaned2dIndices: list[ int ]
    orphanMesh: Optional[ vtkUnstructuredGrid ]
    cleanMesh: Optional[ vtkUnstructuredGrid ]


def getCellFacePoints( cell: vtk.vtkCell ) -> list[ tuple[ int, ...] ]:
    """Extract all face point sets from a 3D cell.

    Args:
        cell: A 3D VTK cell.

    Returns:
        List of tuples containing sorted global point IDs for each face.
    """
    faces = []
    cellType = cell.GetCellType()

    if cellType == vtk.VTK_TETRA:
        # 4 triangular faces
        faces = [ [ 0, 1, 2 ], [ 0, 1, 3 ], [ 0, 2, 3 ], [ 1, 2, 3 ] ]
    elif cellType == vtk.VTK_HEXAHEDRON:
        # 6 quadrilateral faces
        faces = [ [ 0, 1, 2, 3 ], [ 4, 5, 6, 7 ], [ 0, 1, 5, 4 ], [ 1, 2, 6, 5 ], [ 2, 3, 7, 6 ], [ 3, 0, 4, 7 ] ]
    elif cellType == vtk.VTK_WEDGE:
        # 2 triangular + 3 quadrilateral faces
        faces = [ [ 0, 1, 2 ], [ 3, 4, 5 ], [ 0, 1, 4, 3 ], [ 1, 2, 5, 4 ], [ 2, 0, 3, 5 ] ]
    elif cellType == vtk.VTK_PYRAMID:
        # 1 quadrilateral + 4 triangular faces
        faces = [ [ 0, 1, 2, 3 ], [ 0, 1, 4 ], [ 1, 2, 4 ], [ 2, 3, 4 ], [ 3, 0, 4 ] ]
      else:
           raise NotImplementedError(f"Orphaned2d is not implemented for cell type {cellType}. It is supported for TETRAHEDRA ({vtk.VTK_TETRA}), HEXA {(vtk.VTK_HEXAHEDRON}), WEDGE ({vtk.VTK_WEDGE}) and PYRAMID ({vtk.VTK_PYRAMID})")

    # Convert local indices to global point IDs
    pointIds = cell.GetPointIds()
    globalFaces = []
    for face in faces:
        #sort to make comparison permutation invariant
        globalFace = tuple( sorted( [ pointIds.GetId( i ) for i in face ] ) )
        globalFaces.append( globalFace )

    return globalFaces


def buildMeshSubset( mesh: vtkUnstructuredGrid, cellIndices: list[ int ], description: str ) -> vtkUnstructuredGrid:
    """Build a new mesh containing only the specified cells.

    Args:
        mesh: Input unstructured grid.
        cellIndices: List of cell indices to include.
        description: Description for progress messages.

    Returns:
        A new vtkUnstructuredGrid containing only the specified cells.
    """
    if not cellIndices:
        setupLogger.info( f"No {description} to create." )
        return None

    setupLogger.info( f"Creating mesh with {len(cellIndices)} {description}..." )

    # Create new unstructured grid
    newMesh = vtkUnstructuredGrid()
    newPoints = vtk.vtkPoints()

    # Preserve point data type (precision) from input mesh
    oldPoints = mesh.GetPoints()
    newPoints.SetDataType( oldPoints.GetDataType() )

    # Map old point IDs to new point IDs
    pointMap = {}
    newPointId = 0

    # Add cells
    for oldCellId in tqdm( cellIndices, desc=f"Building {description} mesh" ):
        cell = mesh.GetCell( oldCellId )
        pointIds = cell.GetPointIds()

        # Create new point IDs if needed
        newCellPointIds = vtk.vtkIdList()
        for i in range( pointIds.GetNumberOfIds() ):
            oldId = pointIds.GetId( i )
            if oldId not in pointMap:
                pointMap[ oldId ] = newPointId
                newPoints.InsertNextPoint( mesh.GetPoint( oldId ) )
                newPointId += 1
            newCellPointIds.InsertNextId( pointMap[ oldId ] )

        newMesh.InsertNextCell( cell.GetCellType(), newCellPointIds )

    newMesh.SetPoints( newPoints )

    # Copy point data
    setupLogger.debug( "Copying point data..." )
    for i in range( mesh.GetPointData().GetNumberOfArrays() ):
        oldArray = mesh.GetPointData().GetArray( i )

        # Create new array with same type and number of components
        newArray = oldArray.NewInstance()
        newArray.SetName( oldArray.GetName() )
        newArray.SetNumberOfComponents( oldArray.GetNumberOfComponents() )

        for oldId in sorted( pointMap.keys() ):
            newArray.InsertNextTuple( oldArray.GetTuple( oldId ) )

        newMesh.GetPointData().AddArray( newArray )

    # Copy cell data
    setupLogger.debug( "Copying cell data..." )
    for i in range( mesh.GetCellData().GetNumberOfArrays() ):
        oldArray = mesh.GetCellData().GetArray( i )

        # Create new array with same type and number of components
        newArray = oldArray.NewInstance()
        newArray.SetName( oldArray.GetName() )
        newArray.SetNumberOfComponents( oldArray.GetNumberOfComponents() )

        for oldCellId in cellIndices:
            newArray.InsertNextTuple( oldArray.GetTuple( oldCellId ) )

        newMesh.GetCellData().AddArray( newArray )

    return newMesh


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Check if 2D cells are faces of 3D cells.

    Args:
        mesh: The input mesh to analyze.
        options: The options for processing.

    Returns:
        Result: The result of the orphan check.
    """
    setupLogger.info( "Starting orphan 2D cell check..." )

    # Separate 2D and 3D cells
    cell2dIndices = []
    cell3dIndices = []

    setupLogger.info( "Classifying cells by dimension..." )
    for i in tqdm( range( mesh.GetNumberOfCells() ), desc="Scanning cells" ):
        cell = mesh.GetCell( i )
        dim = cell.GetCellDimension()
        if dim == 2:
            cell2dIndices.append( i )
        elif dim == 3:
            cell3dIndices.append( i )

    setupLogger.info( f"Found {len(cell2dIndices)} 2D cells" )
    setupLogger.info( f"Found {len(cell3dIndices)} 3D cells" )

    # Build set of all faces from 3D cells
    setupLogger.info( "Extracting faces from 3D cells..." )
    all3dFaces = set()
    for idx in tqdm( cell3dIndices, desc="Processing 3D cells" ):
        cell = mesh.GetCell( idx )
        faces = getCellFacePoints( cell )
        all3dFaces.update( faces )

    setupLogger.info( f"Total unique faces from 3D cells: {len(all3dFaces)}" )

    # Check each 2D cell
    setupLogger.info( "Checking 2D cells against 3D faces..." )
    orphaned2dIndices = []
    matched2dCount = 0

    for idx in tqdm( cell2dIndices, desc="Checking 2D cells" ):
        cell = mesh.GetCell( idx )
        pointIds = cell.GetPointIds()

        # Get sorted point IDs for the 2D cell
        cellPoints = tuple( sorted( [ pointIds.GetId( i ) for i in range( pointIds.GetNumberOfIds() ) ] ) )

        if cellPoints in all3dFaces:
            matched2dCount += 1
        else:
            orphaned2dIndices.append( idx )

    setupLogger.info( f"2D cells that ARE faces of 3D cells: {matched2dCount}" )
    setupLogger.info( f"2D cells that are NOT faces of 3D cells: {len(orphaned2dIndices)}" )

    # Build orphan mesh if requested
    orphanMesh = None
    if options.orphanVtkOutput and orphaned2dIndices:
        orphanMesh = buildMeshSubset( mesh, orphaned2dIndices, "orphaned 2D cells" )

    # Build clean mesh if requested
    cleanMesh = None
    if options.cleanVtkOutput:
        if orphaned2dIndices:
            allCellIndices = list( range( mesh.GetNumberOfCells() ) )
            orphanedSet = set( orphaned2dIndices )
            cleanCellIndices = [ i for i in allCellIndices if i not in orphanedSet ]
            cleanMesh = buildMeshSubset( mesh, cleanCellIndices, "clean cells" )
        else:
            # No orphans, return the original mesh
            cleanMesh = mesh

    return Result( total2dCells=len( cell2dIndices ),
                   total3dCells=len( cell3dIndices ),
                   matched2dCells=matched2dCount,
                   orphaned2dCells=len( orphaned2dIndices ),
                   orphaned2dIndices=orphaned2dIndices,
                   orphanMesh=orphanMesh,
                   cleanMesh=cleanMesh )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Read a VTU file and check for orphaned 2D cells.

    Args:
        vtuInputFile: The path to the input VTU file.
        options: The options for processing.

    Returns:
        Result: The result of the orphan check.
    """
    mesh = readUnstructuredGrid( vtuInputFile )
    result = meshAction( mesh, options )

    # Write output files if requested
    if options.orphanVtkOutput and result.orphanMesh:
        setupLogger.info( f"Writing orphaned cells to {options.orphanVtkOutput.output}" )
        writeMesh( result.orphanMesh, options.orphanVtkOutput )

    if options.cleanVtkOutput and result.cleanMesh:
        setupLogger.info( f"Writing clean mesh to {options.cleanVtkOutput.output}" )
        writeMesh( result.cleanMesh, options.cleanVtkOutput )

    return result
