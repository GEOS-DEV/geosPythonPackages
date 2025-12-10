# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from __future__ import annotations
from argparse import ArgumentParser, _ArgumentGroup
import textwrap
from typing import Any
from geos.mesh.io.vtkIO import VtkOutput

__OUTPUT_FILE = "output"
__OUTPUT_BINARY_MODE = "data-mode"
__OUTPUT_BINARY_MODE_VALUES = "binary", "ascii"
__OUTPUT_BINARY_MODE_DEFAULT = __OUTPUT_BINARY_MODE_VALUES[ 0 ]
__CAN_OVERWRITE = "canOverwrite"


def getVtkOutputHelp() -> str:
    """Get help text for VTK output options.

    Returns:
        str: Formatted help text describing output file and data mode options.
    """
    msg = ( f"{__OUTPUT_FILE} [string]: The vtk output file destination.\n"
            f"    {__OUTPUT_BINARY_MODE} [string]: For \".vtu\" output format, "
            f"the data mode can be {' or '.join(__OUTPUT_BINARY_MODE_VALUES)}. "
            f"Defaults to {__OUTPUT_BINARY_MODE_DEFAULT}.\n"
            f"    {__CAN_OVERWRITE} [flag]: Allow overwriting existing output files. Defaults to False." )
    return textwrap.dedent( msg )


def __buildArg( prefix: str, main: str ) -> str:
    """Build an argument name by joining prefix and main with a hyphen.

    Args:
        prefix: The prefix string (can be empty).
        main: The main argument name.

    Returns:
        str: The joined argument name.
    """
    return "-".join( filter( None, ( prefix, main ) ) )


def fillVtkOutputSubparser( parser: ArgumentParser | _ArgumentGroup, prefix: str = "" ) -> None:
    """Add VTK output arguments to an argument parser.

    Args:
        parser: The argument parser or argument group to add arguments to.
        prefix: Optional prefix for argument names.
    """
    parser.add_argument( '--' + __buildArg( prefix, __OUTPUT_FILE ),
                         type=str,
                         required=True,
                         help="[string]: The vtk output file destination." )
    help_text = ( f"[string]: For \".vtu\" output format, the data mode can be "
                  f"{' or '.join(__OUTPUT_BINARY_MODE_VALUES)}. Defaults to {__OUTPUT_BINARY_MODE_DEFAULT}." )
    parser.add_argument( '--' + __buildArg( prefix, __OUTPUT_BINARY_MODE ),
                         type=str,
                         metavar=", ".join( __OUTPUT_BINARY_MODE_VALUES ),
                         default=__OUTPUT_BINARY_MODE_DEFAULT,
                         help=help_text )
    parser.add_argument( '--' + __buildArg( prefix, __CAN_OVERWRITE ),
                         action='store_true',
                         default=False,
                         help="[flag]: Allow overwriting existing output files. Defaults to False." )


def convert( parsedOptions: dict[ str, Any ], prefix: str = "" ) -> VtkOutput:
    """Convert parsed command-line options to a VtkOutput object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.
        prefix: Optional prefix used when parsing arguments.

    Returns:
        VtkOutput: Configured VTK output object.
    """
    outputKey = __buildArg( prefix, __OUTPUT_FILE ).replace( "-", "_" )
    binaryModeKey = __buildArg( prefix, __OUTPUT_BINARY_MODE ).replace( "-", "_" )
    canOverwriteKey = __buildArg( prefix, __CAN_OVERWRITE )
    output = parsedOptions[ outputKey ]
    isDataModeBinary: bool = parsedOptions[ binaryModeKey ] == __OUTPUT_BINARY_MODE_DEFAULT
    canOverwrite: bool = parsedOptions.get( canOverwriteKey, False )
    return VtkOutput( output=output, isDataModeBinary=isDataModeBinary, canOverwrite=canOverwrite )
