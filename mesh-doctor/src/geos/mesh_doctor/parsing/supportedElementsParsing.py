from __future__ import annotations
import multiprocessing
from argparse import _SubParsersAction
from typing import Any
from geos.mesh_doctor.actions.supportedElements import Options, Result
from geos.mesh_doctor.parsing import SUPPORTED_ELEMENTS
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger

__CHUNK_SIZE = "chunkSize"
__NUM_PROC = "nproc"

__CHUNK_SIZE_DEFAULT = 1
__NUM_PROC_DEFAULT = multiprocessing.cpu_count()

__SUPPORTED_ELEMENTS_DEFAULT = { __CHUNK_SIZE: __CHUNK_SIZE_DEFAULT, __NUM_PROC: __NUM_PROC_DEFAULT }


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    return Options( chunkSize=parsedOptions[ __CHUNK_SIZE ], nproc=parsedOptions[ __NUM_PROC ] )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( SUPPORTED_ELEMENTS,
                               help="Check that all the elements of the mesh are supported by GEOSX." )
    p.add_argument( '--' + __CHUNK_SIZE,
                    type=int,
                    required=False,
                    metavar=__CHUNK_SIZE_DEFAULT,
                    default=__CHUNK_SIZE_DEFAULT,
                    help=f"[int]: Defaults chunk size for parallel processing to {__CHUNK_SIZE_DEFAULT}" )
    p.add_argument(
        '--' + __NUM_PROC,
        type=int,
        required=False,
        metavar=__NUM_PROC_DEFAULT,
        default=__NUM_PROC_DEFAULT,
        help=f"[int]: Number of threads used for parallel processing. Defaults to your CPU count {__NUM_PROC_DEFAULT}."
    )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the supported elements check.

    Args:
        options: The options used for the check.
        result: The result of the supported elements check.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    loggerResults( setupLogger, result.unsupportedPolyhedronElements, result.unsupportedStdElementsTypes )


def loggerResults( logger: Any, unsupportedPolyhedronElements: frozenset[ int ],
                   unsupportedStdElementsTypes: list[ str ] ) -> None:
    """Log the results of the supported elements check.

    Args:
        logger: Logger instance for output.
        unsupportedPolyhedronElements (frozenset[ int ]): List of unsupported polyhedron elements.
        unsupportedStdElementsTypes (list[ str ]): List of unsupported standard element types.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    logMethod: Any = logger.info
    if hasattr( logger, 'results' ):
        logMethod = logger.results

    if unsupportedPolyhedronElements:
        logMethod( f"There is/are {len(unsupportedPolyhedronElements)} polyhedra that may not be converted to"
                   " supported elements." )
        logMethod( f"The list of the unsupported polyhedra is\n{tuple( sorted( unsupportedPolyhedronElements ) )}." )
    else:
        logMethod( "All the polyhedra (if any) can be converted to supported elements." )
    if unsupportedStdElementsTypes:
        logMethod( "There are unsupported vtk standard element types. The list of those vtk types is"
                   f" {tuple( sorted( unsupportedStdElementsTypes ) )}." )
    else:
        logMethod( "All the standard vtk element types (if any) are supported." )
