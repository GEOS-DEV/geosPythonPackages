# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for the refineMesh action."""

from __future__ import annotations

import argparse
from typing import Any

from geos.mesh_doctor.actions.refineMesh import Options, Result
from geos.mesh_doctor.parsing import REFINE_MESH
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh_doctor.parsing import vtkOutputParsing

__ITERATIONS = "iterations"
__ITERATIONS_DEFAULT = 1


def fillSubparser( subparsers: argparse._SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the refineMesh action.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser(
        REFINE_MESH,
        help="Refine a mesh by splitting each cell using edge midpoints.",
        description="""\
Refine a VTU mesh by repeatedly splitting each cell into smaller cells of the same type.

Splitting rules (one iteration):
  hexahedron  -> 8 hexahedra
  tetrahedron -> 8 tetrahedra
  pyramid     -> 6 pyramids + 4 tetrahedra
  triangle    -> 4 triangles
  quad        -> 4 quads

Cell data arrays are propagated to child cells. The OriginalID array
records which input cell each output cell was split from.

Examples:
  mesh-doctor refineMesh -i mesh.vtu --output refined.vtu
  mesh-doctor refineMesh -i mesh.vtu --output refined.vtu --iterations 2
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    addVtuInputFileArgument( p )
    vtkOutputParsing.fillVtkOutputSubparser( p )
    p.add_argument(
        "--" + __ITERATIONS,
        type=int,
        default=__ITERATIONS_DEFAULT,
        metavar="N",
        help=f"[int]: Number of refinement iterations. Each iteration multiplies the cell count "
        f"by 4 (2D) or 8 (3D). Default: {__ITERATIONS_DEFAULT}.",
    )


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to an Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options for the refineMesh action.
    """
    iterations: int = parsedOptions.get( __ITERATIONS, __ITERATIONS_DEFAULT )
    if iterations < 1:
        raise ValueError( f"--{__ITERATIONS} must be >= 1, got {iterations}." )
    return Options(
        outputFile=vtkOutputParsing.convert( parsedOptions ),
        iterations=iterations,
    )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of mesh refinement.

    Args:
        options: The options used for refinement.
        result: The result of the refinement action.
    """
    setupLogger.results( "=" * 60 )
    setupLogger.results( "REFINE MESH" )
    setupLogger.results( "=" * 60 )
    setupLogger.results( f"Iterations applied : {result.iterations}" )
    setupLogger.results( f"Input  points      : {result.inputNumPoints:,}" )
    setupLogger.results( f"Input  cells       : {result.inputNumCells:,}" )
    setupLogger.results( f"Output points      : {result.outputNumPoints:,}" )
    setupLogger.results( f"Output cells       : {result.outputNumCells:,}" )
    cellFactor = result.outputNumCells / result.inputNumCells if result.inputNumCells else 0
    setupLogger.results( f"Cell count factor  : {cellFactor:.1f}x" )
    setupLogger.results( f"Output written to  : {options.outputFile.output}" )
    setupLogger.results( "=" * 60 )
