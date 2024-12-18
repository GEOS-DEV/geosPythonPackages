import os
import shutil
from numpy import array, arange, full, array_equal, sqrt, nan, log, log10
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from scipy.spatial import KDTree
from geos.mesh.doctor.checks import field_operations as fo
from geos.mesh.doctor.checks import vtk_utils as vu
from tests import test_vtk_utils as tvu
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_HEXAHEDRON
"""
For tests creation
"""
# yapf: disable
## GRID 1
eight_hex_points_coords: list[ list[ float ] ] = [ [ 0.0, 0.0, 0.0 ],  #point0
                                                   [ 1.0, 0.0, 0.0 ],  #point1
                                                   [ 2.0, 0.0, 0.0 ],  #point2
                                                   [ 0.0, 1.0, 0.0 ],  #point3
                                                   [ 1.0, 1.0, 0.0 ],  #point4
                                                   [ 2.0, 1.0, 0.0 ],  #point5
                                                   [ 0.0, 2.0, 0.0 ],  #point6
                                                   [ 1.0, 2.0, 0.0 ],  #point7
                                                   [ 2.0, 2.0, 0.0 ],  #point8
                                                   [ 0.0, 0.0, 1.0 ],  #point9
                                                   [ 1.0, 0.0, 1.0 ],  #point10
                                                   [ 2.0, 0.0, 1.0 ],  #point11
                                                   [ 0.0, 1.0, 1.0 ],  #point12
                                                   [ 1.0, 1.0, 1.0 ],  #point13
                                                   [ 2.0, 1.0, 1.0 ],  #point14
                                                   [ 0.0, 2.0, 1.0 ],  #point15
                                                   [ 1.0, 2.0, 1.0 ],  #point16
                                                   [ 2.0, 2.0, 1.0 ],  #point17
                                                   [ 0.0, 0.0, 2.0 ],  #point18
                                                   [ 1.0, 0.0, 2.0 ],  #point19
                                                   [ 2.0, 0.0, 2.0 ],  #point20
                                                   [ 0.0, 1.0, 2.0 ],  #point21
                                                   [ 1.0, 1.0, 2.0 ],  #point22
                                                   [ 2.0, 1.0, 2.0 ],  #point23
                                                   [ 0.0, 2.0, 2.0 ],  #point24
                                                   [ 1.0, 2.0, 2.0 ],  #point25
                                                   [ 2.0, 2.0, 2.0 ] ] #point26
eight_hex_ids = [ [ 0, 1, 4, 3, 9, 10, 13, 12 ],
                  [ 0 + 1, 1 + 1, 4 + 1, 3 + 1, 9 + 1, 10 + 1, 13 + 1, 12 + 1 ],
                  [ 0 + 3, 1 + 3, 4 + 3, 3 + 3, 9 + 3, 10 + 3, 13 + 3, 12 + 3 ],
                  [ 0 + 4, 1 + 4, 4 + 4, 3 + 4, 9 + 4, 10 + 4, 13 + 4, 12 + 4 ],
                  [ 0 + 9, 1 + 9, 4 + 9, 3 + 9, 9 + 9, 10 + 9, 13 + 9, 12 + 9 ],
                  [ 0 + 10, 1 + 10, 4 + 10, 3 + 10, 9 + 10, 10 + 10, 13 + 10, 12 + 10 ],
                  [ 0 + 12, 1 + 12, 4 + 12, 3 + 12, 9 + 12, 10 + 12, 13 + 12, 12 + 12 ],
                  [ 0 + 13, 1 + 13, 4 + 13, 3 + 13, 9 + 13, 10 + 13, 13 + 13, 12 + 13 ] ]
eight_hex_grid: vtkUnstructuredGrid = tvu.create_type_vtk_grid( eight_hex_points_coords, eight_hex_ids, VTK_HEXAHEDRON )
eight_hex_grid_output = vu.VtkOutput( os.path.join( tvu.dir_name, "eight_hex.vtu" ), False )

