from dataclasses import dataclass
from geos.mesh.doctor.register import __load_module_action
from geos.mesh.doctor.parsing.cli_parsing import setup_logger


@dataclass( frozen=True )
class Options:
    checks_to_perform: list[ str ]
    checks_options: dict[ str, any ]
    check_displays: dict[ str, any ]


@dataclass( frozen=True )
class Result:
    check_results: dict[ str, any ]


def get_check_results( vtk_input_file: str, options: Options ) -> dict[ str, any ]:
    check_results: dict[ str, any ] = dict()
    for check_name in options.checks_to_perform:
        check_action = __load_module_action( check_name )
        setup_logger.info( f"Performing check '{check_name}'." )
        option = options.checks_options[ check_name ]
        check_result = check_action( vtk_input_file, option )
        check_results[ check_name ] = check_result
    return check_results


def action( vtk_input_file: str, options: Options ) -> Result:
    check_results: dict[ str, any ] = get_check_results( vtk_input_file, options )
    return Result( check_results=check_results )
