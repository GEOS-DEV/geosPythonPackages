# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for Euler characteristic computation."""

from __future__ import annotations
import argparse
from typing import Any, Optional

from geos.mesh_doctor.actions.euler import Options, Result, action
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
    p = subparsers.add_parser(
        EULER,
        help="Compute Euler characteristic (χ = V - E + F) for mesh topology analysis.",
        description="""\
Computes the Euler characteristic for a mesh by:
  1. Filtering to 3D volumetric elements only (ignores 2D boundary cells)
  2. Extracting the surface from these 3D elements
  3. Counting vertices (V), edges (E), and faces (F)
  4. Computing χ = V - E + F

Expected Euler values:
  χ = 2  → Closed surface (sphere-like, e.g., cube, tetrahedron)
  χ = 0  → Torus or cylinder topology
  χ = 1  → Disk or open surface
  Other  → Complex topology with genus g = (2 - χ)/2

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
    setupLogger.results( f"Mesh Topology (from {result.num3dCells} 3D elements):" )
    setupLogger.results( f"  Surface Vertices (V): {result.numVertices:,}" )
    setupLogger.results( f"  Surface Edges    (E): {result.numEdges:,}" )
    setupLogger.results( f"  Surface Faces    (F): {result.numFaces:,}" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Euler Characteristic (χ = V - E + F): {result.eulerCharacteristic}" )
    setupLogger.results( "=" * 80 )

    # Interpret topology
    if result.eulerCharacteristic == 2:
        setupLogger.results( "Topology: Closed surface (sphere-like)" )
    elif result.eulerCharacteristic == 0:
        setupLogger.results( "Topology: Torus-like or open cylinder" )
    elif result.eulerCharacteristic == 1:
        setupLogger.results( "Topology: Disk-like (open surface)" )
    else:
        genus = ( 2 - result.eulerCharacteristic ) / 2
        setupLogger.results( f"Topology: Complex (genus g ≈ {genus:.1f})" )

    # Show input cell breakdown if there were 2D cells filtered out
    if result.num2dCells > 0:
        setupLogger.results( "" )
        setupLogger.results( f"Input cell breakdown:" )
        setupLogger.results( f"  3D volumetric cells: {result.num3dCells} (used for surface extraction)" )
        setupLogger.results( f"  2D surface cells:    {result.num2dCells} (filtered out)" )
        if result.numOtherCells > 0:
            setupLogger.results( f"  Other cells:         {result.numOtherCells} (filtered out)" )

    # Quality check results (always performed)
    setupLogger.results( "" )
    setupLogger.results( "Mesh Quality Check:" )
    setupLogger.results( "-" * 80 )
    setupLogger.results( f"  Boundary edges:     {result.numBoundaryEdges:,}" )
    setupLogger.results( f"  Non-manifold edges: {result.numNonManifoldEdges:,}" )

    if result.numBoundaryEdges == 0 and result.numNonManifoldEdges == 0:
        setupLogger.results( "  Status: Perfect closed manifold mesh!" )
    else:
        if result.numBoundaryEdges > 0:
            setupLogger.results( "  Status: Open surface detected (has boundaries)" )
        if result.numNonManifoldEdges > 0:
            setupLogger.results( "  Status: Non-manifold edges detected (mesh has issues!)" )

    setupLogger.results( "=" * 80 )
