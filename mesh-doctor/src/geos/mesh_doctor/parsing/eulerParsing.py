# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
"""Command line parsing for the Euler characteristic action."""

from __future__ import annotations
import argparse
from typing import Any

from geos.mesh_doctor.actions.euler import Options, Result, SurfaceGroup
from geos.mesh_doctor.parsing import EULER
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument

__MODE = "mode"
__TAG_ARRAY = "tagArray"
__TAG_VALUE = "tagValue"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object."""
    return Options(
        mode=parsedOptions.get( __MODE, "solid" ),
        tagArray=parsedOptions.get( __TAG_ARRAY ),
        tagValue=parsedOptions.get( __TAG_VALUE ),
    )


def fillSubparser( subparsers: argparse._SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the Euler characteristic action."""
    p = subparsers.add_parser( EULER,
                               help="Compute Euler characteristic for 3D solids and/or 2D surfaces.",
                               description="""\
Compute the Euler characteristic of a mesh.

Modes:
  solid    : 3D cells only, chi = V - E + F - C (volumetric topology).
  surface  : 2D cells only, chi = V - E + F (always per connected component).
  all      : both, in one report. Missing dimension is silently skipped.

Surface analysis is always reported per connected component, because a
single global chi over multiple components hides defects (e.g. one stray
triangle plus one clean disk both pass a global "chi == 2" check).

Tag-based grouping (surface analysis only):
  --tagArray NAME              screen each distinct non-zero value of NAME
                                separately. Useful for FaultMask, HorizonMask,
                                or any per-cell label.
  --tagArray NAME --tagValue V  restrict to a single value.

Examples:
  mesh-doctor euler -i mesh.vtu --mode solid
  mesh-doctor euler -i mesh.vtu --mode surface
  mesh-doctor euler -i mesh.vtu --mode all  --tagArray FaultMask
  mesh-doctor euler -i mesh.vtu --mode surface --tagArray FaultMask --tagValue 12
""" )

    addVtuInputFileArgument( p )
    p.add_argument( "--" + __MODE,
                    type=str,
                    choices=( "solid", "surface", "all" ),
                    default="solid",
                    help="What to analyze. Default: solid (back-compat)." )
    p.add_argument( "--" + __TAG_ARRAY,
                    type=str,
                    default=None,
                    metavar="NAME",
                    help="(surface) Cell-data array used to group surface "
                    "cells; e.g. FaultMask. If set without --tagValue, "
                    "every distinct non-zero value is screened." )
    p.add_argument( "--" + __TAG_VALUE,
                    type=float,
                    default=None,
                    metavar="V",
                    help="(surface) Restrict surface analysis to cells where "
                    "--tagArray equals this value." )


# --- Display helpers ---------------------------------------------------------


