# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Your Name
from __future__ import annotations
from argparse import _SubParsersAction
from typing import Any

from geos.mesh_doctor.parsing.cliParsing import setupLogger, addVtuInputFileArgument
from geos.mesh_doctor.parsing import vtkOutputParsing
from geos.mesh_doctor.actions.mapMFD import Options, Result


__IP = "ip"


def convert( parsedOptions: dict[ str, Any ] ) -> Options:
    vtkOut = vtkOutputParsing.convert( parsedOptions )
    ip = parsedOptions[ __IP ]
    return Options( vtkOutput=vtkOut, ip=ip )


def fillSubparser( subparsers: _SubParsersAction[ Any ] ) -> None:
    p = subparsers.add_parser( "map-mfd", help="Compute MFD indicators and attach results to a VTU" )
    addVtuInputFileArgument( p, required=False )
    p.add_argument( "--" + __IP, type=str, choices=("TPFA", "QTPFA", "BdLVM"), required=True )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def displayResults( options: Options, result: Result ) -> None:
    setupLogger.info( result.info )
