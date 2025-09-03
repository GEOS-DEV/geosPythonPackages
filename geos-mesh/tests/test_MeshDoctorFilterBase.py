import pytest
import logging
import numpy as np
from unittest.mock import Mock
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TETRA
from geos.mesh.utils.genericHelpers import createSingleCellMesh
from geos.mesh.doctor.actions.generate_cube import XYZ, build_rectilinear_blocks_mesh
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase, MeshDoctorGeneratorBase

__doc__ = """
Test module for MeshDoctorFilterBase classes.
Tests the functionality of base classes for mesh doctor filters and generators.
"""


@pytest.fixture( scope="module" )
def simple_test_mesh():
    """Fixture for a simple test mesh."""
    x, y, z = np.array( [ 0, 1 ] ), np.array( [ 0, 1 ] ), np.array( [ 0, 1 ] )
    mesh = build_rectilinear_blocks_mesh( [ XYZ( x, y, z ) ] )
    return mesh


@pytest.fixture( scope="module" )
def single_cell_mesh():
    """Fixture for a single tetrahedron mesh."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def empty_mesh():
    """Fixture for an empty mesh."""
    mesh = vtkUnstructuredGrid()
    points = vtkPoints()
    mesh.SetPoints( points )
    return mesh


class ConcreteFilterForTesting( MeshDoctorFilterBase ):
    """Concrete implementation of MeshDoctorFilterBase for testing purposes."""

    def __init__( self, mesh, filterName="TestFilter", useExternalLogger=False, shouldSucceed=True ):
        super().__init__( mesh, filterName, useExternalLogger )
        self.shouldSucceed = shouldSucceed
        self.applyFilterCalled = False

    def applyFilter( self ):
        """Test implementation that can be configured to succeed or fail."""
        self.applyFilterCalled = True
        if self.shouldSucceed:
            self.logger.info( "Test filter applied successfully" )
            return True
        else:
            self.logger.error( "Test filter failed" )
            return False


class ConcreteGeneratorForTesting( MeshDoctorGeneratorBase ):
    """Concrete implementation of MeshDoctorGeneratorBase for testing purposes."""

    def __init__( self, filterName="TestGenerator", useExternalLogger=False, shouldSucceed=True ):
        super().__init__( filterName, useExternalLogger )
        self.shouldSucceed = shouldSucceed
        self.applyFilterCalled = False

    def applyFilter( self ):
        """Test implementation that generates a simple mesh or fails."""
        self.applyFilterCalled = True
        if self.shouldSucceed:
            # Generate a simple single-cell mesh
            self.mesh = createSingleCellMesh( VTK_TETRA,
                                              np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )
            self.logger.info( "Test generator applied successfully" )
            return True
        else:
            self.logger.error( "Test generator failed" )
            return False


class TestMeshDoctorFilterBase:
    """Test class for MeshDoctorFilterBase functionality."""

    def test_initialization_valid_inputs( self, simple_test_mesh ):
        """Test successful initialization with valid inputs."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter", False )

        assert filter_instance.filterName == "TestFilter"
        assert filter_instance.mesh is not None
        assert filter_instance.mesh.GetNumberOfCells() > 0
        assert filter_instance.logger is not None

        # Verify that mesh is a copy, not the original
        assert filter_instance.mesh is not simple_test_mesh

    def test_initialization_with_external_logger( self, simple_test_mesh ):
        """Test initialization with external logger."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter", True )

        assert filter_instance.filterName == "TestFilter"
        assert isinstance( filter_instance.logger, logging.Logger )

    def test_initialization_invalid_mesh_type( self ):
        """Test initialization with invalid mesh type."""
        for error_obj in [ "not_a_mesh", 123, None ]:
            with pytest.raises( TypeError, match="Input 'mesh' must be a vtkUnstructuredGrid" ):
                ConcreteFilterForTesting( error_obj, "TestFilter" )

    def test_initialization_empty_mesh( self, empty_mesh ):
        """Test initialization with empty mesh."""
        with pytest.raises( ValueError, match="Input 'mesh' cannot be empty" ):
            ConcreteFilterForTesting( empty_mesh, "TestFilter" )

    def test_initialization_invalid_filter_name( self, simple_test_mesh ):
        """Test initialization with invalid filter name."""
        for error_obj in [ 123, None ]:
            with pytest.raises( TypeError, match="Input 'filterName' must be a string" ):
                ConcreteFilterForTesting( simple_test_mesh, error_obj )

        for error_obj in [ "", "   " ]:
            with pytest.raises( ValueError, match="Input 'filterName' cannot be an empty or whitespace-only string" ):
                ConcreteFilterForTesting( simple_test_mesh, error_obj )

    def test_initialization_invalid_external_logger_flag( self, simple_test_mesh ):
        """Test initialization with invalid useExternalLogger flag."""
        for error_obj in [ "not_bool", 1 ]:
            with pytest.raises( TypeError, match="Input 'useExternalLogger' must be a boolean" ):
                ConcreteFilterForTesting( simple_test_mesh, "TestFilter", error_obj )

    def test_get_mesh( self, simple_test_mesh ):
        """Test getMesh method returns the correct mesh."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )
        returned_mesh = filter_instance.getMesh()

        assert returned_mesh is filter_instance.mesh
        assert returned_mesh.GetNumberOfCells() == simple_test_mesh.GetNumberOfCells()
        assert returned_mesh.GetNumberOfPoints() == simple_test_mesh.GetNumberOfPoints()

    def test_copy_mesh( self, simple_test_mesh ):
        """Test copyMesh helper method."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )
        copied_mesh = filter_instance.copyMesh( simple_test_mesh )

        assert copied_mesh is not simple_test_mesh
        assert copied_mesh.GetNumberOfCells() == simple_test_mesh.GetNumberOfCells()
        assert copied_mesh.GetNumberOfPoints() == simple_test_mesh.GetNumberOfPoints()

    def test_apply_filter_success( self, simple_test_mesh ):
        """Test successful filter application."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter", shouldSucceed=True )
        result = filter_instance.applyFilter()

        assert result is True
        assert filter_instance.applyFilterCalled

    def test_apply_filter_failure( self, simple_test_mesh ):
        """Test filter application failure."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter", shouldSucceed=False )
        result = filter_instance.applyFilter()

        assert result is False
        assert filter_instance.applyFilterCalled

    def test_write_grid_with_mesh( self, simple_test_mesh, tmp_path ):
        """Test writing mesh to file when mesh is available."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )
        output_file = tmp_path / "test_output.vtu"

        filter_instance.writeGrid( str( output_file ) )

        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_grid_with_different_options( self, simple_test_mesh, tmp_path ):
        """Test writing mesh with different file options."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )

        # Test ASCII mode
        output_file_ascii = tmp_path / "test_ascii.vtu"
        filter_instance.writeGrid( str( output_file_ascii ), isDataModeBinary=False )
        assert output_file_ascii.exists()

        # Test with overwrite enabled
        output_file_overwrite = tmp_path / "test_overwrite.vtu"
        filter_instance.writeGrid( str( output_file_overwrite ), canOverwrite=True )
        assert output_file_overwrite.exists()

        # Write again with overwrite enabled (should not raise error)
        filter_instance.writeGrid( str( output_file_overwrite ), canOverwrite=True )

    def test_write_grid_without_mesh( self, simple_test_mesh, tmp_path, caplog ):
        """Test writing when no mesh is available."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )
        filter_instance.mesh = None  # Remove the mesh

        output_file = tmp_path / "should_not_exist.vtu"

        with caplog.at_level( logging.ERROR ):
            filter_instance.writeGrid( str( output_file ) )

        # Should log error and not create file
        assert "No mesh available" in caplog.text
        assert not output_file.exists()

    def test_set_logger_handler_without_existing_handlers( self, simple_test_mesh ):
        """Test setting logger handler when no handlers exist."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter", useExternalLogger=True )

        # Clear any existing handlers
        filter_instance.logger.handlers.clear()

        # Create a mock handler
        mock_handler = Mock()
        filter_instance.setLoggerHandler( mock_handler )

        # Verify handler was added
        assert mock_handler in filter_instance.logger.handlers

    def test_set_logger_handler_with_existing_handlers( self, simple_test_mesh, caplog ):
        """Test setting logger handler when handlers already exist."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter_with_handlers",
                                                    useExternalLogger=True )
        filter_instance.logger.addHandler( logging.NullHandler() )

        mock_handler = Mock()
        mock_handler.level = logging.WARNING

        with caplog.at_level( logging.WARNING ):
            filter_instance.setLoggerHandler( mock_handler )

        # Now caplog will capture the warning correctly
        assert "already has a handler" in caplog.text

    def test_logger_functionality( self, simple_test_mesh, caplog ):
        """Test that logging works correctly."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter_functionality" )

        with caplog.at_level( logging.INFO ):
            filter_instance.applyFilter()

        # Should have logged the success message
        assert "Test filter applied successfully" in caplog.text

    def test_mesh_deep_copy_behavior( self, simple_test_mesh ):
        """Test that the filter creates a deep copy of the input mesh."""
        filter_instance = ConcreteFilterForTesting( simple_test_mesh, "TestFilter" )

        # Modify the original mesh
        original_cell_count = simple_test_mesh.GetNumberOfCells()

        # The filter's mesh should be independent of the original
        filter_mesh = filter_instance.getMesh()
        assert filter_mesh.GetNumberOfCells() == original_cell_count
        assert filter_mesh is not simple_test_mesh


class TestMeshDoctorGeneratorBase:
    """Test class for MeshDoctorGeneratorBase functionality."""

    def test_initialization_valid_inputs( self ):
        """Test successful initialization with valid inputs."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", False )

        assert generator_instance.filterName == "TestGenerator"
        assert generator_instance.mesh is None  # Should start with no mesh
        assert generator_instance.logger is not None

    def test_initialization_with_external_logger( self ):
        """Test initialization with external logger."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", True )

        assert generator_instance.filterName == "TestGenerator"
        assert isinstance( generator_instance.logger, logging.Logger )

    def test_initialization_invalid_filter_name( self ):
        """Test initialization with invalid filter name."""
        for error_obj in [ 123, None ]:
            with pytest.raises( TypeError, match="Input 'filterName' must be a string" ):
                ConcreteGeneratorForTesting( error_obj )

        for error_obj in [ "", "   " ]:
            with pytest.raises( ValueError, match="Input 'filterName' cannot be an empty or whitespace-only string" ):
                ConcreteGeneratorForTesting( error_obj )

    def test_initialization_invalid_external_logger_flag( self ):
        """Test initialization with invalid useExternalLogger flag."""
        for error_obj in [ "not_bool", 1 ]:
            with pytest.raises( TypeError, match="Input 'useExternalLogger' must be a boolean" ):
                ConcreteGeneratorForTesting( "TestGenerator", error_obj )

    def test_get_mesh_before_generation( self ):
        """Test getMesh method before mesh generation."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator" )
        returned_mesh = generator_instance.getMesh()

        assert returned_mesh is None

    def test_get_mesh_after_generation( self ):
        """Test getMesh method after successful mesh generation."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        result = generator_instance.applyFilter()

        assert result is True
        assert generator_instance.mesh is not None

        returned_mesh = generator_instance.getMesh()
        assert returned_mesh is generator_instance.mesh
        assert returned_mesh.GetNumberOfCells() > 0

    def test_apply_filter_success( self ):
        """Test successful mesh generation."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        result = generator_instance.applyFilter()

        assert result is True
        assert generator_instance.applyFilterCalled
        assert generator_instance.mesh is not None

    def test_apply_filter_failure( self ):
        """Test mesh generation failure."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=False )
        result = generator_instance.applyFilter()

        assert result is False
        assert generator_instance.applyFilterCalled
        assert generator_instance.mesh is None

    def test_write_grid_with_generated_mesh( self, tmp_path ):
        """Test writing generated mesh to file."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generator_instance.applyFilter()

        output_file = tmp_path / "generated_mesh.vtu"
        generator_instance.writeGrid( str( output_file ) )

        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_write_grid_without_generated_mesh( self, tmp_path, caplog ):
        """Test writing when no mesh has been generated."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator" )
        output_file = tmp_path / "should_not_exist.vtu"

        with caplog.at_level( logging.ERROR ):
            generator_instance.writeGrid( str( output_file ) )

        # Should log error and not create file
        assert "No mesh generated" in caplog.text
        assert not output_file.exists()

    def test_write_grid_with_different_options( self, tmp_path ):
        """Test writing generated mesh with different file options."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generator_instance.applyFilter()

        # Test ASCII mode
        output_file_ascii = tmp_path / "generated_ascii.vtu"
        generator_instance.writeGrid( str( output_file_ascii ), isDataModeBinary=False )
        assert output_file_ascii.exists()

        # Test with overwrite enabled
        output_file_overwrite = tmp_path / "generated_overwrite.vtu"
        generator_instance.writeGrid( str( output_file_overwrite ), canOverwrite=True )
        assert output_file_overwrite.exists()

    def test_set_logger_handler_without_existing_handlers( self ):
        """Test setting logger handler when no handlers exist."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator", useExternalLogger=True )

        # Clear any existing handlers
        generator_instance.logger.handlers.clear()

        # Create a mock handler
        mock_handler = Mock()
        generator_instance.setLoggerHandler( mock_handler )

        # Verify handler was added
        assert mock_handler in generator_instance.logger.handlers

    def test_set_logger_handler_with_existing_handlers( self, caplog ):
        """Test setting logger handler when handlers already exist."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator_with_handlers", useExternalLogger=True )
        generator_instance.logger.addHandler( logging.NullHandler() )

        mock_handler = Mock()
        mock_handler.level = logging.WARNING

        with caplog.at_level( logging.WARNING ):
            generator_instance.setLoggerHandler( mock_handler )

        # Now caplog will capture the warning correctly
        assert "already has a handler" in caplog.text

    def test_logger_functionality( self, caplog ):
        """Test that logging works correctly."""
        generator_instance = ConcreteGeneratorForTesting( "TestGenerator_functionality", shouldSucceed=True )

        with caplog.at_level( logging.INFO ):
            generator_instance.applyFilter()

        # Should have logged the success message
        assert "Test generator applied successfully" in caplog.text


