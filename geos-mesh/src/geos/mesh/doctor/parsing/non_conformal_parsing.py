from geos.mesh.doctor.actions.non_conformal import Options, Result
from geos.mesh.doctor.parsing import NON_CONFORMAL
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import get_options_used_message
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__ANGLE_TOLERANCE = "angle_tolerance"
__POINT_TOLERANCE = "point_tolerance"
__FACE_TOLERANCE = "face_tolerance"

__ANGLE_TOLERANCE_DEFAULT = 10.
__POINT_TOLERANCE_DEFAULT = 0.
__FACE_TOLERANCE_DEFAULT = 0.

__NON_CONFORMAL_DEFAULT = {
    __ANGLE_TOLERANCE: __ANGLE_TOLERANCE_DEFAULT,
    __POINT_TOLERANCE: __POINT_TOLERANCE_DEFAULT,
    __FACE_TOLERANCE: __FACE_TOLERANCE_DEFAULT
}


def convert( parsed_options ) -> Options:
    return Options( angle_tolerance=parsed_options[ __ANGLE_TOLERANCE ],
                    point_tolerance=parsed_options[ __POINT_TOLERANCE ],
                    face_tolerance=parsed_options[ __FACE_TOLERANCE ] )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( NON_CONFORMAL, help="Detects non conformal elements. [EXPERIMENTAL]" )
    p.add_argument( '--' + __ANGLE_TOLERANCE,
                    type=float,
                    metavar=__ANGLE_TOLERANCE_DEFAULT,
                    default=__ANGLE_TOLERANCE_DEFAULT,
                    help=f"[float]: angle tolerance in degrees. Defaults to {__ANGLE_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __POINT_TOLERANCE,
        type=float,
        metavar=__POINT_TOLERANCE_DEFAULT,
        default=__POINT_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two points to be considered collocated. Defaults to {__POINT_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __FACE_TOLERANCE,
        type=float,
        metavar=__FACE_TOLERANCE_DEFAULT,
        default=__FACE_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two faces to be considered \"touching\". Defaults to {__FACE_TOLERANCE_DEFAULT}" )


def display_results( options: Options, result: Result ):
    setup_logger.results( get_options_used_message( options ) )
    logger_results( setup_logger, result.non_conformal_cells )


def logger_results( logger, non_conformal_cells: list[ tuple[ int, int ] ] ) -> None:
    """Log the results of the non-conformal cells check.

    Args:
        logger: Logger instance for output.
        non_conformal_cells (list[ tuple[ int, int ] ]): List of non-conformal cells.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    log_method = logger.info
    if hasattr( logger, 'results' ):
        log_method = logger.results

    unique_cells: list[ int ] = []
    for i, j in non_conformal_cells:
        unique_cells += i, j
    unique_cells: frozenset[ int ] = frozenset( unique_cells )
    log_method( f"You have {len( unique_cells )} non conformal cells." )
    log_method( f"{', '.join( map( str, sorted( unique_cells ) ) )}" )
