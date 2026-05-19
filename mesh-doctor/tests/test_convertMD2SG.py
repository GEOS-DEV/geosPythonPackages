# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: GitHub Copilot, Jacques Franc
import argparse

from geos.mesh_doctor.parsing.convertMD2SGParsing import convert, fillSubparser
from geos.mesh_doctor.actions.convertMD2SG import Options, Result, action


def test_convert_md2sg_parser() -> None:
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fillSubparser( subparsers )

    args = parser.parse_args(
        [ 'convertMD2SG', '-i', 'data/base_tetra_shift.vtm', '-z', '2' ]
    )

    options = convert( vars( args ) )
    assert options.attrs == ( 2, )
    assert options.skipCleanCollocated is False 
    assert options.skipFilterVolumeCells is False 
    assert options.meshVtkOutput.output=="converted.vtu"


def test_convertion() -> None:
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fillSubparser( subparsers )

    args = parser.parse_args(
        [ 'convertMD2SG', '-i', 'data/base_tetra_shift.vtm', '-z', '2', '--outputFile', 'my_converted_mesh.vtu' ]
    )

    options = convert( vars( args ) )
    actionsResult = action( vars(args)['vtuInputFile'], options )
    assert isinstance( actionsResult, Result )
    assert actionsResult.outputMesh is not None
    

