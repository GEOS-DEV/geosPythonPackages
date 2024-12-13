import logging
from numexpr import evaluate
from dataclasses import dataclass
from math import sqrt
from numpy import array, empty, full, int64, nan
from numpy.random import rand
from scipy.spatial import KDTree
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.checks.vtk_utils import ( VtkOutput, get_points_coords_from_vtk, get_cell_centers_array,
                                                get_vtm_filepath_from_pvd, get_vtu_filepaths_from_vtm,
                                                get_all_array_names, read_mesh, write_mesh )


@dataclass( frozen=True )
class Options:
    support: str
    source: str
    copy_fields: dict[ str, list[ str ] ]
    created_fields: dict[ str, str ]
    vtm_index: int
    out_vtk: VtkOutput


@dataclass( frozen=True )
class Result:
    info: bool


__SUPPORT_CHOICES = [ "point", "cell" ]
support_construction: dict[ str, tuple[ any ] ] = {
    __SUPPORT_CHOICES[ 0 ]: get_points_coords_from_vtk,
    __SUPPORT_CHOICES[ 1 ]: get_cell_centers_array
}


def get_distances_mesh_center( mesh: vtkUnstructuredGrid, support: str ) -> array:
    f"""For a specific support type {__SUPPORT_CHOICES}, returns a numpy array filled with the distances between
    their coordinates and the center of the mesh.

    Args:
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        array: [ distance0, distance1, ..., distanceN ] with N being the number of support elements.
    """
    if support == __SUPPORT_CHOICES[ 0 ]:
        coords: array = get_points_coords_from_vtk( mesh )
    elif support == __SUPPORT_CHOICES[ 1 ]:
        coords = get_cell_centers_array( mesh )
    else:
        raise ValueError( f"For support, the only choices available are {__SUPPORT_CHOICES}." )

    center = ( coords.max( axis=0 ) + coords.min( axis=0 ) ) / 2
    distances = empty( coords.shape[ 0 ] )
    for i in range( coords.shape[ 0 ] ):
        distance_squared: float = 0.0
        coord = coords[ i ]
        for j in range( len( coord ) ):
            distance_squared += ( coord[ j ] - center[ j ] ) * ( coord[ j ] - center[ j ] )
        distances[ i ] = sqrt( distance_squared )
    return distances


def get_random_field( mesh: vtkUnstructuredGrid, support: str ) -> array:
    f"""For a specific support type {__SUPPORT_CHOICES}, an array with samples from a uniform distribution over [0, 1).

    Args:
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        array: Array of size N being the number of support elements.
    """
    if support == __SUPPORT_CHOICES[ 0 ]:
        number_elements: int = mesh.GetNumberOfPoints()
    elif support == __SUPPORT_CHOICES[ 1 ]:
        number_elements = mesh.GetNumberOfCells()
    else:
        raise ValueError( f"For support, the only choices available are {__SUPPORT_CHOICES}." )
    return rand( number_elements, 1 )


create_precoded_fields: dict[ str, any ] = {
    "distances_mesh_center": get_distances_mesh_center,
    "random": get_random_field
}


def get_vtu_filepaths( options: Options ) -> tuple[ str ]:
    """Returns the vtu filepaths to use for the rest of the workflow.

    Args:
        options (Options): Options chosen by the user.

    Returns:
        tuple[ str ]: ( "file/path/0.vtu", ..., "file/path/N.vtu" )
    """
    source_filepath: str = options.source
    if source_filepath.endswith( ".vtu" ):
        return ( source_filepath, )
    elif source_filepath.endswith( ".vtm" ):
        return get_vtu_filepaths_from_vtm( source_filepath )
    elif source_filepath.endswith( ".pvd" ):
        vtm_filepath: str = get_vtm_filepath_from_pvd( source_filepath, options.vtm_index )
        return get_vtu_filepaths_from_vtm( vtm_filepath )
    else:
        raise ValueError( f"The filepath '{options.source}' provided targets neither a .vtu, a .vtm nor a .pvd file." )