class TestMeshDoctorBaseEdgeCases:
    """Test class for edge cases and integration scenarios."""

    def test_filter_base_not_implemented_error( self, simple_test_mesh ):
        """Test that base class raises NotImplementedError."""
        filter_instance = MeshDoctorFilterBase( simple_test_mesh, "BaseFilter" )

        with pytest.raises( NotImplementedError, match="Subclasses must implement applyFilter method" ):
            filter_instance.applyFilter()

    def test_generator_base_not_implemented_error( self ):
        """Test that base generator class raises NotImplementedError."""
        generator_instance = MeshDoctorGeneratorBase( "BaseGenerator" )

        with pytest.raises( NotImplementedError, match="Subclasses must implement applyFilter method" ):
            generator_instance.applyFilter()

    def test_filter_with_single_cell_mesh( self, single_cell_mesh ):
        """Test filter with a single cell mesh."""
        filter_instance = ConcreteFilterForTesting( single_cell_mesh, "SingleCellTest" )
        result = filter_instance.applyFilter()

        assert result is True
        assert filter_instance.getMesh().GetNumberOfCells() == 1

    def test_filter_mesh_independence( self, simple_test_mesh ):
        """Test that multiple filters are independent."""
        filter1 = ConcreteFilterForTesting( simple_test_mesh, "Filter1" )
        filter2 = ConcreteFilterForTesting( simple_test_mesh, "Filter2" )

        mesh1 = filter1.getMesh()
        mesh2 = filter2.getMesh()

        # Meshes should be independent copies
        assert mesh1 is not mesh2
        assert mesh1 is not simple_test_mesh
        assert mesh2 is not simple_test_mesh

    def test_generator_multiple_instances( self ):
        """Test that multiple generator instances are independent."""
        gen1 = ConcreteGeneratorForTesting( "Gen1", shouldSucceed=True )
        gen2 = ConcreteGeneratorForTesting( "Gen2", shouldSucceed=True )

        gen1.applyFilter()
        gen2.applyFilter()

        assert gen1.getMesh() is not gen2.getMesh()
        assert gen1.getMesh() is not None
        assert gen2.getMesh() is not None

    def test_filter_logger_names( self, simple_test_mesh ):
        """Test that different filters get different logger names."""
        filter1 = ConcreteFilterForTesting( simple_test_mesh, "Filter1" )
        filter2 = ConcreteFilterForTesting( simple_test_mesh, "Filter2" )

        assert filter1.logger.name != filter2.logger.name

    def test_generator_logger_names( self ):
        """Test that different generators get different logger names."""
        gen1 = ConcreteGeneratorForTesting( "Gen1" )
        gen2 = ConcreteGeneratorForTesting( "Gen2" )

        assert gen1.logger.name != gen2.logger.name


