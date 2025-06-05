import argparse
import logging
import textwrap
from typing import List
from geos.utils.Logger import getLogger as get_custom_logger  # Alias for clarity

__VERBOSE_KEY = "verbose"
__QUIET_KEY = "quiet"

__VERBOSITY_FLAG = "v"
__QUIET_FLAG = "q"

# Get a logger for this setup module itself, using your custom logger
# This ensures its messages (like the "Logger level set to...") use your custom format.
setup_logger = get_custom_logger( "mesh-doctor" )


# --- Conversion Logic ---
def parse_comma_separated_string( value: str ) -> list[ str ]:
    """Helper to parse comma-separated strings, stripping whitespace and removing empty items."""
    if not value or not value.strip():
        return list()
    return [ item.strip() for item in value.split( ',' ) if item.strip() ]


def parse_and_set_verbosity( cli_args: List[ str ] ) -> None:
    """
    Parse the verbosity flag only and set the root logger's level accordingly.
    Messages from loggers created with `get_custom_logger` will inherit this level
    if their own level is set to NOTSET.
    :param cli_args: The list of command-line arguments (e.g., sys.argv)
    :return: None
    """
    dummy_verbosity_parser = argparse.ArgumentParser( add_help=False )
    # Add verbosity arguments to this dummy parser
    dummy_verbosity_parser.add_argument(
        '-' + __VERBOSITY_FLAG,
        '--' + __VERBOSE_KEY,
        action='count',
        default=0,  # Base default, actual interpretation depends on help text mapping
        dest=__VERBOSE_KEY )
    dummy_verbosity_parser.add_argument( '-' + __QUIET_FLAG,
                                         '--' + __QUIET_KEY,
                                         action='count',
                                         default=0,
                                         dest=__QUIET_KEY )

    # Parse only known args to extract verbosity/quiet flags
    # cli_args[1:] is used assuming cli_args[0] is the script name (like sys.argv)
    args, _ = dummy_verbosity_parser.parse_known_args( cli_args[ 1: ] )

    verbose_count = args.verbose
    quiet_count = args.quiet

    if verbose_count == 0 and quiet_count == 0:
        # Default level (no -v or -q flags)
        effective_level = logging.WARNING
    elif verbose_count == 1:
        effective_level = logging.INFO
    elif verbose_count >= 2:
        effective_level = logging.DEBUG
    elif quiet_count == 1:
        effective_level = logging.ERROR
    elif quiet_count >= 2:
        effective_level = logging.CRITICAL
    else:  # Should not happen with count logic but good to have a fallback
        effective_level = logging.WARNING

    # Set the level on the ROOT logger.
    # Loggers from get_custom_logger (with level NOTSET) will inherit this.
    setup_logger.setLevel( effective_level )

    # Use the setup_logger (which uses your custom formatter) for this message
    setup_logger.info( f"Logger level set to \"{logging.getLevelName( effective_level )}\"" )


def init_parser() -> argparse.ArgumentParser:
    vtk_input_file_key = "vtk_input_file"

    epilog_msg = f"""\
        Note that checks are dynamically loaded.
        An option may be missing because of an unloaded module.
        Increase verbosity (-{__VERBOSITY_FLAG}, -{__VERBOSITY_FLAG * 2}) to get full information.
        """
    formatter = lambda prog: argparse.RawTextHelpFormatter( prog, max_help_position=8 )
    parser = argparse.ArgumentParser( description='Inspects meshes for GEOS.',
                                      epilog=textwrap.dedent( epilog_msg ),
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
    parser.add_argument( '-i',
                         '--vtk-input-file',
                         metavar='VTK_MESH_FILE',
                         type=str,
                         required=True,
                         dest=vtk_input_file_key )
    return parser
