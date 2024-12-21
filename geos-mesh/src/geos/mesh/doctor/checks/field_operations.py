import logging
from dataclasses import dataclass
from numexpr import evaluate
from numpy import array, empty, full, sqrt, int64, nan
from numpy.random import rand
from scipy.spatial import KDTree
from tqdm import tqdm
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkDataSetAttributes
from geos.mesh.doctor.checks.vtk_utils import ( VtkOutput, get_points_coords_from_vtk, get_cell_centers_array,
                                                get_vtu_filepaths, get_all_array_names, read_mesh, write_mesh )


@dataclass( frozen=True )
class Options:
    support: str  # choice between 'cell' and 'point' to operate on fields
    source: str  # file from where the data is collected
    operations: list[ tuple[ str, str ] ]  # [ ( function0, new_name0 ), ... ]
    vtm_index: int  # useful when source is a .pvd or .vtm file
    vtk_output: VtkOutput


@dataclass( frozen=True )
class Result:
    info: bool


__SUPPORT_CHOICES = [ "point", "cell" ]


def check_valid_support( support: str ) -> None:
    if support not in __SUPPORT_CHOICES:
        raise ValueError( f"For support, the only choices available are '{__SUPPORT_CHOICES}', not '{support}'." )


def get_support_data( mesh: vtkUnstructuredGrid, support: str ) -> vtkDataSetAttributes:
    f"""Returns the support vtkPointData or vtkCellData.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        any: vtkPointData or vtkCellData.
    """
    check_valid_support( support )
    support_data: dict[ str, any ] = { "point": mesh.GetPointData, "cell": mesh.GetCellData }
    if list( support_data.keys() ).sort() != __SUPPORT_CHOICES.sort():
        raise ValueError( f"No implementation defined to access the {support} data." )
    return support_data[ support ]()


def get_support_elements( mesh: vtkUnstructuredGrid, support: str ) -> array:
    f"""Returns the support elements which are either points coordinates or cell centers coordinates.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        int: Number of points or cells.
    """
    check_valid_support( support )
    support_elements: dict[ str, any ] = { "point": get_points_coords_from_vtk, "cell": get_cell_centers_array }
    if list( support_elements.keys() ).sort() != __SUPPORT_CHOICES.sort():
        raise ValueError( f"No implementation defined to access the {support} data." )
    return support_elements[ support ]( mesh )


def get_number_elements( mesh: vtkUnstructuredGrid, support: str ) -> int:
    f"""Returns the number of points or cells depending on the support.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        int: Number of points or cells.
    """
    check_valid_support( support )
    number_funct: dict[ str, any ] = { 'point': mesh.GetNumberOfPoints, 'cell': mesh.GetNumberOfCells }
    if list( number_funct.keys() ).sort() != __SUPPORT_CHOICES.sort():
        raise ValueError( f"No implementation defined to return the number of elements for {support} data." )
    return number_funct[ support ]()


def build_distances_mesh_center( mesh: vtkUnstructuredGrid, support: str ) -> array:
    f"""For a specific support type {__SUPPORT_CHOICES}, returns an array filled with the distances between
    their coordinates and the center of the mesh.

    Args:
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        array: [ distance0, distance1, ..., distanceN ] with N being the number of support elements.
    """
    coords: array = get_support_elements( mesh, support )
    center = ( coords.max( axis=0 ) + coords.min( axis=0 ) ) / 2
    distances = sqrt( ( ( coords - center )**2 ).sum( axis=1 ) )
    return distances


def build_random_uniform_distribution( mesh: vtkUnstructuredGrid, support: str ) -> array:
    f"""For a specific support type {__SUPPORT_CHOICES}, an array with samples from a uniform distribution over [0, 1).

    Args:
        support (str): Choice between {__SUPPORT_CHOICES}.

    Returns:
        array: Array of size N being the number of support elements.
    """
    return rand( get_number_elements( mesh, support ), 1 )


create_precoded_fields: dict[ str, any ] = {
    "distances_mesh_center": build_distances_mesh_center,
    "random_uniform_distribution": build_random_uniform_distribution
}


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
    support_elements: array = get_support_elements( sub_grid, support )
    # now that you have the support elements, you can map them to the reference grid
    number_elements: int = get_number_elements( sub_grid, support )
    mapping: array = empty( number_elements, dtype=int64 )
    for cell_id in range( number_elements ):
        _, index = kd_tree_grid_ref.query( support_elements[ cell_id ] )
        mapping[ cell_id ] = index
    return mapping


def get_array_names_to_collect_and_options( sub_vtu_filepath: str,
                                            options: Options ) -> tuple[ list[ tuple[ str ] ], Options ]:
    """We need to have the list of array names that are required to perform copy and creation of new arrays. To build
    global_arrays to perform operations, we need only these names and not all array names present in the sub meshes.

    Args:
        sub_vtu_filepath (str): Path to sub vtu file that can be used to find the names of the arrays within its data.
        options (Options): Options chosen by the user.

    Returns:
        list[ str ]: Array names.
    """
    check_valid_support( options.support )
    ref_mesh: vtkUnstructuredGrid = read_mesh( sub_vtu_filepath )
    all_array_names: dict[ str, dict[ str, int ] ] = get_all_array_names( ref_mesh )
    support_array_names: list[ str ] = list( all_array_names[ options.support ].keys() )

    to_use_arrays: set[ str ] = set()
    to_use_operate: list[ tuple[ str ] ] = list()
    for function_newname in options.operations:
        funct: str = function_newname[ 0 ]
        if funct in create_precoded_fields:
            to_use_operate.append( function_newname )
            continue

        if any( name in funct for name in support_array_names ):
            to_use_arrays.update( name for name in support_array_names if name in funct )
            to_use_operate.append( function_newname )
        else:
            logging.warning( f"Cannot perform operations with '{funct}' because some or all the fields do not " +
                             f"exist in '{sub_vtu_filepath}'." )

    updated_options: Options = Options( options.support, options.source, to_use_operate, options.vtm_index,
                                        options.vtk_output )
    return ( list( to_use_arrays ), updated_options )


