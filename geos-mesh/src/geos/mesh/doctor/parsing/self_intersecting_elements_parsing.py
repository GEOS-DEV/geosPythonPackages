import numpy
from geos.mesh.doctor.actions.self_intersecting_elements import Options, Result
from geos.mesh.doctor.parsing import SELF_INTERSECTING_ELEMENTS
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__MIN_DISTANCE = "min_distance"
__MIN_DISTANCE_DEFAULT = numpy.finfo( float ).eps

__SELF_INTERSECTING_ELEMENTS_DEFAULT = { __MIN_DISTANCE: __MIN_DISTANCE_DEFAULT }


def convert( parsed_options ) -> Options:
    min_distance = parsed_options[ __MIN_DISTANCE ]
    if min_distance == 0:
        setup_logger.warning(
            "Having minimum distance set to 0 can induce lots of false positive results (adjacent faces may be considered intersecting)."
        )
    elif min_distance < 0:
        raise ValueError(
            f"Negative minimum distance ({min_distance}) in the {SELF_INTERSECTING_ELEMENTS} check is not allowed." )
    return Options( min_distance=min_distance )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( SELF_INTERSECTING_ELEMENTS,
                               help="Checks if the faces of the elements are self intersecting." )
    p.add_argument(
        '--' + __MIN_DISTANCE,
        type=float,
        required=False,
        metavar=__MIN_DISTANCE_DEFAULT,
        default=__MIN_DISTANCE_DEFAULT,
        help=
        f"[float]: The minimum distance in the computation. Defaults to your machine precision {__MIN_DISTANCE_DEFAULT}."
    )


def display_results( options: Options, result: Result ):
    setup_logger.results( f"You have {len(result.intersecting_faces_elements)} elements with self intersecting faces." )
    if result.intersecting_faces_elements:
        setup_logger.results( "The elements indices are:\n" +
                              ", ".join( map( str, result.intersecting_faces_elements ) ) )
