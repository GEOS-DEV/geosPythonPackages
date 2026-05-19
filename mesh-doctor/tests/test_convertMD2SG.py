# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: GitHub Copilot, Jacques Franc
import argparse

from geos.mesh_doctor.parsing.convertMD2SGParsing import convert, fillSubparser


def test_convert_md2sg_parser() -> None:
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fillSubparser( subparsers )

    args = parser.parse_args(
        [ 'convertMD2SG', '-i', 'input.vtu', '-z', '10', '20', '--skip-clean-collocated' ]
    )

    options = convert( vars( args ) )
    assert args.subparsers == 'convertMD2SG'
    assert args.vtuInputFile == 'input.vtu'
    assert options.attrs == ( 10, 20 )
    assert options.skipCleanCollocated is True
    assert options.skipFilterVolumeCells is False
    assert options.outputFile is None
