import argparse
from dataclasses import dataclass
import pytest
from unittest.mock import MagicMock, patch
# Import the module to test
from geos.mesh_doctor.actions.allChecks import Options as AllChecksOptions
from geos.mesh_doctor.actions.allChecks import Result as AllChecksResult
from geos.mesh_doctor.parsing._sharedChecksParsingLogic import ( CheckFeature, _generateParametersHelp,
                                                                 getOptionsUsedMessage, fillSubparser, convert,
                                                                 displayResults, CHECKS_TO_DO_ARG, PARAMETERS_ARG )


# Mock dataclasses and functions we depend on
@dataclass
class MockOptions:
    param1: float = 1.0
    param2: float = 2.0


@dataclass
class MockResult:
    value: str = "testResult"


def mockDisplayFunc( options: MockOptions, result: MockResult ) -> None:
    """Mock display function for testing."""
    pass


@pytest.fixture
def checkFeaturesConfig() -> dict[ str, CheckFeature ]:
    """Provides a mock check features configuration for testing."""
    return {
        "check1":
        CheckFeature( name="check1",
                      optionsCls=MockOptions,
                      resultCls=MockResult,
                      defaultParams={
                          "param1": 1.0,
                          "param2": 2.0
                      },
                      display=mockDisplayFunc ),
        "check2":
        CheckFeature( name="check2",
                      optionsCls=MockOptions,
                      resultCls=MockResult,
                      defaultParams={
                          "param1": 3.0,
                          "param2": 4.0
                      },
                      display=mockDisplayFunc )
    }


@pytest.fixture
def orderedCheckNames() -> list[ str ]:
    """Provides an ordered list of check names for testing."""
    return [ "check1", "check2" ]


def test_generateParametersHelp( checkFeaturesConfig: dict[ str, CheckFeature ],
                                 orderedCheckNames: list[ str ] ) -> None:
    """Tests _generateParametersHelp functionality."""
    helpText = _generateParametersHelp( orderedCheckNames, checkFeaturesConfig )
    assert "For check1: param1:1.0, param2:2.0" in helpText
    assert "For check2: param1:3.0, param2:4.0" in helpText


def test_getOptionsUsedMessage() -> None:
    """Tests getOptionsUsedMessage functionality."""
    options = MockOptions( param1=10.0, param2=20.0 )
    message = getOptionsUsedMessage( options )
    assert "Parameters used: (" in message
    assert "param1 = 10.0" in message
    assert "param2 = 20.0" in message
    assert ")." in message


def test_fillSubparser( checkFeaturesConfig: dict[ str, CheckFeature ], orderedCheckNames: list[ str ] ) -> None:
    """Tests fillSubparser functionality."""
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers( dest="command" )
    fillSubparser( subparsers, "test-command", "Test help message", orderedCheckNames, checkFeaturesConfig )
    # Parse with no args should use defaults
    args = parser.parse_args( [ "test-command" ] )
    assert getattr( args, CHECKS_TO_DO_ARG ) == ""
    assert getattr( args, PARAMETERS_ARG ) == ""
    # Parse with specified args
    args = parser.parse_args(
        [ "test-command", f"--{CHECKS_TO_DO_ARG}", "check1", f"--{PARAMETERS_ARG}", "param1:10.5" ] )
    assert getattr( args, CHECKS_TO_DO_ARG ) == "check1"
    assert getattr( args, PARAMETERS_ARG ) == "param1:10.5"


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertDefaultChecks( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                               orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when no specific checks or parameters are specified."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "" } )
    options = convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )
    assert options.checksToPerform == orderedCheckNames
    assert len( options.checksOptions ) == 2
    assert options.checksOptions[ "check1" ].param1 == 1.0
    assert options.checksOptions[ "check2" ].param2 == 4.0


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertSpecificChecks( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when specific checks are specified."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "check1", PARAMETERS_ARG: "" } )
    options = convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )
    assert options.checksToPerform == [ "check1" ]
    assert len( options.checksOptions ) == 1
    assert "check1" in options.checksOptions
    assert "check2" not in options.checksOptions


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertWithParameters( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when parameters are specified."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "param1:10.5,param2:20.5" } )
    options = convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )
    assert options.checksToPerform == orderedCheckNames
    assert options.checksOptions[ "check1" ].param1 == 10.5
    assert options.checksOptions[ "check1" ].param2 == 20.5
    assert options.checksOptions[ "check2" ].param1 == 10.5
    assert options.checksOptions[ "check2" ].param2 == 20.5


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertWithInvalidParameters( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                       orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when some invalid parameters are specified."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "param1:invalid,param2:20.5" } )
    options = convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )
    # The invalid parameter should be skipped, but the valid one applied
    assert options.checksOptions[ "check1" ].param1 == 1.0  # Default maintained
    assert options.checksOptions[ "check1" ].param2 == 20.5  # Updated


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertWithInvalidCheck( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                  orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when an invalid check is specified."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "invalid_check,check1", PARAMETERS_ARG: "" } )
    options = convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )
    # The invalid check should be skipped
    assert options.checksToPerform == [ "check1" ]
    assert "check1" in options.checksOptions
    assert "invalid_check" not in options.checksOptions


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_convertWithAllInvalidChecks( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                      orderedCheckNames: list[ str ] ) -> None:
    """Tests convert when all checks are invalid."""
    parsedArgs = argparse.Namespace( **{ CHECKS_TO_DO_ARG: "invalid_check1,invalid_check2", PARAMETERS_ARG: "" } )
    # Should raise ValueError since no valid checks were selected
    with pytest.raises( ValueError, match="No valid checks were selected" ):
        convert( parsedArgs, orderedCheckNames, checkFeaturesConfig )


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_displayResultsWithChecks( mockLogger: MagicMock, checkFeaturesConfig: dict[ str, CheckFeature ],
                                   orderedCheckNames: list[ str ] ) -> None:
    """Tests displayResults when checks were performed."""
    options = AllChecksOptions( checksToPerform=[ "check1", "check2" ],
                                checksOptions={
                                    "check1": MockOptions(),
                                    "check2": MockOptions()
                                },
                                checkDisplays={
                                    "check1": mockDisplayFunc,
                                    "check2": mockDisplayFunc
                                } )
    result = AllChecksResult( checkResults={
        "check1": MockResult( value="result1" ),
        "check2": MockResult( value="result2" )
    } )
    displayResults( options, result )
    # Check that results logger was called for each check
    assert mockLogger.results.call_count >= 2


@patch( 'geos.mesh_doctor.parsing._sharedChecksParsingLogic.setupLogger' )
def test_displayResultsNoChecks( mockLogger: MagicMock ) -> None:
    """Tests displayResults when no checks were performed."""
    options = AllChecksOptions( checksToPerform=[], checksOptions={}, checkDisplays={} )
    result = AllChecksResult( checkResults={} )
    displayResults( options, result )
    # Should display a message that no checks were performed
    mockLogger.results.assert_called_with( "No checks were performed or all failed during configuration." )
