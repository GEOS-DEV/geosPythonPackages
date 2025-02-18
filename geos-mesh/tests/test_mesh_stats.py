import os
import re
import logging
import subprocess
import numpy as np
from geos.mesh.doctor.mesh_doctor import MESH_DOCTOR_FILEPATH
from geos.mesh.doctor.checks import mesh_stats as ms
from geos.mesh.doctor.checks.generate_cube import Options, FieldInfo, __build
from geos.mesh.doctor.checks.vtk_utils import VtkOutput, write_mesh
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkHexahedron
from vtkmodules.util.numpy_support import numpy_to_vtk
"""
For creation of output test meshes
"""
current_file_path: str = __file__
dir_name: str = os.path.dirname( current_file_path )
pattern_test: str = "to_check_mesh"
filepath_mesh_for_stats: str = os.path.join( dir_name, pattern_test + ".vtu" )
test_mesh_for_stats: VtkOutput = VtkOutput( filepath_mesh_for_stats, True )
"""
Grids for stats tests
"""
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
coords_new_hex = ( ( 3.0, 0.0, 0.0 ), ( 4.0, 0.0, 0.0 ), ( 4.0, 1.0, 0.0 ), ( 3.0, 1.0, 0.0 ), ( 3.0, 0.0, 1.0 ),
                   ( 4.0, 0.0, 1.0 ), ( 4.0, 1.0, 1.0 ), ( 3.0, 1.0, 1.0 ) )
for i in range( len( coords_new_hex ) ):
    hex.GetPoints().InsertNextPoint( coords_new_hex[ i ] )
    hex.GetPointIds().SetId( i, number_cells_cube4 + i )
cube4.InsertNextCell( hex.GetCellType(), hex.GetPointIds() )

# Last mesh: test mesh for output and check of execution of mesh_stats
f_poro: FieldInfo = FieldInfo( "POROSITY", 1, "CELLS" )
f_perm: FieldInfo = FieldInfo( "PERMEABILITY", 3, "CELLS" )
f_density: FieldInfo = FieldInfo( "DENSITY", 1, "CELLS" )
f_pressure: FieldInfo = FieldInfo( "PRESSURE", 1, "CELLS" )
f_temp: FieldInfo = FieldInfo( "TEMPERATURE", 1, "POINTS" )
f_displacement: FieldInfo = FieldInfo( "DISPLACEMENT", 3, "POINTS" )
options_cube_output: Options = Options( vtk_output=out,
                                        generate_cells_global_ids=True,
                                        generate_points_global_ids=True,
                                        xs=np.array( [ 0.0, 1.0, 2.0, 3.0 ] ),
                                        ys=np.array( [ 0.0, 1.0, 2.0, 3.0 ] ),
                                        zs=np.array( [ 0.0, 1.0, 2.0, 3.0 ] ),
                                        nxs=[ 1, 1, 1 ],
                                        nys=[ 1, 1, 1 ],
                                        nzs=[ 1, 1, 1 ],
                                        fields=[ f_poro, f_perm, f_density, f_pressure, f_temp, f_displacement ] )
cube_output: vtkUnstructuredGrid = __build( options_cube_output )
number_cells: int = cube_output.GetNumberOfCells()
number_points: int = cube_output.GetNumberOfPoints()
a_poro: np.array = np.linspace( 0, 1, number_cells )
a_perm: np.array = np.empty( ( number_cells, f_perm.dimension ) )
for i in range( f_perm.dimension ):
    a_perm[ :, i ] = np.linspace( 1e-14 * 10**i, 1e-12 * 10**i, number_cells )
a_density: np.array = np.linspace( 500, 40000, number_cells )
a_pressure: np.array = np.linspace( 1e5, 1e7, number_cells )
a_temp: np.array = np.linspace( 1e2, 5e3, number_points )
a_temp = a_temp.reshape( number_points, 1 )
a_displacement: np.array = np.empty( ( number_points, f_displacement.dimension ) )
for i in range( f_displacement.dimension ):
    a_displacement[ :, i ] = np.linspace( 1e-4 * 10**i, 1e-2 * 10**i, number_points )
for array in [ a_density, a_pressure, a_poro ]:
    array = array.reshape( number_cells, 1 )

vtk_a_poro = numpy_to_vtk( a_poro )
vtk_a_perm = numpy_to_vtk( a_perm )
vtk_a_density = numpy_to_vtk( a_density )
vtk_a_pressure = numpy_to_vtk( a_pressure )
vtk_a_temp = numpy_to_vtk( a_temp )
vtk_a_displacement = numpy_to_vtk( a_displacement )
vtk_a_poro.SetName( f_poro.name )
vtk_a_perm.SetName( f_perm.name )
vtk_a_density.SetName( f_density.name + "_invalid" )
vtk_a_pressure.SetName( f_pressure.name )
vtk_a_temp.SetName( f_temp.name + "_invalid" )
vtk_a_displacement.SetName( f_displacement.name )

