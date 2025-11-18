from dataclasses import dataclass
from typing import Any
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh_doctor.register import __loadModuleAction


@dataclass( frozen=True )
class Options:
    checksToPerform: list[ str ]
    checksOptions: dict[ str, Any ]
    checkDisplays: dict[ str, Any ]


@dataclass( frozen=True )
class Result:
    checkResults: dict[ str, Any ]


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs all checks available on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of all checks performed.
    """
    checkResults: dict[ str, Any ] = {}
    for checkName in options.checksToPerform:
        checkAction = __loadModuleAction( checkName )
        setupLogger.info( f"Performing check '{checkName}'." )
        option = options.checksOptions[ checkName ]
        checkResult = checkAction( vtuInputFile, option )
        checkResults[ checkName ] = checkResult
    return Result( checkResults=checkResults )
