import logging

from geos.mesh.doctor.checks.generate_fractures import Options, Result, FracturePolicy

from . import vtk_output_parsing, GENERATE_FRACTURES

__POLICY = "policy"
__FIELD_POLICY = "field"
__INTERNAL_SURFACES_POLICY = "internal_surfaces"
__POLICIES = ( __FIELD_POLICY, __INTERNAL_SURFACES_POLICY )

__FIELD_NAME = "name"
__FIELD_VALUES = "values"

__FRACTURE_PREFIX = "fracture"


def convert_to_fracture_policy( s: str ) -> FracturePolicy:
    """
    Converts the user input to the proper enum chosen.
    I do not want to use the auto conversion already available to force explicit conversion.
    :param s: The user input
    :return: The matching enum.
    """
    if s == __FIELD_POLICY:
        return FracturePolicy.FIELD
    elif s == __INTERNAL_SURFACES_POLICY:
        return FracturePolicy.INTERNAL_SURFACES
    raise ValueError( f"Policy {s} is not valid. Please use one of \"{', '.join(map(str, __POLICIES))}\"." )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( GENERATE_FRACTURES,
                               help="Splits the mesh to generate the faults and fractures. [EXPERIMENTAL]" )
    p.add_argument( '--' + __POLICY,
                    type=convert_to_fracture_policy,
                    metavar=", ".join( __POLICIES ),
                    required=True,
                    help=f"[string]: The criterion to define the surfaces that will be changed into fracture zones. "
                    f"Possible values are \"{', '.join(__POLICIES)}\"" )
    p.add_argument(
        '--' + __FIELD_NAME,
        type=str,
        help=
        f"[string]: If the \"{__FIELD_POLICY}\" {__POLICY} is selected, defines which field will be considered to define the fractures. "
        f"If the \"{__INTERNAL_SURFACES_POLICY}\" {__POLICY} is selected, defines the name of the attribute will be considered to identify the fractures. "
    )
    p.add_argument(
        '--' + __FIELD_VALUES,
        type=str,
        help=
        f"[list of comma separated integers]: If the \"{__FIELD_POLICY}\" {__POLICY} is selected, which changes of the field will be considered as a fracture. If the \"{__INTERNAL_SURFACES_POLICY}\" {__POLICY} is selected, list of the fracture attributes."
    )
    vtk_output_parsing.fill_vtk_output_subparser( p )
    vtk_output_parsing.fill_vtk_output_subparser( p, prefix=__FRACTURE_PREFIX )


def convert( parsed_options ) -> Options:
    policy = parsed_options[ __POLICY ]
    field = parsed_options[ __FIELD_NAME ]
    field_values = frozenset( map( int, parsed_options[ __FIELD_VALUES ].split( "," ) ) )
    vtk_output = vtk_output_parsing.convert( parsed_options )
    vtk_fracture_output = vtk_output_parsing.convert( parsed_options, prefix=__FRACTURE_PREFIX )
    return Options( policy=policy,
                    field=field,
                    field_values=field_values,
                    vtk_output=vtk_output,
                    vtk_fracture_output=vtk_fracture_output )


def display_results( options: Options, result: Result ):
    pass
