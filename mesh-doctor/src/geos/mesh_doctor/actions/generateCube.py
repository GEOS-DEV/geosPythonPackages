# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from typing import Iterable, Sequence
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkCellArray, vtkHexahedron, vtkRectilinearGrid, vtkUnstructuredGrid,
                                            VTK_HEXAHEDRON )
from geos.mesh.io.vtkIO import VtkOutput, writeMesh
from geos.mesh.utils.arrayModifiers import createConstantAttributeDataSet
from geos.mesh_doctor.actions.generateGlobalIds import buildGlobalIds
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.utils.pieceEnum import Piece


@dataclass( frozen=True )
class Result:
    info: str


@dataclass( frozen=True )
class FieldInfo:
    name: str
    dimension: int
    support: str


@dataclass( frozen=True )
class Options:
    vtkOutput: VtkOutput
    generateCellsGlobalIds: bool
    generatePointsGlobalIds: bool
    xs: Sequence[ float ]
    ys: Sequence[ float ]
    zs: Sequence[ float ]
    nxs: Sequence[ int ]
    nys: Sequence[ int ]
    nzs: Sequence[ int ]
    fields: Iterable[ FieldInfo ]


@dataclass( frozen=True )
class XYZ:
    x: npt.NDArray
    y: npt.NDArray
    z: npt.NDArray


def buildCoordinates( positions: Sequence[ float ], numElements: Sequence[ int ] ) -> npt.NDArray:
    """Builds the coordinates array from the positions of each mesh block vertex and number of elements in a given direction within each mesh block.

    Args:
        positions (Sequence[ float ]): The positions of each mesh block vertex.
        numElements (Sequence[ int ]): The number of elements in a given direction within each mesh block.

    Returns:
        npt.NDArray: The array of coordinates.
    """
    result: list[ npt.NDArray ] = []
    it = zip( zip( positions, positions[ 1: ] ), numElements )
    try:
        coords, n = next( it )
        while True:
            start, stop = coords
            endPoint: bool = False
            tmp = np.linspace( start=start, stop=stop, num=n + endPoint, endpoint=endPoint )
            coords, n = next( it )
            result.append( tmp )
    except StopIteration:
        endPoint = True
        tmp = np.linspace( start=start, stop=stop, num=n + endPoint, endpoint=endPoint )
        result.append( tmp )
    return np.concatenate( result )


def buildRectilinearGrid( x: npt.NDArray, y: npt.NDArray, z: npt.NDArray ) -> vtkUnstructuredGrid:
    """Builds an unstructured vtk grid from the x,y,z coordinates.

    Args:
        x (npt.NDArray): The x coordinates.
        y (npt.NDArray): The y coordinates.
        z (npt.NDArray): The z coordinates.

    Returns:
        The unstructured mesh, even if it's topologically structured.
    """
    rg = vtkRectilinearGrid()
    rg.SetDimensions( len( x ), len( y ), len( z ) )
    rg.SetXCoordinates( numpy_to_vtk( x ) )
    rg.SetYCoordinates( numpy_to_vtk( y ) )
    rg.SetZCoordinates( numpy_to_vtk( z ) )

    numPoints = rg.GetNumberOfPoints()
    numCells = rg.GetNumberOfCells()

    points = vtkPoints()
    points.Allocate( numPoints )
    for i in range( rg.GetNumberOfPoints() ):
        points.InsertNextPoint( rg.GetPoint( i ) )

    cellTypes = [ VTK_HEXAHEDRON ] * numCells
    cells = vtkCellArray()
    cells.AllocateExact( numCells, numCells * 8 )

    m = ( 0, 1, 3, 2, 4, 5, 7, 6 )  # VTK_VOXEL and VTK_HEXAHEDRON do not share the same ordering.
    for i in range( rg.GetNumberOfCells() ):
        c = rg.GetCell( i )
        newCell = vtkHexahedron()
        for j in range( 8 ):
            newCell.GetPointIds().SetId( j, c.GetPointId( m[ j ] ) )
        cells.InsertNextCell( newCell )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )
    return mesh


