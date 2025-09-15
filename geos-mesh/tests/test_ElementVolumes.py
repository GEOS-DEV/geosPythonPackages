import pytest
import numpy as np
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TETRA, VTK_TRIANGLE, VTK_HEXAHEDRON
from geos.mesh.utils.genericHelpers import to_vtk_id_list, createSingleCellMesh, createMultiCellMesh
from geos.mesh.doctor.filters.ElementVolumes import ElementVolumes, elementVolumes

__doc__ = """
Test module for ElementVolumes filter.
Tests the functionality of calculating element volumes and detecting problematic elements.
"""


@pytest.fixture( scope="module" )
def simple_hex_mesh():
    """Fixture for a simple hexahedron mesh with known volumes."""
    return createMultiCellMesh( [ VTK_HEXAHEDRON, VTK_HEXAHEDRON ], [
        np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 1, 1, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ], [ 1, 0, 1 ], [ 1, 1, 1 ],
                    [ 0, 1, 1 ] ] ),
        np.array( [ [ 1, 0, 0 ], [ 2, 0, 0 ], [ 2, 1, 0 ], [ 1, 1, 0 ], [ 1, 0, 1 ], [ 2, 0, 1 ], [ 2, 1, 1 ],
                    [ 1, 1, 1 ] ] )
    ] )


@pytest.fixture( scope="module" )
def mesh_with_negative_volume():
    """Fixture for a mesh containing an element with negative volume (inverted tetrahedron)."""
    mesh = vtkUnstructuredGrid()
    points = vtkPoints()
    mesh.SetPoints( points )

    # Create a normal tetrahedron
    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 0
    points.InsertNextPoint( 1.0, 0.0, 0.0 )  # Point 1
    points.InsertNextPoint( 0.0, 1.0, 0.0 )  # Point 2
    points.InsertNextPoint( 0.0, 0.0, 1.0 )  # Point 3

    # Inverted tetrahedron with wrong node ordering (creates negative volume)
    points.InsertNextPoint( 2.0, 0.0, 0.0 )  # Point 4
    points.InsertNextPoint( 3.0, 0.0, 0.0 )  # Point 5
    points.InsertNextPoint( 2.0, 1.0, 0.0 )  # Point 6
    points.InsertNextPoint( 2.0, 0.0, 1.0 )  # Point 7

    # Normal tetrahedron [0, 1, 2, 3]
    mesh.InsertNextCell( VTK_TETRA, to_vtk_id_list( [ 0, 1, 2, 3 ] ) )
    # Inverted tetrahedron [4, 6, 5, 7] - wrong ordering
    mesh.InsertNextCell( VTK_TETRA, to_vtk_id_list( [ 4, 6, 5, 7 ] ) )

    return mesh


@pytest.fixture( scope="module" )
def mesh_with_zero_volume():
    """Fixture for a mesh containing degenerate elements with zero volume."""
    mesh = vtkUnstructuredGrid()
    points = vtkPoints()
    mesh.SetPoints( points )

    # Degenerate tetrahedron - all points in the same plane
    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 0
    points.InsertNextPoint( 1.0, 0.0, 0.0 )  # Point 1
    points.InsertNextPoint( 0.5, 0.5, 0.0 )  # Point 2
    points.InsertNextPoint( 0.2, 0.3, 0.0 )  # Point 3 - all points are coplanar

    # Normal tetrahedron for comparison
    points.InsertNextPoint( 2.0, 0.0, 0.0 )  # Point 4
    points.InsertNextPoint( 3.0, 0.0, 0.0 )  # Point 5
    points.InsertNextPoint( 2.0, 1.0, 0.0 )  # Point 6
    points.InsertNextPoint( 2.0, 0.0, 1.0 )  # Point 7

    # Degenerate tetrahedron (should have zero or near-zero volume)
    mesh.InsertNextCell( VTK_TETRA, to_vtk_id_list( [ 0, 1, 2, 3 ] ) )
    # Normal tetrahedron
    mesh.InsertNextCell( VTK_TETRA, to_vtk_id_list( [ 4, 5, 6, 7 ] ) )

    return mesh


