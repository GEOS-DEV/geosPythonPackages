import logging
from geos.mesh.doctor.checks.non_conformal import Options, Result
from geos.mesh.doctor.parsing import NON_CONFORMAL

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
    non_conformal_cells: list[ int ] = []
    for i, j in result.non_conformal_cells:
        non_conformal_cells += i, j
    non_conformal_cells: frozenset[ int ] = frozenset( non_conformal_cells )
    logging.error(
        f"You have {len(non_conformal_cells)} non conformal cells.\n{', '.join(map(str, sorted(non_conformal_cells)))}"
    )
