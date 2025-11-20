from __future__ import annotations
from argparse import _SubParsersAction
import os
from typing import Any
from geos.mesh_doctor.actions.generateFractures import Options, Result, FracturePolicy
from geos.mesh_doctor.parsing import vtkOutputParsing, GENERATE_FRACTURES
from geos.mesh_doctor.parsing.cliParsing import addVtuInputFileArgument
from geos.mesh.io.vtkIO import VtkOutput

__POLICY = "policy"
__FIELD_POLICY = "field"
__INTERNAL_SURFACES_POLICY = "internalSurfaces"
__POLICIES = ( __FIELD_POLICY, __INTERNAL_SURFACES_POLICY )

__FIELD_NAME = "name"
__FIELD_VALUES = "values"

__FRACTURES_OUTPUT_DIR = "fracturesOutputDir"
__FRACTURES_DATA_MODE = "fracturesDataMode"
__FRACTURES_DATA_MODE_VALUES = "binary", "ascii"
__FRACTURES_DATA_MODE_DEFAULT = __FRACTURES_DATA_MODE_VALUES[ 0 ]


def convertToFracturePolicy( s: str ) -> FracturePolicy:
    """Converts the user input to the proper enum chosen.

    I do not want to use the auto conversion already available to force explicit conversion.

    Args:
        s (str): The user input

    Raises:
        ValueError: If the parsed options are invalid.

    Returns:
        FracturePolicy: The matching enum.
    """
    if s == __FIELD_POLICY:
        return FracturePolicy.FIELD
    elif s == __INTERNAL_SURFACES_POLICY:
        return FracturePolicy.INTERNAL_SURFACES
    raise ValueError( f"Policy {s} is not valid. Please use one of \"{', '.join(map(str, __POLICIES))}\"." )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add supported elements check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( GENERATE_FRACTURES, help="Splits the mesh to generate the faults and fractures." )
    addVtuInputFileArgument( p )
    p.add_argument( '--' + __POLICY,
                    type=convertToFracturePolicy,
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
        "You can create multiple fractures by separating the values with ':' like shown in this example. "
        f"--{__FIELD_VALUES} 10,12:13,14,16,18:22 will create 3 fractures identified respectively with the values (10,12), (13,14,16,18) and (22). "
        "If no ':' is found, all values specified will be assumed to create only 1 single fracture." )
    vtkOutputParsing.fillVtkOutputSubparser( p )
    p.add_argument(
        '--' + __FRACTURES_OUTPUT_DIR,
        type=str,
        help="[string]: The output directory for the fractures meshes that will be generated from the mesh." )
    p.add_argument(
        '--' + __FRACTURES_DATA_MODE,
        type=str,
        metavar=", ".join( __FRACTURES_DATA_MODE_VALUES ),
        default=__FRACTURES_DATA_MODE_DEFAULT,
        help='[string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.' )


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for supported elements check.
    """
    policy: str = parsedOptions[ __POLICY ]
    field: str = parsedOptions[ __FIELD_NAME ]
    allValues: str = parsedOptions[ __FIELD_VALUES ]
    if not areValuesParsable( allValues ):
        raise ValueError(
            f"When entering --{__FIELD_VALUES}, respect this given format example:\n--{__FIELD_VALUES} " +
            "10,12:13,14,16,18:22 to create 3 fractures identified with respectively the values (10,12), (13,14,16,18) and (22)."
        )
    allValuesNoSeparator: str = allValues.replace( ":", "," )
    fieldValuesCombined: frozenset[ int ] = frozenset( map( int, allValuesNoSeparator.split( "," ) ) )
    meshVtkOutput = vtkOutputParsing.convert( parsedOptions )
    # create the different fractures
    perFracture: list[ str ] = allValues.split( ":" )
    fieldValuesPerFracture: list[ frozenset[ int ] ] = [
        frozenset( map( int, fracture.split( "," ) ) ) for fracture in perFracture
    ]
    fractureNames: list[ str ] = [ "fracture_" + frac.replace( ",", "_" ) + ".vtu" for frac in perFracture ]
    fracturesOutputDir: str = parsedOptions[ __FRACTURES_OUTPUT_DIR ]
    fracturesDataMode: str = parsedOptions[ __FRACTURES_DATA_MODE ]
    fracturesDataModeResult: bool = fracturesDataMode == __FRACTURES_DATA_MODE_DEFAULT
    allFracturesVtkOutput: list[ VtkOutput ] = buildAllFracturesVtkOutput( fracturesOutputDir, fracturesDataModeResult,
                                                                           meshVtkOutput, fractureNames )
    return Options( policy=policy,
                    field=field,
                    fieldValuesCombined=fieldValuesCombined,
                    fieldValuesPerFracture=fieldValuesPerFracture,
                    meshVtkOutput=meshVtkOutput,
                    allFracturesVtkOutput=allFracturesVtkOutput )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the generate fractures feature.

    Args:
        options: The options used for the check.
        result: The result of the generate fractures feature.
    """
    pass


def areValuesParsable( values: str ) -> bool:
    """Check if a string contains parsable values.

    Args:
        values (str): The string containing values to be checked.

    Returns:
        bool: True if the string contains parsable values, False otherwise.
    """
    if not all( character.isdigit() or character in { ':', ',' } for character in values ):
        return False
    if values.startswith( ":" ) or values.startswith( "," ):
        return False
    return not ( values.endswith( ":" ) or values.endswith( "," ) )


def buildAllFracturesVtkOutput( fractureOutputDir: str, fracturesDataMode: bool, meshVtkOutput: VtkOutput,
                                fractureNames: list[ str ] ) -> list[ VtkOutput ]:
    """Create all the VtkOutput objects for every fracture mesh that will be output.

    Args:
        fractureOutputDir (str): The directory where fracture output files will be saved.
        fracturesDataMode (bool): Whether the fractures data mode is enabled.
        meshVtkOutput (VtkOutput): The VtkOutput object for the mesh.
        fractureNames (list[ str ]): The list of fracture file names.

    Raises:
        ValueError: If the given fracture output directory does not exist.
        ValueError: If the given fracture output directory is not writable.

    Returns:
        list[ VtkOutput ]: All the VtkOutput objects for every fracture mesh that will be output.
    """
    if not os.path.exists( fractureOutputDir ):
        raise ValueError( f"The --{__FRACTURES_OUTPUT_DIR} given directory '{fractureOutputDir}' does not exist." )

    if not os.access( fractureOutputDir, os.W_OK ):
        raise ValueError( f"The --{__FRACTURES_OUTPUT_DIR} given directory '{fractureOutputDir}' is not writable." )

    outputName = os.path.basename( meshVtkOutput.output )
    splittedNameWithoutExtension: list[ str ] = outputName.split( "." )[ :-1 ]
    nameWithoutExtension: str = '_'.join( splittedNameWithoutExtension ) + "_"
    allFracturesVtkOutput: list[ VtkOutput ] = []
    for fractureName in fractureNames:
        fracturePath = os.path.join( fractureOutputDir, nameWithoutExtension + fractureName )
        allFracturesVtkOutput.append( VtkOutput( fracturePath, fracturesDataMode ) )
    return allFracturesVtkOutput
