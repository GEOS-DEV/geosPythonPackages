from dataclasses import dataclass
from geos.mesh_doctor.actions.generateGlobalIds import Options, Result
from geos.mesh_doctor.parsing import vtkOutputParsing, GENERATE_GLOBAL_IDS
from geos.mesh_doctor.parsing.cliParsing import setupLogger

__CELLS, __POINTS = "cells", "points"


@dataclass( frozen=True )
class GlobalIdsInfo:
    cells: bool
    points: bool


def convertGlobalIds( parsedOptions ) -> GlobalIdsInfo:
    return GlobalIdsInfo( cells=parsedOptions[ __CELLS ], points=parsedOptions[ __POINTS ] )


def convert( parsedOptions ) -> Options:
    gids: GlobalIdsInfo = convertGlobalIds( parsedOptions )
    return Options( vtkOutput=vtkOutputParsing.convert( parsedOptions ),
                    generateCellsGlobalIds=gids.cells,
                    generatePointsGlobalIds=gids.points )


def fillGenerateGlobalIdsSubparser( p ):
    p.add_argument( '--' + __CELLS,
                    action="store_true",
                    help="[bool]: Generate global ids for cells. Defaults to true." )
    p.add_argument( '--no-' + __CELLS,
                    action="store_false",
                    dest=__CELLS,
                    help="[bool]: Don't generate global ids for cells." )
    p.set_defaults( **{ __CELLS: True } )
    p.add_argument( '--' + __POINTS,
                    action="store_true",
                    help="[bool]: Generate global ids for points. Defaults to true." )
    p.add_argument( '--no-' + __POINTS,
                    action="store_false",
                    dest=__POINTS,
                    help="[bool]: Don't generate global ids for points." )
    p.set_defaults( **{ __POINTS: True } )


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( GENERATE_GLOBAL_IDS, help="Adds globals ids for points and cells." )
    fillGenerateGlobalIdsSubparser( p )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ):
    setupLogger.info( result.info )
