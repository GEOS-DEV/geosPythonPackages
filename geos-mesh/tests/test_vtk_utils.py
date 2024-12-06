import glob
import os
import shutil
import xml.etree.ElementTree as ET
from geos.mesh.doctor.checks import vtk_utils as vu
from numpy import array, ones, array_equal
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkCommonDataModel import ( vtkMultiBlockDataSet, vtkUnstructuredGrid, vtkCellArray, vtkHexahedron,
                                            vtkCompositeDataSet, VTK_HEXAHEDRON )


"""
For creation of output test meshes
"""
current_file_path: str = __file__
dir_name: str = os.path.dirname( current_file_path )
pattern_test: str = "to_check_mesh"
filepath_mesh_for_stats: str = os.path.join( dir_name, pattern_test + ".vtu" )
test_mesh_for_stats: vu.VtkOutput = vu.VtkOutput( filepath_mesh_for_stats, True )
geos_hierarchy: str = os.path.join( "mesh", "Level0" )


"""
Utility functions for tests
"""
def split_list( initial_list: list[ any ], number_sub_lists: int ) -> list[ list[ any ] ]:
    initial_len: int = len( initial_list )
    assert number_sub_lists <= initial_len
    average: int = initial_len // number_sub_lists
    remainder: int = initial_len % number_sub_lists
    new_lists: list = list()
    start: int = 0
    for i in range( initial_len ):
        end: int = start + average + ( 1 if i < remainder else 0 )
        new_lists.append( initial_list[ start:end ] )
        start = end
    return new_lists


def create_vtk_points( point_3D_coords: list[ list[ float ] ] ) -> vtkPoints:
    points: vtkPoints = vtkPoints()
    for coord in point_3D_coords:
        points.InsertNextPoint( coord )
    return points


def create_vtk_hexahedron( point_ids: list[ int ] ) -> vtkHexahedron:
    hex: vtkHexahedron = vtkHexahedron()
    for i, point_id in enumerate( point_ids ):
        hex.GetPointIds().SetId( i, point_id )
    return hex


def create_type_vtk_grid( point_3D_coords: list[ list[  float ] ],
                          all_point_ids: list[ list[ int ] ],
                          vtk_type: int ) -> vtkUnstructuredGrid:
    points: vtkPoints = create_vtk_points( point_3D_coords )
    cells: vtkCellArray = vtkCellArray()
    for point_ids in all_point_ids:
        cells.InsertNextCell( create_vtk_hexahedron( point_ids ) )
    grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
    grid.SetPoints( points )
    grid.SetCells( vtk_type, cells )
    return grid


def create_geos_pvd( all_grids_per_vtm: dict[ str, dict[ str, list[ vtkUnstructuredGrid ] ] ],
                     pvd_dir_path: str ) -> str:
    # Create the .pvd
    os.makedirs( pvd_dir_path, exist_ok=True )
    pvd_name = os.path.basename( pvd_dir_path )
    root_pvd = ET.Element( "VTKFile", type="Collection", version="1.0" )
    collection = ET.SubElement( root_pvd, "Collection" )

    for timestep, regions_with_grids in all_grids_per_vtm.items():
        vtm_directory: str = os.path.join( pvd_dir_path, timestep )
        os.makedirs( vtm_directory, exist_ok=True )
        vtm_sub_path: str = os.path.join( pvd_name, timestep + ".vtm" )
        ET.SubElement( collection, "DataSet", timestep=timestep, file=vtm_sub_path )

        # Create the .vtm file respecting GEOS format
        root_vtm = ET.Element( "VTKFile", type="vtkMultiBlockDataSet", version="1.0" )
        vtm = ET.SubElement( root_vtm, "vtkMultiBlockDataSet" )
        mesh_block = ET.SubElement( vtm, "Block", name="mesh" )
        level0_block = ET.SubElement( mesh_block, "Block", name="Level0" )
        cell_element_region_block = ET.SubElement( level0_block, "Block", name="CellElementRegion" )

        for region, grids in regions_with_grids.items():
            region_directory: str = os.path.join( vtm_directory, geos_hierarchy, region )
            os.makedirs( region_directory, exist_ok=True )

            # Create block element for regions
            region_block = ET.SubElement( cell_element_region_block, "Block", name=region )
            for i, grid in enumerate( grids ):
                rank_name: str = "rank_0" + str( i )
                vtu_name: str = rank_name + ".vtu"
                path_from_vtm: str = os.path.join( timestep, geos_hierarchy, region, vtu_name )
                ET.SubElement( region_block, "DataSet", name=rank_name, file=path_from_vtm )
                vtu_filepath: str = os.path.join( region_directory, vtu_name )
                output_vtu: vu.VtkOutput = vu.VtkOutput( vtu_filepath, False )
                vu.write_mesh( grid, output_vtu )

        # write the vtm for each timestep
        vtm_filepath: str = os.path.join( pvd_directory, timestep + ".vtm" )
        tree_vtm = ET.ElementTree( root_vtm )
        tree_vtm.write( vtm_filepath, encoding='utf-8', xml_declaration=True )

    # write the pvd file link to the vtms written before
    tree_pvd = ET.ElementTree( root_pvd )
    pvd_filepath: str = os.path.join( os.path.dirname( pvd_dir_path ), pvd_name + ".pvd" )
    tree_pvd.write( pvd_filepath, encoding='utf-8', xml_declaration=True )

    return pvd_filepath


