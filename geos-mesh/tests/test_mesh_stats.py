import numpy as np

from geos.mesh.doctor.checks import mesh_stats as ms
from geos.mesh.doctor.checks.generate_cube import Options, FieldInfo, __build
from geos.mesh.doctor.checks.vtk_utils import VtkOutput
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkHexahedron
from vtkmodules.util.numpy_support import numpy_to_vtk

# First mesh: no anomalies to look for
out: VtkOutput = VtkOutput( "test", False )
field0: FieldInfo = FieldInfo( "scalar_cells", 1, "CELLS" )
field1: FieldInfo = FieldInfo( "tensor_cells", 3, "CELLS" )
field2: FieldInfo = FieldInfo( "scalar_points", 1, "POINTS" )
field3: FieldInfo = FieldInfo( "tensor_points", 3, "POINTS" )
options_cube0: Options = Options( vtk_output=out,
                                  generate_cells_global_ids=True,
                                  generate_points_global_ids=True,
                                  xs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  ys=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  zs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  nxs=[ 1, 1 ],
                                  nys=[ 1, 1 ],
                                  nzs=[ 1, 1 ],
                                  fields=[ field0, field1, field2, field3 ] )
cube0: vtkUnstructuredGrid = __build( options_cube0 )

# Second mesh: disconnected nodes are added
cube1: vtkUnstructuredGrid = __build( options_cube0 )
cube1.GetPoints().InsertNextPoint( ( 3.0, 0.0, 0.0 ) )
cube1.GetPoints().InsertNextPoint( ( 3.0, 1.0, 0.0 ) )
cube1.GetPoints().InsertNextPoint( ( 3.0, 2.0, 0.0 ) )

# Third mesh: fields with invalid ranges of values are added
field_poro: FieldInfo = FieldInfo( "POROSITY", 1, "CELLS" )
field_perm: FieldInfo = FieldInfo( "PERMEABILITY", 3, "CELLS" )
field_density: FieldInfo = FieldInfo( "DENSITY", 1, "CELLS" )
field_temp: FieldInfo = FieldInfo( "TEMPERATURE", 1, "POINTS" )
field_pressure: FieldInfo = FieldInfo( "PRESSURE", 3, "POINTS" )
options_cube2: Options = Options( vtk_output=out,
                                  generate_cells_global_ids=True,
                                  generate_points_global_ids=True,
                                  xs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  ys=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  zs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  nxs=[ 1, 1 ],
                                  nys=[ 1, 1 ],
                                  nzs=[ 1, 1 ],
                                  fields=[ field_poro, field_perm, field_density, field_temp, field_pressure ] )
cube2: vtkUnstructuredGrid = __build( options_cube2 )
number_cells: int = cube2.GetNumberOfCells()
number_points: int = cube2.GetNumberOfPoints()
array_poro: np.array = np.ones( ( number_cells, field_poro.dimension ), dtype=float ) * ( -1.0 )
array_perm: np.array = np.ones( ( number_cells, field_perm.dimension ), dtype=float ) * 2.0
array_density: np.array = np.ones( ( number_cells, field_density.dimension ), dtype=float ) * ( 100000.0 )
array_temp: np.array = np.ones( ( number_points, field_temp.dimension ), dtype=float ) * ( -1.0 )
array_pressure: np.array = np.ones( ( number_points, field_pressure.dimension ), dtype=float ) * ( -1.0 )
vtk_array_poro = numpy_to_vtk( array_poro )
vtk_array_perm = numpy_to_vtk( array_perm )
vtk_array_density = numpy_to_vtk( array_density )
vtk_array_temp = numpy_to_vtk( array_temp )
vtk_array_pressure = numpy_to_vtk( array_pressure )
vtk_array_poro.SetName( field_poro.name + "_invalid" )
vtk_array_perm.SetName( field_perm.name + "_invalid" )
vtk_array_density.SetName( field_density.name + "_invalid" )
vtk_array_temp.SetName( field_temp.name + "_invalid" )
vtk_array_pressure.SetName( field_pressure.name + "_invalid" )
cell_data = cube2.GetCellData()
point_data = cube2.GetPointData()
cell_data.AddArray( vtk_array_poro )
cell_data.AddArray( vtk_array_perm )
cell_data.AddArray( vtk_array_density )
point_data.AddArray( vtk_array_temp )
point_data.AddArray( vtk_array_pressure )

