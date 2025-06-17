# TODO Reimplement the tests
# import pytest
# import argparse
# from unittest.mock import patch, MagicMock, call
# from geos.mesh.doctor.actions.all_checks import Options as AllChecksOptions
# from geos.mesh.doctor.actions.all_checks import Result as AllChecksResult
# from geos.mesh.doctor.actions.all_checks import action
# from geos.mesh.doctor.parsing.all_checks_parsing import convert, fill_subparser, display_results
# from geos.mesh.doctor.parsing.all_checks_parsing import DEFAULT_CHECK_NAMES, ORDERED_CHECK_NAMES, CHECK_FEATURES_CONFIG


# # Mock data and fixtures
# @pytest.fixture
# def mock_parser():
#     parser = argparse.ArgumentParser()
#     subparsers = parser.add_subparsers( dest="action" )
#     return parser, subparsers


# @pytest.fixture
# def mock_check_action():
#     return MagicMock( return_value={ "status": "success" } )


# @pytest.fixture
# def mock_args():
#     return {
#         "checks_to_perform": "collocated_nodes, element_volumes",
#         "set_parameters": "tolerance:1.0, min_volume:0.5"
#     }


# # Tests for all_checks_parsing.py
# class TestAllChecksParsing:

#     def test_fill_subparser( self, mock_parser ):
#         parser, subparsers = mock_parser
#         fill_subparser( subparsers )

#         # Verify subparser was created
#         subparsers_actions = [
#             action for action in parser._subparsers._actions if isinstance( action, argparse._SubParsersAction )
#         ]
#         assert len( subparsers_actions ) == 1

#         # Check if our subparser is in the choices
#         subparser_choices = subparsers_actions[ 0 ].choices
#         assert "all_checks" in subparser_choices  # assuming ALL_CHECKS is "all_checks"

#     def test_convert_with_default_checks( self ):
#         # Test with empty string for checks_to_perform (should use all checks)
#         args = { "checks_to_perform": "", "set_parameters": "" }
#         with patch( 'geos.mesh.doctor.parsing.all_checks_parsing.setup_logger' ) as mock_logger:
#             options = convert( args )

#             # Should log that all checks will be performed
#             mock_logger.info.assert_any_call( "All current available checks in mesh-doctor will be performed." )

#             # Should include all checks
#             assert options.checks_to_perform == DEFAULT_CHECK_NAMES

#             # Should use default parameters
#             for check_name in DEFAULT_CHECK_NAMES:
#                 assert check_name in options.checks_options

#     def test_convert_with_specific_checks( self, mock_args ):
#         with patch( 'geos.mesh.doctor.parsing.all_checks_parsing.setup_logger' ):
#             options = convert( mock_args )

#             # Should only include the specified checks
#             expected_checks = [ "collocated_nodes", "element_volumes" ]
#             assert options.checks_to_perform == expected_checks

#             # Should only have options for specified checks
#             assert set( options.checks_options.keys() ) == set( expected_checks )

#     def test_convert_with_invalid_check( self ):
#         args = { "checks_to_perform": "invalid_check_name", "set_parameters": "" }
#         with patch( 'geos.mesh.doctor.parsing.all_checks_parsing.setup_logger' ) as mock_logger:
#             with pytest.raises( ValueError, match="No valid checks selected" ):
#                 convert( args )

#             # Should log warning about invalid check
#             mock_logger.warning.assert_called()

#     def test_convert_with_parameter_override( self ):
#         # Choose a check and parameter that exists in DEFAULT_PARAMS
#         check_name = "collocated_nodes"
#         param_name = next( iter( CHECK_FEATURES_CONFIG[ check_name ].default_params.keys() ) )
#         args = { "checks_to_perform": check_name, "set_parameters": f"{param_name}:99.9" }
#         with patch( 'geos.mesh.doctor.parsing.all_checks_parsing.setup_logger' ):
#             options = convert( args )

#             # Get the options object for the check
#             check_options = options.checks_options[ check_name ]

#             # Verify the parameter was overridden
#             # This assumes the parameter is accessible as an attribute of the options object
#             # May need adjustment based on your actual implementation
#             assert getattr( check_options, param_name, None ) == 99.9

#     def test_display_results( self ):
#         # Create mock options and results
#         mock_display_func = MagicMock()
#         check_name = ORDERED_CHECK_NAMES[ 0 ]
#         options = AllChecksOptions( checks_to_perform=[ check_name ],
#                                     checks_options={ check_name: "mock_options" },
#                                     check_displays={ check_name: mock_display_func } )
#         result = AllChecksResult( check_results={ check_name: "mock_result" } )
#         with patch( 'geos.mesh.doctor.parsing.all_checks_parsing.setup_logger' ):
#             display_results( options, result )

#             # Verify display function was called with correct arguments
#             mock_display_func.assert_called_once_with( "mock_options", "mock_result" )


# # Tests for all_checks.py
# class TestAllChecks:

#     def test_action_calls_check_modules( self, mock_check_action ):
#         # Setup mock options
#         check_name = ORDERED_CHECK_NAMES[ 0 ]
#         mock_options = AllChecksOptions( checks_to_perform=[ check_name ],
#                                          checks_options={ check_name: "mock_options" },
#                                          check_displays={ check_name: MagicMock() } )
#         # Mock the module loading function
#         with patch( 'geos.mesh.doctor.actions.all_checks.__load_module_action',
#                     return_value=mock_check_action ) as mock_load:
#             with patch( 'geos.mesh.doctor.actions.all_checks.setup_logger' ):
#                 result = action( "test_file.vtk", mock_options )

#                 # Verify the module was loaded
#                 mock_load.assert_called_once_with( check_name )

#                 # Verify the check action was called with correct args
#                 mock_check_action.assert_called_once_with( "test_file.vtk", "mock_options" )

#                 # Verify result contains the check result
#                 assert check_name in result.check_results
#                 assert result.check_results[ check_name ] == { "status": "success" }

#     def test_action_with_multiple_checks( self, mock_check_action ):
#         # Setup mock options with multiple checks
#         check_names = [ ORDERED_CHECK_NAMES[ 0 ], ORDERED_CHECK_NAMES[ 1 ] ]
#         mock_options = AllChecksOptions( checks_to_perform=check_names,
#                                          checks_options={
#                                              name: f"mock_options_{i}"
#                                              for i, name in enumerate( check_names )
#                                          },
#                                          check_displays={ name: MagicMock()
#                                                           for name in check_names } )
#         # Mock the module loading function
#         with patch( 'geos.mesh.doctor.actions.all_checks.__load_module_action',
#                     return_value=mock_check_action ) as mock_load:
#             with patch( 'geos.mesh.doctor.actions.all_checks.setup_logger' ):
#                 result = action( "test_file.vtk", mock_options )

#                 # Verify the modules were loaded
#                 assert mock_load.call_count == 2
#                 mock_load.assert_has_calls( [ call( check_names[ 0 ] ), call( check_names[ 1 ] ) ] )

#                 # Verify all checks were called
#                 assert mock_check_action.call_count == 2

#                 # Verify result contains all check results
#                 for name in check_names:
#                     assert name in result.check_results
#                     assert result.check_results[ name ] == { "status": "success" }
