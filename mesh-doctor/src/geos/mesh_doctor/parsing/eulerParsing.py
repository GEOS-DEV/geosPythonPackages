# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for solid Euler characteristic computation."""

from __future__ import annotations
import argparse
from typing import Any

from geos.mesh_doctor.actions.euler import Options, Result
from geos.mesh_doctor.parsing import EULER
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for Euler computation.
    """
    return Options()


def fillSubparser( subparsers: argparse._SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the solid Euler characteristic action.

    Args:
        subparsers: Subparsers from the main argument parser
    """
    p = subparsers.add_parser(
        EULER,
        help="Compute solid Euler characteristic (chi = V - E + F - C) for 3D mesh topology validation.",
        description="""\
Computes the solid Euler characteristic for a 3D mesh by:
  1. Filtering to 3D volumetric elements only (ignores 2D boundary cells)
  2. Counting vertices (V), edges (E), faces (F), and cells (C) in the 3D mesh
  3. Computing chi = V - E + F - C

Solid Euler characteristic values:
  chi = 1   Simple solid region (contractible, ball-like) - standard
  chi = 0   Solid torus (has through-hole)
  chi = 2   Complex internal topology (may indicate internal features)
  chi > 2   Multiple components or complex structure

Primary validation criteria (what matters for simulation):
  - 3D connectivity = 1 region (cells properly connected via shared faces)
  - Boundary edges = 0 (closed manifold surface)
  - Non-manifold edges = 0 (no overlapping cells)

The Euler characteristic provides topological information but is secondary.
3D connectivity and manifold properties are the definitive validation checks.
""" )

    addVtuInputFileArgument( p )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the solid Euler characteristic computation.

    Args:
        options: The options used for the computation.
        result: The result of the computation.
    """
    setupLogger.results( "=" * 80 )
    setupLogger.results( "SOLID EULER CHARACTERISTIC RESULTS" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( f"3D Mesh Topology (from {result.num3dCells:,} 3D elements):" )
    setupLogger.results( f"  Vertices (V): {result.numVertices:,}" )
    setupLogger.results( f"  Edges    (E): {result.numEdges:,}" )
    setupLogger.results( f"  Faces    (F): {result.numFaces:,}" )
    setupLogger.results( f"  Cells    (C): {result.numCells:,}" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Euler Characteristic (chi = V - E + F - C): {result.solidEulerCharacteristic}" )
    setupLogger.results( f"  3D Connected Components: {result.numConnectedComponents}" )
    setupLogger.results( "=" * 80 )

    # PRIMARY VALIDATION: 3D connectivity
    setupLogger.results( "" )
    setupLogger.results( "3D CONNECTIVITY CHECK:" )
    setupLogger.results( "-" * 80 )

    if result.numConnectedComponents == 1:
        setupLogger.results( "PASS: Single connected 3D region" )
        setupLogger.results( "  All 3D cells form one continuous volume via shared faces" )
    else:
        setupLogger.results( f"FAIL: {result.numConnectedComponents} disconnected 3D regions!" )
        setupLogger.results( "  Mesh has separate volumes not connected by shared faces" )
        setupLogger.results( "  NOT suitable for simulation - requires fixing" )

    # TOPOLOGY INTERPRETATION
    setupLogger.results( "" )
    setupLogger.results( "TOPOLOGY INTERPRETATION:" )
    setupLogger.results( "-" * 80 )

    if result.numConnectedComponents == 1:
        # Single connected region - interpret Euler
        if result.solidEulerCharacteristic == 1:
            setupLogger.results( "chi = 1: Simple solid ball (contractible)" )
            setupLogger.results( "  Standard topology for simulation meshes" )

        elif result.solidEulerCharacteristic == 0:
            setupLogger.results( "chi = 0: Solid torus topology" )
            setupLogger.results( "  Domain has through-hole or tunnel" )
            setupLogger.results( "  Verify this matches your expected geometry" )

        elif result.solidEulerCharacteristic == 2:
            setupLogger.results( "chi = 2: Hollow shell or internal cavity" )
            setupLogger.results( "  Expected chi = 1 for simple solid ball" )
            setupLogger.results( "  Suggests internal void or nested structure" )
            setupLogger.results( "  3D cells ARE connected (verified above)" )
            setupLogger.results( "  ACCEPTABLE if internal structure is intentional" )

        else:
            setupLogger.results( f"chi = {result.solidEulerCharacteristic}: Unusual value" )
            if result.solidEulerCharacteristic > 2:
                setupLogger.results( "  May indicate complex internal structure" )
            setupLogger.results( "  Verify mesh structure and topology are correct" )
    else:
        # Multiple disconnected regions
        expectedEuler = result.numConnectedComponents  # Each component contributes
        setupLogger.results( "Multiple regions: topology analysis not meaningful" )
        setupLogger.results(
            f"Expected chi approx {expectedEuler} for {result.numConnectedComponents} disconnected balls" )
        setupLogger.results( f"Actual chi = {result.solidEulerCharacteristic}" )

    # MESH QUALITY
    setupLogger.results( "" )
    setupLogger.results( "MESH QUALITY:" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Boundary edges:     {result.numBoundaryEdges:,}" )
    setupLogger.results( f"  Non-manifold edges: {result.numNonManifoldEdges:,}" )

    if result.numBoundaryEdges == 0:
        setupLogger.results( "  Closed manifold (no open boundaries)" )
    else:
        setupLogger.results( "  Open boundaries detected" )

    if result.numNonManifoldEdges == 0:
        setupLogger.results( "  Manifold geometry (no overlapping cells)" )
    else:
        setupLogger.results( "  Non-manifold edges (overlapping/duplicate cells)" )

    # FINAL VALIDATION
    setupLogger.results( "" )
    setupLogger.results( "FINAL VALIDATION:" )
    setupLogger.results( "=" * 80 )

    # Check all three critical criteria
    has_single_component = result.numConnectedComponents == 1
    is_closed = result.numBoundaryEdges == 0
    is_manifold = result.numNonManifoldEdges == 0

    if has_single_component and is_closed and is_manifold:
        # All critical checks pass
        if result.solidEulerCharacteristic == 1:
            setupLogger.results( "STATUS: PERFECT" )
            setupLogger.results( "  Single connected region: YES" )
            setupLogger.results( "  Closed manifold: YES" )
            setupLogger.results( "  Simple topology (chi = 1): YES" )
            setupLogger.results( "  READY for simulation" )
        else:
            setupLogger.results( "STATUS: VALID (with complex topology)" )
            setupLogger.results( "  Single connected region: YES" )
            setupLogger.results( "  Closed manifold: YES" )
            setupLogger.results( f"  Complex topology (chi = {result.solidEulerCharacteristic}): WARNING" )
            setupLogger.results( "  ACCEPTABLE for simulation" )
            setupLogger.results( "  Verify internal structure is intentional" )
    else:
        # Failed critical checks
        setupLogger.results( "STATUS: INVALID" )
        setupLogger.results( "  Mesh has critical issues:" )

        if not has_single_component:
            setupLogger.results( f"    Multiple disconnected regions ({result.numConnectedComponents}): FAIL" )
        else:
            setupLogger.results( "    Single connected region: PASS" )

        if not is_closed:
            setupLogger.results( f"    Open boundaries ({result.numBoundaryEdges:,} boundary edges): FAIL" )
        else:
            setupLogger.results( "    Closed manifold: PASS" )

        if not is_manifold:
            setupLogger.results( f"    Non-manifold geometry ({result.numNonManifoldEdges:,} edges): FAIL" )
        else:
            setupLogger.results( "    Manifold geometry: PASS" )

        setupLogger.results( "" )
        setupLogger.results( "  NOT SUITABLE for simulation without fixing" )

    # Show input cell breakdown
    if result.num2dCells > 0 or result.numOtherCells > 0:
        setupLogger.results( "" )
        setupLogger.results( "Input cell breakdown:" )
        setupLogger.results( f"  3D volumetric cells: {result.num3dCells:,} (used for analysis)" )
        if result.num2dCells > 0:
            setupLogger.results( f"  2D surface cells:    {result.num2dCells:,} (filtered out)" )
        if result.numOtherCells > 0:
            setupLogger.results( f"  Other cells:         {result.numOtherCells:,} (filtered out)" )

    setupLogger.results( "=" * 80 )
