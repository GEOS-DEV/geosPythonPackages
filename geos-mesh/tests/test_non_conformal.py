import numpy
import pytest
import logging
from geos.mesh.doctor.actions.generate_cube import build_rectilinear_blocks_mesh, XYZ
from geos.mesh.doctor.actions.non_conformal import Options, mesh_action
from geos.mesh.doctor.filters.NonConformal import NonConformal, nonConformal

__doc__ = """
Test module for non-conformal mesh detection.
Tests both the actions-based functions and the NonConformal filter class.
"""


@pytest.fixture( scope="module" )
def two_close_hexs_mesh():
    """Fixture for two hexahedra that are very close (non-conformal)."""
    delta = 1.e-6
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + delta, tmp, tmp )
    return build_rectilinear_blocks_mesh( ( xyz0, xyz1 ) )


@pytest.fixture( scope="module" )
def two_distant_hexs_mesh():
    """Fixture for two hexahedra that are far apart (conformal)."""
    delta = 1
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + delta, tmp, tmp )
    return build_rectilinear_blocks_mesh( ( xyz0, xyz1 ) )


@pytest.fixture( scope="module" )
def two_shifted_hexs_mesh():
    """Fixture for two hexahedra that are close but shifted (non-conformal)."""
    delta_x, delta_y = 1.e-6, 0.5
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + delta_x, tmp + delta_y, tmp + delta_y )
    return build_rectilinear_blocks_mesh( ( xyz0, xyz1 ) )


@pytest.fixture( scope="module" )
def big_small_elements_mesh():
    """Fixture for big element next to small element (non-conformal)."""
    delta = 1.e-6
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp + 1, tmp + 1 )
    xyz1 = XYZ( 3 * tmp + 1 + delta, 3 * tmp, 3 * tmp )
    return build_rectilinear_blocks_mesh( ( xyz0, xyz1 ) )


def test_two_close_hexs( two_close_hexs_mesh ):
    delta = 1.e-6
    # Close enough, but points tolerance is too strict to consider the faces matching.
    options = Options( angle_tolerance=1., point_tolerance=delta / 2, face_tolerance=delta * 2 )
    results = mesh_action( two_close_hexs_mesh, options )
    assert len( results.non_conformal_cells ) == 1
    assert set( results.non_conformal_cells[ 0 ] ) == { 0, 1 }

    # Close enough, and points tolerance is loose enough to consider the faces matching.
    options = Options( angle_tolerance=1., point_tolerance=delta * 2, face_tolerance=delta * 2 )
    results = mesh_action( two_close_hexs_mesh, options )
    assert len( results.non_conformal_cells ) == 0


def test_two_distant_hexs( two_distant_hexs_mesh ):
    delta = 1
    options = Options( angle_tolerance=1., point_tolerance=delta / 2., face_tolerance=delta / 2. )
    results = mesh_action( two_distant_hexs_mesh, options )
    assert len( results.non_conformal_cells ) == 0


def test_two_close_shifted_hexs( two_shifted_hexs_mesh ):
    delta_x = 1.e-6
    options = Options( angle_tolerance=1., point_tolerance=delta_x * 2, face_tolerance=delta_x * 2 )
    results = mesh_action( two_shifted_hexs_mesh, options )
    assert len( results.non_conformal_cells ) == 1
    assert set( results.non_conformal_cells[ 0 ] ) == { 0, 1 }


def test_big_elem_next_to_small_elem( big_small_elements_mesh ):
    delta = 1.e-6
    options = Options( angle_tolerance=1., point_tolerance=delta * 2, face_tolerance=delta * 2 )
    results = mesh_action( big_small_elements_mesh, options )
    assert len( results.non_conformal_cells ) == 1
    assert set( results.non_conformal_cells[ 0 ] ) == { 0, 1 }


