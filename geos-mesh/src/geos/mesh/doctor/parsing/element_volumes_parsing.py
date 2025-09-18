from geos.mesh.doctor.actions.element_volumes import Options, Result
from geos.mesh.doctor.parsing import ELEMENT_VOLUMES
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import get_options_used_message
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

__MIN_VOLUME = "min_volume"
__MIN_VOLUME_DEFAULT = 0.

__ELEMENT_VOLUMES_DEFAULT = { __MIN_VOLUME: __MIN_VOLUME_DEFAULT }


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( ELEMENT_VOLUMES,
                               help=f"Checks if the volumes of the elements are greater than \"{__MIN_VOLUME}\"." )
    p.add_argument( '--' + __MIN_VOLUME,
                    type=float,
                    metavar=__MIN_VOLUME_DEFAULT,
                    default=__MIN_VOLUME_DEFAULT,
                    required=True,
                    help=f"[float]: The minimum acceptable volume. Defaults to {__MIN_VOLUME_DEFAULT}." )


def convert( parsed_options ) -> Options:
    """
    From the parsed cli options, return the converted options for elements volumes check.
    :param options_str: Parsed cli options.
    :return: Options instance.
    """
    return Options( min_volume=parsed_options[ __MIN_VOLUME ] )


def display_results( options: Options, result: Result ):
    setup_logger.results( get_options_used_message( options ) )
    logger_results( setup_logger, result.element_volumes )


def logger_results( logger, element_volumes: list[ tuple[ int, float ] ] ) -> None:
    """Show the results of the element volumes check.

    Args:
        logger: Logger instance for output.
        element_volumes (list[ tuple[ int, float ] ]): List of element volumes.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    log_method = logger.info
    if hasattr( logger, 'results' ):
        log_method = logger.results

    log_method( "Elements index | Volumes calculated" )
    log_method( "-----------------------------------" )
    max_length: int = len( "Elements index " )
    for ( ind, volume ) in element_volumes:
        log_method( f"{ind:<{max_length}}" + "| " + str( volume ) )
