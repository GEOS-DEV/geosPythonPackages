# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: GitHub Copilot, Jacques Franc
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any

from geos.mesh_doctor.actions.convertMD2SG import Options, Result
from geos.mesh_doctor.parsing import CONVERT_MD2SG
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh.io.vtkIO import VtkOutput

__ATTRS = "attrs"
__OUTPUT_FILE = "outputFile"
__SKIP_CLEAN = "skipCleanCollocated"
__SKIP_FILTER = "skipFilterVolumeCells"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Converted options object.
    """
    return Options( attrs=tuple( parsedOptions.get( __ATTRS, [] ) ),
                    skipCleanCollocated=parsedOptions.get( __SKIP_CLEAN, False ),
                    skipFilterVolumeCells=parsedOptions.get( __SKIP_FILTER, False ),
                    meshVtkOutput=VtkOutput( output=parsedOptions.get( __OUTPUT_FILE ), isDataModeBinary=True ) )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the convertMD2SG action.

    Args:
        subparsers: Subparsers from the main argument parser.
    """
    p = subparsers.add_parser( CONVERT_MD2SG,
                               help="Convert a mesh-doctor dataset to a SurfaceGen-compatible VTU file." )
    addVtuInputFileArgument( p )
    p.add_argument( '-z',
                    '--' + __ATTRS,
                    type=int,
                    nargs='+',
                    default=[],
                    help="[int ...]: Attributes to include when filtering surface cells." )
    p.add_argument( '--' + __OUTPUT_FILE,
                    type=str,
                    default="converted.vtu",
                    help="[string]: Optional output VTU file path." )
    p.add_argument( '--' + __SKIP_CLEAN, action='store_true', help="Skip the collocated node cleanup step." )
    p.add_argument( '--' + __SKIP_FILTER,
                    action='store_true',
                    help="Skip the surface/volume extraction step when input is a single VTU file." )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the convertMD2SG action.

    Args:
        options: The options used for the conversion.
        result: The results of the conversion.
    """
    setupLogger.results( getOptionsUsedMessage( options ) )
    setupLogger.results( "Converted mesh saved to: {0}".format( result.outputFile ) )
    setupLogger.results( f"  Points: {result.numPoints:,}" )
    setupLogger.results( f"  Cells: {result.numCells:,}" )
    setupLogger.results( f"  Bounds: {result.bounds}" )
    setupLogger.results(
        f"  Skip clean collocated(npoints cleaned): {result.skipCleanCollocated} ({result.nCleanCollocated})" )
    setupLogger.results(
        f"  Skip filter volume cells(ncells removed): {result.skipFilterVolumeCells} ({result.nFilterVolumeCells})" )
