from argparse import _SubParsersAction
from typing import Any
from geos.mesh_doctor.actions.generateCube import Options, Result, FieldInfo
from geos.mesh_doctor.parsing import vtkOutputParsing, generateGlobalIdsParsing, GENERATE_CUBE
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh_doctor.parsing.generateGlobalIdsParsing import GlobalIdsInfo

__X, __Y, __Z, __NX, __NY, __NZ = "x", "y", "z", "nx", "ny", "nz"
__FIELDS = "fields"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    def checkDiscretizations( x: tuple[ float, ... ], nx: tuple[ int, ... ], title: str ) -> None:
        if len( x ) != len( nx ) + 1:
            raise ValueError( f"{title} information (\"{x}\" and \"{nx}\") does not have consistent size." )

    checkDiscretizations( parsedOptions[ __X ], parsedOptions[ __NX ], __X )
    checkDiscretizations( parsedOptions[ __Y ], parsedOptions[ __NY ], __Y )
    checkDiscretizations( parsedOptions[ __Z ], parsedOptions[ __NZ ], __Z )

    def parseFields( s: str ) -> FieldInfo:
        name, support, dim = s.split( ":" )
        if support not in ( "CELLS", "POINTS" ):
            raise ValueError( f"Support {support} for field \"{name}\" must be one of \"CELLS\" or \"POINTS\"." )
        try:
            dimension = int( dim )
            assert dimension > 0
        except ValueError as e:
            raise ValueError( f"Dimension {dimension} cannot be converted to an integer." ) from e
        except AssertionError as e:
            raise ValueError( f"Dimension {dimension} must be a positive integer" ) from e
        return FieldInfo( name=name, support=support, dimension=dimension )

    gids: GlobalIdsInfo = generateGlobalIdsParsing.convertGlobalIds( parsedOptions )

    return Options( vtkOutput=vtkOutputParsing.convert( parsedOptions ),
                    generateCellsGlobalIds=gids.cells,
                    generatePointsGlobalIds=gids.points,
                    xs=parsedOptions[ __X ],
                    ys=parsedOptions[ __Y ],
                    zs=parsedOptions[ __Z ],
                    nxs=parsedOptions[ __NX ],
                    nys=parsedOptions[ __NY ],
                    nzs=parsedOptions[ __NZ ],
                    fields=tuple( map( parseFields, parsedOptions[ __FIELDS ] ) ) )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( GENERATE_CUBE, help="Generate a cube and its fields." )
    p.add_argument( '--' + __X,
                    type=lambda s: tuple( map( float, s.split( ":" ) ) ),
                    metavar="0:1.5:3",
                    help="[list of floats]: X coordinates of the points." )
    p.add_argument( '--' + __Y,
                    type=lambda s: tuple( map( float, s.split( ":" ) ) ),
                    metavar="0:5:10",
                    help="[list of floats]: Y coordinates of the points." )
    p.add_argument( '--' + __Z,
                    type=lambda s: tuple( map( float, s.split( ":" ) ) ),
                    metavar="0:1",
                    help="[list of floats]: Z coordinates of the points." )
    p.add_argument( '--' + __NX,
                    type=lambda s: tuple( map( int, s.split( ":" ) ) ),
                    metavar="2:2",
                    help="[list of integers]: Number of elements in the X direction." )
    p.add_argument( '--' + __NY,
                    type=lambda s: tuple( map( int, s.split( ":" ) ) ),
                    metavar="1:1",
                    help="[list of integers]: Number of elements in the Y direction." )
    p.add_argument( '--' + __NZ,
                    type=lambda s: tuple( map( int, s.split( ":" ) ) ),
                    metavar="4",
                    help="[list of integers]: Number of elements in the Z direction." )
    p.add_argument( '--' + __FIELDS,
                    type=str,
                    metavar="name:support:dim",
                    nargs="+",
                    required=False,
                    default=(),
                    help="Create fields on CELLS or POINTS, with given dimension (typically 1 or 3)." )
    generateGlobalIdsParsing.fillGenerateGlobalIdsSubparser( p )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the generate cube feature.

    Args:
        options: The options used for the check.
        result: The result of the generate cube feature.
    """
    setupLogger.info( result.info )
