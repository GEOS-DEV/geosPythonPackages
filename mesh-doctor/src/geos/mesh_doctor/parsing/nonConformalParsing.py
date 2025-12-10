# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any
from geos.mesh_doctor.actions.nonConformal import Options, Result
from geos.mesh_doctor.baseTypes import NON_CONFORMAL, UserInputs
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__ANGLE_TOLERANCE = "angleTolerance"
__POINT_TOLERANCE = "pointTolerance"
__FACE_TOLERANCE = "faceTolerance"

__ANGLE_TOLERANCE_DEFAULT = 10.
__POINT_TOLERANCE_DEFAULT = 0.
__FACE_TOLERANCE_DEFAULT = 0.

__NON_CONFORMAL_DEFAULT = {
    __ANGLE_TOLERANCE: __ANGLE_TOLERANCE_DEFAULT,
    __POINT_TOLERANCE: __POINT_TOLERANCE_DEFAULT,
    __FACE_TOLERANCE: __FACE_TOLERANCE_DEFAULT
}


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( NON_CONFORMAL, help="Detects non conformal elements. [EXPERIMENTAL]" )
    addVtuInputFileArgument( p )
    p.add_argument( '--' + __ANGLE_TOLERANCE,
                    type=float,
                    metavar=__ANGLE_TOLERANCE_DEFAULT,
                    default=__ANGLE_TOLERANCE_DEFAULT,
                    help=f"[float]: angle tolerance in degrees. Defaults to {__ANGLE_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __POINT_TOLERANCE,
        type=float,
        metavar=__POINT_TOLERANCE_DEFAULT,
        default=__POINT_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two points to be considered collocated. Defaults to {__POINT_TOLERANCE_DEFAULT}" )
    p.add_argument(
        '--' + __FACE_TOLERANCE,
        type=float,
        metavar=__FACE_TOLERANCE_DEFAULT,
        default=__FACE_TOLERANCE_DEFAULT,
        help=f"[float]: tolerance for two faces to be considered \"touching\". Defaults to {__FACE_TOLERANCE_DEFAULT}" )


def convert( parsedOptions: UserInputs ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    return Options( angleTolerance=parsedOptions[ __ANGLE_TOLERANCE ],
                    pointTolerance=parsedOptions[ __POINT_TOLERANCE ],
                    faceTolerance=parsedOptions[ __FACE_TOLERANCE ] )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the non conformal elements check.

    Args:
        options: The options used for the check.
        result: The result of the non conformal elements check.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    loggerResults( setupLogger, result.nonConformalCells )


def loggerResults( logger: Any, nonConformalCells: list[ tuple[ int, int ] ] ) -> None:
    """Log the results of the non-conformal cells check.

    Args:
        logger: Logger instance for output.
        nonConformalCells (list[ tuple[ int, int ] ]): List of non-conformal cells.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    logMethod = logger.info
    if hasattr( logger, 'results' ):
        logMethod = logger.results

    cells: list[ int ] = []
    for i, j in nonConformalCells:
        cells += i, j
    uniqueCells: frozenset[ int ] = frozenset( cells )
    logMethod( f"You have {len( uniqueCells )} non conformal cells." )
    logMethod( f"{', '.join( map( str, sorted( uniqueCells ) ) )}" )