def get_reorder_mapping( kd_tree_grid_ref: KDTree, sub_grid: vtkUnstructuredGrid, support: str ) -> array:
    """Builds an array containing the indexes of the reference grid linked to every
    cell ids / point ids of the subset grid.

    Args:
        kd_tree_grid_ref (KDTree): A KDTree of the nearest neighbor cell centers for every cells /
        points coordinates for point of the reference grid.
        sub_grid (vtkUnstructuredGrid): A vtk grid that is a subset of the reference grid.
        support (str): Either "point" or "cell".

    Returns:
        np.array: [ cell_idK_grid, cell_idN_grid, ... ] or [ point_idK_grid, point_idN_grid, ... ]
    """
    support_elements: array = support_construction[ support ]( sub_grid )
    # now that you have the support elements, you can map them to the reference grid
    number_elements: int = support_elements.shape[ 0 ]
    mapping: array = empty( number_elements, dtype=int64 )
    for cell_id in range( number_elements ):
        _, index = kd_tree_grid_ref.query( support_elements[ cell_id ] )
        mapping[ cell_id ] = index
    return mapping


def __compatible_meshes( dest_mesh, source_mesh ) -> bool:
    # for now, just check that meshes have same number of elements and same number of nodes
    # and require that each cell has same nodes, each node has same coordinate
    dest_ne = dest_mesh.GetNumberOfCells()
    dest_nn = dest_mesh.GetNumberOfPoints()
    source_ne = source_mesh.GetNumberOfCells()
    source_nn = source_mesh.GetNumberOfPoints()

    if dest_ne != source_ne:
        logging.error( 'meshes have different number of cells' )
        return False
    if dest_nn != source_nn:
        logging.error( 'meshes have different number of nodes' )
        return False

    for i in range( dest_nn ):
        if not ( ( dest_mesh.GetPoint( i ) ) == ( source_mesh.GetPoint( i ) ) ):
            logging.error( 'at least one node is in a different location' )
            return False

    for i in range( dest_ne ):
        if not ( vtk_to_numpy( dest_mesh.GetCell( i ).GetPoints().GetData() ) == vtk_to_numpy(
                source_mesh.GetCell( i ).GetPoints().GetData() ) ).all():
            logging.error( 'at least one cell has different nodes' )
            return False

    return True


def get_array_names_to_collect( sub_vtu_filepath: str, options: Options ) -> list[ str ]:
    """We need to have the list of array names that are required to perform copy and creation of new arrays. To build
    global_arrays to perform operations, we need only these names and not all array names present in the sub meshes.

    Args:
        sub_vtu_filepath (str): Path to sub vtu file that can be used to find the names of the arrays within its data.
        options (Options): Options chosen by the user.

    Returns:
        list[ str ]: Array names.
    """
    ref_mesh: vtkUnstructuredGrid = read_mesh( sub_vtu_filepath )
    all_array_names: dict[ str, dict[ str, int ] ] = get_all_array_names( ref_mesh )
    if options.support == __SUPPORT_CHOICES[ 0 ]:  # point
        support_array_names: list[ str ] = list( all_array_names[ "PointData" ].keys() )
    else:  # cell
        support_array_names: list[ str ] = list( all_array_names[ "CellData" ].keys() )

    to_use_arrays: set[ str ] = set()
    for name in options.copy_fields.keys():
        if name in support_array_names:
            to_use_arrays.add( name )
        else:
            logging.warning( f"The field named '{name}' does not exist in '{sub_vtu_filepath}' in the data. " +
                             "Cannot perform operations on it." )

    for function in options.created_fields.values():
        for support_array_name in support_array_names:
            if support_array_name in function:
                to_use_arrays.add( support_array_name )

    return list( to_use_arrays )


def merge_local_in_global_array( global_array: array, local_array: array, mapping: array ) -> None:
    """Fill the values of a global_array using the values contained in a local_array that is smaller or equal to the
    size as the global_array. A mapping is used to copy the values from the local_array to the right indexes in
    the global_array.

    Args:
        global_array (np.array): Array of size N.
        local_array (np.array): Array of size M <= N that is representing a subset of the global_array.
        mapping (np.array): Array of global indexes of size M.
    """
    size_global, size_local = global_array.shape, local_array.shape
    assert size_global[ 0 ] >= size_local[ 0 ], "The global array to fill is smaller than the local array to merge."
    number_columns_global: int = size_global[ 1 ] if len( size_global ) == 2 else 1
    number_columns_local: int = size_local[ 1 ] if len( size_local ) == 2 else 1
    assert number_columns_global == number_columns_local, "The arrays do not have same number of columns."
    # when converting a numpy array to vtk array, you need to make sure to have a 2D array
    if len( size_local ) == 1:
        local_array = local_array.reshape( -1, 1 )
    global_array[ mapping ] = local_array


