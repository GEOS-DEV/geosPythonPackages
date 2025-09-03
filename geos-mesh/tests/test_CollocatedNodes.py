import pytest
import numpy as np
import os
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_TRIANGLE
from vtkmodules.vtkCommonCore import vtkPoints
from geos.mesh.doctor.actions.generate_cube import XYZ, build_rectilinear_blocks_mesh
from geos.mesh.doctor.filters.CollocatedNodes import CollocatedNodes, collocatedNodes
from geos.mesh.utils.genericHelpers import to_vtk_id_list

__doc__ = """
Test module for CollocatedNodes filter.
Tests the functionality of detecting and handling collocated/duplicated nodes in meshes.
"""


@pytest.fixture( scope="module" )
def mesh_with_collocated_nodes():
    """Fixture for a mesh with exactly duplicated and nearly collocated nodes."""
    x, y, z = np.array( [ 0, 1, 2 ] ), np.array( [ 0, 1 ] ), np.array( [ 0, 1 ] )
    mesh = build_rectilinear_blocks_mesh( [ XYZ( x, y, z ) ] )
    points = mesh.GetPoints()

    # Add nodes to create collocated situations:
    # 1. Exact duplicate of point 0
    points.InsertNextPoint( 0.0, 0.0, 0.0 )
    # 2. Exact duplicate of point 1
    points.InsertNextPoint( 1.0, 0.0, 0.0 )
    # 3. A point very close to an existing point (2, 0, 0)
    points.InsertNextPoint( 2.0, 0.0, 1e-8 )

    return mesh


@pytest.fixture( scope="module" )
def mesh_with_wrong_support():
    """Fixture for a mesh containing a cell with repeated node indices."""
    mesh = vtkUnstructuredGrid()
    points = vtkPoints()
    mesh.SetPoints( points )

    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 0
    points.InsertNextPoint( 1.0, 0.0, 0.0 )  # Point 1
    points.InsertNextPoint( 0.0, 1.0, 0.0 )  # Point 2
    points.InsertNextPoint( 1.0, 1.0, 0.0 )  # Point 3

    # A degenerate triangle with a repeated node [0, 1, 1]
    mesh.InsertNextCell( VTK_TRIANGLE, to_vtk_id_list( [ 0, 1, 1 ] ) )
    # A normal triangle for comparison
    mesh.InsertNextCell( VTK_TRIANGLE, to_vtk_id_list( [ 1, 2, 3 ] ) )

    return mesh


@pytest.fixture( scope="module" )
def clean_mesh():
    """Fixture for a simple, valid mesh with no issues."""
    x, y, z = np.array( [ 0, 1, 2 ] ), np.array( [ 0, 1 ] ), np.array( [ 0, 1 ] )
    return build_rectilinear_blocks_mesh( [ XYZ( x, y, z ) ] )


def test_filter_on_clean_mesh( clean_mesh ):
    """Verify the filter runs correctly on a mesh with no issues."""
    filter_instance = CollocatedNodes( clean_mesh, writeWrongSupportElements=True )
    assert filter_instance.applyFilter()

    # Assert that no issues were found
    assert not filter_instance.getCollocatedNodeBuckets()
    assert not filter_instance.getWrongSupportElements()

    # Assert that no "WrongSupportElements" array was added if none were found
    output_mesh = filter_instance.getMesh()
    assert output_mesh.GetCellData().GetArray( "WrongSupportElements" ) is None


def test_filter_detection_and_bucket_structure( mesh_with_collocated_nodes ):
    """Test basic detection and validate the structure of the result."""
    filter_instance = CollocatedNodes( mesh_with_collocated_nodes, tolerance=1e-7 )
    assert filter_instance.applyFilter()

    collocated_buckets = filter_instance.getCollocatedNodeBuckets()

    # Verify that collocated nodes were detected
    assert len( collocated_buckets ) > 0

    # Verify the structure of the output
    for bucket in collocated_buckets:
        assert isinstance( bucket, tuple )
        assert len( bucket ) >= 2
        for node_id in bucket:
            assert isinstance( node_id, ( int, np.integer ) )
            assert 0 <= node_id < mesh_with_collocated_nodes.GetNumberOfPoints()