def __displaySolid( result: Result ) -> None:
    setupLogger.results( "=" * 80 )
    setupLogger.results( "SOLID EULER CHARACTERISTIC" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( f"3D mesh topology (from {result.num3dCells:,} 3D cells):" )
    setupLogger.results( f"  V = {result.numVertices:,}" )
    setupLogger.results( f"  E = {result.numEdges:,}" )
    setupLogger.results( f"  F = {result.numFaces:,}" )
    setupLogger.results( f"  C = {result.numCells:,}" )
    setupLogger.results( f"  chi (V - E + F - C) = {result.solidEulerCharacteristic}" )
    setupLogger.results( f"  3D connected components: {result.numConnectedComponents}" )
    setupLogger.results( f"  Boundary edges        : {result.numBoundaryEdges:,}" )
    setupLogger.results( f"  Non-manifold edges    : {result.numNonManifoldEdges:,}" )

    has_single = result.numConnectedComponents == 1
    is_closed = result.numBoundaryEdges == 0
    is_manifold = result.numNonManifoldEdges == 0
    if has_single and is_closed and is_manifold:
        if result.solidEulerCharacteristic == 1:
            setupLogger.results( "  STATUS: PERFECT (chi=1, single closed manifold ball)" )
        else:
            setupLogger.results( f"  STATUS: VALID with complex topology (chi={result.solidEulerCharacteristic})" )
    else:
        setupLogger.results( "  STATUS: ISSUES" )
        if not has_single:
            setupLogger.results( f"    - {result.numConnectedComponents} disconnected 3D regions" )
        if not is_closed:
            setupLogger.results( f"    - {result.numBoundaryEdges:,} boundary edges (open surface)" )
        if not is_manifold:
            setupLogger.results( f"    - {result.numNonManifoldEdges:,} non-manifold edges" )


def __displaySurfaceGroup( g: SurfaceGroup ) -> None:
    """Display global aggregate followed by per-component breakdown."""
    if g.tagArray is None:
        head = f"surface (all 2D cells, {g.numCells:,} cells, {len(g.components)} component(s))"
    else:
        head = ( f"{g.tagArray} = {int(g.tagValue) if g.tagValue.is_integer() else g.tagValue} "
                 f"({g.numCells:,} cells, {len(g.components)} component(s))" )
    setupLogger.results( "" )
    setupLogger.results( head )
    if g.numCells == 0:
        return
    if len( g.components ) > 1:
        setupLogger.results( f"  GLOBAL: V={g.numVertices:,}  E={g.numEdges:,}  F={g.numFaces:,}  "
                             f"chi={g.eulerCharacteristic}  ∂E={g.numBoundaryEdges:,}  "
                             f"NM={g.numNonManifoldEdges:,}" )
    setupLogger.results( "  " + f"{'comp':>5} {'cells':>9} {'V':>8} {'E':>8} {'F':>8} {'chi':>5} "
                         f"{'∂E':>6} {'NM':>4}  interpretation" )
    setupLogger.results( "  " + "-" * 76 )
    for c in g.components:
        setupLogger.results( "  " + f"{c.componentId:>5} {c.numCells:>9,} {c.numVertices:>8,} {c.numEdges:>8,} "
                             f"{c.numFaces:>8,} {c.eulerCharacteristic:>5} {c.numBoundaryEdges:>6,} "
                             f"{c.numNonManifoldEdges:>4,}  {c.interpretation}" )
    if len( g.components ) > 1:
        setupLogger.results( f"  WARNING: {len(g.components)} components — verify isolated cells" )


def __displaySurface( result: Result ) -> None:
    setupLogger.results( "=" * 80 )
    setupLogger.results( "SURFACE EULER CHARACTERISTIC" )
    setupLogger.results( "=" * 80 )
    if not result.surfaceGroups:
        setupLogger.results( "(no surface groups produced)" )
        return
    for g in result.surfaceGroups:
        __displaySurfaceGroup( g )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the Euler characteristic computation."""
    if result.solidComputed:
        __displaySolid( result )
    elif options.mode in ( "solid", "all" ):
        setupLogger.results( "=" * 80 )
        setupLogger.results( "SOLID EULER CHARACTERISTIC: skipped (no 3D cells in input)" )
        setupLogger.results( "=" * 80 )

    if result.surfaceComputed:
        __displaySurface( result )
    elif options.mode in ( "surface", "all" ):
        setupLogger.results( "=" * 80 )
        setupLogger.results( "SURFACE EULER CHARACTERISTIC: skipped (no 2D cells in input)" )
        setupLogger.results( "=" * 80 )

    if result.num2dCells > 0 or result.numOtherCells > 0:
        setupLogger.results( "" )
        setupLogger.results( "Input cell breakdown:" )
        setupLogger.results( f"  3D cells   : {result.num3dCells:,}" )
        setupLogger.results( f"  2D cells   : {result.num2dCells:,}" )
        setupLogger.results( f"  Other cells: {result.numOtherCells:,}" )
    setupLogger.results( "=" * 80 )