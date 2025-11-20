from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any
from geos.mesh_doctor.actions.elementVolumes import Options, Result
from geos.mesh_doctor.parsing import ELEMENT_VOLUMES
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__MIN_VOLUME = "minVolume"
__MIN_VOLUME_DEFAULT = 0.

__ELEMENT_VOLUMES_DEFAULT = { __MIN_VOLUME: __MIN_VOLUME_DEFAULT }


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( ELEMENT_VOLUMES,
                               help=f"Checks if the volumes of the elements are greater than \"{__MIN_VOLUME}\"." )
    addVtuInputFileArgument( p )
    p.add_argument( '--' + __MIN_VOLUME,
                    type=float,
                    metavar=__MIN_VOLUME_DEFAULT,
                    default=__MIN_VOLUME_DEFAULT,
                    required=True,
                    help=f"[float]: The minimum acceptable volume. Defaults to {__MIN_VOLUME_DEFAULT}." )


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """From the parsed cli options, return the converted options for elements volumes check.

    Args:
        parsedOptions: Parsed cli options.

    Returns:
        Options: The converted options for elements volumes check.
    """
    return Options( minVolume=parsedOptions[ __MIN_VOLUME ] )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the element volumes check.

    Args:
        options: The options used for the check.
        result: The result of the element volumes check.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    loggerResults( setupLogger, result.elementVolumes )


def loggerResults( logger: Any, elementVolumes: list[ tuple[ int, float ] ] ) -> None:
    """Show the results of the element volumes check.

    Args:
        logger: Logger instance for output.
        elementVolumes (list[ tuple[ int, float ] ]): List of element volumes.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    logMethod = logger.info
    if hasattr( logger, 'results' ):
        logMethod = logger.results

    logMethod( "Elements index | Volumes calculated" )
    logMethod( "-----------------------------------" )
    max_length: int = len( "Elements index " )
    for ( ind, volume ) in elementVolumes:
        logMethod( f"{ind:<{max_length}}" + "| " + str( volume ) )