"""
Grids to perform tests on.
"""
# 4 Hexahedrons
four_hex_ids: list[ list[ int ] ] = [ [ 0, 1, 4, 3, 6, 7, 10, 9 ],
                                      [ 1, 2, 5, 4, 7, 8, 11, 10 ],
                                      [ 6, 7, 10, 9, 12, 13, 16, 15 ],
                                      [ 7, 8, 11, 10, 13, 14, 17, 16 ] ]

four_hexs_points_coords: list[ list[ float ] ] = [ [ 0.0, 0.0, 0.0 ],  # point0
                                                   [ 1.0, 0.0, 0.0 ],  # point1
                                                   [ 2.0, 0.0, 0.0 ],  # point2
                                                   [ 0.0, 1.0, 0.0 ],  # point3
                                                   [ 1.0, 1.0, 0.0 ],  # point4
                                                   [ 2.0, 1.0, 0.0 ],  # point5
                                                   [ 0.0, 0.0, 1.0 ],  # point6
                                                   [ 1.0, 0.0, 1.0 ],  # point7
                                                   [ 2.0, 0.0, 1.0 ],  # point8
                                                   [ 0.0, 1.0, 1.0 ],  # point9
                                                   [ 1.0, 1.0, 1.0 ],  # point10
                                                   [ 2.0, 1.0, 1.0 ],  # point11
                                                   [ 0.0, 0.0, 2.0 ],  # point12
                                                   [ 1.0, 0.0, 2.0 ],  # point13
                                                   [ 2.0, 0.0, 2.0 ],  # point14
                                                   [ 0.0, 1.0, 2.0 ],  # point15
                                                   [ 1.0, 1.0, 2.0 ],  # point16
                                                   [ 2.0, 1.0, 2.0 ] ] # point17
# Create grid
four_hex_grid: vtkUnstructuredGrid = create_type_vtk_grid( four_hexs_points_coords, four_hex_ids, VTK_HEXAHEDRON )
# Create output paths
path_four_hex_vtu: str = os.path.join( dir_name, "4_hex.vtu" )
path_four_hex_vtk: str = os.path.join( dir_name, "4_hex.vtk" )
output_four_hex_vtu: vu.VtkOutput = vu.VtkOutput( path_four_hex_vtu, False )
output_four_hex_vtk: vu.VtkOutput = vu.VtkOutput( path_four_hex_vtk, False )


# 8 Hexahedrons divided in 2 regions and for each region into 2 ranks
two_hex_ids = [ [ 0, 1, 4, 3, 6, 7, 10, 9 ],
                [ 1, 2, 5, 4, 7, 8, 11, 10 ] ]
## GRID 1
two_hex1_points_coords: list[ list[ float ] ] = [ [ 0.0, 0.0, 0.0 ],  # point0
                                                  [ 1.0, 0.0, 0.0 ],  # point1
                                                  [ 2.0, 0.0, 0.0 ],  # point2
                                                  [ 0.0, 1.0, 0.0 ],  # point3
                                                  [ 1.0, 1.0, 0.0 ],  # point4
                                                  [ 2.0, 1.0, 0.0 ],  # point5
                                                  [ 0.0, 0.0, 1.0 ],  # point6
                                                  [ 1.0, 0.0, 1.0 ],  # point7
                                                  [ 2.0, 0.0, 1.0 ],  # point8
                                                  [ 0.0, 1.0, 1.0 ],  # point9
                                                  [ 1.0, 1.0, 1.0 ],  # point10
                                                  [ 2.0, 1.0, 1.0 ] ] # point11
