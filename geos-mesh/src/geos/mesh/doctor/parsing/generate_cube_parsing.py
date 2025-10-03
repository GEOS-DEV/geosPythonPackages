from geos.mesh.doctor.actions.generate_cube import Options, Result, FieldInfo
from geos.mesh.doctor.parsing import vtk_output_parsing, generate_global_ids_parsing, GENERATE_CUBE
from geos.mesh.doctor.parsing.cli_parsing import setupLogger
from geos.mesh.doctor.parsing.generate_global_ids_parsing import GlobalIdsInfo

__X, __Y, __Z, __NX, __NY, __NZ = "x", "y", "z", "nx", "ny", "nz"
__FIELDS = "fields"


def convert( parsedOptions ) -> Options:

    def checkDiscretizations( x, nx, title ):
        if len( x ) != len( nx ) + 1:
            raise ValueError( f"{title} information (\"{x}\" and \"{nx}\") does not have consistent size." )

    checkDiscretizations( parsedOptions[ __X ], parsedOptions[ __NX ], __X )
    checkDiscretizations( parsedOptions[ __Y ], parsedOptions[ __NY ], __Y )
    checkDiscretizations( parsedOptions[ __Z ], parsedOptions[ __NZ ], __Z )

    def parseFields( s ):
        name, support, dim = s.split( ":" )
        if support not in ( "CELLS", "POINTS" ):
            raise ValueError( f"Support {support} for field \"{name}\" must be one of \"CELLS\" or \"POINTS\"." )
        try:
            dim = int( dim )
            assert dim > 0
        except ValueError:
            raise ValueError( f"Dimension {dim} cannot be converted to an integer." )
        except AssertionError:
            raise ValueError( f"Dimension {dim} must be a positive integer" )
        return FieldInfo( name=name, support=support, dimension=dim )

    gids: GlobalIdsInfo = generate_global_ids_parsing.convertGlobalIds( parsedOptions )

    return Options( vtkOutput=vtk_output_parsing.convert( parsedOptions ),
                    generateCellsGlobalIds=gids.cells,
                    generatePointsGlobalIds=gids.points,
                    xs=parsedOptions[ __X ],
                    ys=parsedOptions[ __Y ],
                    zs=parsedOptions[ __Z ],
                    nxs=parsedOptions[ __NX ],
                    nys=parsedOptions[ __NY ],
                    nzs=parsedOptions[ __NZ ],
                    fields=tuple( map( parseFields, parsedOptions[ __FIELDS ] ) ) )


def fillSubparser( subparsers ) -> None:
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
    generate_global_ids_parsing.fillGenerateGlobalIdsSubparser( p )
    vtk_output_parsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ):
    setupLogger.info( result.info )
