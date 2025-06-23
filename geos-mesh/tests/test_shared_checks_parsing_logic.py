import argparse
from dataclasses import dataclass
import pytest
from unittest.mock import patch
# Import the module to test
from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
from geos.mesh.doctor.actions.all_checks import Result as AllChecksResult
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import ( CheckFeature, _generate_parameters_help,
                                                                    get_options_used_message, fill_subparser, convert,
                                                                    display_results, CHECKS_TO_DO_ARG, PARAMETERS_ARG )


# Mock dataclasses and functions we depend on
@dataclass
class MockOptions:
    param1: float = 1.0
    param2: float = 2.0


@dataclass
class MockResult:
    value: str = "test_result"


def mock_display_func( options, result ):
    pass


@pytest.fixture
def check_features_config():
    return {
        "check1":
        CheckFeature( name="check1",
                      options_cls=MockOptions,
                      result_cls=MockResult,
                      default_params={
                          "param1": 1.0,
                          "param2": 2.0
                      },
                      display=mock_display_func ),
        "check2":
        CheckFeature( name="check2",
                      options_cls=MockOptions,
                      result_cls=MockResult,
                      default_params={
                          "param1": 3.0,
                          "param2": 4.0
                      },
                      display=mock_display_func )
    }


@pytest.fixture
def ordered_check_names():
    return [ "check1", "check2" ]


def test_generate_parameters_help( check_features_config, ordered_check_names ):
    help_text = _generate_parameters_help( ordered_check_names, check_features_config )
    assert "For check1: param1:1.0, param2:2.0" in help_text
    assert "For check2: param1:3.0, param2:4.0" in help_text


def test_get_options_used_message():
    options = MockOptions( param1=10.0, param2=20.0 )
    message = get_options_used_message( options )
    assert "Parameters used: (" in message
    assert "param1 = 10.0" in message
    assert "param2 = 20.0" in message
    assert ")." in message


def test_fill_subparser( check_features_config, ordered_check_names ):
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers( dest="command" )
    fill_subparser( subparsers, "test-command", "Test help message", ordered_check_names, check_features_config )
    # Parse with no args should use defaults
    args = parser.parse_args( [ "test-command" ] )
    assert getattr( args, CHECKS_TO_DO_ARG ) == ""
    assert getattr( args, PARAMETERS_ARG ) == ""
    # Parse with specified args
    args = parser.parse_args(
        [ "test-command", f"--{CHECKS_TO_DO_ARG}", "check1", f"--{PARAMETERS_ARG}", "param1:10.5" ] )
    assert getattr( args, CHECKS_TO_DO_ARG ) == "check1"
    assert getattr( args, PARAMETERS_ARG ) == "param1:10.5"


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_default_checks( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "" }
    options = convert( parsed_args, ordered_check_names, check_features_config )
    assert options.checks_to_perform == ordered_check_names
    assert len( options.checks_options ) == 2
    assert options.checks_options[ "check1" ].param1 == 1.0
    assert options.checks_options[ "check2" ].param2 == 4.0


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_specific_checks( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "check1", PARAMETERS_ARG: "" }
    options = convert( parsed_args, ordered_check_names, check_features_config )
    assert options.checks_to_perform == [ "check1" ]
    assert len( options.checks_options ) == 1
    assert "check1" in options.checks_options
    assert "check2" not in options.checks_options


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_with_parameters( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "param1:10.5,param2:20.5" }
    options = convert( parsed_args, ordered_check_names, check_features_config )
    assert options.checks_to_perform == ordered_check_names
    assert options.checks_options[ "check1" ].param1 == 10.5
    assert options.checks_options[ "check1" ].param2 == 20.5
    assert options.checks_options[ "check2" ].param1 == 10.5
    assert options.checks_options[ "check2" ].param2 == 20.5


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_with_invalid_parameters( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "", PARAMETERS_ARG: "param1:invalid,param2:20.5" }
    options = convert( parsed_args, ordered_check_names, check_features_config )
    # The invalid parameter should be skipped, but the valid one applied
    assert options.checks_options[ "check1" ].param1 == 1.0  # Default maintained
    assert options.checks_options[ "check1" ].param2 == 20.5  # Updated


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_with_invalid_check( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "invalid_check,check1", PARAMETERS_ARG: "" }
    options = convert( parsed_args, ordered_check_names, check_features_config )
    # The invalid check should be skipped
    assert options.checks_to_perform == [ "check1" ]
    assert "check1" in options.checks_options
    assert "invalid_check" not in options.checks_options


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_convert_with_all_invalid_checks( mock_logger, check_features_config, ordered_check_names ):
    parsed_args = { CHECKS_TO_DO_ARG: "invalid_check1,invalid_check2", PARAMETERS_ARG: "" }
    # Should raise ValueError since no valid checks were selected
    with pytest.raises( ValueError, match="No valid checks were selected" ):
        convert( parsed_args, ordered_check_names, check_features_config )


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_display_results_with_checks( mock_logger, check_features_config, ordered_check_names ):
    options = AllChecksOptions( checks_to_perform=[ "check1", "check2" ],
                                checks_options={
                                    "check1": MockOptions(),
                                    "check2": MockOptions()
                                },
                                check_displays={
                                    "check1": mock_display_func,
                                    "check2": mock_display_func
                                } )
    result = AllChecksResult( check_results={
        "check1": MockResult( value="result1" ),
        "check2": MockResult( value="result2" )
    } )
    display_results( options, result )
    # Check that results logger was called for each check
    assert mock_logger.results.call_count >= 2


@patch( 'geos.mesh.doctor.parsing._shared_checks_parsing_logic.setup_logger' )
def test_display_results_no_checks( mock_logger ):
    options = AllChecksOptions( checks_to_perform=[], checks_options={}, check_displays={} )
    result = AllChecksResult( check_results={} )
    display_results( options, result )
    # Should display a message that no checks were performed
    mock_logger.results.assert_called_with( "No checks were performed or all failed during configuration." )
