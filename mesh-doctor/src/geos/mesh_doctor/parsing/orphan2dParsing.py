# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any, Optional
from geos.mesh_doctor.actions.orphan2d import Options, Result
from geos.mesh_doctor.parsing import ORPHAN_2D
from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh.io.vtkIO import VtkOutput

__ORPHAN_OUTPUT = "orphanOutput"
__CLEAN_OUTPUT = "cleanOutput"
__DATA_MODE = "dataMode"
__DATA_MODE_VALUES = "binary", "ascii"
__DATA_MODE_DEFAULT = __DATA_MODE_VALUES[ 0 ]


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for orphan check.
    """
    orphanOutput: Optional[ str ] = parsedOptions.get( __ORPHAN_OUTPUT )
    cleanOutput: Optional[ str ] = parsedOptions.get( __CLEAN_OUTPUT )
    dataMode: str = parsedOptions.get( __DATA_MODE, __DATA_MODE_DEFAULT )
    isDataModeBinary: bool = dataMode == __DATA_MODE_DEFAULT

    # Create VtkOutput for orphan file if specified
    orphanVtkOutput = None
    if orphanOutput:
        orphanVtkOutput = VtkOutput( output=orphanOutput, isDataModeBinary=isDataModeBinary )

    # Create VtkOutput for clean file if specified
    cleanVtkOutput = None
    if cleanOutput:
        cleanVtkOutput = VtkOutput( output=cleanOutput, isDataModeBinary=isDataModeBinary )

    return Options( orphanVtkOutput=orphanVtkOutput, cleanVtkOutput=cleanVtkOutput )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Add orphan 2D cell check subparser with its arguments.

    Args:
        subparsers: The subparsers action to add the parser to.
    """
    p = subparsers.add_parser( ORPHAN_2D,
                               help="Check if 2D cells are faces of 3D cells and identify orphaned 2D elements." )
    addVtuInputFileArgument( p )
    p.add_argument( '--' + __ORPHAN_OUTPUT,
                    type=str,
                    metavar='FILE',
                    help="[string]: Output VTU file for orphaned 2D cells (cells not matching any 3D face)." )
    p.add_argument( '--' + __CLEAN_OUTPUT,
                    type=str,
                    metavar='FILE',
                    help="[string]: Output VTU file with orphaned 2D cells removed." )
    p.add_argument(
        '--' + __DATA_MODE,
        type=str,
        metavar=", ".join( __DATA_MODE_VALUES ),
        default=__DATA_MODE_DEFAULT,
        help='[string]: For ".vtu" output format, the data mode can be binary or ascii. Defaults to binary.' )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the orphan 2D cell check.

    Args:
        options: The options used for the check.
        result: The result of the orphan check.
    """
    setupLogger.results( "=" * 80 )
    setupLogger.results( "ORPHAN 2D CELL CHECK RESULTS" )
    setupLogger.results( "=" * 80 )
    setupLogger.results( f"Total 2D cells: {result.total2dCells}" )
    setupLogger.results( f"Total 3D cells: {result.total3dCells}" )
    setupLogger.results( f"2D cells matching 3D faces: {result.matched2dCells}" )
    setupLogger.results( f"Orphaned 2D cells: {result.orphaned2dCells}" )

    if result.orphaned2dCells == 0:
        setupLogger.results( "Validation PASSED: All 2D cells are faces of 3D cells" )
    else:
        setupLogger.results( f"Validation FAILED: {result.orphaned2dCells} 2D cells are not faces of 3D cells" )

        # Show first few orphaned cell indices for debugging
        if result.orphaned2dIndices:
            numToShow = min( 10, len( result.orphaned2dIndices ) )
            indices = ", ".join( map( str, result.orphaned2dIndices[ :numToShow ] ) )
            if len( result.orphaned2dIndices ) > numToShow:
                indices += ", ..."
            setupLogger.results( f"   First orphaned cell indices: {indices}" )

    setupLogger.results( "=" * 80 )
