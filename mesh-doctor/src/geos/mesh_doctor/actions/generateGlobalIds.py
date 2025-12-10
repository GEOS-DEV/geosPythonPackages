# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
from vtkmodules.vtkCommonCore import vtkIdTypeArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import VtkOutput, readUnstructuredGrid, writeMesh
from geos.mesh_doctor.parsing.cliParsing import setupLogger


@dataclass( frozen=True )
class Options:
    vtkOutput: VtkOutput
    generateCellsGlobalIds: bool
    generatePointsGlobalIds: bool


@dataclass( frozen=True )
class Result:
    info: str


def buildGlobalIds( mesh: vtkUnstructuredGrid, generateCellsGlobalIds: bool, generatePointsGlobalIds: bool ) -> None:
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


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the addition of global ids on a vtkUnstructuredGrid if options given to do so.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to add global ids.
        options (Options): The options for processing.

    Returns:
        Result: The result of the global ids addition.
    """
    buildGlobalIds( mesh, options.generateCellsGlobalIds, options.generatePointsGlobalIds )
    try:
        writeMesh( mesh, options.vtkOutput, options.vtkOutput.canOverwrite )
    except FileExistsError as e:
        setupLogger.error( f"{e} Use --canOverwrite to allow overwriting existing files." )
        raise SystemExit( 1 )
    return Result( info=f"Mesh was written to {options.vtkOutput.output}" )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtkUnstructuredGrid and adds global ids as per options.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the global ids addition.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
