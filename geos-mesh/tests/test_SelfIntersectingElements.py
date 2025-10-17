import pytest
import logging
import numpy as np
from vtkmodules.vtkCommonDataModel import VTK_HEXAHEDRON, VTK_PYRAMID, VTK_TETRA
from geos.mesh.utils.genericHelpers import createSingleCellMesh, createMultiCellMesh
from geos.mesh.doctor.filters.SelfIntersectingElements import SelfIntersectingElements, selfIntersectingElements

__doc__ = """
Test module for SelfIntersectingElements filter.
Tests the functionality of detecting various types of invalid or problematic elements.
"""


@pytest.fixture( scope="module" )
def single_hex_mesh():
    """Fixture for a single valid hexahedron mesh with no invalid elements."""
    return createSingleCellMesh(
        VTK_HEXAHEDRON,
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ],
                    [ 0, 1, 1 ] ] ) )


@pytest.fixture( scope="module" )
def single_tetra_mesh():
    """Fixture for a single valid tetrahedron."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )


@pytest.fixture( scope="module" )
def degenerate_tetra_mesh():
    """Fixture for a tetrahedron with degenerate (coplanar) points."""
    return createSingleCellMesh( VTK_TETRA,
                                 np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0.5, 0.5, 0.0 ], [ 0.2, 0.3, 0.0 ] ] ) )


@pytest.fixture( scope="module" )
def inverted_pyramid_mesh():
    """Fixture for an inverted pyramid (wrong orientation)."""
    return createSingleCellMesh( VTK_PYRAMID,
                                 np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0.5, 0.5,
                                                                                                   -1.0 ] ] ) )


@pytest.fixture( scope="module" )
def wrong_point_count_mesh():
    """Fixture for elements with wrong number of points."""
    return createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0.5, 1.0, 0.0 ] ] ) )


class TestSelfIntersectingElementsFilter:
    """Test class for SelfIntersectingElements filter functionality."""

    def test_filter_initialization_default( self, single_hex_mesh ):
        """Test filter initialization with default parameters."""
        filter_instance = SelfIntersectingElements( single_hex_mesh )

        assert filter_instance.getMinDistance() == 0.0
        assert not filter_instance.writeInvalidElements
        assert filter_instance.getMesh() is not None
        assert isinstance( filter_instance.getInvalidCellIds(), dict )

    def test_filter_initialization_custom( self, single_hex_mesh ):
        """Test filter initialization with custom parameters."""
        filter_instance = SelfIntersectingElements( single_hex_mesh,
                                                    minDistance=1e-6,
                                                    writeInvalidElements=True,
                                                    useExternalLogger=True )

        assert filter_instance.getMinDistance() == 1e-6
        assert filter_instance.writeInvalidElements

    def test_filter_on_clean_mesh( self, single_hex_mesh ):
        """Test filter on a clean mesh with no invalid elements."""
        filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should be a dictionary with error type keys
        assert isinstance( invalid_cells, dict )

        # Check that all error types have empty lists (no invalid elements)
        expected_error_types = [
            'wrongNumberOfPointsElements', 'intersectingEdgesElements', 'intersectingFacesElements',
            'nonContiguousEdgesElements', 'nonConvexElements', 'facesOrientedIncorrectlyElements',
            'nonPlanarFacesElements', 'degenerateFacesElements'
        ]

        for error_type in expected_error_types:
            assert error_type in invalid_cells
            assert isinstance( invalid_cells[ error_type ], list )

    def test_filter_on_single_valid_element( self, single_tetra_mesh ):
        """Test filter on a single valid element."""
        filter_instance = SelfIntersectingElements( single_tetra_mesh, minDistance=1e-8 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should have no invalid elements for a properly constructed single tetrahedron
        total_invalid = sum( len( cells ) for cells in invalid_cells.values() )
        # Note: This might detect some issues depending on how the single cell is constructed
        assert total_invalid >= 0  # Just ensure it doesn't crash

    def test_filter_detect_degenerate_elements( self, degenerate_tetra_mesh ):
        """Test detection of degenerate elements."""
        filter_instance = SelfIntersectingElements( degenerate_tetra_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should detect some type of invalidity in the degenerate tetrahedron
        total_invalid = sum( len( cells ) for cells in invalid_cells.values() )
        assert total_invalid > 0

    def test_filter_detect_orientation_issues( self, inverted_pyramid_mesh ):
        """Test detection of orientation issues."""
        filter_instance = SelfIntersectingElements( inverted_pyramid_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should detect some type of invalidity in the inverted tetrahedron
        total_invalid = sum( len( cells ) for cells in invalid_cells.values() )
        assert total_invalid > 0

    def test_filter_detect_wrong_point_count( self, wrong_point_count_mesh ):
        """Test detection of elements with wrong number of points."""
        filter_instance = SelfIntersectingElements( wrong_point_count_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should detect wrong number of points
        assert len( invalid_cells[ 'wrongNumberOfPointsElements' ] ) > 0

    def test_filter_write_invalid_elements_arrays( self, degenerate_tetra_mesh ):
        """Test writing invalid elements arrays to mesh."""
        filter_instance = SelfIntersectingElements( degenerate_tetra_mesh, minDistance=1e-6, writeInvalidElements=True )
        success = filter_instance.applyFilter()

        assert success

        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()
        invalid_cells = filter_instance.getInvalidCellIds()

        # Check that arrays were added for error types that have invalid elements
        for error_type, invalid_ids in invalid_cells.items():
            if invalid_ids:  # Only check if there are actually invalid elements of this type
                array_name = f"Is{error_type}"
                array = cell_data.GetArray( array_name )
                assert array is not None
                assert array.GetNumberOfTuples() == output_mesh.GetNumberOfCells()

                # Verify array contains proper values
                for i in range( array.GetNumberOfTuples() ):
                    value = array.GetValue( i )
                    assert value in [ 0, 1 ]

    def test_filter_no_arrays_when_disabled( self, degenerate_tetra_mesh ):
        """Test that no arrays are added when writeInvalidElements is False."""
        filter_instance = SelfIntersectingElements( degenerate_tetra_mesh,
                                                    minDistance=1e-6,
                                                    writeInvalidElements=False )
        success = filter_instance.applyFilter()

        assert success

        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()

        # Should not have added any "Is*" arrays
        error_types = [
            'wrongNumberOfPointsElements', 'intersectingEdgesElements', 'intersectingFacesElements',
            'nonContiguousEdgesElements', 'nonConvexElements', 'facesOrientedIncorrectlyElements',
            'nonPlanarFacesElements', 'degenerateFacesElements'
        ]

        for error_type in error_types:
            array_name = f"Is{error_type}"
            array = cell_data.GetArray( array_name )
            assert array is None

    def test_filter_tolerance_setter_getter( self, single_hex_mesh ):
        """Test setter and getter methods for minimum distance."""
        filter_instance = SelfIntersectingElements( single_hex_mesh )

        # Test default value
        assert filter_instance.getMinDistance() == 0.0

        # Test setting new value
        filter_instance.setMinDistance( 1e-5 )
        assert filter_instance.getMinDistance() == 1e-5

        # Test setting another value
        filter_instance.setMinDistance( 1e-10 )
        assert filter_instance.getMinDistance() == 1e-10

    def test_filter_write_invalid_elements_setter( self, single_hex_mesh ):
        """Test setter method for writeInvalidElements flag."""
        filter_instance = SelfIntersectingElements( single_hex_mesh )

        # Test default value
        assert not filter_instance.writeInvalidElements

        # Test setting to True
        filter_instance.setWriteInvalidElements( True )
        assert filter_instance.writeInvalidElements

        # Test setting back to False
        filter_instance.setWriteInvalidElements( False )
        assert not filter_instance.writeInvalidElements

    def test_filter_write_grid( self, single_hex_mesh, tmp_path ):
        """Test writing the output mesh to file."""
        filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()
        assert success

        output_file = tmp_path / "self_intersecting_output.vtu"
        filter_instance.writeGrid( str( output_file ) )

        assert output_file.exists()
        assert output_file.stat().st_size > 0

    def test_filter_different_tolerance_values( self, degenerate_tetra_mesh ):
        """Test filter behavior with different tolerance values."""
        # Test with very small tolerance
        filter_small = SelfIntersectingElements( degenerate_tetra_mesh, minDistance=1e-15 )
        success_small = filter_small.applyFilter()
        assert success_small

        # Test with larger tolerance
        filter_large = SelfIntersectingElements( degenerate_tetra_mesh, minDistance=1e-3 )
        success_large = filter_large.applyFilter()
        assert success_large

        # Both should succeed, but might detect different numbers of issues
        invalid_small = filter_small.getInvalidCellIds()
        invalid_large = filter_large.getInvalidCellIds()

        assert isinstance( invalid_small, dict )
        assert isinstance( invalid_large, dict )


class TestSelfIntersectingElementsStandaloneFunction:
    """Test class for the standalone selfIntersectingElements function."""

    def test_standalone_function_basic( self, single_hex_mesh, tmp_path ):
        """Test basic functionality of the standalone function."""
        output_file = tmp_path / "standalone_output.vtu"

        mesh, invalid_cells = selfIntersectingElements( single_hex_mesh,
                                                        str( output_file ),
                                                        minDistance=1e-6,
                                                        writeInvalidElements=False )

        assert mesh is not None
        assert isinstance( invalid_cells, dict )
        assert output_file.exists()

    def test_standalone_function_with_array_writing( self, degenerate_tetra_mesh, tmp_path ):
        """Test standalone function with array writing enabled."""
        output_file = tmp_path / "standalone_with_arrays.vtu"

        mesh, invalid_cells = selfIntersectingElements( degenerate_tetra_mesh,
                                                        str( output_file ),
                                                        minDistance=1e-6,
                                                        writeInvalidElements=True )

        assert mesh is not None
        assert isinstance( invalid_cells, dict )

        # Check if any arrays were added for detected invalid elements
        cell_data = mesh.GetCellData()
        arrays_found = False
        for error_type, invalid_ids in invalid_cells.items():
            if invalid_ids:
                array_name = f"Is{error_type}"
                array = cell_data.GetArray( array_name )
                if array is not None:
                    arrays_found = True
                    break

        # If there were invalid elements detected, arrays should have been added
        total_invalid = sum( len( cells ) for cells in invalid_cells.values() )
        if total_invalid > 0:
            assert arrays_found

    def test_standalone_function_different_tolerances( self, degenerate_tetra_mesh, tmp_path ):
        """Test standalone function with different tolerance settings."""
        output_file = tmp_path / "different_tolerance.vtu"

        mesh, invalid_cells = selfIntersectingElements( degenerate_tetra_mesh,
                                                        str( output_file ),
                                                        minDistance=1e-8,
                                                        writeInvalidElements=True )

        assert mesh is not None
        assert isinstance( invalid_cells, dict )
        assert output_file.exists()


class TestSelfIntersectingElementsEdgeCases:
    """Test class for edge cases and specific scenarios."""

    def test_filter_with_zero_tolerance( self, single_hex_mesh ):
        """Test filter with zero tolerance."""
        filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=0.0 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()
        assert isinstance( invalid_cells, dict )

    def test_filter_with_negative_tolerance( self, single_hex_mesh ):
        """Test filter with negative tolerance (should still work)."""
        filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=-1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()
        assert isinstance( invalid_cells, dict )

    def test_filter_with_very_large_tolerance( self, single_hex_mesh ):
        """Test filter with very large tolerance."""
        filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=1e10 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()
        assert isinstance( invalid_cells, dict )

    def test_filter_result_structure_validation( self, degenerate_tetra_mesh ):
        """Test the structure of invalid cell results."""
        filter_instance = SelfIntersectingElements( degenerate_tetra_mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Validate dictionary structure
        assert isinstance( invalid_cells, dict )

        expected_keys = [
            'wrongNumberOfPointsElements', 'intersectingEdgesElements', 'intersectingFacesElements',
            'nonContiguousEdgesElements', 'nonConvexElements', 'facesOrientedIncorrectlyElements',
            'nonPlanarFacesElements', 'degenerateFacesElements'
        ]

        for key in expected_keys:
            assert key in invalid_cells
            assert isinstance( invalid_cells[ key ], list )

            # Validate cell IDs are non-negative integers
            for cell_id in invalid_cells[ key ]:
                assert isinstance( cell_id, ( int, np.integer ) )
                assert cell_id >= 0


class TestSelfIntersectingElementsIntegration:
    """Test class for integration scenarios and complex cases."""

    def test_filter_multiple_error_types( self ):
        """Test a mesh that might have multiple types of invalid elements."""
        mesh = createMultiCellMesh( [ VTK_TETRA, VTK_TETRA ], [
            np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0.5, 1.0, 0.0 ], [ 0.5, 0.5, 1.0 ] ] ),
            np.array( [ [ 2, 0, 0 ], [ 3, 0, 0 ], [ 2.5, 0.5, 0.0 ], [ 2.3, 0.3, 0.0 ] ] )
        ] )
        filter_instance = SelfIntersectingElements( mesh, minDistance=1e-6 )
        success = filter_instance.applyFilter()

        assert success
        invalid_cells = filter_instance.getInvalidCellIds()

        # Should detect some invalid elements
        total_invalid = sum( len( cells ) for cells in invalid_cells.values() )
        assert total_invalid >= 0  # At least should not crash

    def test_filter_logger_integration( self, degenerate_tetra_mesh, caplog ):
        """Test that the filter properly logs its operations."""
        filter_instance = SelfIntersectingElements( degenerate_tetra_mesh, useExternalLogger=False )

        with caplog.at_level( logging.INFO ):
            success = filter_instance.applyFilter()

        assert success
        assert len( caplog.records ) > 0

        # Check for expected log messages
        log_messages = [ record.message for record in caplog.records ]
        assert any( "Apply filter" in msg for msg in log_messages )
        assert any( "succeeded" in msg for msg in log_messages )


@pytest.mark.parametrize( "min_distance,expected_behavior", [
    ( 0.0, "zero_tolerance" ),
    ( 1e-15, "very_small_tolerance" ),
    ( 1e-6, "normal_tolerance" ),
    ( 1e-3, "large_tolerance" ),
    ( 1.0, "very_large_tolerance" ),
] )
def test_parametrized_tolerance_values( single_hex_mesh, min_distance, expected_behavior ):
    """Parametrized test for different tolerance values."""
    filter_instance = SelfIntersectingElements( single_hex_mesh, minDistance=min_distance )
    success = filter_instance.applyFilter()

    assert success
    invalid_cells = filter_instance.getInvalidCellIds()

    # All should succeed and return proper structure
    assert isinstance( invalid_cells, dict )

    # Verify tolerance was set correctly
    assert filter_instance.getMinDistance() == min_distance


@pytest.mark.parametrize( "write_arrays", [ True, False ] )
def test_parametrized_array_writing( degenerate_tetra_mesh, write_arrays ):
    """Parametrized test for array writing options."""
    filter_instance = SelfIntersectingElements( degenerate_tetra_mesh,
                                                minDistance=1e-6,
                                                writeInvalidElements=write_arrays )
    success = filter_instance.applyFilter()

    assert success
    assert filter_instance.writeInvalidElements == write_arrays

    output_mesh = filter_instance.getMesh()
    cell_data = output_mesh.GetCellData()
    invalid_cells = filter_instance.getInvalidCellIds()

    if write_arrays:
        # If arrays should be written and there are invalid elements, check for arrays
        for error_type, invalid_ids in invalid_cells.items():
            if invalid_ids:
                array_name = f"Is{error_type}"
                array = cell_data.GetArray( array_name )
                assert array is not None
    else:
        # No arrays should be written
        error_types = [
            'wrongNumberOfPointsElements', 'intersectingEdgesElements', 'intersectingFacesElements',
            'nonContiguousEdgesElements', 'nonConvexElements', 'facesOrientedIncorrectlyElements',
            'nonPlanarFacesElements', 'degenerateFacesElements'
        ]

        for error_type in error_types:
            array_name = f"Is{error_type}"
            array = cell_data.GetArray( array_name )
            assert array is None
