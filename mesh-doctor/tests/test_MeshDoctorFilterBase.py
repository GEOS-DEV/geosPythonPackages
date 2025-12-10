import logging
import pytest
import numpy as np
from pathlib import Path
from _pytest.logging import LogCaptureFixture
from unittest.mock import Mock
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TETRA
from geos.mesh.utils.genericHelpers import createSingleCellMesh
from geos.mesh_doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase, MeshDoctorGeneratorBase

__doc__ = """
Test module for MeshDoctorFilterBase classes.
Tests the functionality of base classes for mesh doctor filters and generators.
"""


@pytest.fixture( scope="module" )
def singleTetrahedronMesh() -> vtkUnstructuredGrid:
    """Fixture for a single tetrahedron mesh."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


class ConcreteFilterForTesting( MeshDoctorFilterBase ):
    """Concrete implementation of MeshDoctorFilterBase for testing purposes."""

    def __init__( self,
                  mesh: vtkUnstructuredGrid,
                  filterName: str = "TestFilter",
                  speHandler: bool = False,
                  disableMeshCopy: bool = False,
                  shouldSucceed: bool = True ) -> None:
        """Initializes the test filter."""
        super().__init__( mesh, filterName, speHandler, disableMeshCopy )
        self.shouldSucceed = shouldSucceed
        self.applyFilterCalled = False

    def applyFilter( self ) -> None:
        """Test implementation that can be configured to succeed or fail."""
        self.applyFilterCalled = True
        if self.shouldSucceed:
            self.logger.info( "Test filter applied successfully" )
        else:
            self.logger.error( "Test filter failed" )


class ConcreteGeneratorForTesting( MeshDoctorGeneratorBase ):
    """Concrete implementation of MeshDoctorGeneratorBase for testing purposes."""

    def __init__( self,
                  filterName: str = "TestGenerator",
                  speHandler: bool = False,
                  shouldSucceed: bool = True ) -> None:
        """Initializes the test generator."""
        super().__init__( filterName, speHandler )
        self.shouldSucceed = shouldSucceed
        self.applyFilterCalled = False

    def applyFilter( self ) -> None:
        """Test implementation that generates a simple mesh or fails."""
        self.applyFilterCalled = True
        if self.shouldSucceed:
            # Generate a simple single-cell mesh
            self._mesh = createSingleCellMesh( VTK_TETRA,
                                               np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )
            self.logger.info( "Test generator applied successfully" )
        else:
            self.logger.error( "Test generator failed" )


class TestMeshDoctorFilterBase:
    """Test class for MeshDoctorFilterBase functionality."""

    def test_initializationValidInputs( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test successful initialization with valid inputs."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", False, False )

        assert filterInstance.name == "TestFilter"
        assert filterInstance.mesh is not None
        assert filterInstance.mesh.GetNumberOfCells() > 0
        assert filterInstance.logger is not None

        # Verify that mesh is a copy, not the original
        assert filterInstance.mesh is not singleTetrahedronMesh

    def test_initializationWithSpecialHandler( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test initialization with special handler."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", True, False )

        assert filterInstance.name == "TestFilter"
        assert isinstance( filterInstance.logger, logging.Logger )

    def test_initializationInvalidMeshType( self ) -> None:
        """Test initialization with invalid mesh type."""
        for errorObj in [ "notAMesh", 123, None ]:
            with pytest.raises( TypeError, match="Input 'mesh' must be a vtkUnstructuredGrid" ):
                ConcreteFilterForTesting( errorObj, "TestFilter" )  # type: ignore[arg-type]

    def test_initializationEmptyMesh( self ) -> None:
        """Test initialization with empty mesh."""
        with pytest.raises( ValueError, match="Input 'mesh' cannot be empty" ):
            ConcreteFilterForTesting( vtkUnstructuredGrid(), "TestFilter" )

    def test_initializationInvalidFilterName( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test initialization with invalid filter name."""
        for errorObj in [ 123, None ]:
            with pytest.raises( TypeError, match="Input 'filterName' must be a string" ):
                ConcreteFilterForTesting( singleTetrahedronMesh, errorObj )  # type: ignore[arg-type]

        for errorObj2 in [ "", "   " ]:
            with pytest.raises( ValueError, match="Input 'filterName' cannot be an empty or whitespace-only string" ):
                ConcreteFilterForTesting( singleTetrahedronMesh, errorObj2 )

    def test_initializationInvalidSpecialHandlerFlag( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test initialization with invalid speHandler flag."""
        for errorObj in [ "notBool", 1 ]:
            with pytest.raises( TypeError, match="Input 'speHandler' must be a boolean" ):
                ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", errorObj,
                                          False )  # type: ignore[arg-type]

    def test_meshProperty( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test mesh property returns the correct mesh."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter" )
        returnedMesh = filterInstance.mesh

        assert returnedMesh is filterInstance.mesh
        assert returnedMesh.GetNumberOfCells() == singleTetrahedronMesh.GetNumberOfCells()
        assert returnedMesh.GetNumberOfPoints() == singleTetrahedronMesh.GetNumberOfPoints()

    def test_disableMeshCopy( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that disableMeshCopy=True uses the original mesh."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", False, True )

        # With disableMeshCopy=True, mesh should be the same object
        assert filterInstance.mesh is singleTetrahedronMesh

    def test_meshCopyDefault( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that by default mesh is copied."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter" )

        # By default (disableMeshCopy=False), mesh should be a copy
        assert filterInstance.mesh is not singleTetrahedronMesh
        assert filterInstance.mesh.GetNumberOfCells() == singleTetrahedronMesh.GetNumberOfCells()
        assert filterInstance.mesh.GetNumberOfPoints() == singleTetrahedronMesh.GetNumberOfPoints()

    def test_applyFilterSuccess( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test successful filter application."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", shouldSucceed=True )
        filterInstance.applyFilter()

        assert filterInstance.applyFilterCalled

    def test_applyFilterFailure( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test filter application failure."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", shouldSucceed=False )
        filterInstance.applyFilter()

        assert filterInstance.applyFilterCalled

    def test_writeMeshWithMesh( self, singleTetrahedronMesh: vtkUnstructuredGrid, tmp_path: Path ) -> None:
        """Test writing mesh to file when mesh is available."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter" )
        outputFile = tmp_path / "test_output.vtu"

        filterInstance.writeMesh( str( outputFile ) )

        # Verify file was created
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeMeshWithDifferentOptions( self, singleTetrahedronMesh: vtkUnstructuredGrid, tmp_path: Path ) -> None:
        """Test writing mesh with different file options."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter" )

        # Test ASCII mode
        outputFileAscii = tmp_path / "test_ascii.vtu"
        filterInstance.writeMesh( str( outputFileAscii ), isDataModeBinary=False )
        assert outputFileAscii.exists()

        # Test with overwrite enabled
        outputFileOverwrite = tmp_path / "test_overwrite.vtu"
        filterInstance.writeMesh( str( outputFileOverwrite ), canOverwrite=True )
        assert outputFileOverwrite.exists()

        # Write again with overwrite enabled (should not raise error)
        filterInstance.writeMesh( str( outputFileOverwrite ), canOverwrite=True )

    def test_writeMeshWithoutMesh( self, singleTetrahedronMesh: vtkUnstructuredGrid, tmp_path: Path,
                                   caplog: LogCaptureFixture ) -> None:
        """Test writing when no mesh is available."""
        # Use speHandler=True to get standard logging that works with caplog
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", speHandler=True )
        # Enable propagation so caplog can capture the logs
        filterInstance.logger.propagate = True
        filterInstance._mesh = None  # Remove the mesh (accessing private attribute for testing)

        outputFile = tmp_path / "should_not_exist.vtu"

        with caplog.at_level( logging.ERROR ):
            filterInstance.writeMesh( str( outputFile ) )

        # Should log error and not create file
        errorMessages = [ record.message for record in caplog.records if record.levelname == "ERROR" ]
        assert any( "No mesh available" in msg for msg in errorMessages )
        assert not outputFile.exists()

    def test_setLoggerHandlerWithoutExistingHandlers( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test setting logger handler when no handlers exist."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter", True, False )

        # Clear any existing handlers
        filterInstance.logger.handlers.clear()

        # Create a mock handler
        mockHandler = Mock()
        filterInstance.setLoggerHandler( mockHandler )

        # Verify handler was added
        assert mockHandler in filterInstance.logger.handlers

    def test_setLoggerHandlerWithExistingHandlers( self, singleTetrahedronMesh: vtkUnstructuredGrid,
                                                   caplog: LogCaptureFixture ) -> None:
        """Test setting logger handler when handlers already exist."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter_with_handlers", True, False )
        filterInstance.logger.addHandler( logging.NullHandler() )

        mockHandler = Mock()
        mockHandler.level = logging.WARNING

        with caplog.at_level( logging.WARNING ):
            filterInstance.setLoggerHandler( mockHandler )

        # Now caplog will capture the warning correctly
        assert "already has a handler" in caplog.text

    def test_loggerFunctionality( self, singleTetrahedronMesh: vtkUnstructuredGrid, caplog: LogCaptureFixture ) -> None:
        """Test that logging works correctly."""
        # Use speHandler=True to get standard logging that works with caplog
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter_functionality", speHandler=True )
        # Enable propagation so caplog can capture the logs
        filterInstance.logger.propagate = True

        with caplog.at_level( logging.INFO ):
            filterInstance.applyFilter()

        # Should have logged the success message
        infoMessages = [ record.message for record in caplog.records if record.levelname == "INFO" ]
        assert any( "Test filter applied successfully" in msg for msg in infoMessages )

    def test_meshDeepCopyBehavior( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that the filter creates a deep copy of the input mesh."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "TestFilter" )

        # Modify the original mesh
        originalCellCount = singleTetrahedronMesh.GetNumberOfCells()

        # The filter's mesh should be independent of the original
        filterMesh = filterInstance.mesh
        assert filterMesh.GetNumberOfCells() == originalCellCount
        assert filterMesh is not singleTetrahedronMesh


class TestMeshDoctorGeneratorBase:
    """Test class for MeshDoctorGeneratorBase functionality."""

    def test_initializationValidInputs( self ) -> None:
        """Test successful initialization with valid inputs."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", False )

        assert generatorInstance.name == "TestGenerator"
        assert generatorInstance.mesh is None  # Should start with no mesh
        assert generatorInstance.logger is not None

    def test_initializationWithSpecialHandler( self ) -> None:
        """Test initialization with special handler."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", True )

        assert generatorInstance.name == "TestGenerator"
        assert isinstance( generatorInstance.logger, logging.Logger )

    def test_initializationInvalidFilterName( self ) -> None:
        """Test initialization with invalid filter name."""
        for errorObj in [ 123, None ]:
            with pytest.raises( TypeError, match="Input 'filterName' must be a string" ):
                ConcreteGeneratorForTesting( errorObj )  # type: ignore[arg-type]

        for errorObj2 in [ "", "   " ]:
            with pytest.raises( ValueError, match="Input 'filterName' cannot be an empty or whitespace-only string" ):
                ConcreteGeneratorForTesting( errorObj2 )

    def test_initializationInvalidSpecialHandlerFlag( self ) -> None:
        """Test initialization with invalid speHandler flag."""
        for errorObj in [ "notBool", 1 ]:
            with pytest.raises( TypeError, match="Input 'speHandler' must be a boolean" ):
                ConcreteGeneratorForTesting( "TestGenerator", errorObj )  # type: ignore[arg-type]

    def test_meshPropertyBeforeGeneration( self, caplog: LogCaptureFixture ) -> None:
        """Test mesh property before mesh generation."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", speHandler=True )
        # Enable propagation so caplog can capture the logs
        generatorInstance.logger.propagate = True

        with caplog.at_level( logging.WARNING ):
            returnedMesh = generatorInstance.mesh

        assert returnedMesh is None
        # Verify that a warning was logged
        warningMessages = [ record.message for record in caplog.records if record.levelname == "WARNING" ]
        assert any( "Mesh has not been generated yet" in msg for msg in warningMessages )

    def test_meshPropertyAfterGeneration( self ) -> None:
        """Test mesh property after successful mesh generation."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generatorInstance.applyFilter()

        assert generatorInstance.mesh is not None

        returnedMesh = generatorInstance.mesh
        assert returnedMesh is generatorInstance.mesh
        assert returnedMesh.GetNumberOfCells() > 0

    def test_applyFilterSuccess( self ) -> None:
        """Test successful mesh generation."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generatorInstance.applyFilter()

        assert generatorInstance.applyFilterCalled
        assert generatorInstance.mesh is not None

    def test_applyFilterFailure( self ) -> None:
        """Test mesh generation failure."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=False )
        generatorInstance.applyFilter()

        assert generatorInstance.applyFilterCalled
        assert generatorInstance.mesh is None

    def test_writeMeshWithGeneratedMesh( self, tmp_path: Path ) -> None:
        """Test writing generated mesh to file."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generatorInstance.applyFilter()

        outputFile = tmp_path / "generated_mesh.vtu"
        generatorInstance.writeMesh( str( outputFile ) )

        # Verify file was created
        assert outputFile.exists()
        assert outputFile.stat().st_size > 0

    def test_writeMeshWithoutGeneratedMesh( self, tmp_path: Path, caplog: LogCaptureFixture ) -> None:
        """Test writing when no mesh has been generated."""
        # Use speHandler=True to get standard logging that works with caplog
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", speHandler=True )
        # Enable propagation so caplog can capture the logs
        generatorInstance.logger.propagate = True
        outputFile = tmp_path / "should_not_exist.vtu"

        with caplog.at_level( logging.WARNING ):  # Changed to WARNING to catch both warning and error
            generatorInstance.writeMesh( str( outputFile ) )

        # Should log warning when accessing mesh property and error when trying to write
        warningMessages = [ record.message for record in caplog.records if record.levelname == "WARNING" ]
        errorMessages = [ record.message for record in caplog.records if record.levelname == "ERROR" ]
        assert any( "Mesh has not been generated yet" in msg for msg in warningMessages )
        assert any( "No mesh generated" in msg for msg in errorMessages )
        assert not outputFile.exists()

    def test_writeMeshWithDifferentOptions( self, tmp_path: Path ) -> None:
        """Test writing generated mesh with different file options."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", shouldSucceed=True )
        generatorInstance.applyFilter()

        # Test ASCII mode
        outputFileAscii = tmp_path / "generated_ascii.vtu"
        generatorInstance.writeMesh( str( outputFileAscii ), isDataModeBinary=False )
        assert outputFileAscii.exists()

        # Test with overwrite enabled
        outputFileOverwrite = tmp_path / "generated_overwrite.vtu"
        generatorInstance.writeMesh( str( outputFileOverwrite ), canOverwrite=True )
        assert outputFileOverwrite.exists()

    def test_setLoggerHandlerWithoutExistingHandlers( self ) -> None:
        """Test setting logger handler when no handlers exist."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator", True )

        # Clear any existing handlers
        generatorInstance.logger.handlers.clear()

        # Create a mock handler
        mockHandler = Mock()
        generatorInstance.setLoggerHandler( mockHandler )

        # Verify handler was added
        assert mockHandler in generatorInstance.logger.handlers

    def test_setLoggerHandlerWithExistingHandlers( self, caplog: LogCaptureFixture ) -> None:
        """Test setting logger handler when handlers already exist."""
        generatorInstance = ConcreteGeneratorForTesting( "TestGenerator_with_handlers", True )
        generatorInstance.logger.addHandler( logging.NullHandler() )

        mockHandler = Mock()
        mockHandler.level = logging.WARNING

        with caplog.at_level( logging.WARNING ):
            generatorInstance.setLoggerHandler( mockHandler )

        # Now caplog will capture the warning correctly
        assert "already has a handler" in caplog.text

    def test_loggerFunctionality( self, caplog: LogCaptureFixture ) -> None:
        """Test that logging works correctly."""
        # Use speHandler=True to get standard logging that works with caplog
        generatorInstance = ConcreteGeneratorForTesting( "TestGeneratorFunctionality",
                                                         speHandler=True,
                                                         shouldSucceed=True )
        # Enable propagation so caplog can capture the logs
        generatorInstance.logger.propagate = True

        with caplog.at_level( logging.INFO ):
            generatorInstance.applyFilter()

        # Should have logged the success message
        infoMessages = [ record.message for record in caplog.records if record.levelname == "INFO" ]
        assert any( "Test generator applied successfully" in msg for msg in infoMessages )


class TestMeshDoctorBaseEdgeCases:
    """Test class for edge cases and integration scenarios."""

    def test_filterBaseNotImplementedError( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that base class raises NotImplementedError."""
        filterInstance = MeshDoctorFilterBase( singleTetrahedronMesh, "BaseFilter" )

        with pytest.raises( NotImplementedError, match="Subclasses must implement applyFilter method" ):
            filterInstance.applyFilter()

    def test_generatorBaseNotImplementedError( self ) -> None:
        """Test that base generator class raises NotImplementedError."""
        generatorInstance = MeshDoctorGeneratorBase( "BaseGenerator" )

        with pytest.raises( NotImplementedError, match="Subclasses must implement applyFilter method" ):
            generatorInstance.applyFilter()

    def test_filterWithSingleCellMesh( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test filter with a single cell mesh."""
        filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, "SingleCellTest" )
        filterInstance.applyFilter()

        assert filterInstance.mesh.GetNumberOfCells() == 1

    def test_filterMeshIndependence( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that multiple filters are independent."""
        filter1 = ConcreteFilterForTesting( singleTetrahedronMesh, "Filter1" )
        filter2 = ConcreteFilterForTesting( singleTetrahedronMesh, "Filter2" )

        mesh1 = filter1.mesh
        mesh2 = filter2.mesh

        # Meshes should be independent copies
        assert mesh1 is not mesh2
        assert mesh1 is not singleTetrahedronMesh
        assert mesh2 is not singleTetrahedronMesh

    def test_generatorMultipleInstances( self ) -> None:
        """Test that multiple generator instances are independent."""
        gen1 = ConcreteGeneratorForTesting( "Gen1", shouldSucceed=True )
        gen2 = ConcreteGeneratorForTesting( "Gen2", shouldSucceed=True )

        gen1.applyFilter()
        gen2.applyFilter()

        assert gen1.mesh is not gen2.mesh
        assert gen1.mesh is not None
        assert gen2.mesh is not None

    def test_filterLoggerNames( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that different filters get different logger names."""
        filter1 = ConcreteFilterForTesting( singleTetrahedronMesh, "Filter1" )
        filter2 = ConcreteFilterForTesting( singleTetrahedronMesh, "Filter2" )

        assert filter1.logger.name != filter2.logger.name

    def test_generatorLoggerNames( self ) -> None:
        """Test that different generators get different logger names."""
        gen1 = ConcreteGeneratorForTesting( "Gen1" )
        gen2 = ConcreteGeneratorForTesting( "Gen2" )

        assert gen1.logger.name != gen2.logger.name


@pytest.mark.parametrize( "filterName,shouldSucceed", [
    ( "ParametrizedFilter1", True ),
    ( "ParametrizedFilter2", False ),
    ( "LongFilterNameForTesting", True ),
    ( "UnicodeFilter", True ),
] )
def test_parametrizedFilterBehavior( singleTetrahedronMesh: vtkUnstructuredGrid, filterName: str,
                                     shouldSucceed: bool ) -> None:
    """Parametrized test for different filter configurations."""
    filterInstance = ConcreteFilterForTesting( singleTetrahedronMesh, filterName, shouldSucceed=shouldSucceed )

    filterInstance.applyFilter()
    assert filterInstance.applyFilterCalled
    assert filterInstance.name == filterName


@pytest.mark.parametrize( "generatorName,shouldSucceed", [
    ( "ParametrizedGen1", True ),
    ( "ParametrizedGen2", False ),
    ( "LongGeneratorNameForTesting", True ),
    ( "UnicodeGenerator", True ),
] )
def test_parametrizedGeneratorBehavior( generatorName: str, shouldSucceed: bool ) -> None:
    """Parametrized test for different generator configurations."""
    generatorInstance = ConcreteGeneratorForTesting( generatorName, shouldSucceed=shouldSucceed )

    generatorInstance.applyFilter()
    assert generatorInstance.applyFilterCalled
    assert generatorInstance.name == generatorName

    if shouldSucceed:
        assert generatorInstance.mesh is not None
    else:
        assert generatorInstance.mesh is None
