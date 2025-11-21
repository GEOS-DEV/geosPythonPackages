# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from __future__ import annotations
from argparse import _SubParsersAction
import numpy
from typing import Any
from geos.mesh_doctor.actions.selfIntersectingElements import Options, Result
from geos.mesh_doctor.parsing import SELF_INTERSECTING_ELEMENTS
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__MIN_DISTANCE = "minDistance"
__MIN_DISTANCE_DEFAULT = numpy.finfo( float ).eps

__SELF_INTERSECTING_ELEMENTS_DEFAULT = { __MIN_DISTANCE: __MIN_DISTANCE_DEFAULT }


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for self intersecting elements check.

    Raises:
        ValueError: If minimum distance is negative.
    """
    minDistance = parsedOptions[ __MIN_DISTANCE ]
    if minDistance == 0:
        setupLogger.warning( "Having minimum distance set to 0 can induce lots of false positive results "
                             "(adjacent faces may be considered intersecting)." )
    elif minDistance < 0:
        raise ValueError(
            f"Negative minimum distance ({minDistance}) in the {SELF_INTERSECTING_ELEMENTS} check is not allowed." )
    return Options( minDistance=minDistance )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add self intersecting elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( SELF_INTERSECTING_ELEMENTS,
                               help="Checks if the faces of the elements are self intersecting." )
    addVtuInputFileArgument( p )
    help_text = ( "[float]: The minimum distance in the computation. "
                  f"Defaults to your machine precision {__MIN_DISTANCE_DEFAULT}." )
    p.add_argument( '--' + __MIN_DISTANCE,
                    type=float,
                    required=False,
                    metavar=__MIN_DISTANCE_DEFAULT,
                    default=__MIN_DISTANCE_DEFAULT,
                    help=help_text )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the self intersecting elements check.

    Args:
        options: The options used for the check.
        result: The result of the self intersecting elements check.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    loggerResults( setupLogger, result.invalidCellIds )


def loggerResults( logger: Any, invalidCellIds: dict[ str, list[ int ] ] ) -> None:
    """Log the results of the self-intersecting elements check.

    Args:
        logger: Logger instance for output.
        invalidCellIds: Dictionary of invalid cell IDs by error type.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    logMethod: Any = logger.info
    if hasattr( logger, 'results' ):
        logMethod = logger.results

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
    for errorType, invalidIds in invalidCellIds.items():
        if invalidIds:
            description = error_descriptions.get( errorType, f'elements with {errorType}' )
            logMethod( f"You have {len(invalidIds)} {description}." )
            logMethod( "The elements indices are:\n" + ", ".join( map( str, invalidIds ) ) )
