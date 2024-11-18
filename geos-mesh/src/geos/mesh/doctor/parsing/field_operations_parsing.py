import logging
from geos.mesh.doctor.checks.field_operations import Options, Result, __SUPPORT_CHOICES, __OPERATION_CHOICES
from geos.mesh.doctor.parsing import vtk_output_parsing, FIELD_OPERATIONS

__OPERATION = "operation"

__SUPPORT = "support"

__FIELD_NAMES = "field_names"
__SOURCE = "source"

__WHICH_VTM = "which_vtm"
__WHICH_VTM_SUGGESTIONS = [ "first", "last" ]


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( FIELD_OPERATIONS, help=f"Allows to perform an operation on fields from a source to your input mesh." )
    p.add_argument( '--' + __OPERATION,
                    type=str,
                    required=True,
                    metavar=", ".join( map( str, __OPERATION_CHOICES ) ),
                    default=__OPERATION_CHOICES[ 0 ],
                    help="[string]: Choose what operation you want to perform from the source to your input mesh. "
                         f"'{__OPERATION_CHOICES[ 0 ]}' copies field(s) from the source to the input mesh." )
    p.add_argument( '--' + __SUPPORT,
                    type=str,
                    required=True,
                    metavar=", ".join( map( str, __SUPPORT_CHOICES ) ),
                    default=__SUPPORT_CHOICES[ 0 ],
                    help="[string]: Where to define field." )
    p.add_argument( '--' + __FIELD_NAMES,
                    type=str,
                    required=True,
                    help="[list of string comma separated]: Name of each field to use for the operation." )
    p.add_argument( '--' + __SOURCE,
                    type=str,
                    required=True,
                    help="[string]: Where field data to use for operation comes from (function, .vtu, .vtm, .pvd file)." )
    p.add_argument( '--' + __WHICH_VTM,
                    type=str,
                    required=False,
                    default=__WHICH_VTM_SUGGESTIONS[ 1 ],
                    help="[string]: If your input is a .pvd, choose which .vtm (each .vtm corresponding to a unique "
                         "timestep) will be used for the operation. To do so, you can choose amongst these possibilities: "
                         "'first' will select the initial timestep; 'last' will select the final timestep; or you can enter "
                         "directly the index starting from 0 of the timestep (not the time). By default, the value is set to 'last'." )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    operation: str = parsed_options[ __OPERATION ]
    if operation not in __OPERATION_CHOICES:
        raise ValueError( f"For --{__OPERATION}, the only choices available are {__OPERATION_CHOICES}." )
    support: str = parsed_options[ __SUPPORT ]
    if support not in __SUPPORT_CHOICES:
        raise ValueError( f"For --{__SUPPORT}, the only choices available are {__SUPPORT_CHOICES}." )
    field_names: list[ str ] = list( map( str, parsed_options[ __FIELD_NAMES ].split( "," ) ) )
    which_vtm: str = parsed_options[ __WHICH_VTM ]
    if which_vtm in __WHICH_VTM_SUGGESTIONS:
        vtm_index: int = 0 if which_vtm == __WHICH_VTM_SUGGESTIONS[ 0 ] else -1
    else:
        try:
            vtm_index = int( which_vtm )
        except ValueError:
            raise ValueError( f"The choice for --{__WHICH_VTM} needs to be an integer or " +
                              f"'{__WHICH_VTM_SUGGESTIONS[ 0 ]}' or '{__WHICH_VTM_SUGGESTIONS[ 1 ]}'." )
    return Options( operation=operation,
                    support=support,
                    field_names=field_names,
                    source=parsed_options[ __SOURCE ],
                    vtm_index=vtm_index,
                    out_vtk=vtk_output_parsing.convert( parsed_options ) )


def display_results( options: Options, result: Result ):
    if result.info != "OK":
        logging.error( f"Field addition failed" )
