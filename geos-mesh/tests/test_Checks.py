import pytest
import numpy as np
from unittest.mock import patch, MagicMock
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TETRA, VTK_HEXAHEDRON
from geos.mesh.utils.genericHelpers import createSingleCellMesh, createMultiCellMesh
from geos.mesh.doctor.filters.Checks import Checks, AllChecks, MainChecks, allChecks, mainChecks
from geos.mesh.doctor.actions.all_checks import Options

__doc__ = """
Test module for Checks filters.
Tests the functionality of AllChecks, MainChecks, and base Checks class for mesh validation.
"""


@pytest.fixture( scope="module" )
def simple_hex_mesh() -> vtkUnstructuredGrid:
    """Fixture for a simple hexahedron mesh."""
    return createSingleCellMesh(
        VTK_HEXAHEDRON,
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ],
                    [ 0, 1, 1 ] ] ) )


@pytest.fixture( scope="module" )
def simple_tetra_mesh() -> vtkUnstructuredGrid:
    """Fixture for a simple tetrahedron mesh."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def mixed_quality_mesh() -> vtkUnstructuredGrid:
    """Fixture for a mesh with elements of varying quality."""
    return createMultiCellMesh( [ VTK_TETRA, VTK_TETRA ], [
        np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 0.5, 1.0, 0.0 ], [ 0.5, 0.5, 1.0 ] ] ),
        np.array( [ [ 2.0, 0.0, 0.0 ], [ 5.0, 0.0, 0.0 ], [ 3.5, 0.1, 0.0 ], [ 3.5, 0.05, 0.05 ] ] )
    ] )


@pytest.fixture( scope="module" )
def mesh_with_collocated_nodes() -> vtkUnstructuredGrid:
    """Fixture for a mesh with collocated (duplicate) nodes."""
    return createMultiCellMesh( [ VTK_TETRA, VTK_TETRA ], [
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ),
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] )
    ] )


class TestChecksBase:
    """Test class for base Checks filter functionality."""

    def test_base_checks_initialization( self, simple_hex_mesh ):
        """Test basic initialization of Checks base class."""
        # Create mock configurations for testing
        mock_check_features = { "test_check": MagicMock( default_params={ "param1": 1.0, "param2": "value" } ) }
        mock_ordered_names = [ "test_check" ]

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "test_check" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=mock_ordered_names )

        assert filter_instance.checksToPerform == [ "test_check" ]
        assert filter_instance.checkParameters == {}
        assert filter_instance.checkResults == {}
        assert filter_instance.checkFeaturesConfig == mock_check_features
        assert filter_instance.orderedCheckNames == mock_ordered_names

        # Test getMesh returns a copy
        processed_mesh = filter_instance.getMesh()
        assert processed_mesh is not simple_hex_mesh
        assert processed_mesh.GetNumberOfPoints() == simple_hex_mesh.GetNumberOfPoints()
        assert processed_mesh.GetNumberOfCells() == simple_hex_mesh.GetNumberOfCells()

    def test_parameter_setting( self, simple_hex_mesh ):
        """Test setting parameters for checks."""
        mock_check_features = {
            "check1": MagicMock( default_params={
                "tolerance": 1e-6,
                "param2": "default"
            } ),
            "check2": MagicMock( default_params={ "minValue": 0.0 } )
        }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "check1", "check2" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "check1", "check2" ] )

        # Test setting individual check parameter
        filter_instance.setCheckParameter( "check1", "tolerance", 1e-8 )
        assert filter_instance.checkParameters[ "check1" ][ "tolerance" ] == 1e-8

        # Test setting parameter for all checks
        filter_instance.setAllChecksParameter( "tolerance", 1e-10 )
        assert filter_instance.checkParameters[ "check1" ][ "tolerance" ] == 1e-10
        # check2 doesn't have tolerance parameter, so it shouldn't be set
        assert "check2" not in filter_instance.checkParameters or \
               "tolerance" not in filter_instance.checkParameters.get("check2", {})

    def test_get_available_checks( self, simple_hex_mesh ):
        """Test getting available checks."""
        mock_check_features = { "check1": MagicMock(), "check2": MagicMock() }
        ordered_names = [ "check1", "check2" ]

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "check1" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=ordered_names )

        available = filter_instance.getAvailableChecks()
        assert available == ordered_names

    def test_get_default_parameters( self, simple_hex_mesh ):
        """Test getting default parameters for a check."""
        default_params = { "tolerance": 1e-6, "minValue": 0.0 }
        mock_check_features = { "test_check": MagicMock( default_params=default_params ) }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "test_check" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "test_check" ] )

        params = filter_instance.getDefaultParameters( "test_check" )
        assert params == default_params

        # Test non-existent check
        params = filter_instance.getDefaultParameters( "nonexistent" )
        assert params == {}

    def test_set_checks_to_perform( self, simple_hex_mesh ):
        """Test changing which checks to perform."""
        mock_check_features = { "check1": MagicMock(), "check2": MagicMock(), "check3": MagicMock() }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "check1" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "check1", "check2", "check3" ] )

        assert filter_instance.checksToPerform == [ "check1" ]

        filter_instance.setChecksToPerform( [ "check2", "check3" ] )
        assert filter_instance.checksToPerform == [ "check2", "check3" ]

    @patch( 'geos.mesh.doctor.filters.Checks.get_check_results' )
    @patch( 'geos.mesh.doctor.filters.Checks.display_results' )
    def test_apply_filter_success( self, mock_display, mock_get_results, simple_hex_mesh ):
        """Test successful filter application."""
        # Mock the check results
        mock_results = { "test_check": { "status": "passed", "details": "All good" } }
        mock_get_results.return_value = mock_results

        mock_check_features = {
            "test_check":
            MagicMock( default_params={ "tolerance": 1e-6 }, options_cls=MagicMock( return_value=MagicMock() ) )
        }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "test_check" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "test_check" ] )

        success = filter_instance.applyFilter()
        assert success
        assert filter_instance.getCheckResults() == mock_results

        # Verify that get_check_results was called with proper arguments
        mock_get_results.assert_called_once()
        args = mock_get_results.call_args[ 0 ]
        assert isinstance( args[ 0 ], vtkUnstructuredGrid )
        assert args[ 0 ] is not simple_hex_mesh  # mesh argument
        assert isinstance( args[ 1 ], Options )  # options argument


class TestAllChecks:
    """Test class for AllChecks filter functionality."""

    def test_all_checks_initialization( self, simple_hex_mesh ):
        """Test AllChecks filter initialization."""
        filter_instance = AllChecks( simple_hex_mesh )

        # AllChecks should have all available checks configured
        assert len( filter_instance.checksToPerform ) > 0
        assert len( filter_instance.checkFeaturesConfig ) > 0
        assert len( filter_instance.orderedCheckNames ) > 0

        # Check that checksToPerform matches orderedCheckNames for AllChecks
        assert filter_instance.checksToPerform == filter_instance.orderedCheckNames

    def test_all_checks_with_external_logger( self, simple_hex_mesh ):
        """Test AllChecks initialization with external logger."""
        filter_instance = AllChecks( simple_hex_mesh, useExternalLogger=True )
        assert filter_instance is not None

    @patch( 'geos.mesh.doctor.filters.Checks.get_check_results' )
    @patch( 'geos.mesh.doctor.filters.Checks.display_results' )
    def test_all_checks_apply_filter( self, mock_display, mock_get_results, simple_hex_mesh ):
        """Test applying AllChecks filter."""
        # Mock successful check results
        mock_results = {
            "element_volumes": {
                "status": "passed"
            },
            "collocated_nodes": {
                "status": "passed"
            },
        }
        mock_get_results.return_value = mock_results

        filter_instance = AllChecks( simple_hex_mesh )
        success = filter_instance.applyFilter()

        assert success
        results = filter_instance.getCheckResults()
        assert results == mock_results


class TestMainChecks:
    """Test class for MainChecks filter functionality."""

    def test_main_checks_initialization( self, simple_hex_mesh ):
        """Test MainChecks filter initialization."""
        filter_instance = MainChecks( simple_hex_mesh )

        # MainChecks should have a subset of checks
        assert len( filter_instance.checksToPerform ) > 0
        assert len( filter_instance.checkFeaturesConfig ) > 0
        assert len( filter_instance.orderedCheckNames ) > 0

        # Check that checksToPerform matches orderedCheckNames for MainChecks
        assert filter_instance.checksToPerform == filter_instance.orderedCheckNames

    def test_main_checks_with_external_logger( self, simple_hex_mesh ):
        """Test MainChecks initialization with external logger."""
        filter_instance = MainChecks( simple_hex_mesh, useExternalLogger=True )
        assert filter_instance is not None

    @patch( 'geos.mesh.doctor.filters.Checks.get_check_results' )
    @patch( 'geos.mesh.doctor.filters.Checks.display_results' )
    def test_main_checks_apply_filter( self, mock_display, mock_get_results, simple_hex_mesh ):
        """Test applying MainChecks filter."""
        # Mock successful check results
        mock_results = {
            "element_volumes": {
                "status": "passed"
            },
            "collocated_nodes": {
                "status": "passed"
            },
        }
        mock_get_results.return_value = mock_results

        filter_instance = MainChecks( simple_hex_mesh )
        success = filter_instance.applyFilter()

        assert success
        results = filter_instance.getCheckResults()
        assert results == mock_results

    def test_main_vs_all_checks_difference( self, simple_hex_mesh ):
        """Test that MainChecks and AllChecks have different check sets."""
        all_checks_filter = AllChecks( simple_hex_mesh )
        main_checks_filter = MainChecks( simple_hex_mesh )

        # MainChecks should typically be a subset of AllChecks
        all_checks_set = set( all_checks_filter.checksToPerform )
        main_checks_set = set( main_checks_filter.checksToPerform )

        # Main checks should be a subset (or equal) to all checks
        assert main_checks_set.issubset( all_checks_set ) or main_checks_set == all_checks_set


class TestStandaloneFunctions:
    """Test class for standalone allChecks and mainChecks functions."""

    @patch( 'geos.mesh.doctor.filters.Checks.AllChecks' )
    def test_all_checks_function( self, mock_all_checks_class, simple_hex_mesh ):
        """Test standalone allChecks function."""
        # Mock the filter instance
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = True
        mock_filter.getMesh.return_value = simple_hex_mesh
        mock_filter.getCheckResults.return_value = { "test": "results" }
        mock_all_checks_class.return_value = mock_filter

        # Test without custom parameters
        result_mesh, results = allChecks( simple_hex_mesh )

        assert result_mesh == simple_hex_mesh
        assert results == { "test": "results" }
        mock_all_checks_class.assert_called_once_with( simple_hex_mesh )
        mock_filter.applyFilter.assert_called_once()

    @patch( 'geos.mesh.doctor.filters.Checks.AllChecks' )
    def test_all_checks_function_with_parameters( self, mock_all_checks_class, simple_hex_mesh ):
        """Test standalone allChecks function with custom parameters."""
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = True
        mock_filter.getMesh.return_value = simple_hex_mesh
        mock_filter.getCheckResults.return_value = { "test": "results" }
        mock_all_checks_class.return_value = mock_filter

        custom_params = { "collocated_nodes": { "tolerance": 1e-8 }, "element_volumes": { "minVolume": 0.1 } }

        result_mesh, results = allChecks( simple_hex_mesh, custom_params )

        assert result_mesh == simple_hex_mesh
        assert results == { "test": "results" }

        # Verify custom parameters were set
        mock_filter.setCheckParameter.assert_any_call( "collocated_nodes", "tolerance", 1e-8 )
        mock_filter.setCheckParameter.assert_any_call( "element_volumes", "minVolume", 0.1 )

    @patch( 'geos.mesh.doctor.filters.Checks.AllChecks' )
    def test_all_checks_function_failure( self, mock_all_checks_class, simple_hex_mesh ):
        """Test standalone allChecks function with filter failure."""
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = False
        mock_all_checks_class.return_value = mock_filter

        with pytest.raises( RuntimeError, match="allChecks calculation failed" ):
            allChecks( simple_hex_mesh )

    @patch( 'geos.mesh.doctor.filters.Checks.MainChecks' )
    def test_main_checks_function( self, mock_main_checks_class, simple_hex_mesh ):
        """Test standalone mainChecks function."""
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = True
        mock_filter.getMesh.return_value = simple_hex_mesh
        mock_filter.getCheckResults.return_value = { "test": "results" }
        mock_main_checks_class.return_value = mock_filter

        # Test without custom parameters
        result_mesh, results = mainChecks( simple_hex_mesh )

        assert result_mesh == simple_hex_mesh
        assert results == { "test": "results" }
        mock_main_checks_class.assert_called_once_with( simple_hex_mesh )
        mock_filter.applyFilter.assert_called_once()

    @patch( 'geos.mesh.doctor.filters.Checks.MainChecks' )
    def test_main_checks_function_with_parameters( self, mock_main_checks_class, simple_hex_mesh ):
        """Test standalone mainChecks function with custom parameters."""
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = True
        mock_filter.getMesh.return_value = simple_hex_mesh
        mock_filter.getCheckResults.return_value = { "test": "results" }
        mock_main_checks_class.return_value = mock_filter

        custom_params = { "element_volumes": { "minVolume": 0.05 } }

        result_mesh, results = mainChecks( simple_hex_mesh, custom_params )

        assert result_mesh == simple_hex_mesh
        assert results == { "test": "results" }

        # Verify custom parameters were set
        mock_filter.setCheckParameter.assert_called_with( "element_volumes", "minVolume", 0.05 )

    @patch( 'geos.mesh.doctor.filters.Checks.MainChecks' )
    def test_main_checks_function_failure( self, mock_main_checks_class, simple_hex_mesh ):
        """Test standalone mainChecks function with filter failure."""
        mock_filter = MagicMock()
        mock_filter.applyFilter.return_value = False
        mock_main_checks_class.return_value = mock_filter

        with pytest.raises( RuntimeError, match="mainChecks calculation failed" ):
            mainChecks( simple_hex_mesh )


class TestFileIO:
    """Test class for file I/O operations with checks."""

    def test_write_grid_functionality( self, simple_hex_mesh, tmp_path ):
        """Test writing mesh to file using tmp_path."""
        filter_instance = AllChecks( simple_hex_mesh )

        output_file = tmp_path / "test_output.vtu"

        # The writeGrid method should be inherited from MeshDoctorFilterBase
        # We'll test that the method exists and can be called
        assert hasattr( filter_instance, 'writeGrid' )

        # Test calling writeGrid (it should not raise an exception)
        try:
            filter_instance.writeGrid( str( output_file ) )
            # If the file was created, verify it exists
            if output_file.exists():
                assert output_file.stat().st_size > 0
        except Exception:
            # Some implementations might require the filter to be applied first
            filter_instance.applyFilter()
            filter_instance.writeGrid( str( output_file ) )


class TestOptionsBuilding:
    """Test class for options building functionality."""

    def test_build_options_with_defaults( self, simple_hex_mesh ):
        """Test building options with default parameters."""
        mock_options_cls = MagicMock( return_value=MagicMock() )
        mock_check_features = {
            "test_check": MagicMock( default_params={
                "param1": 1.0,
                "param2": "default"
            },
                                     options_cls=mock_options_cls )
        }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "test_check" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "test_check" ] )

        options = filter_instance._buildOptions()

        assert isinstance( options, Options )
        assert "test_check" in options.checks_to_perform
        # Verify options_cls was called with default parameters
        mock_options_cls.assert_called_once_with( param1=1.0, param2="default" )

    def test_build_options_with_failing_options_creation( self, simple_hex_mesh ):
        """Test building options when options class instantiation fails."""
        mock_options_cls = MagicMock( side_effect=Exception( "Options creation failed" ) )
        mock_check_features = {
            "failing_check": MagicMock( default_params={}, options_cls=mock_options_cls ),
            "working_check": MagicMock( default_params={}, options_cls=MagicMock( return_value=MagicMock() ) )
        }

        filter_instance = Checks( simple_hex_mesh,
                                  checksToPerform=[ "failing_check", "working_check" ],
                                  checkFeaturesConfig=mock_check_features,
                                  orderedCheckNames=[ "failing_check", "working_check" ] )

        options = filter_instance._buildOptions()

        # Only working check should be in the options
        assert options.checks_to_perform == [ "working_check" ]
        assert "failing_check" not in options.checks_to_perform


class TestErrorHandling:
    """Test class for error handling scenarios."""

    def test_empty_checks_list( self, simple_hex_mesh ):
        """Test handling of empty checks list."""
        filter_instance = Checks( simple_hex_mesh, checksToPerform=[], checkFeaturesConfig={}, orderedCheckNames=[] )

        options = filter_instance._buildOptions()
        assert options.checks_to_perform == []

    def test_mesh_copy_integrity( self, simple_hex_mesh ):
        """Test that mesh copy maintains integrity."""
        filter_instance = AllChecks( simple_hex_mesh )

        copied_mesh = filter_instance.getMesh()

        # Verify the copy has the same structure
        assert copied_mesh.GetNumberOfPoints() == simple_hex_mesh.GetNumberOfPoints()
        assert copied_mesh.GetNumberOfCells() == simple_hex_mesh.GetNumberOfCells()

        # Verify it's actually a copy, not the same object
        assert copied_mesh is not simple_hex_mesh

        # Verify point coordinates are the same
        for i in range( simple_hex_mesh.GetNumberOfPoints() ):
            original_point = simple_hex_mesh.GetPoint( i )
            copied_point = copied_mesh.GetPoint( i )
            np.testing.assert_array_equal( original_point, copied_point )


class TestIntegrationScenarios:
    """Test class for integration scenarios with different mesh types."""

    @patch( 'geos.mesh.doctor.filters.Checks.get_check_results' )
    @patch( 'geos.mesh.doctor.filters.Checks.display_results' )
    def test_complex_parameter_workflow( self, mock_display, mock_get_results, mixed_quality_mesh ):
        """Test complex parameter setting workflow."""
        mock_results = { "element_volumes": { "status": "warning", "issues": 1 } }
        mock_get_results.return_value = mock_results

        filter_instance = AllChecks( mixed_quality_mesh )

        # Set various parameters
        filter_instance.setCheckParameter( "element_volumes", "minVolume", 0.01 )
        filter_instance.setAllChecksParameter( "tolerance", 1e-10 )
        filter_instance.setCheckParameter( "collocated_nodes", "tolerance", 1e-12 )

        success = filter_instance.applyFilter()
        assert success

        results = filter_instance.getCheckResults()
        assert results == mock_results

    def test_multiple_filter_instances( self, simple_hex_mesh, simple_tetra_mesh ):
        """Test using multiple filter instances simultaneously."""
        all_checks_filter = AllChecks( simple_hex_mesh )
        main_checks_filter = MainChecks( simple_tetra_mesh )

        # Both should be independent
        assert all_checks_filter.getMesh() is not main_checks_filter.getMesh()
        assert all_checks_filter.checksToPerform != main_checks_filter.checksToPerform or \
               len(all_checks_filter.checksToPerform) >= len(main_checks_filter.checksToPerform)

    def test_parameter_isolation( self, simple_hex_mesh ):
        """Test that parameters are isolated between filter instances."""
        filter1 = AllChecks( simple_hex_mesh )
        filter2 = AllChecks( simple_hex_mesh )

        filter1.setCheckParameter( "element_volumes", "minVolume", 0.1 )
        filter2.setCheckParameter( "element_volumes", "minVolume", 0.2 )

        # Parameters should be independent
        assert filter1.checkParameters[ "element_volumes" ][ "minVolume" ] == 0.1
        assert filter2.checkParameters[ "element_volumes" ][ "minVolume" ] == 0.2
