from dataclasses import dataclass
import numpy
from typing import Iterable, Sequence
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkCellArray, vtkHexahedron, vtkRectilinearGrid, vtkUnstructuredGrid,
                                            VTK_HEXAHEDRON )
from geos.mesh.doctor.actions.generateGlobalIds import __buildGlobalIds
from geos.mesh.doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import VtkOutput, writeMesh


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
    x: numpy.ndarray
    y: numpy.ndarray
    z: numpy.ndarray


def buildRectilinearBlocksMesh( xyzs: Iterable[ XYZ ] ) -> vtkUnstructuredGrid:
    """
    Builds an unstructured vtk grid from the `xyzs` blocks. Kind of InternalMeshGenerator.
    :param xyzs: The blocks.
    :return: The unstructured mesh, even if it's topologically structured.
    """
    rgs = []
    for xyz in xyzs:
        rg = vtkRectilinearGrid()
        rg.SetDimensions( len( xyz.x ), len( xyz.y ), len( xyz.z ) )
        rg.SetXCoordinates( numpy_to_vtk( xyz.x ) )
        rg.SetYCoordinates( numpy_to_vtk( xyz.y ) )
        rg.SetZCoordinates( numpy_to_vtk( xyz.z ) )
        rgs.append( rg )

    numPoints = sum( map( lambda r: r.GetNumberOfPoints(), rgs ) )
    numCells = sum( map( lambda r: r.GetNumberOfCells(), rgs ) )

    points = vtkPoints()
    points.Allocate( numPoints )
    for rg in rgs:
        for i in range( rg.GetNumberOfPoints() ):
            points.InsertNextPoint( rg.GetPoint( i ) )

    cellTypes = [ VTK_HEXAHEDRON ] * numCells
    cells = vtkCellArray()
    cells.AllocateExact( numCells, numCells * 8 )

    m = ( 0, 1, 3, 2, 4, 5, 7, 6 )  # VTK_VOXEL and VTK_HEXAHEDRON do not share the same ordering.
    offset = 0
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


def __addFields( mesh: vtkUnstructuredGrid, fields: Iterable[ FieldInfo ] ) -> vtkUnstructuredGrid:
    for fieldInfo in fields:
        if fieldInfo.support == "CELLS":
            data = mesh.GetCellData()
            n = mesh.GetNumberOfCells()
        elif fieldInfo.support == "POINTS":
            data = mesh.GetPointData()
            n = mesh.GetNumberOfPoints()
        array = numpy.ones( ( n, fieldInfo.dimension ), dtype=float )
        vtkArray = numpy_to_vtk( array )
        vtkArray.SetName( fieldInfo.name )
        data.AddArray( vtkArray )
    return mesh


def __build( options: Options ):

    def buildCoordinates( positions, numElements ):
        result = []
        it = zip( zip( positions, positions[ 1: ] ), numElements )
        try:
            coords, n = next( it )
            while True:
                start, stop = coords
                endPoint = False
                tmp = numpy.linspace( start=start, stop=stop, num=n + endPoint, endpoint=endPoint )
                coords, n = next( it )
                result.append( tmp )
        except StopIteration:
            endPoint = True
            tmp = numpy.linspace( start=start, stop=stop, num=n + endPoint, endpoint=endPoint )
            result.append( tmp )
        return numpy.concatenate( result )

    x = buildCoordinates( options.xs, options.nxs )
    y = buildCoordinates( options.ys, options.nys )
    z = buildCoordinates( options.zs, options.nzs )
    cube = buildRectilinearBlocksMesh( ( XYZ( x, y, z ), ) )
    cube = __addFields( cube, options.fields )
    __buildGlobalIds( cube, options.generateCellsGlobalIds, options.generatePointsGlobalIds )
    return cube


def __action( options: Options ) -> Result:
    outputMesh = __build( options )
    writeMesh( outputMesh, options.vtkOutput )
    return Result( info=f"Mesh was written to {options.vtkOutput.output}" )


def action( vtkInputFile: str, options: Options ) -> Result:
    try:
        return __action( options )
    except BaseException as e:
        setupLogger.error( e )
        return Result( info="Something went wrong." )
