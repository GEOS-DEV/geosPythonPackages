# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
from typing import Any, Callable, TypeAlias
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.io.vtkIO import readUnstructuredGrid
from geos.mesh_doctor.baseTypes import OptionsProtocol, ResultProtocol
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh_doctor.register import __loadModuleAction

CheckOptions: TypeAlias = dict[ str, OptionsProtocol ]  # per check done, an OptionsProtocol instance
CheckResults: TypeAlias = dict[ str, ResultProtocol ]  # per check done, a ResultProtocol instance


@dataclass( frozen=True )
class Options:
    checksToPerform: list[ str ]
    checksOptions: CheckOptions
    checkDisplays: dict[ str, Any ]


@dataclass( frozen=True )
class Result:
    checkResults: CheckResults


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs all checks available on a loaded mesh.

    Args:
        mesh (vtkUnstructuredGrid): The loaded mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of all checks performed.
    """
    checkResults: CheckResults = {}
    for checkName in options.checksToPerform:
        checkMeshAction: Callable[..., ResultProtocol ] = __loadModuleAction( checkName, "meshAction" )
        setupLogger.info( f"Performing check '{checkName}'." )
        option: OptionsProtocol = options.checksOptions[ checkName ]
        checkResult: ResultProtocol = checkMeshAction( mesh, option )
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
