from dataclasses import dataclass
from geos.mesh.doctor.register import __load_module_action
from geos.utils.Logger import getLogger

logger = getLogger()


@dataclass( frozen=True )
class Options:
    checks_to_perform: list[ str ]
    checks_options: list


@dataclass( frozen=True )
class Result:
    check_results: dict


def action( vtk_input_file: str, options: Options ) -> list[ Result ]:
    check_results = dict()
    for check, option in zip( options.checks_to_perform, options.checks_options ):
        check_action = __load_module_action( check )
        logger.info( f"Performing check '{check}'." )
        check_result = check_action( vtk_input_file, option )
        check_results[ check ] = check_result
    return Result( check_results=check_results )
