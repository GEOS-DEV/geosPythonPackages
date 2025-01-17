import logging
from geos.mesh.doctor.checks.field_operations import Options, Result, check_valid_support, __SUPPORT_CHOICES
from geos.mesh.doctor.parsing import vtk_output_parsing, FIELD_OPERATIONS

__SUPPORT = "support"
__SOURCE = "source"

__OPERATIONS = "operations"
__OPERATIONS_DEFAULT = ""

__WHICH_VTM = "which_vtm"
__WHICH_VTM_SUGGESTIONS = [ "first", "last" ]


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( FIELD_OPERATIONS,
                               help=f"Allows to perform an operation on fields from a source to your input mesh." )
    p.add_argument( '--' + __SUPPORT,
                    type=str,
                    required=True,
                    metavar=", ".join( map( str, __SUPPORT_CHOICES ) ),
                    default=__SUPPORT_CHOICES[ 0 ],
                    help="[string]: Where to define field." )
    p.add_argument( '--' + __SOURCE,
                    type=str,
                    required=True,
                    help="[string]: Where field data to use for operation comes from .vtu, .vtm or .pvd file." )
    p.add_argument( '--' + __OPERATIONS,
                    type=str,
                    required=True,
                    default=__OPERATIONS_DEFAULT,
                    help="[list of string comma separated]: The syntax here is function0:new_name0, " +
                    "function1:new_name1, ... Allows to perform a wide arrays of operations to  add new data to your " +
                    "output mesh using the source file data.  Examples are the following: 1. Copy of the field " +
                    " 'poro' from the input to the ouput with 'poro:poro'.  2. Copy of the field 'PERM' from the " +
                    "input to the ouput with a multiplication of the values by 10 with 'PERM*10:PERM'. " +
                    "3. Copy of the field 'TEMP' from the input to the ouput with an addition to the values by 0.5 " +
                    "and change the name of the field to 'temperature' with 'TEMP+0.5:TEMPERATURE'. 4. Create a new " +
                    "field 'NEW_PARAM' using the input 'PERM' field and having the square root of it with " +
                    "'sqrt(PERM):NEW_PARAM'. Another method is to use precoded functions available which are: " +
                    "1. 'distances_mesh_center' will create a field where the distances from the mesh center are " +
                    "calculated for all the elements chosen as support. To use: " +
                    "'distances_mesh_center:NEW_FIELD_NAME'. 2. 'random_uniform_distribution' will create a field " +
                    "with samples from a uniform distribution over (0, 1). To use: 'random:NEW_FIELD_NAME'." )
    p.add_argument( '--' + __WHICH_VTM,
                    type=str,
                    required=False,
                    default=__WHICH_VTM_SUGGESTIONS[ 1 ],
                    help="[string]: If your input is a .pvd, choose which .vtm (each .vtm corresponding to a unique " +
                    "timestep) will be used for the operation. To do so, you can choose amongst these possibilities: " +
                    "'first' will select the initial timestep; 'last' will select the final timestep; or you can " +
                    "enter directly the index starting from 0 of the timestep (not the time). By default, the value" +
                    " is set to 'last'." )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    support: str = parsed_options[ __SUPPORT ]
    check_valid_support( support )

    operations: list[ tuple[ str ] ] = list()
    parsed_operations: str = parsed_options[ __OPERATIONS ]
    if parsed_operations == __OPERATIONS_DEFAULT:
        raise ValueError( f"No operation was found. Cannot execute this feature." )
    splitted_operations: list[ str ] = parsed_operations.split( "," )
    for operation in splitted_operations:
        function_newname: tuple[ str ] = tuple( operation.split( ":" ) )
        if not len( function_newname ) == 2:
            raise ValueError( f"The correct format for '--{__OPERATIONS}' is to have 'function:newname'." )
        operations.append( function_newname )

    which_vtm: str = parsed_options[ __WHICH_VTM ]
    if which_vtm in __WHICH_VTM_SUGGESTIONS:
        vtm_index: int = 0 if which_vtm == __WHICH_VTM_SUGGESTIONS[ 0 ] else -1
    else:
        try:
            vtm_index = int( which_vtm )
        except ValueError:
            raise ValueError( f"The choice for --{__WHICH_VTM} needs to be an integer or " +
                              f"'{__WHICH_VTM_SUGGESTIONS[ 0 ]}' or '{__WHICH_VTM_SUGGESTIONS[ 1 ]}'." )

    return Options( support=support,
                    source=parsed_options[ __SOURCE ],
                    operations=operations,
                    vtm_index=vtm_index,
                    vtk_output=vtk_output_parsing.convert( parsed_options ) )


def display_results( options: Options, result: Result ):
    if result.info != "OK":
        logging.error( f"Field addition failed" )