@pytest.mark.parametrize(
    "tolerance, expected_min_buckets",
    [
        ( 0.0, 2 ),  # Zero tolerance should only find the 2 exact duplicates.
        ( 1e-10, 2 ),  # Strict tolerance should also only find exacts.
        ( 1e-7, 3 ),  # Looser tolerance should find the "nearby" node as well.
        ( 10.0, 1 )  # Large tolerance should group many nodes together.
    ] )
def test_filter_tolerance_effects( mesh_with_collocated_nodes, tolerance, expected_min_buckets ):
    """Test how different tolerance values affect detection."""
    filter_instance = CollocatedNodes( mesh_with_collocated_nodes, tolerance=tolerance )
    filter_instance.applyFilter()
    collocated_buckets = filter_instance.getCollocatedNodeBuckets()

    # The number of buckets found should be consistent with the tolerance
    assert len( collocated_buckets ) >= expected_min_buckets


def test_filter_wrong_support_elements( mesh_with_wrong_support ):
    """Test the detection of cells with repeated nodes (wrong support)."""
    filter_instance = CollocatedNodes( mesh_with_wrong_support, writeWrongSupportElements=True )
    assert filter_instance.applyFilter()

    # Verify the wrong support element was identified
    wrong_support_elements = filter_instance.getWrongSupportElements()
    assert len( wrong_support_elements ) == 1
    assert 0 in wrong_support_elements

    # Verify the corresponding data array was added to the mesh
    output_mesh = filter_instance.getMesh()
    wrong_support_array = output_mesh.GetCellData().GetArray( "WrongSupportElements" )
    assert wrong_support_array is not None
    assert wrong_support_array.GetNumberOfTuples() == mesh_with_wrong_support.GetNumberOfCells()


def test_filter_mesh_integrity( mesh_with_collocated_nodes ):
    """Ensure the filter only adds data arrays and doesn't alter mesh geometry/topology."""
    original_points = mesh_with_collocated_nodes.GetNumberOfPoints()
    original_cells = mesh_with_collocated_nodes.GetNumberOfCells()

    filter_instance = CollocatedNodes( mesh_with_collocated_nodes )
    filter_instance.applyFilter()
    output_mesh = filter_instance.getMesh()

    assert output_mesh.GetNumberOfPoints() == original_points
    assert output_mesh.GetNumberOfCells() == original_cells


@pytest.mark.parametrize(
    "mesh_fixture, write_support, check_collocated, check_wrong_support",
    [
        # Scenario 1: Find collocated nodes
        ( "mesh_with_collocated_nodes", False, True, False ),
        # Scenario 2: Find wrong support elements
        ( "mesh_with_wrong_support", True, False, True ),
    ] )
def test_standalone_function( tmpdir, request, mesh_fixture, write_support, check_collocated, check_wrong_support ):
    """Test the standalone collocatedNodes wrapper function."""
    # Request the fixture by its name string passed from parametrize
    input_mesh = request.getfixturevalue( mesh_fixture )
    output_path = os.path.join( str( tmpdir ), "output.vtu" )

    output_mesh, buckets, wrong_support = collocatedNodes( input_mesh,
                                                           outputPath=output_path,
                                                           tolerance=1e-6,
                                                           writeWrongSupportElements=write_support )

    # General assertions for all runs
    assert output_mesh is not None
    assert os.path.exists( output_path )

    # Scenario-specific assertions
    if check_collocated:
        assert len( buckets ) > 0
    if check_wrong_support:
        assert len( wrong_support ) > 0
        assert output_mesh.GetCellData().GetArray( "WrongSupportElements" ) is not None
