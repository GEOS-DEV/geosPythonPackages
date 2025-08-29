import numpy
from geos.mesh.doctor.actions.self_intersecting_elements import Options, Result
from geos.mesh.doctor.parsing import SELF_INTERSECTING_ELEMENTS
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import get_options_used_message
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__MIN_DISTANCE = "min_distance"
__MIN_DISTANCE_DEFAULT = numpy.finfo( float ).eps

__SELF_INTERSECTING_ELEMENTS_DEFAULT = { __MIN_DISTANCE: __MIN_DISTANCE_DEFAULT }


def convert( parsed_options ) -> Options:
    min_distance = parsed_options[ __MIN_DISTANCE ]
    if min_distance == 0:
        setup_logger.warning( "Having minimum distance set to 0 can induce lots of false positive results"
                              " (adjacent faces may be considered intersecting)." )
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
        help=( "[float]: The minimum distance in the computation."
               f" Defaults to your machine precision {__MIN_DISTANCE_DEFAULT}." )
    )


def display_results( options: Options, result: Result ):
    setup_logger.results( get_options_used_message( options ) )
    logger_results( setup_logger, result.invalid_cell_ids )


def logger_results( logger, invalid_cell_ids ) -> None:
    """Log the results of the self-intersecting elements check.

    Args:
        logger: Logger instance for output.
        invalid_cell_ids: Dictionary of invalid cell IDs by error type.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    log_method = logger.info
    if hasattr(logger, 'results'):
        log_method = logger.results

    # Human-readable descriptions for each error type
    error_descriptions = {
        'wrongNumberOfPointsElements': 'elements with wrong number of points',
        'intersectingEdgesElements': 'elements with intersecting edges',
        'intersectingFacesElements': 'elements with self intersecting faces',
        'nonContiguousEdgesElements': 'elements with non-contiguous edges',
        'nonConvexElements': 'non-convex elements',
        'facesOrientedIncorrectlyElements': 'elements with incorrectly oriented faces',
        'nonPlanarFacesElements': 'elements with non-planar faces',
        'degenerateFacesElements': 'elements with degenerate faces'
    }

    # Log results for each error type that has invalid elements
    for error_type, invalid_ids in invalid_cell_ids.items():
        if invalid_ids:
            description = error_descriptions.get(error_type, f'elements with {error_type}')
            log_method(f"You have {len(invalid_ids)} {description}.")
            log_method("The elements indices are:\n" + ", ".join(map(str, invalid_ids)))