two_hex1_grid: vtkUnstructuredGrid = create_type_vtk_grid( two_hex1_points_coords, two_hex_ids, VTK_HEXAHEDRON )

## GRID 2
two_hex2_points_coords: list[ list[ float ] ] = [ [ 0.0, 1.0, 0.0 ],  # point0
                                                  [ 1.0, 1.0, 0.0 ],  # point1
                                                  [ 2.0, 1.0, 0.0 ],  # point2
                                                  [ 0.0, 2.0, 0.0 ],  # point3
                                                  [ 1.0, 2.0, 0.0 ],  # point4
                                                  [ 2.0, 2.0, 0.0 ],  # point5
                                                  [ 0.0, 1.0, 1.0 ],  # point6
                                                  [ 1.0, 1.0, 1.0 ],  # point7
                                                  [ 2.0, 1.0, 1.0 ],  # point8
                                                  [ 0.0, 2.0, 1.0 ],  # point9
                                                  [ 1.0, 2.0, 1.0 ],  # point10
                                                  [ 2.0, 2.0, 1.0 ] ] # point11
two_hex2_grid: vtkUnstructuredGrid = create_type_vtk_grid( two_hex2_points_coords, two_hex_ids, VTK_HEXAHEDRON )

## GRID 3
two_hex3_points_coords: list[ list[ float ] ] = [ [ 0.0, 0.0, 1.0 ],  # point0
                                                  [ 1.0, 0.0, 1.0 ],  # point1
                                                  [ 2.0, 0.0, 1.0 ],  # point2
                                                  [ 0.0, 1.0, 1.0 ],  # point3
                                                  [ 1.0, 1.0, 1.0 ],  # point4
                                                  [ 2.0, 1.0, 1.0 ],  # point5
                                                  [ 0.0, 0.0, 2.0 ],  # point6
                                                  [ 1.0, 0.0, 2.0 ],  # point7
                                                  [ 2.0, 0.0, 2.0 ],  # point8
                                                  [ 0.0, 1.0, 2.0 ],  # point9
                                                  [ 1.0, 1.0, 2.0 ],  # point10
                                                  [ 2.0, 1.0, 2.0 ] ] # point11
two_hex3_grid: vtkUnstructuredGrid = create_type_vtk_grid( two_hex3_points_coords, two_hex_ids, VTK_HEXAHEDRON )

## GRID 4
two_hex4_points_coords: list[ list[ float ] ] = [ [ 0.0, 1.0, 1.0 ],  # point0
                                                  [ 1.0, 1.0, 1.0 ],  # point1
                                                  [ 2.0, 1.0, 1.0 ],  # point2
                                                  [ 0.0, 2.0, 1.0 ],  # point3
                                                  [ 1.0, 2.0, 1.0 ],  # point4
                                                  [ 2.0, 2.0, 1.0 ],  # point5
                                                  [ 0.0, 1.0, 2.0 ],  # point6
                                                  [ 1.0, 1.0, 2.0 ],  # point7
                                                  [ 2.0, 1.0, 2.0 ],  # point8
                                                  [ 0.0, 2.0, 2.0 ],  # point9
                                                  [ 1.0, 2.0, 2.0 ],  # point10
                                                  [ 2.0, 2.0, 2.0 ] ] # point11
two_hex4_grid: vtkUnstructuredGrid = create_type_vtk_grid( two_hex4_points_coords, two_hex_ids, VTK_HEXAHEDRON )
all_two_hex_grids: list[ vtkUnstructuredGrid ] = [ two_hex1_grid, two_hex2_grid, two_hex3_grid, two_hex4_grid ]


## Duplicated grids but with different DataArrays per region and per timestep
number_timesteps: int = 2
number_regions: int = 2

