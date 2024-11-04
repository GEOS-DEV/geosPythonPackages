import logging
import os
from geos.mesh.doctor.checks.generate_fractures import Options, Result, FracturePolicy
from geos.mesh.doctor.checks.vtk_utils import VtkOutput
from . import vtk_output_parsing, GENERATE_FRACTURES

__POLICY = "policy"
__FIELD_POLICY = "field"
__INTERNAL_SURFACES_POLICY = "internal_surfaces"
__POLICIES = ( __FIELD_POLICY, __INTERNAL_SURFACES_POLICY )

__FIELD_NAME = "name"
__FIELD_VALUES = "values"

__FRACTURES_OUTPUT_DIR = "fractures_output_dir"
__FRACTURES_DATA_MODE = "fractures_data_mode"


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
    p = subparsers.add_parser( GENERATE_FRACTURES, help="Splits the mesh to generate the faults and fractures." )
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
        f"If the \"{__INTERNAL_SURFACES_POLICY}\" {__POLICY} is selected, defines the name of the attribute will be considered to identify the fractures."
    )
    p.add_argument(
        '--' + __FIELD_VALUES,
        type=str,
        help=
        f"[list of comma separated integers]: If the \"{__FIELD_POLICY}\" {__POLICY} is selected, which changes of the field will be considered "
        f"as a fracture. If the \"{__INTERNAL_SURFACES_POLICY}\" {__POLICY} is selected, list of the fracture attributes. "
        f"You can create multiple fractures by separating the values with ':' like shown in this example. "
        f"--{__FIELD_VALUES} 10,12:13,14,16,18:22 will create 3 fractures identified respectively with the values (10,12), (13,14,16,18) and (22). "
        f"If no ':' is found, all values specified will be assumed to create only 1 single fracture." )
    vtk_output_parsing.fill_vtk_output_subparser( p )
    p.add_argument(
        '--' + __FRACTURES_OUTPUT_DIR,
        type=str,
        help=f"[string]: The output directory for the fractures meshes that will be generated from the mesh." )
    p.add_argument(
        '--' + __FRACTURES_DATA_MODE,
        type=str,
        help=f'[string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.' )


def convert( parsed_options ) -> Options:
    policy: str = parsed_options[ __POLICY ]
    field: str = parsed_options[ __FIELD_NAME ]
    all_values: str = parsed_options[ __FIELD_VALUES ]
    if not are_values_parsable( all_values ):
        raise ValueError(
            f"When entering --{__FIELD_VALUES}, respect this given format example:\n--{__FIELD_VALUES} " +
            "10,12:13,14,16,18:22 to create 3 fractures identified with respectively the values (10,12), (13,14,16,18) and (22)."
        )
    all_values_no_separator: str = all_values.replace( ":", "," )
    field_values_combined: frozenset[ int ] = frozenset( map( int, all_values_no_separator.split( "," ) ) )
    mesh_vtk_output = vtk_output_parsing.convert( parsed_options )
    # create the different fractures
    per_fracture: list[ str ] = all_values.split( ":" )
    field_values_per_fracture: list[ frozenset[ int ] ] = [
        frozenset( map( int, fracture.split( "," ) ) ) for fracture in per_fracture
    ]
    fracture_names: list[ str ] = [ "fracture_" + frac.replace( ",", "_" ) + ".vtu" for frac in per_fracture ]
    fractures_output_dir: str = parsed_options[ __FRACTURES_OUTPUT_DIR ]
    fractures_data_mode: str = parsed_options[ __FRACTURES_DATA_MODE ]
    all_fractures_VtkOutput: list[ VtkOutput ] = build_all_fractures_VtkOutput( fractures_output_dir,
                                                                                fractures_data_mode, mesh_vtk_output,
                                                                                fracture_names )
    return Options( policy=policy,
                    field=field,
                    field_values_combined=field_values_combined,
                    field_values_per_fracture=field_values_per_fracture,
                    mesh_VtkOutput=mesh_vtk_output,
                    all_fractures_VtkOutput=all_fractures_VtkOutput )


def display_results( options: Options, result: Result ):
    pass


def are_values_parsable( values: str ) -> bool:
    if not all( character.isdigit() or character in { ':', ',' } for character in values ):
        return False
    if values.startswith( ":" ) or values.startswith( "," ):
        return False
    if values.endswith( ":" ) or values.endswith( "," ):
        return False
    return True


def build_all_fractures_VtkOutput( fracture_output_dir: str, fractures_data_mode: str, mesh_vtk_output: VtkOutput,
                                   fracture_names: list[ str ] ) -> list[ VtkOutput ]:
    if not os.path.exists( fracture_output_dir ):
        raise ValueError( f"The --{__FRACTURES_OUTPUT_DIR} given directory does not exist." )

    if not os.access( fracture_output_dir, os.W_OK ):
        raise ValueError( f"The --{__FRACTURES_OUTPUT_DIR} given directory is not writable." )

    output_name = os.path.basename( mesh_vtk_output.output )
    splitted_name_without_expension: list[ str ] = output_name.split( "." )[ :-1 ]
    name_without_extension: str = '_'.join( splitted_name_without_expension ) + "_"
    all_fractures_VtkOuput: list[ VtkOutput ] = list()
    for fracture_name in fracture_names:
        fracture_path = os.path.join( fracture_output_dir, name_without_extension + fracture_name )
        all_fractures_VtkOuput.append( VtkOutput( fracture_path, fractures_data_mode ) )
    return all_fractures_VtkOuput
