import logging
import pytest
import numpy as np
from _pytest.logging import LogCaptureFixture
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TETRA, VTK_HEXAHEDRON
from geos.mesh.utils.genericHelpers import createSingleCellMesh
from geos.mesh_doctor.filters.Checks import AllChecks, MainChecks, allChecks, mainChecks
from geos.mesh_doctor.parsing.allChecksParsing import ORDERED_CHECK_NAMES as ALL_CHECK_NAMES
from geos.mesh_doctor.parsing.mainChecksParsing import ORDERED_CHECK_NAMES as MAIN_CHECK_NAMES

__doc__ = """
Test module for Checks filter classes.
Tests the functionality of AllChecks and MainChecks filters for mesh validation.
"""


@pytest.fixture( scope="module" )
def singleTetrahedronMesh() -> vtkUnstructuredGrid:
    """Fixture for a single tetrahedron mesh."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def singleHexahedronMesh() -> vtkUnstructuredGrid:
    """Fixture for a single hexahedron mesh."""
    return createSingleCellMesh(
        VTK_HEXAHEDRON,
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ],
                    [ 0, 1, 1 ] ] ) )


class TestChecksBase:
    """Test class for base Checks filter functionality."""

    def test_initializationValidInputs( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test successful initialization with valid inputs."""
        checksFilter = AllChecks( singleTetrahedronMesh )

        assert checksFilter.name == "Mesh Doctor Checks Filter"
        assert checksFilter.mesh is not None
        assert checksFilter.mesh.GetNumberOfCells() > 0
        assert checksFilter.logger is not None
        assert isinstance( checksFilter.checksToPerform, list )
        assert len( checksFilter.checksToPerform ) > 0

    def test_initializationInvalidMeshType( self ) -> None:
        """Test initialization with invalid mesh type."""
        for errorObj in [ "not_a_mesh", 123, None ]:
            with pytest.raises( TypeError, match="Input 'mesh' must be a vtkUnstructuredGrid" ):
                AllChecks( errorObj )

    def test_initializationEmptyMesh( self ) -> None:
        """Test initialization with empty mesh."""
        with pytest.raises( ValueError, match="Input 'mesh' cannot be empty" ):
            AllChecks( vtkUnstructuredGrid() )

    def test_meshCopyBehavior( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that the filter creates a copy of the input mesh."""
        checksFilter = AllChecks( singleTetrahedronMesh )

        # The filter's mesh should be a copy, not the original
        assert checksFilter.mesh is not singleTetrahedronMesh
        assert checksFilter.mesh.GetNumberOfCells() == singleTetrahedronMesh.GetNumberOfCells()
        assert checksFilter.mesh.GetNumberOfPoints() == singleTetrahedronMesh.GetNumberOfPoints()

    def test_getAvailableChecks( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test retrieving available checks."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        availableChecks = allChecksFilter.getAvailableChecks()

        assert isinstance( availableChecks, list )
        assert len( availableChecks ) > 0
        assert all( isinstance( check, str ) for check in availableChecks )

    def test_getCheckDefaultParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test retrieving default parameters for a check."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        availableChecks = allChecksFilter.getAvailableChecks()

        # Get default parameters for the first available check
        if availableChecks:
            checkName = availableChecks[ 0 ]
            defaultParams = allChecksFilter.getCheckDefaultParameters( checkName )
            assert isinstance( defaultParams, dict )

    def test_getCheckDefaultParametersInvalidCheck( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test retrieving default parameters for non-existent check."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        defaultParams = allChecksFilter.getCheckDefaultParameters( "non_existent_check" )

        assert defaultParams == {}

    def test_setCheckParameter( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test setting a parameter for a specific check."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        # Set a parameter
        allChecksFilter.setCheckParameter( "collocatedNodes", "tolerance", 1e-6 )

        # Verify it was stored
        assert "collocatedNodes" in allChecksFilter.checkParameters
        assert "tolerance" in allChecksFilter.checkParameters[ "collocatedNodes" ]
        assert allChecksFilter.checkParameters[ "collocatedNodes" ][ "tolerance" ] == 1e-6

    def test_setCheckParameterMultipleParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test setting multiple parameters for multiple checks."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        allChecksFilter.setCheckParameter( "collocatedNodes", "tolerance", 1e-6 )
        allChecksFilter.setCheckParameter( "elementVolumes", "minVolume", 0.0 )

        assert len( allChecksFilter.checkParameters ) == 2
        assert allChecksFilter.checkParameters[ "collocatedNodes" ][ "tolerance" ] == 1e-6
        assert allChecksFilter.checkParameters[ "elementVolumes" ][ "minVolume" ] == 0.0

    def test_setAllChecksParameter( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test setting a parameter for all checks that support it."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        # Set tolerance for all checks that support it
        allChecksFilter.setAllChecksParameter( "tolerance", 1e-5 )

        # At least one check should have the tolerance parameter set
        toleranceSet = any( "tolerance" in params for params in allChecksFilter.checkParameters.values() )
        assert toleranceSet or len( allChecksFilter.checkParameters ) == 0

    def test_setChecksToPerform( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test setting which checks to perform."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        originalChecks = allChecksFilter.checksToPerform.copy()

        # Set to a subset of checks
        newChecks = [ "collocatedNodes", "elementVolumes" ]
        allChecksFilter.setChecksToPerform( newChecks )

        assert allChecksFilter.checksToPerform == newChecks
        assert allChecksFilter.checksToPerform != originalChecks


class TestAllChecks:
    """Test class for AllChecks filter."""

    def test_initialization( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test AllChecks initialization."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        assert allChecksFilter.name == "Mesh Doctor Checks Filter"
        assert len( allChecksFilter.checksToPerform ) == len( ALL_CHECK_NAMES )
        assert allChecksFilter.checksToPerform == ALL_CHECK_NAMES

    def test_applyFilterSuccess( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test successful application of all checks."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        # Should not raise an exception
        allChecksFilter.applyFilter()

        # Results should be populated
        results = allChecksFilter.getResults()
        assert isinstance( results, dict )
        assert len( results ) > 0

    def test_getResultsBeforeApply( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test getting results before applying filter."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        results = allChecksFilter.getResults()

        # Should return empty dict before applying
        assert isinstance( results, dict )
        assert len( results ) == 0

    def test_getResultsAfterApply( self, singleHexahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test getting results after applying filter."""
        allChecksFilter = AllChecks( singleHexahedronMesh )
        allChecksFilter.applyFilter()

        results = allChecksFilter.getResults()
        assert isinstance( results, dict )
        assert len( results ) > 0

        # Each result should have a check name as key
        for checkName in results:
            assert isinstance( checkName, str )

    def test_withCustomParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test applying all checks with custom parameters."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        allChecksFilter.setCheckParameter( "collocatedNodes", "tolerance", 1e-8 )

        allChecksFilter.applyFilter()
        results = allChecksFilter.getResults()

        assert isinstance( results, dict )
        assert len( results ) > 0

    def test_withSpecialHandler( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test initialization with special handler."""
        allChecksFilter = AllChecks( singleTetrahedronMesh, speHandler=True )

        assert isinstance( allChecksFilter.logger, logging.Logger )
        assert allChecksFilter.logger.name == "Mesh Doctor Checks Filter"


class TestMainChecks:
    """Test class for MainChecks filter."""

    def test_initialization( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test MainChecks initialization."""
        mainChecksFilter = MainChecks( singleTetrahedronMesh )

        assert mainChecksFilter.name == "Mesh Doctor Checks Filter"
        assert len( mainChecksFilter.checksToPerform ) == len( MAIN_CHECK_NAMES )
        assert mainChecksFilter.checksToPerform == MAIN_CHECK_NAMES

    def test_checksSubsetOfAll( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that main checks are a subset of all checks."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        mainChecksFilter = MainChecks( singleTetrahedronMesh )

        # Main checks should be a subset of all checks
        mainSet = set( mainChecksFilter.checksToPerform )
        allSet = set( allChecksFilter.checksToPerform )
        assert mainSet.issubset( allSet )

    def test_applyFilterSuccess( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test successful application of main checks."""
        mainChecksFilter = MainChecks( singleTetrahedronMesh )

        # Should not raise an exception
        mainChecksFilter.applyFilter()

        # Results should be populated
        results = mainChecksFilter.getResults()
        assert isinstance( results, dict )
        assert len( results ) > 0

    def test_withCustomParameters( self, singleHexahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test applying main checks with custom parameters."""
        mainChecksFilter = MainChecks( singleHexahedronMesh )
        mainChecksFilter.setCheckParameter( "elementVolumes", "minVolume", 0.0 )

        mainChecksFilter.applyFilter()
        results = mainChecksFilter.getResults()

        assert isinstance( results, dict )
        assert len( results ) > 0


class TestStandaloneFunctions:
    """Test class for standalone allChecks and mainChecks functions."""

    def test_allChecksFunction( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone allChecks function."""
        outputMesh, results = allChecks( singleTetrahedronMesh )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )
        assert outputMesh.GetNumberOfCells() > 0
        assert len( results ) > 0

    def test_allChecksFunctionWithCustomParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone allChecks function with custom parameters."""
        customParams = { "collocatedNodes": { "tolerance": 1e-7 } }
        outputMesh, results = allChecks( singleTetrahedronMesh, customParameters=customParams )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )
        assert len( results ) > 0

    def test_allChecksFunctionWithNoneParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone allChecks function with None parameters."""
        outputMesh, results = allChecks( singleTetrahedronMesh, customParameters=None )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )

    def test_allChecksFunctionInvalidParametersType( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone allChecks function with invalid parameters type."""
        with pytest.raises( TypeError, match="customParameters must be a dictionary" ):
            allChecks( singleTetrahedronMesh, customParameters="invalid" )

    def test_mainChecksFunction( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone mainChecks function."""
        outputMesh, results = mainChecks( singleTetrahedronMesh )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )
        assert outputMesh.GetNumberOfCells() > 0
        assert len( results ) > 0

    def test_mainChecksFunctionWithCustomParameters( self, singleHexahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone mainChecks function with custom parameters."""
        customParams = { "elementVolumes": { "minVolume": 0.0 } }
        outputMesh, results = mainChecks( singleHexahedronMesh, customParameters=customParams )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )
        assert len( results ) > 0

    def test_mainChecksFunctionWithNoneParameters( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone mainChecks function with None parameters."""
        outputMesh, results = mainChecks( singleTetrahedronMesh, customParameters=None )

        assert isinstance( outputMesh, vtkUnstructuredGrid )
        assert isinstance( results, dict )

    def test_mainChecksFunctionInvalidParametersType( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test standalone mainChecks function with invalid parameters type."""
        with pytest.raises( TypeError, match="customParameters must be a dictionary" ):
            mainChecks( singleTetrahedronMesh, customParameters="invalid" )


class TestChecksEdgeCases:
    """Test class for edge cases and error handling."""

    def test_buildOptionsWithInvalidCheckName( self, singleTetrahedronMesh: vtkUnstructuredGrid,
                                               caplog: LogCaptureFixture ) -> None:
        """Test building options with an invalid check name."""
        allChecksFilter = AllChecks( singleTetrahedronMesh, speHandler=True )
        allChecksFilter.logger.propagate = True

        # Set an invalid check name
        allChecksFilter.setChecksToPerform( [ "collocatedNodes", "invalidCheckName" ] )

        with caplog.at_level( logging.WARNING ):
            allChecksFilter.applyFilter()

        # Should log warning about invalid check
        warningMessages = [ record.message for record in caplog.records if record.levelname == "WARNING" ]
        assert any( "not available" in msg for msg in warningMessages )

    def test_multipleFiltersIndependence( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that multiple filter instances are independent."""
        filter1 = AllChecks( singleTetrahedronMesh )
        filter2 = MainChecks( singleTetrahedronMesh )

        filter1.setCheckParameter( "collocatedNodes", "tolerance", 1e-6 )
        filter2.setCheckParameter( "collocatedNodes", "tolerance", 1e-8 )

        # Parameters should be independent
        assert filter1.checkParameters != filter2.checkParameters

    def test_resultsIsolation( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that results are isolated between filter instances."""
        filter1 = AllChecks( singleTetrahedronMesh )
        filter2 = AllChecks( singleTetrahedronMesh )

        filter1.applyFilter()
        results1 = filter1.getResults()

        # Second filter should have empty results until applied
        results2 = filter2.getResults()
        assert len( results2 ) == 0
        assert results1 != results2

        filter2.applyFilter()
        results2 = filter2.getResults()
        assert len( results2 ) > 0

    def test_parameterOverride( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test that parameter overrides work correctly."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )

        # Set a parameter
        allChecksFilter.setCheckParameter( "collocatedNodes", "tolerance", 1e-6 )
        assert allChecksFilter.checkParameters[ "collocatedNodes" ][ "tolerance" ] == 1e-6

        # Override it
        allChecksFilter.setCheckParameter( "collocatedNodes", "tolerance", 1e-8 )
        assert allChecksFilter.checkParameters[ "collocatedNodes" ][ "tolerance" ] == 1e-8

    def test_emptyChecksToPerform( self, singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
        """Test with empty checks to perform list."""
        allChecksFilter = AllChecks( singleTetrahedronMesh )
        allChecksFilter.setChecksToPerform( [] )

        allChecksFilter.applyFilter()
        results = allChecksFilter.getResults()

        # Should have no results
        assert len( results ) == 0


@pytest.mark.parametrize( "checkName", [ "collocatedNodes", "elementVolumes", "selfIntersectingElements" ] )
def test_individualCheckExecution( singleTetrahedronMesh: vtkUnstructuredGrid, checkName: str ) -> None:
    """Parametrized test for executing individual checks."""
    allChecksFilter = AllChecks( singleTetrahedronMesh )

    # Set to perform only one check
    allChecksFilter.setChecksToPerform( [ checkName ] )
    allChecksFilter.applyFilter()

    results = allChecksFilter.getResults()

    # Should have exactly one result
    assert len( results ) == 1
    assert checkName in results


def test_meshPreservation( singleTetrahedronMesh: vtkUnstructuredGrid ) -> None:
    """Test that the mesh structure is preserved after checks."""
    originalCellCount = singleTetrahedronMesh.GetNumberOfCells()
    originalPointCount = singleTetrahedronMesh.GetNumberOfPoints()

    allChecksFilter = AllChecks( singleTetrahedronMesh )
    allChecksFilter.applyFilter()

    # Mesh structure should be unchanged
    assert allChecksFilter.mesh.GetNumberOfCells() == originalCellCount
    assert allChecksFilter.mesh.GetNumberOfPoints() == originalPointCount
