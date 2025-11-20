from dataclasses import dataclass
from typing import Any
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh_doctor.register import __loadModuleAction
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    checksToPerform: list[ str ]
    checksOptions: dict[ str, Any ]
    checkDisplays: dict[ str, Any ]


@dataclass( frozen=True )
class Result:
    checkResults: dict[ str, Any ]


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs all checks available on a loaded mesh.

    Args:
        mesh (vtkUnstructuredGrid): The loaded mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of all checks performed.
    """
    checkResults: dict[ str, Any ] = {}
    for checkName in options.checksToPerform:
        checkMeshAction = __loadModuleAction( checkName, "meshAction" )
        setupLogger.info( f"Performing check '{checkName}'." )
        option = options.checksOptions[ checkName ]
        checkResult = checkMeshAction( mesh, option )
        checkResults[ checkName ] = checkResult
    return Result( checkResults=checkResults )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs all checks available on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of all checks performed.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
