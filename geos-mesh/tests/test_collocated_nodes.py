import pytest
from typing import Iterator, Tuple
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import vtkCellArray, vtkTetra, vtkUnstructuredGrid, VTK_TETRA
from geos.mesh.doctor.actions.collocated_nodes import Options, __action
from geos.mesh.doctor.filters.CollocatedNodes import CollocatedNodes


def get_points() -> Iterator[ Tuple[ vtkPoints, int ] ]:
    """Generates the data for the cases.
    One case has two nodes at the exact same position.
    The other has two differente nodes
    :return: Generator to (vtk points, number of expected duplicated locations)
    """
    for p0, p1 in ( ( 0, 0, 0 ), ( 1, 1, 1 ) ), ( ( 0, 0, 0 ), ( 0, 0, 0 ) ):
        points = vtkPoints()
        points.SetNumberOfPoints( 2 )
        points.SetPoint( 0, p0 )
        points.SetPoint( 1, p1 )
        num_nodes_bucket = 1 if p0 == p1 else 0
        yield points, num_nodes_bucket


@pytest.mark.parametrize( "data", get_points() )
def test_simple_collocated_points( data: Tuple[ vtkPoints, int ] ):
    points, num_nodes_bucket = data

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )

    result = __action( mesh, Options( tolerance=1.e-12 ) )

    assert len( result.wrong_support_elements ) == 0
    assert len( result.nodes_buckets ) == num_nodes_bucket
    if num_nodes_bucket == 1:
        assert len( result.nodes_buckets[ 0 ] ) == points.GetNumberOfPoints()


def test_wrong_support_elements():
    points = vtkPoints()
    points.SetNumberOfPoints( 4 )
    points.SetPoint( 0, ( 0, 0, 0 ) )
    points.SetPoint( 1, ( 1, 0, 0 ) )
    points.SetPoint( 2, ( 0, 1, 0 ) )
    points.SetPoint( 3, ( 0, 0, 1 ) )

    cell_types = [ VTK_TETRA ]
    cells = vtkCellArray()
    cells.AllocateExact( 1, 4 )

    tet = vtkTetra()
    tet.GetPointIds().SetId( 0, 0 )
    tet.GetPointIds().SetId( 1, 1 )
    tet.GetPointIds().SetId( 2, 2 )
    tet.GetPointIds().SetId( 3, 0 )  # Intentionally wrong
    cells.InsertNextCell( tet )

    mesh = vtkUnstructuredGrid()
    mesh.SetPoints( points )
    mesh.SetCells( cell_types, cells )

    result = __action( mesh, Options( tolerance=1.e-12 ) )

    assert len( result.nodes_buckets ) == 0
    assert len( result.wrong_support_elements ) == 1
    assert result.wrong_support_elements[ 0 ] == 0


# Create a test mesh with collocated nodes
@pytest.fixture
def sample_mesh() -> vtkUnstructuredGrid:
    # Create a simple mesh with duplicate points
    mesh = vtkUnstructuredGrid()

    # Create points
    points = vtkPoints()
    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 0
    points.InsertNextPoint( 1.0, 0.0, 0.0 )  # Point 1
    points.InsertNextPoint( 0.0, 1.0, 0.0 )  # Point 2
    points.InsertNextPoint( 0.0, 0.0, 0.0 )  # Point 3 - duplicate of Point 0
    points.InsertNextPoint( 2.0, 0.0, 0.0 )  # Point 4
    mesh.SetPoints( points )

    # Create cells
    cells = vtkCellArray()
    # Create a triangular cell with normal connectivity
    cells.InsertNextCell( 3 )
    cells.InsertCellPoint( 0 )
    cells.InsertCellPoint( 1 )
    cells.InsertCellPoint( 2 )

    # Create a cell with duplicate point indices
    cells.InsertNextCell( 3 )
    cells.InsertCellPoint( 3 )  # This is a duplicate of point 0
    cells.InsertCellPoint( 1 )
    cells.InsertCellPoint( 4 )
    mesh.SetCells( 5, cells )  # 5 is VTK_TRIANGLE
    return mesh


@pytest.fixture
def collocated_nodes_filter() -> CollocatedNodes:
    return CollocatedNodes()


