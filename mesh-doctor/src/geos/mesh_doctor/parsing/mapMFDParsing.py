# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any

from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh_doctor.parsing import vtkOutputParsing
from geos.mesh_doctor.actions.mapMFD import Options, Result

__IP = "ip"
__PERMEABILITY = "permeability"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    """Convert parsed command-line options to Options object.

    Args:
        parsedOptions: Dictionary of parsed command-line options.

    Returns:
        Options: Configuration options for MFD computation.
    """
    vtkOut = vtkOutputParsing.convert( parsedOptions )
    ip = parsedOptions[ __IP ]
    permeability = parsedOptions[ __PERMEABILITY ]
    return Options( vtkOutput=vtkOut, ip=ip, permeability=permeability )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    """Fill the argument parser for the map MFD action.

    Args:
        subparsers: Subparsers from the main argument parser.
    """
    p = subparsers.add_parser( "map-mfd", help="Compute MFD indicators and attach results to a VTU" )
    addVtuInputFileArgument( p, required=False )
    p.add_argument( "--" + __IP, type=str, choices=( "QTPFA", "BdLVM" ), required=True )
    p.add_argument( "--" + __PERMEABILITY,
                    type=str,
                    default="Permeability",
                    help="Name of the cell data array that stores permeability." )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ) -> None:
    """Display the results of the MFD computation.

    Args:
        options: The options used for the MFD computation.
        result: The results of the MFD computation.
    """
    setupLogger.info( result.info )