eight_hex_grid_empty: vtkUnstructuredGrid = vtkUnstructuredGrid()
eight_hex_grid_empty.DeepCopy( eight_hex_grid )
eight_hex_grid_empty_output = vu.VtkOutput( os.path.join( tvu.dir_name, "eight_hex_empty.vtu" ), False )

#GRID 2 which is a cell0 of GRID 1
hex_ids = [ [ 0, 1, 2, 3, 4, 5, 6, 7 ] ]
hex0_points_coords: list[ list[ float ] ] = [ [ 0.0, 0.0, 0.0 ],  #point0
                                              [ 1.0, 0.0, 0.0 ],  #point1
                                              [ 1.0, 1.0, 0.0 ],  #point2
                                              [ 0.0, 1.0, 0.0 ],  #point3
                                              [ 0.0, 0.0, 1.0 ],  #point4
                                              [ 1.0, 0.0, 1.0 ],  #point5
                                              [ 1.0, 1.0, 1.0 ],  #point6
                                              [ 0.0, 1.0, 1.0 ] ] #point7
hex0_grid: vtkUnstructuredGrid = tvu.create_type_vtk_grid( hex0_points_coords, hex_ids, VTK_HEXAHEDRON )

#GRID 3 which is cell1 of GRID 1
hex1_points_coords: list[ list[ float ] ] = [ [ 1.0, 0.0, 0.0 ],  #point0
                                              [ 2.0, 0.0, 0.0 ],  #point1
                                              [ 2.0, 1.0, 0.0 ],  #point2
                                              [ 1.0, 1.0, 0.0 ],  #point3
                                              [ 1.0, 0.0, 1.0 ],  #point4
                                              [ 2.0, 0.0, 1.0 ],  #point5
                                              [ 2.0, 1.0, 1.0 ],  #point6
                                              [ 1.0, 1.0, 1.0 ] ] #point7
hex1_grid: vtkUnstructuredGrid = tvu.create_type_vtk_grid( hex1_points_coords, hex_ids, VTK_HEXAHEDRON )

sub_grids: list[ vtkUnstructuredGrid ] = [ hex0_grid, hex1_grid ]
sub_grids_values: list[ dict[ str, array ] ] = [ dict() for _ in range( len( sub_grids ) ) ]
sub_grids_output: list[ vu.VtkOutput ] = [ vu.VtkOutput( os.path.join( tvu.dir_name, f"sub_grid{i}.vtu" ), True ) for i in range( len( sub_grids ) ) ]
# yapf: enable
"""
Add arrays in each grid
"""
ncells: int = eight_hex_grid.GetNumberOfCells()
npoints: int = eight_hex_grid.GetNumberOfPoints()
eight_hex_grid_values: dict[ str, array ] = {
    "cell_param0": arange( 0, ncells ).reshape( ncells, 1 ),
    "cell_param1": arange( ncells, ncells * 3 ).reshape( ncells, 2 ),
    "cell_param2": arange( ncells * 3, ncells * 6 ).reshape( ncells, 3 ),
    "point_param0": arange( ncells * 6, ncells * 6 + npoints ).reshape( npoints, 1 ),
    "point_param1": arange( ncells * 6 + npoints, ncells * 6 + npoints * 3 ).reshape( npoints, 2 ),
    "point_param2": arange( ncells * 6 + npoints * 3, ncells * 6 + npoints * 6 ).reshape( npoints, 3 )
}
for name, value in eight_hex_grid_values.items():
    arr_values = numpy_to_vtk( value )
    arr_values.SetName( name )
    if "cell" in name:
        eight_hex_grid.GetCellData().AddArray( arr_values )
    else:
        eight_hex_grid.GetPointData().AddArray( arr_values )
    for i in range( len( sub_grids_values ) ):
        if len( value.shape ) == 1:
            sub_grids_values[ i ][ name ] = value[ i ]
        else:
            sub_grids_values[ i ][ name ] = [ value[ i ][ j ] for j in range( value.shape[ 1 ] ) ]

for i, sub_grid in enumerate( sub_grids ):
    for name, value in sub_grids_values[ i ].items():
        arr_values = numpy_to_vtk( value )
        arr_values.SetName( name )
        if "cell" in name:
            sub_grid.GetCellData().AddArray( arr_values )
        else:
            sub_grid.GetPointData().AddArray( arr_values )