def buildRectilinearBlocksMesh( xyzs: Iterable[ XYZ ] ) -> vtkUnstructuredGrid:
    """Builds an unstructured vtk grid from the `xyzs` blocks. Kind of InternalMeshGenerator.

    Args:
        xyzs (Iterable[ XYZ ]): The blocks.

    Returns:
        The unstructured mesh, even if it's topologically structured.
    """
    rgs: list[ vtkRectilinearGrid ] = []
    for xyz in xyzs:
        rg = vtkRectilinearGrid()
        rg.SetDimensions( len( xyz.x ), len( xyz.y ), len( xyz.z ) )
        rg.SetXCoordinates( numpy_to_vtk( xyz.x ) )
        rg.SetYCoordinates( numpy_to_vtk( xyz.y ) )
        rg.SetZCoordinates( numpy_to_vtk( xyz.z ) )
        rgs.append( rg )

    numPoints: int = sum( r.GetNumberOfPoints() for r in rgs )
    numCells: int = sum( r.GetNumberOfCells() for r in rgs )

    points = vtkPoints()
    points.Allocate( numPoints )
    for rg in rgs:
        for i in range( rg.GetNumberOfPoints() ):
            points.InsertNextPoint( rg.GetPoint( i ) )

    cellTypes: list[ int ] = [ VTK_HEXAHEDRON ] * numCells
    cells = vtkCellArray()
    cells.AllocateExact( numCells, numCells * 8 )

    m = ( 0, 1, 3, 2, 4, 5, 7, 6 )  # VTK_VOXEL and VTK_HEXAHEDRON do not share the same ordering.
    offset: int = 0
    for rg in rgs:
        for i in range( rg.GetNumberOfCells() ):
            c = rg.GetCell( i )
            newCell = vtkHexahedron()
            for j in range( 8 ):
                newCell.GetPointIds().SetId( j, offset + c.GetPointId( m[ j ] ) )
            cells.InsertNextCell( newCell )
        offset += rg.GetNumberOfPoints()

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cellTypes, cells )

    return mesh


def addFields( mesh: vtkUnstructuredGrid, fields: Iterable[ FieldInfo ] ) -> vtkUnstructuredGrid:
    """Add constant fields to the mesh using arrayModifiers utilities.

    Each field is filled with ones (1.0) for all components.

    Args:
        mesh (vtkUnstructuredGrid): The mesh to which fields will be added.
        fields (Iterable[ FieldInfo ]): The fields to add.

    Returns:
        vtkUnstructuredGrid: The mesh with added fields.
    """
    for fieldInfo in fields:
        piece: Piece = Piece.POINTS if fieldInfo.support == "POINTS" else Piece.CELLS
        # Create list of values (all 1.0) for each component
        listValues = [ 1.0 ] * fieldInfo.dimension
        # Use the robust createConstantAttributeDataSet function
        success = createConstantAttributeDataSet( dataSet=mesh,
                                                  listValues=listValues,
                                                  attributeName=fieldInfo.name,
                                                  piece=piece,
                                                  logger=setupLogger )
        if not success:
            setupLogger.warning( f"Failed to create field {fieldInfo.name}" )
    return mesh


def buildCube( options: Options ) -> vtkUnstructuredGrid:
    """Creates a cube vtkUnstructuredGrid from options given.

    Args:
        options (Options): The options for processing.

    Returns:
        vtkUnstructuredGrid: The created mesh.
    """
    x = buildCoordinates( options.xs, options.nxs )
    y = buildCoordinates( options.ys, options.nys )
    z = buildCoordinates( options.zs, options.nzs )
    mesh = buildRectilinearBlocksMesh( ( XYZ( x, y, z ), ) )
    mesh = addFields( mesh, options.fields )
    buildGlobalIds( mesh, options.generateCellsGlobalIds, options.generatePointsGlobalIds )
    return mesh


def meshAction( options: Options ) -> Result:
    """Creates a vtkUnstructuredGrid from options given.

    Args:
        options (Options): The options for processing.

    Returns:
        Result: The result of creation of the mesh.
    """
    outputMesh = buildCube( options )
    writeMesh( outputMesh, options.vtkOutput )
    return Result( info=f"Mesh was written to {options.vtkOutput.output}" )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Creates a vtkUnstructuredGrid from options given.

    Args:
        vtuInputFile (str): The path to the input VTU file. This is unused.
        options (Options): The options for processing.

    Returns:
        Result: The result of the fix elements orderings.
    """
    return meshAction( options )