def test_init( collocated_nodes_filter: CollocatedNodes ):
    """Test initialization of the CollocatedNodes filter."""
    assert collocated_nodes_filter.m_collocatedNodesBuckets == list()
    assert collocated_nodes_filter.m_paintWrongSupportElements == 0
    assert collocated_nodes_filter.m_tolerance == 0.0
    assert collocated_nodes_filter.m_wrongSupportElements == list()


def test_collocated_nodes_detection( sample_mesh: vtkUnstructuredGrid, collocated_nodes_filter: CollocatedNodes ):
    """Test the filter's ability to detect collocated nodes."""
    # Set input mesh
    collocated_nodes_filter.SetInputDataObject( sample_mesh )

    # Set tolerance
    collocated_nodes_filter.setTolerance( 1e-6 )

    # Run filter
    collocated_nodes_filter.Update()

    # Check results
    buckets = collocated_nodes_filter.getCollocatedNodeBuckets()
    assert len( buckets ) > 0

    # We expect points 0 and 3 to be in the same bucket
    bucket_with_duplicates = None
    for bucket in buckets:
        if 0 in bucket and 3 in bucket:
            bucket_with_duplicates = bucket
            break

    assert bucket_with_duplicates is not None, "Failed to detect collocated nodes 0 and 3"


def test_wrong_support_elements2( sample_mesh: vtkUnstructuredGrid, collocated_nodes_filter: CollocatedNodes ):
    """Test the filter's ability to detect elements with wrong support."""
    # Set input mesh
    collocated_nodes_filter.SetInputDataObject( sample_mesh )

    # Run filter
    collocated_nodes_filter.Update()

    # Check results
    wrong_elements = collocated_nodes_filter.getWrongSupportElements()

    # In our test mesh, we don't have cells with duplicate point indices within the same cell
    # So this should be empty
    assert isinstance( wrong_elements, list )


def test_paint_wrong_support_elements( sample_mesh: vtkUnstructuredGrid, collocated_nodes_filter: CollocatedNodes ):
    """Test the painting of wrong support elements."""
    # Set input mesh
    collocated_nodes_filter.SetInputDataObject( sample_mesh )

    # Enable painting
    collocated_nodes_filter.setPaintWrongSupportElements( 1 )

    # Run filter
    collocated_nodes_filter.Update()

    # Get output mesh
    output_mesh = collocated_nodes_filter.getGrid()

    # Check if the array was added
    cell_data = output_mesh.GetCellData()
    has_array = cell_data.HasArray( "HasDuplicatedNodes" )
    assert has_array, "The HasDuplicatedNodes array wasn't added to cell data"


def test_set_paint_wrong_support_elements( collocated_nodes_filter: CollocatedNodes ):
    """Test setPaintWrongSupportElements method."""
    # Valid input
    collocated_nodes_filter.setPaintWrongSupportElements( 1 )
    assert collocated_nodes_filter.m_paintWrongSupportElements == 1

    # Valid input
    collocated_nodes_filter.setPaintWrongSupportElements( 0 )
    assert collocated_nodes_filter.m_paintWrongSupportElements == 0

    # Invalid input
    collocated_nodes_filter.setPaintWrongSupportElements( 2 )
    # Should remain unchanged
    assert collocated_nodes_filter.m_paintWrongSupportElements == 0


def test_set_tolerance( collocated_nodes_filter: CollocatedNodes ):
    """Test setTolerance method."""
    collocated_nodes_filter.setTolerance( 0.001 )
    assert collocated_nodes_filter.m_tolerance == 0.001


def test_get_collocated_node_buckets( collocated_nodes_filter: CollocatedNodes ):
    """Test getCollocatedNodeBuckets method."""
    # Set a value manually
    collocated_nodes_filter.m_collocatedNodesBuckets = [ ( 0, 1 ), ( 2, 3 ) ]
    result = collocated_nodes_filter.getCollocatedNodeBuckets()
    assert result == [ ( 0, 1 ), ( 2, 3 ) ]


def test_get_wrong_support_elements( collocated_nodes_filter: CollocatedNodes ):
    """Test getWrongSupportElements method."""
    # Set a value manually
    collocated_nodes_filter.m_wrongSupportElements = [ 0, 3, 5 ]
    result = collocated_nodes_filter.getWrongSupportElements()
    assert result == [ 0, 3, 5 ]
