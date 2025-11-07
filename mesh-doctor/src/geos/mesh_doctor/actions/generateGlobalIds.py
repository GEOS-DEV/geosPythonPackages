from dataclasses import dataclass
from vtkmodules.vtkCommonCore import vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh


@dataclass( frozen=True )
class Options:
    vtkOutput: VtkOutput
    generateCellsGlobalIds: bool
    generatePointsGlobalIds: bool


@dataclass( frozen=True )
class Result:
    info: str


def __buildGlobalIds( mesh: vtkUnstructuredGrid, generateCellsGlobalIds: bool, generatePointsGlobalIds: bool ) -> None:
    """Adds the global ids for cells and points in place into the mesh instance.

    Args:
        mesh (vtkUnstructuredGrid): The mesh to modify.
        generateCellsGlobalIds (bool): If True, generates the global ids for cells. Else, does nothing.
        generatePointsGlobalIds (bool): If True, generates the global ids for points. Else, does nothing.
    """
    # Building GLOBAL_IDS for points and cells.g GLOBAL_IDS for points and cells.
    # First for points...
    if mesh.GetPointData().GetGlobalIds():
        setupLogger.error( "Mesh already has globals ids for points; nothing done." )
    elif generatePointsGlobalIds:
        pointGlobalIds = vtkIdTypeArray()
        pointGlobalIds.SetName( "GLOBAL_IDS_POINTS" )
        pointGlobalIds.Allocate( mesh.GetNumberOfPoints() )
        for i in range( mesh.GetNumberOfPoints() ):
            pointGlobalIds.InsertNextValue( i )
        mesh.GetPointData().SetGlobalIds( pointGlobalIds )
    # ... then for cells.
    if mesh.GetCellData().GetGlobalIds():
        setupLogger.error( "Mesh already has globals ids for cells; nothing done." )
    elif generateCellsGlobalIds:
        cellsGlobalIds = vtkIdTypeArray()
        cellsGlobalIds.SetName( "GLOBAL_IDS_CELLS" )
        cellsGlobalIds.Allocate( mesh.GetNumberOfCells() )
        for i in range( mesh.GetNumberOfCells() ):
            cellsGlobalIds.InsertNextValue( i )
        mesh.GetCellData().SetGlobalIds( cellsGlobalIds )


def __action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    __buildGlobalIds( mesh, options.generateCellsGlobalIds, options.generatePointsGlobalIds )
    writeMesh( mesh, options.vtkOutput )
    return Result( info=f"Mesh was written to {options.vtkOutput.output}" )


def action( vtkInputFile: str, options: Options ) -> Result:
    try:
        mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtkInputFile )
        return __action( mesh, options )
    except BaseException as e:
        setupLogger.error( e )
        return Result( info="Something went wrong." )