# Create the target directories for the tests and generate the vtms
pvd_name: str = "vtkOutput"
pvd_directory: str = os.path.join( dir_name, pvd_name )
region_name: str = "region"
stored_grids: dict[ str, dict[ str, list[ vtkUnstructuredGrid ] ] ] = dict()
for i in range( number_timesteps ):
    vtm_name: str = "time" + str( i )
    stored_grids[ vtm_name ] = dict()
    splitted_grids_by_region: list[ list[ vtkUnstructuredGrid ] ] = split_list( all_two_hex_grids, number_regions )
    for j in range( number_regions ):
        region: str = region_name + str( j )
        stored_grids[ vtm_name ][ region ] = list()
        for k, grid in enumerate( splitted_grids_by_region[ j ] ):
            new_grid: vtkUnstructuredGrid = vtkUnstructuredGrid()
            new_grid.DeepCopy( grid )
            for dimension in [ 1, 2, 3 ]:
                arr_np: array = ones( ( new_grid.GetNumberOfCells(), dimension ), dtype=int ) * ( i * 100 + 10 * j + k )
                arr_points = numpy_to_vtk( arr_np )
                arr_cells = numpy_to_vtk( arr_np )
                arr_points.SetName( "point_param" + str( dimension ) )
                arr_cells.SetName( "cell_param" + str( dimension ) )
                new_grid.GetPointData().AddArray( arr_points )
                new_grid.GetCellData().AddArray( arr_cells )
            stored_grids[ vtm_name ][ region ].append( new_grid )


