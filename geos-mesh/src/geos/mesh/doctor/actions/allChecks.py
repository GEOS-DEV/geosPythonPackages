from dataclasses import dataclass
from geos.mesh.doctor.register import __loadModuleAction
from geos.mesh.doctor.parsing.cliParsing import setupLogger


@dataclass( frozen=True )
class Options:
    checksToPerform: list[ str ]
    checksOptions: dict[ str, any ]
    checkDisplays: dict[ str, any ]


@dataclass( frozen=True )
class Result:
    checkResults: dict[ str, any ]


def action( vtkInputFile: str, options: Options ) -> list[ Result ]:
    checkResults: dict[ str, any ] = dict()
    for checkName in options.checksToPerform:
        checkAction = __loadModuleAction( checkName )
        setupLogger.info( f"Performing check '{checkName}'." )
        option = options.checksOptions[ checkName ]
        checkResult = checkAction( vtkInputFile, option )
        checkResults[ checkName ] = checkResult
    return Result( checkResults=checkResults )