@pytest.fixture( scope="module" )
def mixed_cell_types_mesh():
    """Fixture for a mesh with different cell types."""
    mesh = vtkUnstructuredGrid()
    points = vtkPoints()
    mesh.SetPoints( points )

    # Points for triangle
    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 0
    points.InsertNextPoint( 1.0, 0.0, 0.0 )  # Point 1
    points.InsertNextPoint( 0.5, 1.0, 0.0 )  # Point 2

    # Points for tetrahedron
    points.InsertNextPoint( 2.0, 0.0, 0.0 )  # Point 3
    points.InsertNextPoint( 3.0, 0.0, 0.0 )  # Point 4
    points.InsertNextPoint( 2.5, 1.0, 0.0 )  # Point 5
    points.InsertNextPoint( 2.5, 0.5, 1.0 )  # Point 6

    # Add triangle (2D element)
    mesh.InsertNextCell( VTK_TRIANGLE, to_vtk_id_list( [ 0, 1, 2 ] ) )
    # Add tetrahedron (3D element)
    mesh.InsertNextCell( VTK_TETRA, to_vtk_id_list( [ 3, 4, 5, 6 ] ) )

    return mesh


class TestElementVolumesFilter:
    """Test class for ElementVolumes filter functionality."""

    def test_filter_initialization( self, simple_hex_mesh ):
        """Test basic filter initialization with different parameters."""
        # Test default initialization
        filter_instance = ElementVolumes( simple_hex_mesh )
        assert filter_instance.minVolume == 0.0
        assert not filter_instance.writeIsBelowVolume

        processed_mesh = filter_instance.getMesh()
        assert processed_mesh is not simple_hex_mesh
        assert processed_mesh.GetNumberOfPoints() == simple_hex_mesh.GetNumberOfPoints()
        assert processed_mesh.GetNumberOfCells() == simple_hex_mesh.GetNumberOfCells()

        # Test initialization with custom parameters
        filter_instance = ElementVolumes( simple_hex_mesh,
                                          minVolume=0.5,
                                          writeIsBelowVolume=True,
                                          useExternalLogger=True )
        assert filter_instance.minVolume == 0.5
        assert filter_instance.writeIsBelowVolume

    def test_apply_filter_success( self, simple_hex_mesh ):
        """Test successful filter application on a clean mesh."""
        filter_instance = ElementVolumes( simple_hex_mesh, minVolume=0.0 )
        success = filter_instance.applyFilter()

        assert success
        # Should not have any volumes below threshold of 0.0 for a normal mesh
        below_volumes = filter_instance.getBelowVolumes()
        assert isinstance( below_volumes, list )

    def test_negative_volume_detection( self, mesh_with_negative_volume ):
        """Test detection of elements with negative volumes."""
        filter_instance = ElementVolumes( mesh_with_negative_volume, minVolume=0.0 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # Should detect at least one element with negative volume
        assert len( below_volumes ) > 0

        # Verify structure of results
        for element_id, volume in below_volumes:
            assert isinstance( element_id, int )
            assert isinstance( volume, float )
            assert element_id >= 0
            assert volume < 0.0  # Should be negative

    def test_zero_volume_detection( self, mesh_with_zero_volume ):
        """Test detection of elements with zero or near-zero volumes."""
        filter_instance = ElementVolumes( mesh_with_zero_volume, minVolume=1e-10 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # Should detect the degenerate element
        assert len( below_volumes ) > 0

        # Check that at least one volume is very small
        volumes = [ vol for _, vol in below_volumes ]
        assert any( abs( vol ) < 1e-10 for vol in volumes )

    def test_threshold_filtering( self, simple_hex_mesh ):
        """Test filtering with different volume thresholds."""
        # Test with very high threshold - should catch all elements
        filter_instance = ElementVolumes( simple_hex_mesh, minVolume=100.0 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # With a high threshold, normal unit cubes should be detected
        assert len( below_volumes ) > 0

        # Test with very low threshold - should catch nothing in a normal mesh
        filter_instance = ElementVolumes( simple_hex_mesh, minVolume=-100.0 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()
        assert len( below_volumes ) == 0

    def test_write_below_volume_array( self, mesh_with_negative_volume ):
        """Test addition of below volume threshold array to mesh."""
        filter_instance = ElementVolumes( mesh_with_negative_volume, minVolume=0.0, writeIsBelowVolume=True )
        success = filter_instance.applyFilter()

        assert success

        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()

        # Should have added the below volume array
        expected_array_name = "BelowVolumeThresholdOf0.0"
        below_volume_array = cell_data.GetArray( expected_array_name )

        assert below_volume_array is not None
        assert below_volume_array.GetNumberOfTuples() == output_mesh.GetNumberOfCells()

        # Verify array contains 0s and 1s
        for i in range( below_volume_array.GetNumberOfTuples() ):
            value = below_volume_array.GetValue( i )
            assert value in [ 0, 1 ]

    def test_no_array_added_when_disabled( self, mesh_with_negative_volume ):
        """Test that no array is added when writeIsBelowVolume is False."""
        # FIX: Create a deep copy to prevent tests from interfering with each other.
        # This solves the state leakage issue from the module-scoped fixture.
        mesh_copy = vtkUnstructuredGrid()
        mesh_copy.DeepCopy( mesh_with_negative_volume )

        filter_instance = ElementVolumes( mesh_copy, minVolume=0.0, writeIsBelowVolume=False )
        success = filter_instance.applyFilter()
        assert success

        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()

        expected_array_name = "BelowVolumeThresholdOf0.0"
        below_volume_array = cell_data.GetArray( expected_array_name )
        assert below_volume_array is None

    def test_mixed_cell_types( self, mixed_cell_types_mesh ):
        """Test filter behavior with mixed cell types."""
        filter_instance = ElementVolumes( mixed_cell_types_mesh, minVolume=0.0 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # Should handle mixed cell types without crashing
        assert isinstance( below_volumes, list )

    def test_get_volumes_method( self, simple_hex_mesh ):
        """Test the getVolumes method returns proper volume data."""
        filter_instance = ElementVolumes( simple_hex_mesh )

        # Before applying filter, volumes should be None
        assert filter_instance.getVolumes() is None

        success = filter_instance.applyFilter()
        assert success

        # After applying filter, should still be None as this method
        # is not implemented to return the actual volume array
        volumes = filter_instance.getVolumes()
        assert volumes is None  # Current implementation returns None

    def test_set_write_below_volume( self, simple_hex_mesh ):
        """Test the setWriteIsBelowVolume method."""
        filter_instance = ElementVolumes( simple_hex_mesh )

        # Initially False
        assert not filter_instance.writeIsBelowVolume

        # Set to True
        filter_instance.setWriteIsBelowVolume( True )
        assert filter_instance.writeIsBelowVolume

        # Set back to False
        filter_instance.setWriteIsBelowVolume( False )
        assert not filter_instance.writeIsBelowVolume

    def test_write_grid_functionality( self, simple_hex_mesh, tmp_path ):
        """Test writing the output mesh to file."""
        filter_instance = ElementVolumes( simple_hex_mesh )
        success = filter_instance.applyFilter()
        assert success

        # Write to temporary file
        output_file = tmp_path / "test_output.vtu"
        filter_instance.writeGrid( str( output_file ) )

        # Verify file was created
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestElementVolumesStandaloneFunction:
    """Test class for the standalone elementVolumes function."""

    def test_standalone_function_basic( self, simple_hex_mesh, tmp_path ):
        """Test basic functionality of the standalone elementVolumes function."""
        output_file = tmp_path / "standalone_output.vtu"

        mesh, volumes, below_volumes = elementVolumes( simple_hex_mesh,
                                                       str( output_file ),
                                                       minVolume=0.0,
                                                       writeIsBelowVolume=False )

        # Verify return values
        assert mesh is not None
        assert isinstance( mesh, vtkUnstructuredGrid )
        assert volumes is None  # Current implementation returns None
        assert isinstance( below_volumes, list )

        # Verify file was written
        assert output_file.exists()

    def test_standalone_function_with_below_volume_writing( self, mesh_with_negative_volume, tmp_path ):
        """Test standalone function with below volume writing enabled."""
        output_file = tmp_path / "standalone_with_array.vtu"

        mesh, volumes, below_volumes = elementVolumes( mesh_with_negative_volume,
                                                       str( output_file ),
                                                       minVolume=0.0,
                                                       writeIsBelowVolume=True )

        assert mesh is not None
        assert len( below_volumes ) > 0

        # Check that the array was added
        expected_array_name = "BelowVolumeThresholdOf0.0"
        below_volume_array = mesh.GetCellData().GetArray( expected_array_name )
        assert below_volume_array is not None

    def test_standalone_function_error_handling( self, tmp_path ):
        """Test error handling in the standalone function."""
        empty_mesh = vtkUnstructuredGrid()
        output_file = tmp_path / "error_test.vtu"

        # FIX: The test should now expect a ValueError during initialization,
        # which is better "fail-fast" behavior.
        with pytest.raises( ValueError, match="Input 'mesh' cannot be empty." ):
            elementVolumes( empty_mesh, str( output_file ), minVolume=0.0, writeIsBelowVolume=False )

    def test_standalone_function_with_threshold( self, simple_hex_mesh, tmp_path ):
        """Test standalone function with different volume thresholds."""
        output_file = tmp_path / "threshold_test.vtu"

        # Test with high threshold
        mesh, volumes, below_volumes = elementVolumes(
            simple_hex_mesh,
            str( output_file ),
            minVolume=10.0,  # High threshold
            writeIsBelowVolume=True )

        # Should detect elements below the high threshold
        assert len( below_volumes ) > 0

        # Check that the array reflects the threshold
        expected_array_name = "BelowVolumeThresholdOf10.0"
        below_volume_array = mesh.GetCellData().GetArray( expected_array_name )
        assert below_volume_array is not None


class TestElementVolumesEdgeCases:
    """Test class for edge cases and error conditions."""

    def test_empty_mesh( self ):
        """Test behavior with an empty mesh."""
        empty_mesh = vtkUnstructuredGrid()
        with pytest.raises( ValueError, match="Input 'mesh' cannot be empty." ):
            ElementVolumes( empty_mesh )

    def test_single_cell_mesh( self ):
        """Test with a mesh containing only one cell."""
        mesh = createSingleCellMesh( VTK_TETRA, np.array( [ [ 0, 0, 0 ], [ 1, 0, 0 ], [ 0, 1, 0 ], [ 0, 0, 1 ] ] ) )
        filter_instance = ElementVolumes( mesh, minVolume=0.0 )
        success = filter_instance.applyFilter()
        assert success

        below_volumes = filter_instance.getBelowVolumes()
        assert isinstance( below_volumes, list )

    def test_very_small_volumes( self, mesh_with_zero_volume ):
        """Test with extremely small volume thresholds."""
        filter_instance = ElementVolumes( mesh_with_zero_volume, minVolume=1e-15 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # Should still be able to detect volumes below extremely small thresholds
        assert isinstance( below_volumes, list )

    def test_very_large_volumes( self, simple_hex_mesh ):
        """Test with very large volume thresholds."""
        filter_instance = ElementVolumes( simple_hex_mesh, minVolume=1e10 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # All elements should be below this huge threshold
        assert len( below_volumes ) == simple_hex_mesh.GetNumberOfCells()

    def test_negative_threshold( self, mesh_with_negative_volume ):
        """Test with negative volume threshold."""
        filter_instance = ElementVolumes( mesh_with_negative_volume, minVolume=-0.5 )
        success = filter_instance.applyFilter()

        assert success
        below_volumes = filter_instance.getBelowVolumes()

        # Only volumes below -0.5 should be detected
        for _, volume in below_volumes:
            assert volume < -0.5


@pytest.mark.parametrize( "min_volume,expected_behavior", [
    ( 0.0, "detect_negative_and_zero" ),
    ( 1.1, "detect_small_positive" ),
    ( -1.0, "detect_very_negative" ),
    ( 1e-10, "detect_near_zero" ),
] )
def test_parametrized_volume_thresholds( simple_hex_mesh, min_volume, expected_behavior ):
    """Parametrized test for different volume thresholds."""
    filter_instance = ElementVolumes( simple_hex_mesh, minVolume=min_volume )
    success = filter_instance.applyFilter()

    assert success
    below_volumes = filter_instance.getBelowVolumes()

    if expected_behavior == "detect_small_positive":
        # Unit cubes with volume 1.0 should be below a threshold of 1.1
        assert len( below_volumes ) > 0
    else:
        # None of the other conditions should be met by the simple_hex_mesh
        assert len( below_volumes ) == 0


def test_logger_integration( simple_hex_mesh, caplog ):
    """Test that the filter properly logs its operations."""
    filter_instance = ElementVolumes( simple_hex_mesh, useExternalLogger=False )

    with caplog.at_level( "INFO" ):
        success = filter_instance.applyFilter()

    assert success
    # Check that some logging occurred
    assert len( caplog.records ) > 0

    # Check for expected log messages
    log_messages = [ record.message for record in caplog.records ]
    assert any( "Apply filter" in msg for msg in log_messages )
    assert any( "succeeded" in msg for msg in log_messages )