@pytest.mark.parametrize( "filter_name,should_succeed", [
    ( "ParametrizedFilter1", True ),
    ( "ParametrizedFilter2", False ),
    ( "LongFilterNameForTesting", True ),
    ( "UnicodeFilter", True ),
] )
def test_parametrized_filter_behavior( simple_test_mesh, filter_name, should_succeed ):
    """Parametrized test for different filter configurations."""
    filter_instance = ConcreteFilterForTesting( simple_test_mesh, filter_name, shouldSucceed=should_succeed )

    result = filter_instance.applyFilter()
    assert result == should_succeed
    assert filter_instance.filterName == filter_name


@pytest.mark.parametrize( "generator_name,should_succeed", [
    ( "ParametrizedGen1", True ),
    ( "ParametrizedGen2", False ),
    ( "LongGeneratorNameForTesting", True ),
    ( "UnicodeGenerator", True ),
] )
def test_parametrized_generator_behavior( generator_name, should_succeed ):
    """Parametrized test for different generator configurations."""
    generator_instance = ConcreteGeneratorForTesting( generator_name, shouldSucceed=should_succeed )

    result = generator_instance.applyFilter()
    assert result == should_succeed
    assert generator_instance.filterName == generator_name

    if should_succeed:
        assert generator_instance.getMesh() is not None
    else:
        assert generator_instance.getMesh() is None