copy_fields_points: list[ tuple[ str ] ] = [ ( "point_param0", ), ( "point_param1", "point_param1" + "_new" ),
                                             ( "point_param2", "point_param2" + "_new", "*3" ) ]
copy_fields_cells: list[ tuple[ str ] ] = [ ( "cell_param0", ), ( "cell_param1", "cell_param1" + "_new" ),
                                            ( "cell_param2", "cell_param2" + "_new", "+ 10" ) ]

created_fields_points: list[ tuple[ str ] ] = [ ( "point_param0" + "_created", "log( point_param0 )" ),
                                                ( "point_param1" + "_created", "sqrt( point_param1 )" ),
                                                ( "point_param2" + "_created", "point_param0 +point_param1 * 2" ) ]
created_fields_cells: dict[ str, str ] = [ ( "cell_param0" + "_created", "log( cell_param0 )" ),
                                           ( "cell_param1" + "_created", "sqrt( cell_param1 )" ),
                                           ( "cell_param2" + "_created", "cell_param0 + cell_param1 * 2" ) ]

out_points: vu.VtkOutput = vu.VtkOutput( os.path.join( tvu.dir_name, "points.vtu" ), True )
out_cells: vu.VtkOutput = vu.VtkOutput( os.path.join( tvu.dir_name, "cells.vtu" ), True )


