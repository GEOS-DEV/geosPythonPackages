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
__VERBOSE = "verbose"
__BOUNDARY_DISTANCE = "boundaryDistance"
__BOUNDARY_MODE = "boundaryMode"

__TAG_ARRAY_DEFAULT = "tags"
__BOUNDARY_MODE_DEFAULT = "all"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for internal tags check.
    """
    # Create VtkOutput for fixed mesh if specified (always binary mode)
    fixedOutput: Optional[ str ] = parsedOptions.get( __FIXED_OUTPUT )
    fixedVtkOutput = None
    if fixedOutput:
        fixedVtkOutput = VtkOutput( output=fixedOutput, isDataModeBinary=True )

    return Options( tagValues=tuple( parsedOptions[ __TAG_VALUES ] ),
                    tagArrayName=parsedOptions.get( __TAG_ARRAY, __TAG_ARRAY_DEFAULT ),
                    outputCsv=parsedOptions.get( __OUTPUT_CSV ),
                    nullTagValue=parsedOptions.get( __NULL_TAG_VALUE ),
                    fixedVtkOutput=fixedVtkOutput,
                    verbose=parsedOptions.get( __VERBOSE, False ),
                    boundaryDistance=parsedOptions.get( __BOUNDARY_DISTANCE ),
                    boundaryMode=parsedOptions.get( __BOUNDARY_MODE, __BOUNDARY_MODE_DEFAULT ) )


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

Optionally, elements within a specified distance from the mesh boundary can be automatically
untagged to handle edge effects. The distance is measured to the outer surface of the 3D
volume mesh. Use --boundaryMode to control which boundaries are considered.
""" )

    addVtuInputFileArgument( p )

    p.add_argument( '--' + __TAG_VALUES,
                    nargs='+',
                    type=int,
                    required=True,
                    metavar='VALUE',
                    help="[ints]: Tag values to check (space-separated list, e.g., --tagValues 8 9 10)" )

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
                    type=int,
                    default=None,
                    metavar='VALUE',
                    help="[int]: Tag value to assign to faulty cells (e.g., 9999). Required to use --fixedOutput." )

    p.add_argument( '--' + __FIXED_OUTPUT,
                    type=str,
                    default=None,
                    metavar='FILE',
                    help="[string]: Output VTU file with faulty cells retagged to nullTagValue (optional)" )

    p.add_argument( '--' + __BOUNDARY_DISTANCE,
                    type=float,
                    default=None,
                    metavar='DISTANCE',
                    help="[float]: Safety distance from mesh boundary. Tagged cells within this distance will be "
                    "untagged (set to nullTagValue). Distance is measured to the outer surface of the 3D "
                    "volume mesh. Use with --boundaryMode to specify which boundaries (optional)" )

    p.add_argument( '--' + __BOUNDARY_MODE,
                    type=str,
                    default=__BOUNDARY_MODE_DEFAULT,
                    choices=[ 'all', 'bottom', 'top' ],
                    metavar='MODE',
                    help=f"[string]: Which boundaries to consider: 'all' (default), 'bottom', 'top'. "
                    f"Only used with --boundaryDistance. Defaults to '{__BOUNDARY_MODE_DEFAULT}'" )

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
        if options.boundaryDistance is not None:
            setupLogger.results(
                f"Cells within {options.boundaryDistance} of boundary ({options.boundaryMode}) were also untagged" )
    else:
        setupLogger.results( "Validation PASSED: All tagged elements are internal" )
        if options.boundaryDistance is not None:
            setupLogger.results(
                f"No cells found within {options.boundaryDistance} of mesh boundary ({options.boundaryMode})" )