# In this mesh, certain fields have NaN values
cube3: vtkUnstructuredGrid = __build( options_cube2 )
array_poro = array_poro * ( -1 )
array_temp = array_temp * ( -1 )
array_poro[ 0 ], array_poro[ -1 ] = np.nan, np.nan
array_temp[ 0 ], array_temp[ -1 ] = np.nan, np.nan
vtk_array_poro = numpy_to_vtk( array_poro )
vtk_array_temp = numpy_to_vtk( array_temp )
vtk_array_poro.SetName( field_poro.name + "_invalid" )
vtk_array_temp.SetName( field_temp.name + "_invalid" )
cell_data = cube3.GetCellData()
point_data = cube3.GetPointData()
cell_data.AddArray( vtk_array_poro )
point_data.AddArray( vtk_array_temp )

# cube4 is a cube with an extra hex cell disconnected added 
options_cube4: Options = Options( vtk_output=out,
                                  generate_cells_global_ids=False,
                                  generate_points_global_ids=False,
                                  xs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  ys=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  zs=np.array( [ 0.0, 1.0, 2.0 ] ),
                                  nxs=[ 1, 1 ],
                                  nys=[ 1, 1 ],
                                  nzs=[ 1, 1 ],
                                  fields=[] )
cube4: vtkUnstructuredGrid = __build( options_cube4 )
number_cells_cube4: int = cube4.GetNumberOfCells()
hex = vtkHexahedron()
coords_new_hex = ( (3.0, 0.0, 0.0), (4.0, 0.0, 0.0), (4.0, 1.0, 0.0), (3.0, 1.0, 0.0),
                   (3.0, 0.0, 1.0), (4.0, 0.0, 1.0), (4.0, 1.0, 1.0), (3.0, 1.0, 1.0) )
for i in range( len( coords_new_hex ) ):
    hex.GetPoints().InsertNextPoint( coords_new_hex[ i ] )
    hex.GetPointIds().SetId( i, number_cells_cube4 + i )
cube4.InsertNextCell( hex.GetCellType(), hex.GetPointIds() )