class TestClass:

    def test_precoded_fields( self ):
        result_points: array = fo.get_distances_mesh_center( eight_hex_grid_empty, "point" )
        result_cells: array = fo.get_distances_mesh_center( eight_hex_grid_empty, "cell" )
        sq2, sq3, sq3h = sqrt( 2 ), sqrt( 3 ), sqrt( 3 ) / 2
        expected_points: array = array( [
            sq3, sq2, sq3, sq2, 1.0, sq2, sq3, sq2, sq3, sq2, 1.0, sq2, 1.0, 0.0, 1.0, sq2, 1.0, sq2, sq3, sq2, sq3,
            sq2, 1.0, sq2, sq3, sq2, sq3
        ] )
        expected_cells: array = array( [ sq3h, sq3h, sq3h, sq3h, sq3h, sq3h, sq3h, sq3h ] )
        assert array_equal( result_points, expected_points )
        assert array_equal( result_cells, expected_cells )
        random_points: array = fo.get_random_field( eight_hex_grid_empty, "point" )
        random_cells: array = fo.get_random_field( eight_hex_grid_empty, "cell" )
        assert eight_hex_grid_empty.GetNumberOfPoints() == random_points.shape[ 0 ]
        assert eight_hex_grid_empty.GetNumberOfCells() == random_cells.shape[ 0 ]

    def test_get_vtu_filepaths( self ):
        pvd_filepath: str = tvu.create_geos_pvd( tvu.stored_grids, tvu.pvd_directory )
        options_pvd0: fo.Options = fo.Options( support="point",
                                               source=pvd_filepath,
                                               copy_fields=dict(),
                                               created_fields=dict(),
                                               vtm_index=0,
                                               vtk_output=out_points )
        options_pvd1: fo.Options = fo.Options( support="point",
                                               source=pvd_filepath,
                                               copy_fields=dict(),
                                               created_fields=dict(),
                                               vtm_index=-1,
                                               vtk_output=out_points )
        result0: tuple[ str ] = fo.get_vtu_filepaths( options_pvd0 )
        result1: tuple[ str ] = fo.get_vtu_filepaths( options_pvd1 )
        try:
            shutil.rmtree( tvu.pvd_directory )
        except OSError as e:
            print( f"Error: {e}" )
        os.remove( pvd_filepath )
        for i in range( len( result0 ) ):
            assert "time0" in result0[ i ]  # looking through first vtm which is time0
            assert "time1" in result1[ i ]  # looking through last vtm which is time1

    def test_get_reorder_mapping( self ):
        support_points: array = fo.support_construction[ "point" ]( eight_hex_grid )
        support_cells: array = fo.support_construction[ "cell" ]( eight_hex_grid )
        kd_tree_points: KDTree = KDTree( support_points )
        kd_tree_cells: KDTree = KDTree( support_cells )
        result_points1: array = fo.get_reorder_mapping( kd_tree_points, hex0_grid, "point" )
        result_cells1: array = fo.get_reorder_mapping( kd_tree_cells, hex0_grid, "cell" )
        result_points2: array = fo.get_reorder_mapping( kd_tree_points, hex1_grid, "point" )
        result_cells2: array = fo.get_reorder_mapping( kd_tree_cells, hex1_grid, "cell" )
        assert result_points1.tolist() == [ 0, 1, 4, 3, 9, 10, 13, 12 ]
        assert result_points2.tolist() == [ 0 + 1, 1 + 1, 4 + 1, 3 + 1, 9 + 1, 10 + 1, 13 + 1, 12 + 1 ]
        assert result_cells1.tolist() == [ 0 ]
        assert result_cells2.tolist() == [ 1 ]

    def test_get_array_names_to_collect_and_options( self ):
        vu.write_mesh( eight_hex_grid, eight_hex_grid_output )
        options1: fo.Options = fo.Options( "cell", eight_hex_grid_output.output, copy_fields_cells,
                                           created_fields_cells, -1, out_cells )
        options2: fo.Options = fo.Options( "point", eight_hex_grid_output.output, copy_fields_points,
                                           created_fields_points, -1, out_points )
        result1, options1_new = fo.get_array_names_to_collect_and_options( eight_hex_grid_output.output, options1 )
        result2, options2_new = fo.get_array_names_to_collect_and_options( eight_hex_grid_output.output, options2 )
        os.remove( eight_hex_grid_output.output )
        assert result1.sort() == [ fc[ 0 ] for fc in copy_fields_cells ].sort()
        assert result2.sort() == [ fp[ 0 ] for fp in copy_fields_points ].sort()
        assert options1_new.copy_fields.sort() == copy_fields_cells.sort()
        assert options2_new.copy_fields.sort() == copy_fields_points.sort()

    def test_merge_local_in_global_array( self ):
        # create arrays filled with nan values
        glob_arr_points_1D: array = full( ( 8, 1 ), nan )
        glob_arr_cells_1D: array = full( ( 8, 1 ), nan )
        glob_arr_points_3D: array = full( ( 8, 3 ), nan )
        glob_arr_cells_3D: array = full( ( 8, 3 ), nan )
        loc_arr_points_1D: array = array( list( range( 0, 4 ) ) )
        loc_arr_cells_1D: array = array( list( range( 4, 8 ) ) )
        loc_arr_points_3D: array = array(
            ( list( range( 0, 3 ) ), list( range( 6, 9 ) ), list( range( 12, 15 ) ), list( range( 18, 21 ) ) ) )
        loc_arr_cells_3D: array = array(
            ( list( range( 3, 6 ) ), list( range( 9, 12 ) ), list( range( 15, 18 ) ), list( range( 21, 24 ) ) ) )
        mapping_points: array = array( [ 0, 2, 4, 6 ] )
        mapping_cells: array = array( [ 7, 5, 3, 1 ] )
        fo.merge_local_in_global_array( glob_arr_points_1D, loc_arr_points_1D, mapping_points )
        fo.merge_local_in_global_array( glob_arr_cells_1D, loc_arr_cells_1D, mapping_cells )
        fo.merge_local_in_global_array( glob_arr_points_3D, loc_arr_points_3D, mapping_points )
        fo.merge_local_in_global_array( glob_arr_cells_3D, loc_arr_cells_3D, mapping_cells )
        expected_points_1D: array = array( [ 0, nan, 1, nan, 2, nan, 3, nan ] ).reshape( -1, 1 )
        expected_cells_1D: array = array( [ nan, 7, nan, 6, nan, 5, nan, 4 ] ).reshape( -1, 1 )
        expected_points_3D: array = array( [ [ 0, 1, 2 ], [ nan, nan, nan ], [ 6, 7, 8 ], [ nan, nan, nan ],
                                             [ 12, 13, 14 ], [ nan, nan, nan ], [ 18, 19, 20 ], [ nan, nan, nan ] ] )
        expected_cells_3D: array = array( [ [ nan, nan, nan ], [ 21, 22, 23 ], [ nan, nan, nan ], [ 15, 16, 17 ],
                                            [ nan, nan, nan ], [ 9, 10, 11 ], [ nan, nan, nan ], [ 3, 4, 5 ] ] )
        assert array_equal( glob_arr_points_1D, expected_points_1D, equal_nan=True )
        assert array_equal( glob_arr_cells_1D, expected_cells_1D, equal_nan=True )
        assert array_equal( glob_arr_points_3D, expected_points_3D, equal_nan=True )
        assert array_equal( glob_arr_cells_3D, expected_cells_3D, equal_nan=True )

    def test_implement_arrays( self ):
        output: vu.VtkOutput = vu.VtkOutput( "filled.vtu", True )
        empty_mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
        empty_mesh.DeepCopy( eight_hex_grid_empty )
        npoints: int = empty_mesh.GetNumberOfPoints()
        ncells: int = empty_mesh.GetNumberOfCells()
        copy_fpoints = [ ( "point_param0", ), ( "point_param1", "point_copy1" ),
                         ( "point_param2", "point_param2", "*10 + 0.1" ) ]
        copy_fcells = [ ( "cell_param0", ), ( "cell_param1", "cell_copy1" ),
                        ( "cell_param2", "cell_param2", "/0.1 - 0.5" ) ]
        create_fpoints = [ ( "new0", "log(point_param0)" ), ( "new1", "sqrt(point_param1)" ),
                           ( "new2", "distances_mesh_center" ) ]
        create_fcells = [ ( "new3", "sqrt(cell_param0)" ), ( "new4", "log10(cell_param1)" ),
                          ( "new5", "cell_param0 + cell_param1" ) ]
        options_point = fo.Options( "point", "empty.vtu", copy_fpoints, create_fpoints, -1, output )
        options_cell = fo.Options( "cell", "empty.vtu", copy_fcells, create_fcells, -1, output )
        fo.implement_arrays( empty_mesh, eight_hex_grid_values, options_point )
        fo.implement_arrays( empty_mesh, eight_hex_grid_values, options_cell )
        point_data_mesh = empty_mesh.GetPointData()
        cell_data_mesh = empty_mesh.GetCellData()
        expected_results: dict[ str, array ] = {
            "point_param0": eight_hex_grid_values[ "point_param0" ],
            "point_copy1": eight_hex_grid_values[ "point_param1" ],
            "point_param2": eight_hex_grid_values[ "point_param2" ] * 10 + 0.1,
            "cell_param0": eight_hex_grid_values[ "cell_param0" ],
            "cell_copy1": eight_hex_grid_values[ "cell_param1" ],
            "cell_param2": eight_hex_grid_values[ "cell_param2" ] / 0.1 - 0.5,
            "new0": log( eight_hex_grid_values[ "point_param0" ] ),
            "new1": sqrt( eight_hex_grid_values[ "point_param1" ] ),
            "new2": fo.get_distances_mesh_center( empty_mesh, "point" ).reshape( ( npoints, 1 ) ),
            "new3": sqrt( eight_hex_grid_values[ "cell_param0" ] ),
            "new4": log10( eight_hex_grid_values[ "cell_param1" ] ),
            "new5": eight_hex_grid_values[ "cell_param0" ] + eight_hex_grid_values[ "cell_param1" ]
        }
        for data, nelements in zip( [ point_data_mesh, cell_data_mesh ], [ npoints, ncells ] ):
            for i in range( data.GetNumberOfArrays() ):
                array_name: str = data.GetArrayName( i )
                result: array = vtk_to_numpy( data.GetArray( i ) )
                if len( result.shape ) == 1:
                    result = result.reshape( ( nelements, 1 ) )
                assert array_equal( result, expected_results[ array_name ] )