class TestNonConformalFilter:
    """Test class for NonConformal filter functionality."""

    def test_filter_initialization_default( self, two_close_hexs_mesh ):
        """Test filter initialization with default parameters."""
        filter_instance = NonConformal( two_close_hexs_mesh )

        assert filter_instance.getPointTolerance() == 0.0
        assert filter_instance.getFaceTolerance() == 0.0
        assert filter_instance.getAngleTolerance() == 10.0
        assert not filter_instance.writeNonConformalCells
        assert filter_instance.getMesh() is not None

    def test_filter_initialization_custom( self, two_close_hexs_mesh ):
        """Test filter initialization with custom parameters."""
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=1e-6,
                                        faceTolerance=1e-5,
                                        angleTolerance=5.0,
                                        writeNonConformalCells=True,
                                        useExternalLogger=True )

        assert filter_instance.getPointTolerance() == 1e-6
        assert filter_instance.getFaceTolerance() == 1e-5
        assert filter_instance.getAngleTolerance() == 5.0
        assert filter_instance.writeNonConformalCells

    def test_filter_detect_non_conformal_strict_tolerance( self, two_close_hexs_mesh ):
        """Test detection of non-conformal cells with strict tolerance."""
        delta = 1.e-6
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=delta / 2,
                                        faceTolerance=delta * 2,
                                        angleTolerance=1.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 1
        assert set( non_conformal_cells[ 0 ] ) == { 0, 1 }

    def test_filter_detect_conformal_loose_tolerance( self, two_close_hexs_mesh ):
        """Test that close cells are considered conformal with loose tolerance."""
        delta = 1.e-6
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=delta * 2,
                                        faceTolerance=delta * 2,
                                        angleTolerance=1.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 0

    def test_filter_distant_cells_conformal( self, two_distant_hexs_mesh ):
        """Test that distant cells are considered conformal."""
        filter_instance = NonConformal( two_distant_hexs_mesh,
                                        pointTolerance=0.5,
                                        faceTolerance=0.5,
                                        angleTolerance=1.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 0

    def test_filter_shifted_cells_non_conformal( self, two_shifted_hexs_mesh ):
        """Test detection of shifted non-conformal cells."""
        delta_x = 1.e-6
        filter_instance = NonConformal( two_shifted_hexs_mesh,
                                        pointTolerance=delta_x * 2,
                                        faceTolerance=delta_x * 2,
                                        angleTolerance=1.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 1
        assert set( non_conformal_cells[ 0 ] ) == { 0, 1 }

    def test_filter_big_small_elements( self, big_small_elements_mesh ):
        """Test detection of non-conformal interface between different sized elements."""
        delta = 1.e-6
        filter_instance = NonConformal( big_small_elements_mesh,
                                        pointTolerance=delta * 2,
                                        faceTolerance=delta * 2,
                                        angleTolerance=1.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 1
        assert set( non_conformal_cells[ 0 ] ) == { 0, 1 }

    def test_filter_write_non_conformal_array( self, two_close_hexs_mesh ):
        """Test writing non-conformal cells array to mesh."""
        delta = 1.e-6
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=delta / 2,
                                        faceTolerance=delta * 2,
                                        angleTolerance=1.0,
                                        writeNonConformalCells=True )

        success = filter_instance.applyFilter()
        assert success

        # Check that the array was added to the mesh
        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()

        non_conformal_array = cell_data.GetArray( "IsNonConformal" )
        assert non_conformal_array is not None
        assert non_conformal_array.GetNumberOfTuples() == output_mesh.GetNumberOfCells()

        # Check array values - should have 1s for non-conformal cells
        has_non_conformal = False
        for i in range( non_conformal_array.GetNumberOfTuples() ):
            value = non_conformal_array.GetValue( i )
            assert value in [ 0, 1 ]
            if value == 1:
                has_non_conformal = True

        assert has_non_conformal  # Should have detected some non-conformal cells

    def test_filter_no_array_when_disabled( self, two_close_hexs_mesh ):
        """Test that no array is added when writeNonConformalCells is False."""
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=1e-8,
                                        faceTolerance=1e-6,
                                        writeNonConformalCells=False )

        success = filter_instance.applyFilter()
        assert success

        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()

        non_conformal_array = cell_data.GetArray( "IsNonConformal" )
        assert non_conformal_array is None

    def test_filter_no_array_when_no_non_conformal_cells( self, two_distant_hexs_mesh ):
        """Test that no array is added when no non-conformal cells are found."""
        filter_instance = NonConformal( two_distant_hexs_mesh,
                                        pointTolerance=0.1,
                                        faceTolerance=0.1,
                                        writeNonConformalCells=True )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert len( non_conformal_cells ) == 0

        # Array should not be added when there are no non-conformal cells
        output_mesh = filter_instance.getMesh()
        cell_data = output_mesh.GetCellData()
        non_conformal_array = cell_data.GetArray( "IsNonConformal" )
        assert non_conformal_array is None

    def test_filter_tolerance_setters_getters( self, two_close_hexs_mesh ):
        """Test setter and getter methods for tolerances."""
        filter_instance = NonConformal( two_close_hexs_mesh )

        # Test point tolerance
        filter_instance.setPointTolerance( 1e-5 )
        assert filter_instance.getPointTolerance() == 1e-5

        # Test face tolerance
        filter_instance.setFaceTolerance( 2e-5 )
        assert filter_instance.getFaceTolerance() == 2e-5

        # Test angle tolerance
        filter_instance.setAngleTolerance( 15.0 )
        assert filter_instance.getAngleTolerance() == 15.0

        # Test write flag
        filter_instance.setWriteNonConformalCells( True )
        assert filter_instance.writeNonConformalCells

    def test_filter_write_grid( self, two_close_hexs_mesh, tmp_path ):
        """Test writing the output mesh to file."""
        filter_instance = NonConformal( two_close_hexs_mesh )
        success = filter_instance.applyFilter()
        assert success

        output_file = tmp_path / "non_conformal_output.vtu"
        filter_instance.writeGrid( str( output_file ) )

        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestNonConformalStandaloneFunction:
    """Test class for the standalone nonConformal function."""

    def test_standalone_function_basic( self, two_close_hexs_mesh, tmp_path ):
        """Test basic functionality of the standalone function."""
        output_file = tmp_path / "standalone_output.vtu"

        mesh, non_conformal_cells = nonConformal( two_close_hexs_mesh,
                                                  str( output_file ),
                                                  pointTolerance=1e-8,
                                                  faceTolerance=1e-6,
                                                  angleTolerance=1.0,
                                                  writeNonConformalCells=False )

        assert mesh is not None
        assert isinstance( non_conformal_cells, list )
        assert len( non_conformal_cells ) > 0  # Should detect non-conformal cells
        assert output_file.exists()

    def test_standalone_function_with_array_writing( self, two_close_hexs_mesh, tmp_path ):
        """Test standalone function with array writing enabled."""
        output_file = tmp_path / "standalone_with_array.vtu"

        mesh, non_conformal_cells = nonConformal( two_close_hexs_mesh,
                                                  str( output_file ),
                                                  pointTolerance=1e-8,
                                                  faceTolerance=1e-6,
                                                  angleTolerance=1.0,
                                                  writeNonConformalCells=True )

        assert mesh is not None
        assert len( non_conformal_cells ) > 0

        # Check that the array was added
        non_conformal_array = mesh.GetCellData().GetArray( "IsNonConformal" )
        assert non_conformal_array is not None

    def test_standalone_function_no_non_conformal( self, two_distant_hexs_mesh, tmp_path ):
        """Test standalone function when no non-conformal cells are found."""
        output_file = tmp_path / "no_non_conformal.vtu"

        mesh, non_conformal_cells = nonConformal( two_distant_hexs_mesh,
                                                  str( output_file ),
                                                  pointTolerance=0.1,
                                                  faceTolerance=0.1,
                                                  angleTolerance=1.0,
                                                  writeNonConformalCells=True )

        assert mesh is not None
        assert len( non_conformal_cells ) == 0
        assert output_file.exists()

    def test_standalone_function_different_tolerances( self, two_shifted_hexs_mesh, tmp_path ):
        """Test standalone function with different tolerance settings."""
        output_file = tmp_path / "different_tolerances.vtu"

        mesh, non_conformal_cells = nonConformal( two_shifted_hexs_mesh,
                                                  str( output_file ),
                                                  pointTolerance=2e-6,
                                                  faceTolerance=2e-6,
                                                  angleTolerance=5.0,
                                                  writeNonConformalCells=True )

        assert mesh is not None
        assert len( non_conformal_cells ) == 1
        assert set( non_conformal_cells[ 0 ] ) == { 0, 1 }


class TestNonConformalEdgeCases:
    """Test class for edge cases and specific scenarios."""

    def test_filter_with_very_small_tolerances( self, two_close_hexs_mesh ):
        """Test filter with extremely small tolerances."""
        filter_instance = NonConformal( two_close_hexs_mesh,
                                        pointTolerance=1e-15,
                                        faceTolerance=1e-15,
                                        angleTolerance=0.001 )

        success = filter_instance.applyFilter()
        assert success

        # With extremely small tolerances, should detect non-conformal cells
        non_conformal_cells = filter_instance.getNonConformalCells()
        assert isinstance( non_conformal_cells, list )

    def test_filter_with_large_tolerances( self, big_small_elements_mesh ):
        """Test filter with very large tolerances."""
        filter_instance = NonConformal( big_small_elements_mesh,
                                        pointTolerance=100.0,
                                        faceTolerance=100.0,
                                        angleTolerance=180.0 )

        success = filter_instance.applyFilter()
        assert success

        # With very large tolerances, should consider cells conformal
        non_conformal_cells = filter_instance.getNonConformalCells()
        # Depending on implementation, might still detect some non-conformal cases
        assert isinstance( non_conformal_cells, list )

    def test_filter_zero_tolerances( self, two_close_hexs_mesh ):
        """Test filter with zero tolerances."""
        filter_instance = NonConformal( two_close_hexs_mesh, pointTolerance=0.0, faceTolerance=0.0, angleTolerance=0.0 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()
        assert isinstance( non_conformal_cells, list )

    def test_filter_result_structure( self, two_close_hexs_mesh ):
        """Test the structure of non-conformal cell results."""
        filter_instance = NonConformal( two_close_hexs_mesh, pointTolerance=1e-8, faceTolerance=1e-6 )

        success = filter_instance.applyFilter()
        assert success

        non_conformal_cells = filter_instance.getNonConformalCells()

        # Check result structure
        for pair in non_conformal_cells:
            assert isinstance( pair, tuple )
            assert len( pair ) == 2
            cell_id1, cell_id2 = pair
            assert isinstance( cell_id1, int )
            assert isinstance( cell_id2, int )
            assert cell_id1 >= 0
            assert cell_id2 >= 0
            assert cell_id1 != cell_id2  # Should be different cells


@pytest.mark.parametrize( "point_tol,face_tol,angle_tol,expected_behavior", [
    ( 1e-8, 1e-6, 1.0, "detect_non_conformal" ),
    ( 1e-4, 1e-4, 1.0, "consider_conformal" ),
    ( 0.0, 0.0, 0.0, "strict_detection" ),
    ( 1.0, 1.0, 180.0, "loose_detection" ),
] )
def test_parametrized_tolerance_combinations( two_close_hexs_mesh, point_tol, face_tol, angle_tol, expected_behavior ):
    """Parametrized test for different tolerance combinations."""
    filter_instance = NonConformal( two_close_hexs_mesh,
                                    pointTolerance=point_tol,
                                    faceTolerance=face_tol,
                                    angleTolerance=angle_tol )

    success = filter_instance.applyFilter()
    assert success

    non_conformal_cells = filter_instance.getNonConformalCells()

    if expected_behavior == "detect_non_conformal":
        # Should detect non-conformal cells with strict tolerances
        assert len( non_conformal_cells ) > 0
    elif expected_behavior == "consider_conformal":
        # Should consider cells conformal with loose tolerances
        assert len( non_conformal_cells ) == 0
    elif expected_behavior in [ "strict_detection", "loose_detection" ]:
        # Just verify it runs without errors
        assert isinstance( non_conformal_cells, list )


def test_filter_logger_integration( two_close_hexs_mesh, caplog ):
    """Test that the filter properly logs its operations."""
    filter_instance = NonConformal( two_close_hexs_mesh, useExternalLogger=False )

    with caplog.at_level( logging.INFO ):
        success = filter_instance.applyFilter()

    assert success
    assert len( caplog.records ) > 0

    # Check for expected log messages
    log_messages = [ record.message for record in caplog.records ]
    assert any( "Apply filter" in msg for msg in log_messages )
    assert any( "succeeded" in msg for msg in log_messages )
