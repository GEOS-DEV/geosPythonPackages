import numpy
from geos.mesh.doctor.actions.self_intersecting_elements import Options, Result
from geos.mesh.doctor.parsing import SELF_INTERSECTING_ELEMENTS
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import getOptionsUsedMessage
from geos.mesh.doctor.parsing.cli_parsing import setupLogger

__MIN_DISTANCE = "minDistance"
__MIN_DISTANCE_DEFAULT = numpy.finfo( float ).eps

__SELF_INTERSECTING_ELEMENTS_DEFAULT = { __MIN_DISTANCE: __MIN_DISTANCE_DEFAULT }


def convert( parsedOptions ) -> Options:
    minDistance = parsedOptions[ __MIN_DISTANCE ]
    if minDistance == 0:
        setupLogger.warning(
            "Having minimum distance set to 0 can induce lots of false positive results (adjacent faces may be considered intersecting)."
        )
    elif minDistance < 0:
        raise ValueError(
            f"Negative minimum distance ({minDistance}) in the {SELF_INTERSECTING_ELEMENTS} check is not allowed." )
    return Options( minDistance=minDistance )


def fillSubparser( subparsers ) -> None:
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


def displayResults( options: Options, result: Result ):
    setupLogger.results( getOptionsUsedMessage( options ) )
    setupLogger.results( f"You have {len(result.intersectingFacesElements)} elements with self intersecting faces." )
    if result.intersectingFacesElements:
        setupLogger.results( "The elements indices are:\n" +
                             ", ".join( map( str, result.intersectingFacesElements ) ) )
