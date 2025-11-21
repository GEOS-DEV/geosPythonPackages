# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import argparse
from dataclasses import dataclass
import pytest
from typing import Iterator, Sequence
from geos.mesh_doctor.actions.generateFractures import FracturePolicy, Options
from geos.mesh_doctor.parsing.generateFracturesParsing import convert, displayResults, fillSubparser
from geos.mesh.io.vtkIO import VtkOutput


@dataclass( frozen=True )
class TestCase:
    __test__ = False
    cliArgs: Sequence[ str ]
    options: Options
    exception: bool = False


def __generateGenerateFracturesParsingTestData() -> Iterator[ TestCase ]:
    field: str = "attribute"
    inputMesh: str = "input.vtu"
    mainMesh: str = "output.vtu"
    fractureMesh: str = "fracture.vtu"

    cliBase: str = f"generateFractures -i {inputMesh} --policy {{}} --name {field} --values 0,1"
    cliEnd: str = f"--output {mainMesh} --fracturesOutputDir ."
    cliGen: str = f"{cliBase} {cliEnd}"
    allCliArgs = cliGen.format( "field" ).split(), cliGen.format( "internalSurfaces" ).split(), cliGen.format(
        "dummy" ).split()
    policies = FracturePolicy.FIELD, FracturePolicy.INTERNAL_SURFACES, FracturePolicy.FIELD
    exceptions = False, False, True
    for cliArgs, policy, exception in zip( allCliArgs, policies, exceptions ):
        options: Options = Options( policy=policy,
                                    field=field,
                                    fieldValuesCombined=frozenset( ( 0, 1 ) ),
                                    fieldValuesPerFracture=[ frozenset( ( 0, 1 ) ) ],
                                    meshVtkOutput=VtkOutput( output=mainMesh, isDataModeBinary=True ),
                                    allFracturesVtkOutput=[ VtkOutput( output=fractureMesh, isDataModeBinary=True ) ] )
        yield TestCase( cliArgs, options, exception )


def __parseAndValidateOptions( testCase: TestCase ) -> None:
    """Parse CLI arguments and validate that the resulting options match expected values.

    This helper function simulates the CLI parsing process by:
    1. Creating an argument parser with the generateFractures subparser
    2. Parsing the test case's CLI arguments
    3. Converting the parsed arguments to Options
    4. Asserting that key fields match the expected options

    Args:
        testCase (TestCase): Test case containing CLI arguments and expected options.

    Raises:
        AssertionError: If any of the parsed options don't match expected values.
    """
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fillSubparser( subparsers )
    args = parser.parse_args( testCase.cliArgs )
    options = convert( vars( args ) )
    assert options.policy == testCase.options.policy
    assert options.field == testCase.options.field
    assert options.fieldValuesCombined == testCase.options.fieldValuesCombined


def test_displayResults() -> None:
    """Test displayResults function for code coverage."""
    # Dummy test for code coverage only. Shame on me!
    displayResults( None, None )


@pytest.mark.parametrize( "testCase", __generateGenerateFracturesParsingTestData() )
def test( testCase: TestCase ) -> None:
    """Test CLI parsing for generateFractures action."""
    if testCase.exception:
        with pytest.raises( SystemExit ):
            __parseAndValidateOptions( testCase )
    else:
        __parseAndValidateOptions( testCase )
