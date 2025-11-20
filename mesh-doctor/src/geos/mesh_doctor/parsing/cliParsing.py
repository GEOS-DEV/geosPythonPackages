import argparse
import logging
import textwrap
from geos.utils.Logger import getLogger

__VERBOSE_KEY = "verbose"
__QUIET_KEY = "quiet"

__VERBOSITY_FLAG = "v"
__QUIET_FLAG = "q"

setupLogger = getLogger( "mesh-doctor" )
setupLogger.propagate = False


def parseCommaSeparatedString( value: str ) -> list[ str ]:
    """Helper to parse comma-separated strings, stripping whitespace and removing empty items."""
    if not value or not value.strip():
        return []
    return [ item.strip() for item in value.split( ',' ) if item.strip() ]


def addVtuInputFileArgument( parser: argparse.ArgumentParser, required: bool = True ) -> None:
    """Add the VTU input file argument to a parser.

    Args:
        parser: The argument parser to add the input file argument to.
        required: Whether the input file argument is required. Defaults to True.
    """
    parser.add_argument( '-i',
                         '--vtu-input-file',
                         metavar='VTU_MESH_FILE',
                         type=str,
                         required=required,
                         dest='vtuInputFile',
                         help="[string]: The VTU mesh file to process." + ( "" if required else " (optional)" ) )


def parseAndSetVerbosity( cliArgs: list[ str ] ) -> None:
    """Parse the verbosity flag only and set the root logger's level accordingly.

    The verbosity is controlled via -v and -q flags:
        No flags: WARNING level
        -v: INFO level
        -vv or more: DEBUG level
        -q: ERROR level
        -qq or more: CRITICAL level
    Messages from loggers created with `get_custom_logger` will inherit this level
    if their own level is set to NOTSET.

    Args:
        cliArgs (list[ str ]): The list of command-line arguments (e.g., sys.argv)
    """
    dummyVerbosityParser = argparse.ArgumentParser( add_help=False )
    # Add verbosity arguments to this dummy parser
    dummyVerbosityParser.add_argument(
        '-' + __VERBOSITY_FLAG,
        '--' + __VERBOSE_KEY,
        action='count',
        default=0,  # Base default, actual interpretation depends on help text mapping
        dest=__VERBOSE_KEY )
    dummyVerbosityParser.add_argument( '-' + __QUIET_FLAG,
                                       '--' + __QUIET_KEY,
                                       action='count',
                                       default=0,
                                       dest=__QUIET_KEY )

    # Parse only known args to extract verbosity/quiet flags
    # cliArgs[1:] is used assuming cliArgs[0] is the script name (like sys.argv)
    args, _ = dummyVerbosityParser.parse_known_args( cliArgs[ 1: ] )

    verboseCount = args.verbose
    quietCount = args.quiet

    if verboseCount == 0 and quietCount == 0:
        # Default level (no -v or -q flags)
        effectiveLevel = logging.WARNING
    elif verboseCount == 1:
        effectiveLevel = logging.INFO
    elif verboseCount >= 2:
        effectiveLevel = logging.DEBUG
    elif quietCount == 1:
        effectiveLevel = logging.ERROR
    elif quietCount >= 2:
        effectiveLevel = logging.CRITICAL
    else:  # Should not happen with count logic but good to have a fallback
        effectiveLevel = logging.WARNING

    # Set the level on the ROOT logger.
    # Loggers from getCustomLogger (with level NOTSET) will inherit this.
    setupLogger.setLevel( effectiveLevel )

    # Use the setupLogger (which uses your custom formatter) for this message
    setupLogger.info( f"Logger level set to \"{logging.getLevelName( effectiveLevel )}\"" )


def initParser() -> argparse.ArgumentParser:
    """Initialize the main argument parser for mesh-doctor."""
    epilogMsg = f"""\
        Note that checks are dynamically loaded.
        An option may be missing because of an unloaded module.
        Increase verbosity (-{__VERBOSITY_FLAG}, -{__VERBOSITY_FLAG * 2}) to get full information.
        """

    def formatter( prog: str ) -> argparse.RawTextHelpFormatter:
        return argparse.RawTextHelpFormatter( prog, max_help_position=8 )

    parser = argparse.ArgumentParser( description='Inspects meshes for GEOS.',
                                      epilog=textwrap.dedent( epilogMsg ),
                                      formatter_class=formatter )
    # Nothing will be done with this verbosity/quiet input.
    # It's only here for the `--help` message.
    # `parse_verbosity` does the real parsing instead.
    parser.add_argument(
        '-' + __VERBOSITY_FLAG,
        action='count',
        default=2,
        dest=__VERBOSE_KEY,
        help=f"Use -{__VERBOSITY_FLAG} 'INFO', -{__VERBOSITY_FLAG * 2} for 'DEBUG'. Defaults to 'WARNING'." )
    parser.add_argument( '-' + __QUIET_FLAG,
                         action='count',
                         default=0,
                         dest=__QUIET_KEY,
                         help=f"Use -{__QUIET_FLAG} to reduce the verbosity of the output." )
    return parser
