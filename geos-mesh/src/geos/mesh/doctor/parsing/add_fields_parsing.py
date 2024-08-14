import logging

from checks.add_fields import Options, Result

from . import vtk_output_parsing, ADD_FIELDS

__SUPPORT = "support"
__NAME = "name"
__SOURCE = "source"


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( ADD_FIELDS, help=f"Add cell or point data to a mesh." )
    p.add_argument( '--' + __SUPPORT, type=str, required=True, help=f"[string]: Where to define field (point/cell)." )
    p.add_argument( '--' + __NAME, type=str, required=True, help=f"[string]: Name of the field to add." )
    p.add_argument( '--' + __SOURCE,
                    type=str,
                    required=True,
                    help=f"[string]: Where field data to add comes from (function, mesh)." )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    """
    """
    return Options( support=parsed_options[ __SUPPORT ],
                    field_name=parsed_options[ __NAME ],
                    source=parsed_options[ __SOURCE ],
                    out_vtk=vtk_output_parsing.convert( parsed_options ) )


def display_results( options: Options, result: Result ):
    if result.info != True:
        logging.error( f"Field addition failed" )
