import pytest
from geos.mesh.doctor.actions.generate_cube import FieldInfo, Options, __build
from geos.mesh.doctor.filters.GenerateRectilinearGrid import GenerateRectilinearGrid, generateRectilinearGrid


def test_generate_cube():
    options = Options( vtk_output=None,
                       generate_cells_global_ids=True,
                       generate_points_global_ids=False,
                       xs=( 0, 5, 10 ),
                       ys=( 0, 4, 8 ),
                       zs=( 0, 1 ),
                       nxs=( 5, 2 ),
                       nys=( 1, 1 ),
                       nzs=( 1, ),
                       fields=( FieldInfo( name="test", dimension=2, support="CELLS" ), ) )
    output = __build( options )
    assert output.GetNumberOfCells() == 14
    assert output.GetNumberOfPoints() == 48
    assert output.GetCellData().GetArray( "test" ).GetNumberOfComponents() == 2
    assert output.GetCellData().GetGlobalIds()
    assert not output.GetPointData().GetGlobalIds()


def test_generate_rectilinear_grid_filter():
    """Test the GenerateRectilinearGrid filter class."""
    # Create filter instance
    filter_instance = GenerateRectilinearGrid( generateCellsGlobalIds=True, generatePointsGlobalIds=True )

    # Set coordinates and number of elements
    filter_instance.setCoordinates( [ 0.0, 5.0, 10.0 ], [ 0.0, 5.0, 10.0 ], [ 0.0, 10.0 ] )
    filter_instance.setNumberElements( [ 5, 5 ], [ 5, 5 ], [ 10 ] )

    # Add fields
    cells_dim1 = FieldInfo( "cell1", 1, "CELLS" )
    cells_dim3 = FieldInfo( "cell3", 3, "CELLS" )
    points_dim1 = FieldInfo( "point1", 1, "POINTS" )
    points_dim3 = FieldInfo( "point3", 3, "POINTS" )
    filter_instance.setFields( [ cells_dim1, cells_dim3, points_dim1, points_dim3 ] )

    # Apply filter
    success = filter_instance.applyFilter()
    assert success, "Filter should succeed"

    # Get the generated mesh
    output_mesh = filter_instance.getMesh()

    # Verify mesh properties
    assert output_mesh is not None, "Output mesh should not be None"
    assert output_mesh.GetNumberOfCells() == 1000, "Should have 1000 cells (10x10x10)"
    assert output_mesh.GetNumberOfPoints() == 1331, "Should have 1331 points (11x11x11)"

    # Verify global IDs
    assert output_mesh.GetCellData().GetGlobalIds() is not None, "Should have cell global IDs"
    assert output_mesh.GetPointData().GetGlobalIds() is not None, "Should have point global IDs"

    # Verify fields
    assert output_mesh.GetCellData().GetArray( "cell1" ) is not None, "Should have cell1 array"
    assert output_mesh.GetCellData().GetArray( "cell1" ).GetNumberOfComponents() == 1, "cell1 should have 1 component"
    assert output_mesh.GetCellData().GetArray( "cell3" ) is not None, "Should have cell3 array"
    assert output_mesh.GetCellData().GetArray( "cell3" ).GetNumberOfComponents() == 3, "cell3 should have 3 components"

    assert output_mesh.GetPointData().GetArray( "point1" ) is not None, "Should have point1 array"
    assert output_mesh.GetPointData().GetArray(
        "point1" ).GetNumberOfComponents() == 1, "point1 should have 1 component"
    assert output_mesh.GetPointData().GetArray( "point3" ) is not None, "Should have point3 array"
    assert output_mesh.GetPointData().GetArray(
        "point3" ).GetNumberOfComponents() == 3, "point3 should have 3 components"


def test_generate_rectilinear_grid_filter_no_global_ids():
    """Test the GenerateRectilinearGrid filter without global IDs."""
    filter_instance = GenerateRectilinearGrid( generateCellsGlobalIds=False, generatePointsGlobalIds=False )

    filter_instance.setCoordinates( [ 0.0, 2.0 ], [ 0.0, 3.0 ], [ 0.0, 1.0 ] )
    filter_instance.setNumberElements( [ 2 ], [ 3 ], [ 1 ] )

    success = filter_instance.applyFilter()
    assert success, "Filter should succeed"

    output_mesh = filter_instance.getMesh()

    # Verify no global IDs
    assert output_mesh.GetCellData().GetGlobalIds() is None, "Should not have cell global IDs"
    assert output_mesh.GetPointData().GetGlobalIds() is None, "Should not have point global IDs"

    # Verify basic mesh properties
    assert output_mesh.GetNumberOfCells() == 6, "Should have 6 cells (2x3x1)"
    assert output_mesh.GetNumberOfPoints() == 24, "Should have 24 points (3x4x2)"


def test_generate_rectilinear_grid_filter_missing_parameters():
    """Test that filter fails gracefully when required parameters are missing."""
    filter_instance = GenerateRectilinearGrid()

    # Try to apply filter without setting coordinates
    success = filter_instance.applyFilter()
    assert not success, "Filter should fail when coordinates are not set"


def test_generate_rectilinear_grid_standalone(tmp_path):
    """Test the standalone generateRectilinearGrid function."""
    output_path = tmp_path / "test_grid.vtu"

    # Create a simple rectilinear grid
    output_mesh = generateRectilinearGrid( coordsX=[ 0.0, 1.0, 2.0 ],
                                           coordsY=[ 0.0, 1.0 ],
                                           coordsZ=[ 0.0, 1.0 ],
                                           numberElementsX=[ 2, 3 ],
                                           numberElementsY=[ 2 ],
                                           numberElementsZ=[ 2 ],
                                           outputPath=output_path,
                                           fields=[ FieldInfo( "test_field", 2, "CELLS" ) ],
                                           generateCellsGlobalIds=True,
                                           generatePointsGlobalIds=False )

    # Verify mesh properties
    assert output_mesh is not None, "Output mesh should not be None"
    assert output_mesh.GetNumberOfCells() == 20, "Should have 20 cells (5x2x2)"
    assert output_mesh.GetNumberOfPoints() == 54, "Should have 54 points (6x3x3)"

    # Verify field
    assert output_mesh.GetCellData().GetArray( "test_field" ) is not None, "Should have test_field array"
    test_field_array = output_mesh.GetCellData().GetArray( "test_field" )
    assert test_field_array.GetNumberOfComponents() == 2, "test_field should have 2 components"

    # Verify global IDs
    assert output_mesh.GetCellData().GetGlobalIds() is not None, "Should have cell global IDs"
    assert output_mesh.GetPointData().GetGlobalIds() is None, "Should not have point global IDs"

    # Verify output file was written
    assert output_path.exists(), "Output file should exist"
