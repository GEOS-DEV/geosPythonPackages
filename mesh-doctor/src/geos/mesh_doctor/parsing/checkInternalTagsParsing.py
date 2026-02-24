# SPDX-License-Identifier: Apache-2.0
"""Command line parsing for internal tags check."""

from __future__ import annotations
import argparse
from typing import Any, Optional

from geos.mesh_doctor.actions.checkInternalTags import Options, Result
from geos.mesh_doctor.parsing import CHECK_INTERNAL_TAGS
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh.io.vtkIO import VtkOutput

__TAG_VALUES = "tagValues"
__TAG_ARRAY = "tagArray"
__OUTPUT_CSV = "outputCsv"
__NULL_TAG_VALUE = "nullTagValue"
__FIXED_OUTPUT = "fixedOutput"
__DATA_MODE = "dataMode"
__VERBOSE = "verbose"

__TAG_ARRAY_DEFAULT = "tags"
__DATA_MODE_VALUES = "binary", "ascii"
__DATA_MODE_DEFAULT = __DATA_MODE_VALUES[ 0 ]


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for internal tags check.
    """
    # Get dataMode setting
    dataMode: str = parsedOptions.get( __DATA_MODE, __DATA_MODE_DEFAULT )
    isDataModeBinary: bool = dataMode == __DATA_MODE_DEFAULT

    # Create VtkOutput for fixed mesh if specified
    fixedOutput: Optional[ str ] = parsedOptions.get( __FIXED_OUTPUT )
    fixedVtkOutput = None
    if fixedOutput:
        fixedVtkOutput = VtkOutput( output=fixedOutput, isDataModeBinary=isDataModeBinary )

    return Options( tagValues=tuple( parsedOptions[ __TAG_VALUES ] ),
                    tagArrayName=parsedOptions.get( __TAG_ARRAY, __TAG_ARRAY_DEFAULT ),
                    outputCsv=parsedOptions.get( __OUTPUT_CSV ),
                    nullTagValue=parsedOptions.get( __NULL_TAG_VALUE ),
                    fixedVtkOutput=fixedVtkOutput,
                    verbose=parsedOptions.get( __VERBOSE, False ) )


def fillSubparser( subparsers: argparse._SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the checkInternalTags action.

    Args:
        subparsers: Subparsers from the main argument parser
    """
    p = subparsers.add_parser( CHECK_INTERNAL_TAGS,
                               help="Check that tagged 2D elements are internal (have exactly 2 volume neighbors).",
                               description="""\
Validates that 2D elements with specified tag values have exactly 2 volume neighbors.
Elements with 0, 1, or 3+ neighbors are reported as problematic, as they indicate elements
on the mesh boundary or other geometric issues.

This check helps ensure that tagged internal surfaces (e.g., fractures) are properly embedded
in the volume mesh and not inadvertently placed on external boundaries.
""" )

    addVtuInputFileArgument( p )

    p.add_argument( '--' + __TAG_VALUES,
                    nargs='+',
                    type=float,
                    required=True,
                    metavar='VALUE',
                    help="[floats]: Tag values to check (space-separated list, e.g., --tagValues 8 9 10)" )

    p.add_argument( '--' + __TAG_ARRAY,
                    type=str,
                    default=__TAG_ARRAY_DEFAULT,
                    metavar='NAME',
                    help=f"[string]: Name of the cell data array containing tags. Defaults to '{__TAG_ARRAY_DEFAULT}'" )

    p.add_argument( '--' + __OUTPUT_CSV,
                    type=str,
                    default=None,
                    metavar='FILE',
                    help="[string]: Output CSV file for problematic elements (optional)" )

    p.add_argument( '--' + __NULL_TAG_VALUE,
                    type=float,
                    default=None,
                    metavar='VALUE',
                    help="[float]: Tag value to assign to faulty cells (e.g., 9999). Required to use --fixedOutput." )

    p.add_argument( '--' + __FIXED_OUTPUT,
                    type=str,
                    default=None,
                    metavar='FILE',
                    help="[string]: Output VTU file with faulty cells retagged to nullTagValue (optional)" )

    p.add_argument(
        '--' + __DATA_MODE,
        type=str,
        metavar=", ".join( __DATA_MODE_VALUES ),
        default=__DATA_MODE_DEFAULT,
        help='[string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.' )

    p.add_argument( '--' + __VERBOSE,
                    '-v',
                    action='store_true',
                    help="[flag]: Enable detailed connectivity diagnostics for problematic cells" )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the internal tags check.

    Args:
        options: The options used for the check.
        result: The result of the check.
    """
    setupLogger.results( "=" * 80 )
    setupLogger.results( "INTERNAL TAGS CHECK RESULTS" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( result.info )
    setupLogger.results( "=" * 80 )

    if "FAILED" in result.info:
        setupLogger.results( "Validation FAILED: Some tagged elements are not internal" )
        if options.outputCsv:
            setupLogger.results( f"See {options.outputCsv} for details on problematic elements" )
        if options.fixedVtkOutput and options.nullTagValue is not None:
            setupLogger.results(
                f"Fixed mesh written to {options.fixedVtkOutput.output} (faulty cells retagged to {options.nullTagValue})"
            )
    else:
        setupLogger.results( "Validation PASSED: All tagged elements are internal" )
