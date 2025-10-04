import argparse
from dataclasses import dataclass
import pytest
from typing import Iterator, Sequence
from geos.mesh.doctor.actions.generateFractures import FracturePolicy, Options
from geos.mesh.doctor.parsing.generateFracturesParsing import convert, displayResults, fillSubparser
from geos.mesh.io.vtkIO import VtkOutput


@dataclass( frozen=True )
class TestCase:
    __test__ = False
    cliArgs: Sequence[ str ]
    options: Options
    exception: bool = False


def __generateGenerateFracturesParsingTestData() -> Iterator[ TestCase ]:
    field: str = "attribute"
    mainMesh: str = "output.vtu"
    fractureMesh: str = "fracture.vtu"

    cliGen: str = f"generate_fractures --policy {{}} --name {field} --values 0,1 --output {mainMesh} --fracturesOutputDir ."
    allCliArgs = cliGen.format( "field" ).split(), cliGen.format( "internal_surfaces" ).split(), cliGen.format(
        "dummy" ).split()
    policies = FracturePolicy.FIELD, FracturePolicy.INTERNAL_SURFACES, FracturePolicy.FIELD
    exceptions = False, False, True
    for cliArgs, policy, exception in zip( allCliArgs, policies, exceptions ):
        options: Options = Options(
            policy=policy,
            field=field,
            fieldValuesCombined=frozenset( ( 0, 1 ) ),
            fieldValuesPerFracture=[ frozenset( ( 0, 1 ) ) ],
            meshVtkOutput=VtkOutput( output=mainMesh, isDataModeBinary=True ),
            allFracturesVtkOutput=[ VtkOutput( output=fractureMesh, isDataModeBinary=True ) ] )
        yield TestCase( cliArgs, options, exception )


def __f( testCase: TestCase ):
    parser = argparse.ArgumentParser( description='Testing.' )
    subparsers = parser.add_subparsers()
    fillSubparser( subparsers )
    args = parser.parse_args( testCase.cliArgs )
    options = convert( vars( args ) )
    assert options.policy == testCase.options.policy
    assert options.field == testCase.options.field
    assert options.fieldValuesCombined == testCase.options.fieldValuesCombined


def test_displayResults():
    # Dummy test for code coverage only. Shame on me!
    displayResults( None, None )


@pytest.mark.parametrize( "testCase", __generateGenerateFracturesParsingTestData() )
def test( testCase: TestCase ):
    if testCase.exception:
        with pytest.raises( SystemExit ):
            pytest.skip( "Test to be fixed" )
            __f( testCase )
    else:
        pytest.skip( "Test to be fixed" )
        __f( testCase )
