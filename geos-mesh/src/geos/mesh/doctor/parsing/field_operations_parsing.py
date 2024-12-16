import logging
from geos.mesh.doctor.checks.field_operations import Options, Result, __SUPPORT_CHOICES
from geos.mesh.doctor.parsing import vtk_output_parsing, FIELD_OPERATIONS


__SUPPORT = "support"
__SOURCE = "source"

__COPY_FIELDS = "copy_fields"
__CREATE_FIELDS = "create_fields"

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
                    required=False,
                    help="[string]: Where field data to use for operation comes from .vtu, .vtm or .pvd file." )
    p.add_argument( '--' + __COPY_FIELDS,
                    type=str,
                    required=False,
                    help="[list of string comma separated]: Allows to copy a field from an input mesh to an output mesh. " +
                    "This copy can also be done while applying a coefficient on the copied field. The syntax to use " +
                    "is 'old_field_name:new_field_name:function'. Example: The available fields in your input mesh " +
                    "are 'poro,perm,temp,pressure,'. First, to copy 'poro' without any modification use 'poro'. " +
                    "Then, to copy 'perm' and change its name to 'permeability' use 'perm:permeability'. " +
                    "After, to copy 'temp' and change its name to 'temperature' and to increase the values by 3 use 'temp:temperature:+3'. " +
                    "Finally, to copy 'pressure' without changing its name and to multiply the values by 10 use 'pressure:pressure:*10'. " +
                    f"The combined syntax is '--{__COPY_FIELDS} poro,perm:permeability,temp:temperature:+3,pressure:pressure:*10'." )
    p.add_argument( '--' + __CREATE_FIELDS,
                    type=str,
                    required=False,
                    help="[list of string comma separated]: Allows to create new fields by using a function that is " +
                    "either pre-defined or to implement one. The syntax to use is 'new_field_name:function'. " +
                    "Predefined functions are: 1) 'distances_mesh_center' calculates the distance from the center. " +
                    "2) 'random' populates an array with samples from a uniform distribution over [0, 1). An example " +
                    f" would be '--{__CREATE_FIELDS} new_distances:distances_mesh_center'." +
                    "The other method is to implement a function using the 'numexpr' library functionalities. For " +
                    "example, if in your source vtk data you have a cell array called 'PERMEABILITY' and you want to " +
                    f"create a new field that is the log of this field, you can use: '--{__CREATE_FIELDS} log_perm:log(PERMEABILITY)'.")
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
    support: str = parsed_options[ __SUPPORT ]
    if support not in __SUPPORT_CHOICES:
        raise ValueError( f"For --{__SUPPORT}, the only choices available are {__SUPPORT_CHOICES}." )

    copy_fields: list[ tuple[ str ] ] = list()
    splitted_copy_fields: list[ str ] = parsed_options[ __COPY_FIELDS ].split( "," )
    for copy_field in splitted_copy_fields:
        name_newname_function: tuple[ str ] = tuple( copy_field.split( ":" ) )
        if len( name_newname_function ) == 0 or len( name_newname_function ) > 3:
            raise ValueError( f"The correct format for '--{__COPY_FIELDS}' is to have either: 'field_name', or " +
                              f"'field_name:new_field_name' or 'field_name:new_field_name:function' "
                              f"but not '{copy_field}'." )
        else:
            copy_fields.append( name_newname_function )

    created_fields: list[ tuple[ str ] ] = list()
    splitted_created_fields: list[ str ] = parsed_options[ __CREATE_FIELDS ].split( "," )
    for created_field in splitted_created_fields:
        newname_function = tuple( created_field.split( ":" ) )
        if len( newname_function ) == 2:
            created_fields.append( newname_function )
        else:
            raise ValueError( f"The correct format for '--{__CREATE_FIELDS}' is to have 'new_field_name:function', " +
                              f"but not '{created_field}'." )

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
                    copy_fields=copy_fields,
                    created_fields=created_fields,
                    vtm_index=vtm_index,
                    out_vtk=vtk_output_parsing.convert( parsed_options ) )


def display_results( options: Options, result: Result ):
    if result.info != "OK":
        logging.error( f"Field addition failed" )