def merge_local_in_global_array( global_array: array, local_array: array, mapping: array ) -> None:
    """Fill the values of a global_array using the values contained in a local_array that is smaller or equal to the
    size as the global_array. A mapping is used to copy the values from the local_array to the right indexes in
    the global_array.

    Args:
        global_array (np.array): Array of size N.
        local_array (np.array): Array of size M <= N that is representing a subset of the global_array.
        mapping (np.array): Array of global indexes of size M.
    """
    global_shape, local_shape = global_array.shape, local_array.shape
    if global_shape[ 0 ] < local_shape[ 0 ]:
        raise ValueError( "The global array to fill is smaller than the local array to merge." )
    number_columns_global: int = global_shape[ 1 ] if len( global_shape ) == 2 else 1
    number_columns_local: int = local_shape[ 1 ] if len( local_shape ) == 2 else 1
    if number_columns_global != number_columns_local:
        raise ValueError( "The arrays do not have same number of columns." )
    # when converting a numpy array to vtk array, you need to make sure to have a 2D array
    if len( local_shape ) == 1:
        local_array = local_array.reshape( -1, 1 )
    global_array[ mapping ] = local_array


def implement_arrays( mesh: vtkUnstructuredGrid, global_arrays: dict[ str, array ], options: Options ) -> None:
    """Implement the arrays that are contained in global_arrays into the Data of a mesh.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.
        global_arrays (dict[ str, np.array ]): { "array_name0": np.array, ..., "array_nameN": np.array }
        options (Options): Options chosen by the user.
    """
    support_data: vtkDataSetAttributes = get_support_data( mesh, options.support )
    number_elements: int = get_number_elements( mesh, options.support )
    arrays_to_implement: dict[ str, array ] = dict()
    # proceed operations
    for function_newname in tqdm( options.operations, desc="Performing operations" ):
        funct, new_name = function_newname
        if funct in create_precoded_fields:
            created_arr: array = create_precoded_fields[ funct ]( mesh, options.support )
        else:
            created_arr = evaluate( funct, local_dict=global_arrays )
        arrays_to_implement[ new_name ] = created_arr

    # once the data is selected, we can implement the global arrays inside it
    for final_name, final_array in arrays_to_implement.items():
        number_columns: int = final_array.shape[ 1 ] if len( final_array.shape ) == 2 else 1
        if number_columns > 1:  # Reshape the VTK array to match the original dimensions
            vtk_array = numpy_to_vtk( final_array.flatten() )
            vtk_array.SetNumberOfComponents( number_columns )
            vtk_array.SetNumberOfTuples( number_elements )
        else:
            vtk_array = numpy_to_vtk( final_array )
        vtk_array.SetName( final_name )
        support_data.AddArray( vtk_array )


def __check( grid_ref: vtkUnstructuredGrid, options: Options ) -> Result:
    sub_vtu_filepaths: tuple[ str ] = get_vtu_filepaths( options )
    array_names_to_collect, new_options = get_array_names_to_collect_and_options( sub_vtu_filepaths[ 0 ], options )
    if len( array_names_to_collect ) == 0:
        raise ValueError( "No array corresponding to the operations suggested was found in the source" +
                          f" {new_options.support} data. Check your support and source file." )
    # create the output grid
    output_mesh: vtkUnstructuredGrid = grid_ref.NewInstance()
    output_mesh.CopyStructure( grid_ref )
    output_mesh.CopyAttributes( grid_ref )
    # find the support elements to use and construct their KDTree
    support_elements: array = get_support_elements( output_mesh, options.support )
    number_elements: int = support_elements.shape[ 0 ]
    kd_tree_ref: KDTree = KDTree( support_elements )
    # perform operations to construct the global arrays to implement in the output mesh from copy
    global_arrays: dict[ str, array ] = dict()
    for vtu_id in tqdm( range( len( sub_vtu_filepaths ) ), desc="Processing VTU files" ):
        sub_grid: vtkUnstructuredGrid = read_mesh( sub_vtu_filepaths[ vtu_id ] )
        sub_data: vtkDataSetAttributes = get_support_data( sub_grid, options.support )
        usable_arrays: list[ tuple[ int, str ] ] = list()
        for array_index in range( sub_data.GetNumberOfArrays() ):
            array_name: str = sub_data.GetArrayName( array_index )
            if array_name in array_names_to_collect:
                usable_arrays.append( ( array_index, array_name ) )
                if not array_name in global_arrays:
                    number_components: int = sub_data.GetArray( array_index ).GetNumberOfComponents()
                    global_arrays[ array_name ] = full( ( number_elements, number_components ), nan )

        if len( usable_arrays ) > 0:
            reorder_mapping: array = get_reorder_mapping( kd_tree_ref, sub_grid, new_options.support )
            for index_name in usable_arrays:
                sub_array: array = vtk_to_numpy( sub_data.GetArray( index_name[ 0 ] ) )
                merge_local_in_global_array( global_arrays[ index_name[ 1 ] ], sub_array, reorder_mapping )
    # The global arrays have been filled, so now we need to implement them in the output_mesh
    implement_arrays( output_mesh, global_arrays, new_options )
    write_mesh( output_mesh, new_options.vtk_output )
    return Result( info="OK" )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
