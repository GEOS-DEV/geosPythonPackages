# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for Euler characteristic computation."""

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
    """Fill the argument parser for the Euler characteristic action.

    Args:
        subparsers: Subparsers from the main argument parser
    """
    p = subparsers.add_parser( EULER,
                               help="Compute Euler characteristic (X = V - E + F) for mesh topology analysis.",
                               description="""\
Computes the Euler characteristic for a mesh by:
  1. Filtering to 3D volumetric elements only (ignores 2D boundary cells)
  2. Extracting the surface from these 3D elements
  3. Counting vertices (V), edges (E), and faces (F)
  4. Computing X = V - E + F

Expected Euler values:
  X = 2   Closed surface (sphere-like, e.g., cube, tetrahedron)
  X = 0   Torus or cylinder topology
  X = 1   Disk or open surface
  Other   Complex topology with genus g = (2 - X)/2

This tool helps verify that meshes form proper closed volumes for simulation.
""" )

    addVtuInputFileArgument( p )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the Euler characteristic computation.

    Args:
        options: The options used for the computation.
        result: The result of the computation.
    """
    setupLogger.results( "=" * 80 )
    setupLogger.results( "EULER CHARACTERISTIC RESULTS" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( f"Mesh Topology (from {result.num3dCells:,} 3D elements):" )
    setupLogger.results( f"  Surface Vertices (V): {result.numVertices:,}" )
    setupLogger.results( f"  Surface Edges    (E): {result.numEdges:,}" )
    setupLogger.results( f"  Surface Faces    (F): {result.numFaces:,}" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Euler Characteristic (X = V - E + F): {result.eulerCharacteristic}" )
    setupLogger.results( f"  Connected Components: {result.numConnectedComponents}" )
    setupLogger.results( "=" * 80 )

    # Interpret topology with validation
    if result.numConnectedComponents == 1:
        # Single component - standard interpretation
        if result.eulerCharacteristic == 2:
            setupLogger.results( "VALIDATION PASSED: Single closed surface (sphere-like)" )
            setupLogger.results( "  Status: MESH IS VALID FOR SIMULATION" )
        elif result.eulerCharacteristic == 0:
            setupLogger.results( "WARNING: Torus-like topology (genus 1)" )
            setupLogger.results( "  Expected X = 2 for standard simulation mesh" )
        elif result.eulerCharacteristic == 1:
            setupLogger.results( "WARNING: Open surface (not closed)" )
            setupLogger.results( "  Mesh has boundary - expected X = 2" )
        elif result.eulerCharacteristic < 0:
            genus = ( 2 - result.eulerCharacteristic ) // 2
            setupLogger.results( f"WARNING: Complex topology with handles (genus g = {genus})" )
            setupLogger.results( f"  Surface has {genus} hole(s)/handle(s)" )
            setupLogger.results( "  Expected X = 2 for standard simulation mesh" )
        else:
            setupLogger.results( f"WARNING: Unexpected topology (X = {result.eulerCharacteristic})" )
    else:
        # Multiple components - indicates disconnected regions or internal cavities
        expectedEuler = 2 * result.numConnectedComponents
        numCavities = result.numConnectedComponents - 1

        setupLogger.results( f"VALIDATION FAILED: {result.numConnectedComponents} DISCONNECTED COMPONENTS DETECTED!" )
        setupLogger.results( f"  Euler characteristic: {result.eulerCharacteristic}" )
        setupLogger.results( f"  Expected (if all spherical): X = {expectedEuler}" )
        setupLogger.results( f"  Likely internal void(s)/cavity(ies): {numCavities}" )
        setupLogger.results( "" )

        if result.eulerCharacteristic == expectedEuler:
            setupLogger.results( "  All components are sphere-like (X=2 each)" )
            setupLogger.results( "  Issue: Mesh has internal hollow regions (outer + inner surfaces)" )
        elif result.eulerCharacteristic < expectedEuler:
            avgGenus = ( expectedEuler - result.eulerCharacteristic ) / 2
            setupLogger.results( f"  Some components have handles/holes (avg genus ~{avgGenus:.1f})" )
        else:
            setupLogger.results( "  Unusual topology - verify mesh integrity" )

        setupLogger.results( "" )
        setupLogger.results( "  NOT SUITABLE FOR SIMULATION without fixing!" )
        setupLogger.results( "  Expected: Single closed volume (X = 2, components = 1)" )

    # Show input cell breakdown if there were 2D cells filtered out
    if result.num2dCells > 0:
        setupLogger.results( "" )
        setupLogger.results( "Input cell breakdown:" )
        setupLogger.results( f"  3D volumetric cells: {result.num3dCells:,} (used for surface extraction)" )
        setupLogger.results( f"  2D surface cells:    {result.num2dCells:,} (filtered out)" )
        if result.numOtherCells > 0:
            setupLogger.results( f"  Other cells:         {result.numOtherCells:,} (filtered out)" )

    # Quality check results
    setupLogger.results( "" )
    setupLogger.results( "Mesh Quality Check:" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Boundary edges:     {result.numBoundaryEdges:,}" )
    setupLogger.results( f"  Non-manifold edges: {result.numNonManifoldEdges:,}" )

    if result.numBoundaryEdges == 0 and result.numNonManifoldEdges == 0:
        if result.eulerCharacteristic == 2 and result.numConnectedComponents == 1:
            setupLogger.results( "  Status: PERFECT - Ready for simulation!" )
        else:
            setupLogger.results( "  Status: Manifold but topology issues (X != 2 or internal cavities)" )
    else:
        if result.numBoundaryEdges > 0:
            setupLogger.results( "  Status: Open surface detected (has boundaries)" )
        if result.numNonManifoldEdges > 0:
            setupLogger.results( "  Status: Non-manifold edges detected!" )

    setupLogger.results( "=" * 80 )
