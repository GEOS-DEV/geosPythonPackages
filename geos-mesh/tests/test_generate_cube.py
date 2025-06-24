import pytest
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkPointData, vtkCellData
from vtkmodules.vtkCommonCore import vtkDataArray
from geos.mesh.doctor.actions.generate_cube import FieldInfo, Options, __build
from geos.mesh.doctor.filters.GenerateRectilinearGrid import GenerateRectilinearGrid


@pytest.fixture
def generate_rectilinear_grid_filter() -> GenerateRectilinearGrid:
    filter = GenerateRectilinearGrid()
    filter.setCoordinates( [ 0.0, 5.0, 10.0 ], [ 0.0, 10.0, 20.0 ], [ 0.0, 50.0 ] )
    filter.setNumberElements( [ 5, 5 ], [ 5, 5 ], [ 10 ] )  # 10 cells along X, Y, Z axis
    filter.setGenerateCellsGlobalIds( True )
    filter.setGeneratePointsGlobalIds( True )

    cells_dim1 = FieldInfo( "cell1", 1, "CELLS" )
    cells_dim3 = FieldInfo( "cell3", 3, "CELLS" )
    points_dim1 = FieldInfo( "point1", 1, "POINTS" )
    points_dim3 = FieldInfo( "point3", 3, "POINTS" )
    filter.setFields( [ cells_dim1, cells_dim3, points_dim1, points_dim3 ] )

    return filter


def test_generate_rectilinear_grid( generate_rectilinear_grid_filter: GenerateRectilinearGrid ) -> None:
    generate_rectilinear_grid_filter.Update()
    mesh = generate_rectilinear_grid_filter.GetOutputDataObject( 0 )

    assert isinstance( mesh, vtkUnstructuredGrid )
    assert mesh.GetNumberOfCells() == 1000
    assert mesh.GetNumberOfPoints() == 1331
    assert mesh.GetBounds() == ( 0.0, 10.0, 0.0, 20.0, 0.0, 50.0 )

    pointData: vtkPointData = mesh.GetPointData()
    ptArray1: vtkDataArray = pointData.GetArray( "point1" )
    ptArray3: vtkDataArray = pointData.GetArray( "point3" )
    assert ptArray1.GetNumberOfComponents() == 1
    assert ptArray3.GetNumberOfComponents() == 3

    cellData: vtkCellData = mesh.GetCellData()
    cellArray1: vtkDataArray = cellData.GetArray( "cell1" )
    cellArray3: vtkDataArray = cellData.GetArray( "cell3" )
    assert cellArray1.GetNumberOfComponents() == 1
    assert cellArray3.GetNumberOfComponents() == 3


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
