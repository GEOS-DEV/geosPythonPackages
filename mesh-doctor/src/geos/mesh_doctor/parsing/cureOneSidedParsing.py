# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for the cureOneSided action."""

from __future__ import annotations

import argparse
from typing import Any

from geos.mesh_doctor.actions.cureOneSided import Options, Result
from geos.mesh_doctor.parsing import CURE_ONE_SIDED, vtkOutputParsing
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__TAG_ARRAY = "tagArray"
__TAG_VALUES = "tagValues"
__TOLERANCE = "tolerance"
__TOLERANCE_DEFAULT = 1.e-6


def parseTagValues( spec: str ) -> tuple[ int, ...]:
    """Parse a fault value specification into a sorted tuple of integers.

    Args:
        spec: A comma-separated list of values and inclusive ranges, e.g. "1-7", "18,19,20" or
            "1,4-6". An empty string yields an empty tuple.

    Returns:
        The sorted, deduplicated values.

    Raises:
        ValueError: If a range is malformed or a value is not an integer.
    """
    values: set[ int ] = set()
    for part in spec.split( "," ):
        part = part.strip()
        if not part:
            continue
        separator = part.find( "-", 1 )  # A leading minus is a negative value, not a range separator.
        if separator < 0:
            values.add( int( part ) )
        else:
            low, high = int( part[ :separator ] ), int( part[ separator + 1: ] )
            if high < low:
                raise ValueError( f"Invalid range \"{part}\": the upper bound is below the lower bound." )
            values.update( range( low, high + 1 ) )
    return tuple( sorted( values ) )


def fillSubparser( subparsers: argparse._SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the cureOneSided action.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser(
        CURE_ONE_SIDED,
        help="Rewrite the fault faces of a split mesh onto one consistent side per fault.",
        description="""\
Cure the one-sided fault issue on a split (post-generateFractures) mesh.

Node splitting duplicates the fault nodes, but writes one surface polygon per fault
location remapped onto whichever 3D neighbour was enumerated first. The fault surface
is then a patchwork: adjacent faces sit on different collocated node copies, the seal
node set GEOS derives from it holds mixed sides, and fluid crosses the fault even
though most faces look sealed.

This action rewrites every tagged fault face onto the coincident real 3D-cell face of
ONE consistent side per fault value, so that:
  - all the open matrix/fracture taps land on the same side (cross-fault flow blocked,
    and the fracture stays anchored to one matrix side so the flow solve converges);
  - every fault face stays a real 3D-cell face (orphan2d still passes);
  - fault junctions (nodes with 3-4 collocated copies) are resolved geometrically.

Collocated nodes are detected by coordinate coincidence, so no separate fault or
faceBlock file is needed. Global id arrays are preserved. Two cell arrays are added
for display and QC:
  faultSide  +1 reference side, -1 residual degeneracy (e.g. a fault-fault
             intersection line, where no single side exists), 0 on non-fault cells.
  onHole     1 on faces bordering a residual hole (a boundary loop other than the
             fault perimeter), 0 elsewhere. A fully cured fault has onHole all 0.

Examples:
  mesh-doctor cureOneSided -i domain.vtu --output cured.vtu --tagArray FaultMask --tagValues 1-7
  mesh-doctor cureOneSided -i domain.vtu --output cured.vtu --tagArray attribute --tagValues 18-24
  mesh-doctor cureOneSided -i domain.vtu --output cured.vtu --tagArray region

Verify the output with:
  mesh-doctor orphan2d -i cured.vtu
  mesh-doctor euler -i cured.vtu --mode surface --tagArray FaultMask
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    addVtuInputFileArgument( p )
    vtkOutputParsing.fillVtkOutputSubparser( p )
    p.add_argument( "--" + __TAG_ARRAY,
                    type=str,
                    required=True,
                    metavar="NAME",
                    help="[string]: Cell-data array tagging the fault faces, e.g. FaultMask." )
    p.add_argument( "--" + __TAG_VALUES,
                    type=str,
                    default="",
                    metavar="SPEC",
                    help="[string]: Fault values to cure, as values and inclusive ranges, e.g. "
                    "\"1-7\", \"18,19,20\" or \"1,4-6\". Defaults to every distinct non-zero value "
                    "of --tagArray carried by a 2D cell." )
    p.add_argument( "--" + __TOLERANCE,
                    type=float,
                    default=__TOLERANCE_DEFAULT,
                    metavar="D",
                    help=f"[float]: Distance below which two nodes are considered collocated, i.e. two "
                    f"copies of a single split node. Default: {__TOLERANCE_DEFAULT}." )


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to an Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options for the cureOneSided action.

    Raises:
        ValueError: If the tolerance is negative.
    """
    tolerance: float = parsedOptions.get( __TOLERANCE, __TOLERANCE_DEFAULT )
    if tolerance < 0.:
        raise ValueError( f"--{__TOLERANCE} must be >= 0, got {tolerance}." )
    return Options(
        outputFile=vtkOutputParsing.convert( parsedOptions ),
        tagArray=parsedOptions[ __TAG_ARRAY ],
        tagValues=parseTagValues( parsedOptions.get( __TAG_VALUES, "" ) ),
        tolerance=tolerance,
    )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the cure.

    Args:
        options: The options used for the cure.
        result: The result of the cureOneSided action.
    """
    setupLogger.results( "=" * 80 )
    setupLogger.results( "CURE ONE-SIDED FAULTS" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( f"Tag array          : {options.tagArray}" )
    setupLogger.results( f"Collocation tol.   : {options.tolerance}" )
    setupLogger.results( f"{'value':>8} {'faces':>10} {'moved':>10} {'kept':>10} {'degenerate':>12} "
                         f"{'skipped':>10} {'onHole':>10}" )
    for fault in result.faults:
        setupLogger.results( f"{fault.tagValue:>8} {fault.numFaces:>10,} {fault.numMovedFaces:>10,} "
                             f"{fault.numAlreadyCorrectFaces:>10,} {fault.numDegenerateFaces:>12,} "
                             f"{fault.numSkippedFaces:>10,} {fault.numHoleBorderFaces:>10,}" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"Fault faces        : {result.numFaultFaces:,}" )
    setupLogger.results( f"Moved to reference : {result.numMovedFaces:,}" )
    setupLogger.results( f"Degenerate (kept)  : {result.numDegenerateFaces:,}" )
    setupLogger.results( f"Skipped (no owner) : {result.numSkippedFaces:,}" )
    setupLogger.results( f"Hole-border faces  : {result.numHoleBorderFaces:,}" )
    if result.numDegenerateFaces == 0 and result.numHoleBorderFaces == 0:
        setupLogger.results( "STATUS: CURED (every fault is single-sided, no residual hole)" )
    else:
        setupLogger.results( "STATUS: RESIDUAL DEGENERACY - inspect the faultSide and onHole arrays. "
                             "A fault-fault intersection line leaves a harmless slit, not a leak." )
    if result.numSkippedFaces > 0:
        setupLogger.results( f"WARNING: {result.numSkippedFaces:,} face(s) have no 3D owner cell. "
                             "Run orphan2d on the input mesh." )
    setupLogger.results( f"Output written to  : {options.outputFile.output}" )
    setupLogger.results( "=" * 80 )
