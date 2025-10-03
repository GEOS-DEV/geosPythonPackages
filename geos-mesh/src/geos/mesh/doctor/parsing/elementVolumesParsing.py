from geos.mesh.doctor.actions.elementVolumes import Options, Result
from geos.mesh.doctor.parsing import ELEMENT_VOLUMES
from geos.mesh.doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh.doctor.parsing.cliParsing import setupLogger

__MIN_VOLUME = "minVolume"
__MIN_VOLUME_DEFAULT = 0.

__ELEMENT_VOLUMES_DEFAULT = { __MIN_VOLUME: __MIN_VOLUME_DEFAULT }


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( ELEMENT_VOLUMES,
                               help=f"Checks if the volumes of the elements are greater than \"{__MIN_VOLUME}\"." )
    p.add_argument( '--' + __MIN_VOLUME,
                    type=float,
                    metavar=__MIN_VOLUME_DEFAULT,
                    default=__MIN_VOLUME_DEFAULT,
                    required=True,
                    help=f"[float]: The minimum acceptable volume. Defaults to {__MIN_VOLUME_DEFAULT}." )


def convert( parsedOptions ) -> Options:
    """
    From the parsed cli options, return the converted options for elements volumes check.
    :param parsedOptions: Parsed cli options.
    :return: Options instance.
    """
    return Options( minVolume=parsedOptions[ __MIN_VOLUME ] )


def displayResults( options: Options, result: Result ):
    setupLogger.results( getOptionsUsedMessage( options ) )
    setupLogger.results(
        f"You have {len(result.elementVolumes)} elements with volumes smaller than {options.minVolume}." )
    if result.elementVolumes:
        setupLogger.results( "Elements index | Volumes calculated" )
        setupLogger.results( "-----------------------------------" )
        maxLength: int = len( "Elements index " )
        for ( ind, volume ) in result.elementVolumes:
            setupLogger.results( f"{ind:<{maxLength}}" + "| " + str( volume ) )
