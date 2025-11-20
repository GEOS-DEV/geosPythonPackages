from __future__ import annotations
from argparse import _SubParsersAction, ArgumentParser, _ArgumentGroup
from dataclasses import dataclass
from typing import Any
from geos.mesh_doctor.actions.generateGlobalIds import Options, Result
from geos.mesh_doctor.parsing import vtkOutputParsing, GENERATE_GLOBAL_IDS
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__CELLS, __POINTS = "cells", "points"


@dataclass( frozen=True )
class GlobalIdsInfo:
    cells: bool
    points: bool


def convertToGlobalIdsInfo( parsedOptions: dict[ str, Any ] ) -> GlobalIdsInfo:
    """Extract GlobalIdsInfo from parsed options.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        GlobalIdsInfo: The global IDs configuration.
    """
    return GlobalIdsInfo( cells=parsedOptions[ __CELLS ], points=parsedOptions[ __POINTS ] )


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    gids: GlobalIdsInfo = convertToGlobalIdsInfo( parsedOptions )
    return Options( vtkOutput=vtkOutputParsing.convert( parsedOptions ),
                    generateCellsGlobalIds=gids.cells,
                    generatePointsGlobalIds=gids.points )


def addArguments( parser: ArgumentParser | _ArgumentGroup ) -> None:
    """Add global IDs arguments to an existing parser.

    Args:
        parser: The argument parser or argument group to add arguments to.
    """
    parser.add_argument( '--' + __CELLS,
                         action="store_true",
                         help="[bool]: Generate global ids for cells. Defaults to true." )
    parser.add_argument( '--no-' + __CELLS,
                         action="store_false",
                         dest=__CELLS,
                         help="[bool]: Don't generate global ids for cells." )
    parser.set_defaults( **{ __CELLS: True } )
    parser.add_argument( '--' + __POINTS,
                         action="store_true",
                         help="[bool]: Generate global ids for points. Defaults to true." )
    parser.add_argument( '--no-' + __POINTS,
                         action="store_false",
                         dest=__POINTS,
                         help="[bool]: Don't generate global ids for points." )
    parser.set_defaults( **{ __POINTS: True } )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( GENERATE_GLOBAL_IDS, help="Adds globals ids for points and cells." )
    addVtuInputFileArgument( p )
    addArguments( p )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the generate global ids feature.

    Args:
        options: The options used for the check.
        result: The result of the generate global ids feature.
    """
    setupLogger.info( result.info )