class TestClass:

    def test_get_cell_types_and_counts( self ):
        result: tuple[ int, int, list[ str ], list[ int ] ] = ms.get_cell_types_and_counts( cube0 )
        assert result[ 0 ] == 8
        assert result[ 1 ] == 1
        assert result[ 2 ] == [ "Hex" ]
        assert result[ 3 ] == [ 8 ]

    def test_get_number_cells_per_nodes( self ):
        result: dict[ int, int ] = ms.get_number_cells_per_nodes( cube0 )
        for node_id in [ 0, 2, 6, 8, 18, 20, 24, 26 ]:
            assert result[ node_id ] == 1
        for node_id in [ 1, 3, 5, 7, 9, 11, 15, 17, 19, 21, 23, 25 ]:
            assert result[ node_id ] == 2
        for node_id in [ 4, 10, 12, 14, 16, 22 ]:
            assert result[ node_id ] == 4
        assert result[ 13 ] == 8
        result2: dict[ int, int ] = ms.summary_number_cells_per_nodes( result )
        assert result2 == { 1: 8, 2: 12, 4: 6, 8: 1 }

    def test_get_coords_min_max( self ):
        result: tuple[ np.ndarray ] = ms.get_coords_min_max( cube0 )
        assert np.array_equal( result[ 0 ], np.array( [ 0.0, 0.0, 0.0 ] ) )
        assert np.array_equal( result[ 1 ], np.array( [ 2.0, 2.0, 2.0 ] ) )

    def test_build_MeshComponentData( self ):
        result: ms.MeshComponentData = ms.build_MeshComponentData( cube0, "point" )
        assert result.componentType == "point"
        assert result.scalar_names == [ "scalar_points", "GLOBAL_IDS_POINTS" ]
        assert result.scalar_min_values == [ np.float64( 1.0 ), np.int64( 0 ) ]
        assert result.scalar_max_values == [ np.float64( 1.0 ), np.int64( 26 ) ]
        assert result.tensor_names == [ "tensor_points" ]
        assert np.array_equal( result.tensor_min_values[ 0 ], np.array( [ 1.0, 1.0, 1.0 ] ) )
        assert np.array_equal( result.tensor_max_values[ 0 ], np.array( [ 1.0, 1.0, 1.0 ] ) )

        result2: ms.MeshComponentData = ms.build_MeshComponentData( cube0, "cell" )
        assert result2.componentType == "cell"
        assert result2.scalar_names == [ "scalar_cells", "GLOBAL_IDS_CELLS" ]
        assert result2.scalar_min_values == [ np.float64( 1.0 ), np.int64( 0 ) ]
        assert result2.scalar_max_values == [ np.float64( 1.0 ), np.int64( 7 ) ]
        assert result2.tensor_names == [ "tensor_cells" ]
        assert np.array_equal( result2.tensor_min_values[ 0 ], np.array( [ 1.0, 1.0, 1.0 ] ) )
        assert np.array_equal( result2.tensor_max_values[ 0 ], np.array( [ 1.0, 1.0, 1.0 ] ) )

        result3: ms.MeshComponentData = ms.build_MeshComponentData( cube0, "random" )
        assert result3.componentType == "point"

    def test_get_disconnected_nodes( self ):
        result: list[ int ] = ms.get_disconnected_nodes_id( cube1 )
        assert result == [ 27, 28, 29 ]
        result2: dict[ int, tuple[ float ] ] = ms.get_disconnected_nodes_coords( cube1 )
        assert result2 == { 27: ( 3.0, 0.0, 0.0 ), 28: ( 3.0, 1.0, 0.0 ), 29: ( 3.0, 2.0, 0.0 ) }

    def test_field_values_validity( self ):
        mcd_point: ms.MeshComponentData = ms.build_MeshComponentData( cube2, "point" )
        mcd_cell: ms.MeshComponentData = ms.build_MeshComponentData( cube2, "cell" )
        result_points: dict[ str, tuple[ bool, tuple[ float ] ] ] = ms.field_values_validity( mcd_point )
        result_cells: dict[ str, tuple[ bool, tuple[ float ] ] ] = ms.field_values_validity( mcd_cell )
        assert result_points == {
            "TEMPERATURE": ( True, ( ms.MIN_FIELD.TEMPERATURE.value, ms.MAX_FIELD.TEMPERATURE.value ) ),
            "PRESSURE": ( True, ( ms.MIN_FIELD.PRESSURE.value, ms.MAX_FIELD.PRESSURE.value ) ),
            "TEMPERATURE_invalid": ( False, ( ms.MIN_FIELD.TEMPERATURE.value, ms.MAX_FIELD.TEMPERATURE.value ) ),
            "PRESSURE_invalid": ( False, ( ms.MIN_FIELD.PRESSURE.value, ms.MAX_FIELD.PRESSURE.value ) ),
        }
        assert result_cells == {
            "PERMEABILITY": ( True, ( ms.MIN_FIELD.PERM.value, ms.MAX_FIELD.PERM.value ) ),
            "POROSITY": ( True, ( ms.MIN_FIELD.PORO.value, ms.MAX_FIELD.PORO.value ) ),
            "DENSITY": ( True, ( ms.MIN_FIELD.DENSITY.value, ms.MAX_FIELD.DENSITY.value ) ),
            "PERMEABILITY_invalid": ( False, ( ms.MIN_FIELD.PERM.value, ms.MAX_FIELD.PERM.value ) ),
            "POROSITY_invalid": ( False, ( ms.MIN_FIELD.PORO.value, ms.MAX_FIELD.PORO.value ) ),
            "DENSITY_invalid": ( False, ( ms.MIN_FIELD.DENSITY.value, ms.MAX_FIELD.DENSITY.value ) ),
        }

    def test_check_NaN_fields( self ):
        result: dict[ str, int ] = ms.check_NaN_fields( cube3 )
        assert result == { "POROSITY_invalid": 2, "TEMPERATURE_invalid": 2 }

    def test_get_cells_neighbors_number( self ):
        result: np.array = ms.get_cells_neighbors_number( cube0 )
        expected: np.array = np.ones( ( 8, 1 ), dtype=int ) * 3
        assert np.array_equal( result, expected )
        result2: np.array = ms.get_cells_neighbors_number( cube4 )
        expected2: np.array = np.ones( ( 9, 1 ), dtype=int ) * 3
        expected2[ 8 ] = 0
        assert np.array_equal( result2, expected2 )