class TestClass:

    def test_to_vtk_id_list_and_vtk_iter( self ):
        # vtk_id_list
        data1: list[ int ] = [ 0, 1, 2 ]
        data2: tuple[ int ] = ( 3, 4, 5, 6 )
        result = vu.to_vtk_id_list( data1 )
        result2 = vu.to_vtk_id_list( data2 )
        assert result.IsA("vtkIdList")
        assert result2.IsA("vtkIdList")
        assert result.GetNumberOfIds() == 3
        assert result2.GetNumberOfIds() == 4
        # vtk_iter
        result3 = list( vu.vtk_iter( result ) )
        result4 = tuple( vu.vtk_iter( result2 ) )
        assert len( result3 ) == 3
        assert len( result4 ) == 4
        assert result3 == data1
        assert result4 == data2

    def test_write_and_read_mesh( self ):
        found_files_vtu: list[ str ] = list()
        found_files_vtk: list[ str ] = list()
        found_files_vtu.extend( glob.glob( os.path.join( dir_name, "*.vtu" ) ) )
        found_files_vtu.extend( glob.glob( os.path.join( dir_name, "*.vtk" ) ) )
        assert len( found_files_vtu ) == 0
        assert len( found_files_vtk ) == 0
        vu.write_mesh( four_hex_grid, output_four_hex_vtu )
        vu.write_mesh( four_hex_grid, output_four_hex_vtk )
        found_files_vtu.extend( glob.glob( os.path.join( dir_name, "*.vtu" ) ) )
        found_files_vtk.extend( glob.glob( os.path.join( dir_name, "*.vtk" ) ) )
        assert len( found_files_vtu ) == 1
        assert len( found_files_vtk ) == 1
        # no overwritting possible
        vu.write_mesh( four_hex_grid, output_four_hex_vtu )
        vu.write_mesh( four_hex_grid, output_four_hex_vtk )
        assert len( found_files_vtu ) == 1
        assert len( found_files_vtk ) == 1
        # read the meshes
        read_vtu: vtkUnstructuredGrid = vu.read_mesh( output_four_hex_vtu.output )
        read_vtk: vtkUnstructuredGrid = vu.read_mesh( output_four_hex_vtu.output )
        try:
            os.remove( output_four_hex_vtu.output )
            os.remove( output_four_hex_vtk.output )
        except Exception as e:
            raise ValueError( f"test_write_and_read_mesh failed because of '{e}'." )
        assert read_vtu.GetNumberOfCells() == four_hex_grid.GetNumberOfCells()
        assert read_vtk.GetNumberOfCells() == four_hex_grid.GetNumberOfCells()

    def test_write_and_read_vtm( self ):
        multiblock: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        for i in range( 5 ):
            vtu: vtkUnstructuredGrid = vtkUnstructuredGrid()
            multiblock.SetBlock( i, vtu )
            multiblock.GetMetaData( i ).Set( vtkCompositeDataSet.NAME(), "rank" + str( i ) )
        output_vtk: vu.VtkOutput = vu.VtkOutput( os.path.join( dir_name, "test.vtm" ), True )
        vu.write_VTM( multiblock, output_vtk )
        mulltiblock_read: vtkMultiBlockDataSet = vu.read_vtm( output_vtk.output )
        os.remove( output_vtk.output )
        assert multiblock.GetNumberOfBlocks() == mulltiblock_read.GetNumberOfBlocks() == 5

    def test_get_filepath_from_pvd_and_vtm( self ):
        pvd_filepath: str = create_geos_pvd( stored_grids, pvd_directory )
        result0: str = vu.get_vtm_filepath_from_pvd( pvd_filepath, 0 )
        result1: str = vu.get_vtm_filepath_from_pvd( pvd_filepath, 1 )
        result2: list[ str ] = vu.get_vtu_filepaths_from_vtm( result0 )

        try:
            shutil.rmtree( pvd_directory )
        except OSError as e:
            print( f"Error: {e}" )
        os.remove( pvd_filepath )

        assert result0.endswith( "time0.vtm" )
        assert result1.endswith( "time1.vtm" )
        for i, path2 in enumerate( result2 ):
            if i % 4 < 2:
                region_name: str = "region0"
            else:
                region_name = "region1"
            if i % 2 == 0:
                assert path2.endswith( os.path.join( geos_hierarchy, region_name, "rank_00.vtu" ) )
            else:
                assert path2.endswith( os.path.join( geos_hierarchy, region_name, "rank_01.vtu" ) )
        

    def test_has_invalid_field( self ):
        # initialize test meshes
        test_mesh_points: vtkUnstructuredGrid = four_hex_grid.NewInstance()
        test_mesh_cells: vtkUnstructuredGrid = four_hex_grid.NewInstance()
        test_mesh: vtkUnstructuredGrid = four_hex_grid.NewInstance()
        test_mesh_points.CopyStructure( four_hex_grid )
        test_mesh_cells.CopyStructure( four_hex_grid )
        test_mesh.CopyStructure( four_hex_grid )
        test_mesh_points.CopyAttributes( four_hex_grid )
        test_mesh_cells.CopyAttributes( four_hex_grid )
        test_mesh.CopyAttributes( four_hex_grid )
        # create vtk arrays
        array_for_points: array = ones( ( test_mesh_points.GetNumberOfPoints(), 1 ) )
        array_for_cells: array = ones( ( test_mesh_cells.GetNumberOfCells(), 1 ) )
        vtk_array_points_invalid = numpy_to_vtk( array_for_points )
        vtk_array_cells_invalid = numpy_to_vtk( array_for_cells )
        vtk_array_points_valid = numpy_to_vtk( array_for_points )
        vtk_array_cells_valid = numpy_to_vtk( array_for_cells )
        invalid_fields: list[ str ] = [ "PointsWrong", "CellsWrong" ]
        vtk_array_points_invalid.SetName( invalid_fields[ 0 ] )
        vtk_array_cells_invalid.SetName( invalid_fields[ 1 ] )
        vtk_array_points_valid.SetName( "PointsValid" )
        vtk_array_cells_valid.SetName( "CellsValid" )
        # add vtk arrays
        test_mesh_points.GetPointData().AddArray( vtk_array_points_invalid )
        test_mesh_cells.GetCellData().AddArray( vtk_array_cells_invalid )
        test_mesh.GetPointData().AddArray( vtk_array_points_valid )
        test_mesh.GetCellData().AddArray( vtk_array_cells_valid )
        # check invalid_fields
        assert vu.has_invalid_field( test_mesh_points, invalid_fields ) == True
        assert vu.has_invalid_field( test_mesh_cells, invalid_fields ) == True
        assert vu.has_invalid_field( test_mesh, invalid_fields ) == False

    def test_get_points_coords_from_vtk( self ):
        result: array = vu.get_points_coords_from_vtk( four_hex_grid )
        assert four_hexs_points_coords == result.tolist()

    def test_get_cell_centers_array( self ):
        result: array = vu.get_cell_centers_array( four_hex_grid )
        assert array_equal( result,
                            array( [ [ 0.5, 0.5, 0.5 ], [ 1.5, 0.5, 0.5 ], [ 0.5, 0.5, 1.5 ], [ 1.5, 0.5, 1.5 ] ] ) )
