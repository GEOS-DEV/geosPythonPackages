# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import argparse
import logging
import textwrap
from geos.utils.Logger import getLogger

__VERBOSE_KEY = "verbose"
__QUIET_KEY = "quiet"
__OUTPUT_LOG_KEY = "outputLog"

__VERBOSITY_FLAG = "v"
__QUIET_FLAG = "q"

setupLogger = getLogger( "mesh-doctor" )
setupLogger.propagate = False


class LineWrappingFormatter( logging.Formatter ):
    """Custom formatter that wraps long lines at a specified width."""

    def __init__( self, fmt: str = None, datefmt: str = None, max_width: int = 120 ) -> None:
        """Initialize the formatter with optional line wrapping.

        Args:
            fmt: Log message format string
            datefmt: Date format string
            max_width: Maximum line width before wrapping
        """
        super().__init__( fmt, datefmt )
        self.max_width = max_width

    def format( self, record: logging.LogRecord ) -> str:
        """Format the log record and wrap long lines.

        Args:
            record: The log record to format

        Returns:
            Formatted and wrapped log message
        """
        formatted = super().format( record )
        if len( formatted ) <= self.max_width:
            return formatted

        # Split into lines and wrap each line
        lines = formatted.split( '\n' )
        wrapped_lines = []
        for line in lines:
            if len( line ) <= self.max_width:
                wrapped_lines.append( line )
            else:
                # Wrap long lines
                wrapped = textwrap.fill( line, width=self.max_width, subsequent_indent='    ' )
                wrapped_lines.append( wrapped )
        return '\n'.join( wrapped_lines )


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
    dummyVerbosityParser.add_argument( '--' + __OUTPUT_LOG_KEY,
                                       type=str,
                                       default=None,
                                       dest=__OUTPUT_LOG_KEY )

    # Parse only known args to extract verbosity/quiet flags and outputLog
    # cliArgs[1:] is used assuming cliArgs[0] is the script name (like sys.argv)
    args, _ = dummyVerbosityParser.parse_known_args( cliArgs[ 1: ] )

    verboseCount = args.verbose
    quietCount = args.quiet
    outputLogFile = args.outputLog

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

    # Add file handler if outputLog is specified
    if outputLogFile:
        try:
            fileHandler = logging.FileHandler( outputLogFile, mode='w' )
            fileHandler.setLevel( effectiveLevel )
            # Use custom formatter with 120 character max width
            fmt = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            fileHandler.setFormatter( LineWrappingFormatter( fmt=fmt, max_width=120 ) )
            setupLogger.addHandler( fileHandler )
            setupLogger.info( f"Log output will be written to \"{outputLogFile}\"" )
        except Exception as e:
            setupLogger.error( f"Failed to create log file \"{outputLogFile}\": {e}" )

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
    parser.add_argument( '--' + __OUTPUT_LOG_KEY,
                         type=str,
                         default=None,
                         dest=__OUTPUT_LOG_KEY,
                         metavar='LOG_FILE',
                         help="[string]: Path to output file (.txt or .out) where logs will be written." )
    return parser