def implement_arrays( mesh: vtkUnstructuredGrid, global_arrays: dict[ str, array ], options: Options ) -> None:
    """Implement the arrays that are contained in global_arrays into the Data of a mesh.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        global_arrays (dict[ str, np.array ]): { "array_name0": np.array, ..., "array_nameN": np.array }
        options (Options): Options chosen by the user.
    """
    data = mesh.GetPointData() if options.support == __SUPPORT_CHOICES[ 0 ] else mesh.GetCellData()
    number_elements: int = mesh.GetNumberOfPoints() if options.support == __SUPPORT_CHOICES[ 0 ] else \
                           mesh.GetNumberOfCells()

    arrays_to_implement: dict[ str, array ] = dict()
    # proceed copy operations
    for name, new_name_expression in options.copy_fields.items():
        new_name: str = name
        if len( new_name_expression ) > 0:
            new_name: str = new_name_expression[ 0 ]
        if len( new_name_expression ) == 2:
            expression: str = new_name_expression[ 1 ]
            copy_arr: array = evaluate( name + expression, local_dict=global_arrays )
        else:
            copy_arr = global_arrays[ name ]
        arrays_to_implement[ new_name ] = copy_arr

    # proceed create operations
    for new_name, expression in options.created_fields.items():
        if expression in create_precoded_fields:
            created_arr: array = create_precoded_fields[ expression ]( mesh, options.support )
        else:
            created_arr = evaluate( expression, local_dict=global_arrays )
        arrays_to_implement[ new_name ] = created_arr

    # once the data is selected, we can implement the global arrays inside it
    for final_name, final_array in arrays_to_implement.items():
        dimension: int = final_array.shape[ 1 ] if len( final_array.shape ) == 2 else 1
        if dimension > 1:  # Reshape the VTK array to match the original dimensions
            vtk_array = numpy_to_vtk( final_array.flatten() )
            vtk_array.SetNumberOfComponents( dimension )
            vtk_array.SetNumberOfTuples( number_elements )
        else:
            vtk_array = numpy_to_vtk( final_array )
        vtk_array.SetName( final_name )
        data.AddArray( vtk_array )


def __check( grid_ref: vtkUnstructuredGrid, options: Options ) -> Result:
    sub_vtu_filepaths: tuple[ str ] = get_vtu_filepaths( options )
    useful_array_names: list[ str ] = get_array_names_to_collect( sub_vtu_filepaths[ 0 ], options )
    # create the output grid
    output_mesh: vtkUnstructuredGrid = grid_ref.NewInstance()
    output_mesh.CopyStructure( grid_ref )
    output_mesh.CopyAttributes( grid_ref )
    # find the support elements to use and construct their KDTree
    support_elements: array = support_construction[ options.support ]( output_mesh )
    size_support: int = support_elements.shape[ 0 ]
    kd_tree_ref: KDTree = KDTree( support_elements )
    # perform operations to construct the global arrays to implement in the output mesh from copy
    global_arrays: dict[ str, array ] = dict()
    for vtu_id in range( len( sub_vtu_filepaths ) ):
        sub_grid: vtkUnstructuredGrid = read_mesh( sub_vtu_filepaths[ vtu_id ] )
        if options.support == __SUPPORT_CHOICES[ 0 ]:
            sub_data = sub_grid.GetPointData()
        else:
            sub_data = sub_grid.GetCellData()

        arrays_available: list[ str ] = [ sub_data.GetArrayName( i ) for i in range( sub_data.GetNumberOfArrays() ) ]
        to_operate_on_indexes: list[ int ] = list()
        for name in useful_array_names:
            array_index: int = arrays_available.index( name )
            to_operate_on_indexes.append( array_index )
            if not name in global_arrays:
                dimension: int = sub_data.GetArray( array_index ).GetNumberOfComponents()
                global_arrays[ name ] = full( ( size_support, dimension ), nan )

        reorder_mapping: array = get_reorder_mapping( kd_tree_ref, sub_grid, options.support )
        for index in to_operate_on_indexes:
            name = arrays_available[ index ]
            sub_array: array = vtk_to_numpy( sub_data.GetArray( index ) )
            merge_local_in_global_array( global_arrays[ name ], sub_array, reorder_mapping )
    # The global arrays have been filled, so now we need to implement them in the output_mesh
    implement_arrays( output_mesh, global_arrays, options )
    write_mesh( output_mesh, options.out_vtk )
    return Result( info="OK" )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
