import logging
from geos.mesh.doctor.checks.non_conformal import Options, Result
from . import NON_CONFORMAL

__ANGLE_TOLERANCE = "angle_tolerance"
__POINT_TOLERANCE = "point_tolerance"
__FACE_TOLERANCE = "face_tolerance"

__ANGLE_TOLERANCE_DEFAULT = 10.


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
    p.add_argument( '--' + __POINT_TOLERANCE,
                    type=float,
                    help="[float]: tolerance for two points to be considered collocated." )
    p.add_argument( '--' + __FACE_TOLERANCE,
                    type=float,
                    help="[float]: tolerance for two faces to be considered \"touching\"." )


def display_results( options: Options, result: Result ):
    non_conformal_cells_extended = [ cell_id for pair in result.non_conformal_cells for cell_id in pair ]
    unique_non_conformal_cells = frozenset( non_conformal_cells_extended )
    logging.error( f"You have {len( unique_non_conformal_cells )} non conformal cells.\n" +
                   f"{', '.join( map( str, sorted( non_conformal_cells_extended ) ) )}" )
