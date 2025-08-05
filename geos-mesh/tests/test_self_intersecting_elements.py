from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkHexahedron, vtkUnstructuredGrid, VTK_HEXAHEDRON
from geos.mesh.doctor.actions.self_intersecting_elements import Options, mesh_action
from geos.mesh.doctor.filters.SelfIntersectingElements import SelfIntersectingElements
import pytest


def test_jumbled_hex():
    # creating a simple hexahedron
    points = vtkPoints()
    points.SetNumberOfPoints( 8 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 1, 1, 0 ) )
    points.SetPoint( 3, ( 0, 1, 0 ) )
    points.SetPoint( 4, ( 0, 0, 1 ) )
    points.SetPoint( 5, ( 1, 0, 1 ) )
    points.SetPoint( 6, ( 1, 1, 1 ) )
    points.SetPoint( 7, ( 0, 1, 1 ) )

    cell_types = [ VTK_HEXAHEDRON ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 8 )

    hex = vtkHexahedron()
    hex.GetPointIds().SetId( 0, 0 )
    hex.GetPointIds().SetId( 1, 1 )
    hex.GetPointIds().SetId( 2, 3 )  # Intentionally wrong
    hex.GetPointIds().SetId( 3, 2 )  # Intentionally wrong
    hex.GetPointIds().SetId( 4, 4 )
    hex.GetPointIds().SetId( 5, 5 )
    hex.GetPointIds().SetId( 6, 6 )
    hex.GetPointIds().SetId( 7, 7 )
    cells.InsertNextCell( hex )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cell_types, cells )

    result = mesh_action( mesh, Options( min_distance=0. ) )

    assert len( result.intersecting_faces_elements ) == 1
    assert result.intersecting_faces_elements[ 0 ] == 0


@pytest.fixture
def jumbled_hex_mesh():
    """Create a hexahedron with intentionally swapped nodes to create self-intersecting faces."""
    points = vtkPoints()
    points.SetNumberOfPoints( 8 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 1, 1, 0 ) )
    points.SetPoint( 3, ( 0, 1, 0 ) )
    points.SetPoint( 4, ( 0, 0, 1 ) )
    points.SetPoint( 5, ( 1, 0, 1 ) )
    points.SetPoint( 6, ( 1, 1, 1 ) )
    points.SetPoint( 7, ( 0, 1, 1 ) )

    cell_types = [ VTK_HEXAHEDRON ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 8 )

    hex = vtkHexahedron()
    hex.GetPointIds().SetId( 0, 0 )
    hex.GetPointIds().SetId( 1, 1 )
    hex.GetPointIds().SetId( 2, 3 )  # Intentionally wrong
    hex.GetPointIds().SetId( 3, 2 )  # Intentionally wrong
    hex.GetPointIds().SetId( 4, 4 )
    hex.GetPointIds().SetId( 5, 5 )
    hex.GetPointIds().SetId( 6, 6 )
    hex.GetPointIds().SetId( 7, 7 )
    cells.InsertNextCell( hex )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cell_types, cells )
    return mesh


@pytest.fixture
def valid_hex_mesh():
    """Create a properly ordered hexahedron with no self-intersecting faces."""
    points = vtkPoints()
    points.SetNumberOfPoints( 8 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 1, 1, 0 ) )
    points.SetPoint( 3, ( 0, 1, 0 ) )
    points.SetPoint( 4, ( 0, 0, 1 ) )
    points.SetPoint( 5, ( 1, 0, 1 ) )
    points.SetPoint( 6, ( 1, 1, 1 ) )
    points.SetPoint( 7, ( 0, 1, 1 ) )

    cell_types = [ VTK_HEXAHEDRON ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 8 )

    hex = vtkHexahedron()
    for i in range( 8 ):
        hex.GetPointIds().SetId( i, i )
    cells.InsertNextCell( hex )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cell_types, cells )
    return mesh


def test_self_intersecting_elements_filter_detects_invalid_elements( jumbled_hex_mesh ):
    """Test that the SelfIntersectingElements filter correctly detects invalid elements."""
    filter = SelfIntersectingElements()
    filter.setMinDistance( 0.0 )
    filter.SetInputDataObject( 0, jumbled_hex_mesh )
    filter.Update()

    output = filter.getGrid()
    # Check that the filter detected the invalid element
    intersecting_faces = filter.getIntersectingFacesElements()
    assert len( intersecting_faces ) == 1
    assert intersecting_faces[ 0 ] == 0

    # Check that output mesh has same structure
    assert output.GetNumberOfCells() == 1
    assert output.GetNumberOfPoints() == 8


def test_self_intersecting_elements_filter_valid_mesh( valid_hex_mesh ):
    """Test that the SelfIntersectingElements filter finds no issues in a valid mesh."""
    filter = SelfIntersectingElements()
    filter.setMinDistance( 1e-12 )  # Use small tolerance instead of 0.0
    filter.SetInputDataObject( 0, valid_hex_mesh )
    filter.Update()

    output = filter.getGrid()
    # Check that no invalid elements were found
    assert len( filter.getIntersectingFacesElements() ) == 0
    assert len( filter.getWrongNumberOfPointsElements() ) == 0
    assert len( filter.getIntersectingEdgesElements() ) == 0
    assert len( filter.getNonContiguousEdgesElements() ) == 0
    assert len( filter.getNonConvexElements() ) == 0
    assert len( filter.getFacesOrientedIncorrectlyElements() ) == 0

    # Check that output mesh has same structure
    assert output.GetNumberOfCells() == 1
    assert output.GetNumberOfPoints() == 8


def test_self_intersecting_elements_filter_paint_invalid_elements( jumbled_hex_mesh ):
    """Test that the SelfIntersectingElements filter can paint invalid elements."""
    filter = SelfIntersectingElements()
    filter.setMinDistance( 0.0 )
    filter.setPaintInvalidElements( 1 )  # Enable painting
    filter.SetInputDataObject( 0, jumbled_hex_mesh )
    filter.Update()

    output = filter.getGrid()
    # Check that painting arrays were added to the output
    cell_data = output.GetCellData()

    # Should have arrays marking the invalid elements
    # The exact array names depend on the implementation
    assert cell_data.GetNumberOfArrays() > 0

    # Check that invalid elements were detected
    intersecting_faces = filter.getIntersectingFacesElements()
    assert len( intersecting_faces ) == 1


def test_self_intersecting_elements_filter_getters_setters():
    """Test getter and setter methods of the SelfIntersectingElements filter."""
    filter = SelfIntersectingElements()

    # Test min distance getter/setter
    filter.setMinDistance( 0.5 )
    assert filter.getMinDistance() == 0.5

    # Test paint invalid elements setter (no getter available)
    filter.setPaintInvalidElements( 1 )
    # No exception should be raised