cell_data_output = cube_output.GetCellData()
point_data_output = cube_output.GetPointData()
cell_data_output.AddArray( vtk_a_poro )
cell_data_output.AddArray( vtk_a_perm )
cell_data_output.AddArray( vtk_a_density )
cell_data_output.AddArray( vtk_a_pressure )
point_data_output.AddArray( vtk_a_temp )
point_data_output.AddArray( vtk_a_displacement )


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

    def test_mesh_stats_execution( self ):
        write_mesh( cube_output, test_mesh_for_stats )
        invalidTest = False
        command = [
            "python", MESH_DOCTOR_FILEPATH, "-v", "-i", test_mesh_for_stats.output, "mesh_stats", "--write_stats", "0",
            "--output", dir_name, "--disconnected", "0", "--field_values", "0"
        ]
        try:
            result = subprocess.run( command, shell=True, stderr=subprocess.PIPE, universal_newlines=True )
            os.remove( test_mesh_for_stats.output )
            stderr = result.stderr
            assert result.returncode == 0
            raw_stderr = r"{}".format( stderr )
            pattern = r"\[.*?\]\[.*?\] (.*)"
            matches = re.findall( pattern, raw_stderr )
            no_log = "\n".join( matches )
            mesh_output_stats: str = no_log[ no_log.index( "The mesh has" ): ]
            # yapf: disable
            expected_stats: str = ( "The mesh has 27 cells and 64 points.\n" +
                                    "There are 1 different types of cells in the mesh:\n" +
                                    "\tHex\t\t(27 cells)\n" +
                                    "Number of cells that have exactly N neighbors:\n" +
                                    "\tNeighbors\tNumber of cells concerned\n" +
                                    "\t3\t\t8\n" +
                                    "\t4\t\t12\n" +
                                    "\t5\t\t6\n" +
                                    "\t6\t\t1\n" +
                                    "Number of nodes being shared by exactly N cells:\n" +
                                    "\tCells\t\tNumber of nodes\n" +
                                    "\t8\t\t8\n" +
                                    "\t1\t\t8\n" +
                                    "\t2\t\t24\n" +
                                    "\t4\t\t24\n" +
                                    "Number of disconnected cells in the mesh: 0\n" +
                                    "Number of disconnected nodes in the mesh: 0\n" +
                                    "The domain is contained in:\n" +
                                    "\t0.0 <= x <= 3.0\n" +
                                    "\t0.0 <= y <= 3.0\n" +
                                    "\t0.0 <= z <= 3.0\n" +
                                    "Does the mesh have global point ids: True\n" +
                                    "Does the mesh have global cell ids: True\n" +
                                    "Number of fields data containing NaNs values: 0\n" +
                                    "There are 5 scalar fields from the CellData:\n" +
                                    "\tPOROSITY           min = 0.0   max = 1.0\n" +
                                    "\tDENSITY            min = 1.0   max = 1.0\n" +
                                    "\tPRESSURE           min = 100000.0   max = 10000000.0\n" +
                                    "\tGLOBAL_IDS_CELLS   min = 0.0   max = 26.0\n" +
                                    "\tDENSITY_invalid    min = 500.0   max = 40000.0\n" +
                                    "There are 1 vector/tensor fields from the CellData:\n" +
                                    "\tPERMEABILITY   min = [1e-14, 1e-13, 1e-12]   max = [1e-12, 1e-11, 1e-10]\n" +
                                    "There are 3 scalar fields from the PointData:\n" +
                                    "\tTEMPERATURE           min = 1.0   max = 1.0\n" +
                                    "\tGLOBAL_IDS_POINTS     min = 0.0   max = 63.0\n" +
                                    "\tTEMPERATURE_invalid   min = 100.0   max = 5000.0\n" +
                                    "There are 1 vector/tensor fields from the PointData:\n" +
                                    "\tDISPLACEMENT   min = [0.0001, 0.001, 0.01]   max = [0.01, 0.1, 1.0]\n" +
                                    "There are 0 scalar fields from the FieldData:\n" +
                                    "There are 0 vector/tensor fields from the FieldData:\n" +
                                    "Unexpected range of values for vector/tensor fields from the CellData:\n" +
                                    "DENSITY_invalid expected to be between 0.0 and 25000.0.\n" +
                                    "Unexpected range of values for vector/tensor fields from the PointData:\n" +
                                    "TEMPERATURE_invalid expected to be between 0.0 and 2000.0.\n" +
                                    "Unexpected range of values for vector/tensor fields from the FieldData:" )
            # yapf: enable
            assert mesh_output_stats == expected_stats
        except Exception as e:
            logging.error( "Invalid command input. Test has failed." )
            logging.error( e )
            invalidTest = True

        if invalidTest:
            raise ValueError( "test_mesh_stats_execution has failed." )
