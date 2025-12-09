# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any
from geos.mesh_doctor.actions.collocatedNodes import Options, Result
from geos.mesh_doctor.baseTypes import COLLOCATES_NODES, UserInputs
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__TOLERANCE = "tolerance"
__TOLERANCE_DEFAULT = 0.

__COLLOCATED_NODES_DEFAULT = { __TOLERANCE: __TOLERANCE_DEFAULT }


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( COLLOCATES_NODES, help="Checks if nodes are collocated." )
    addVtuInputFileArgument( p )
    p.add_argument( '--' + __TOLERANCE,
                    type=float,
                    metavar=__TOLERANCE_DEFAULT,
                    default=__TOLERANCE_DEFAULT,
                    required=True,
                    help="[float]: The absolute distance between two nodes for them to be considered collocated." )


def convert( parsedOptions: UserInputs ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    return Options( parsedOptions[ __TOLERANCE ] )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the collocated nodes check.

    Args:
        options: The options used for the check.
        result: The result of the collocated nodes check.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    loggerResults( setupLogger, result.nodesBuckets, result.wrongSupportElements )


def loggerResults( logger: Any, nodesBuckets: list[ tuple[ int ] ], wrongSupportElements: list[ int ] ) -> None:
    """Log the results of the collocated nodes check.

    Args:
        logger: Logger instance for output.
        nodesBuckets (list[ tuple[ int ] ]): List of collocated nodes buckets.
        wrongSupportElements (list[ int ]): List of elements with wrong support nodes.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    logMethod = logger.info
    if hasattr( logger, 'results' ):
        logMethod = logger.results

    allCollocatedNodes: list[ int ] = []
    for bucket in nodesBuckets:
        for node in bucket:
            allCollocatedNodes.append( node )
    allCollocatedNodesUnique = list( set( allCollocatedNodes ) )
    if allCollocatedNodesUnique:
        logMethod( f"You have {len( allCollocatedNodesUnique )} collocated nodes." )
        logMethod( "Here are all the buckets of collocated nodes." )
        tmp: list[ str ] = []
        for bucket in nodesBuckets:
            tmp.append( f"({', '.join( map( str, bucket ) )})" )
        logMethod( f"({', '.join( tmp )})" )
    else:
        logMethod( "You have no collocated node." )

    if wrongSupportElements:
        wsElements: str = ", ".join( map( str, wrongSupportElements ) )
        logMethod( f"You have {len( wrongSupportElements )} elements with duplicated support nodes.\n" + wsElements )
    else:
        logMethod( "You have no element with duplicated support nodes." )
