from dataclasses import dataclass
from geos.mesh.doctor.actions.generate_global_ids import Options, Result
from geos.mesh.doctor.parsing import vtk_output_parsing, GENERATE_GLOBAL_IDS
from geos.mesh.doctor.parsing.cli_parsing import setupLogger

__CELLS, __POINTS = "cells", "points"


@dataclass( frozen=True )
class GlobalIdsInfo:
    cells: bool
    points: bool


def convertGlobalIds( parsedOptions ) -> GlobalIdsInfo:
    return GlobalIdsInfo( cells=parsedOptions[ __CELLS ], points=parsedOptions[ __POINTS ] )


def convert( parsedOptions ) -> Options:
    gids: GlobalIdsInfo = convertGlobalIds( parsedOptions )
    return Options( vtkOutput=vtk_output_parsing.convert( parsedOptions ),
                    generateCellsGlobalIds=gids.cells,
                    generatePointsGlobalIds=gids.points )


def fillGenerateGlobalIdsSubparser( p ):
    p.add_argument( '--' + __CELLS,
                    action="store_true",
                    help=f"[bool]: Generate global ids for cells. Defaults to true." )
    p.add_argument( '--no-' + __CELLS,
                    action="store_false",
                    dest=__CELLS,
                    help=f"[bool]: Don't generate global ids for cells." )
    p.set_defaults( **{ __CELLS: True } )
    p.add_argument( '--' + __POINTS,
                    action="store_true",
                    help=f"[bool]: Generate global ids for points. Defaults to true." )
    p.add_argument( '--no-' + __POINTS,
                    action="store_false",
                    dest=__POINTS,
                    help=f"[bool]: Don't generate global ids for points." )
    p.set_defaults( **{ __POINTS: True } )


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( GENERATE_GLOBAL_IDS, help="Adds globals ids for points and cells." )
    fillGenerateGlobalIdsSubparser( p )
    vtk_output_parsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ):
    setupLogger.info( result.info )
