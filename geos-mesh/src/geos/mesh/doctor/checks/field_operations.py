import logging
import numpy as np
from dataclasses import dataclass
from math import sqrt
from numpy import empty
from numpy.random import rand
from scipy.spatial import KDTree
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkFiltersCore import vtkCellCenters
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.checks.vtk_utils import ( VtkOutput, read_mesh, write_mesh, get_vtm_filepath_from_pvd,
                                                get_vtu_filepaths_from_vtm )


@dataclass( frozen=True )
class Options:
    operation: str
    support: str
    field_names: list[ str ]
    source: str
    vtm_index: int
    out_vtk: VtkOutput


@dataclass( frozen=True )
class Result:
    info: bool

__SUPPORT_CHOICES = [ "point", "cell" ]
__OPERATION_CHOICES = [ "transfer" ]


def get_vtu_filepaths( options: Options ) -> tuple[ str ]:
    """Returns the vtu filepaths to use for the rest of the workflow.

    Args:
        options (Options): Options chosen by the user.

    Returns:
        tuple[ str ]: ( "file/path/0.vtu", ..., "file/path/N.vtu" )
    """
    source_filepath: str = options.source
    if source_filepath.endswith( ".vtu" ):
        return ( source_filepath )
    elif source_filepath.endswith( ".vtm" ):
        return get_vtu_filepaths_from_vtm( source_filepath )
    elif source_filepath.endswith( ".pvd" ):
        vtm_filepath: str = get_vtm_filepath_from_pvd( source_filepath, options.vtm_index )
        return get_vtu_filepaths_from_vtm( vtm_filepath )
    else:
        raise ValueError( f"The filepath '{options.source}' provided targets neither a .vtu, a .vtm nor a .pvd file." )


def build_cell_centers_array( mesh: vtkUnstructuredGrid ) -> np.array:
    """Builds an array containing the cell centers coordinates for every cell of a mesh.

    Args:
        mesh (vtkUnstructuredGrid): A vtk grid.

    Returns:
        np.array: Shape=( 3, mesh number of cells )
    """
    cell_centers_filter: vtkCellCenters = vtkCellCenters()
    cell_centers_filter.SetInputData( mesh )
    cell_centers_filter.Update()
    cell_centers = cell_centers_filter.GetOutput()
    points = cell_centers.GetPoints()
    num_points: int = points.GetNumberOfPoints()
    cell_centers_array: np.array = np.array( [ points.GetPoint( i ) for i in range( num_points ) ], dtype=float )
    return cell_centers_array


def get_cells_reorder_mapping( kd_tree_grid_ref: KDTree, sub_grid: vtkUnstructuredGrid ) -> np.array:
    """Builds an array containing the indexes of the reference grid linked to every cell ids of the subset grid.

    Args:
        kd_tree_grid_ref (KDTree): A KDTree of the nearest neighbor cell centers for every cells of the reference grid.
        sub_grid (vtkUnstructuredGrid): A vtk grid that is a subset of the reference grid.

    Returns:
        np.array: [ cell_idK_grid, cell_idN_grid, ... ]
    """
    cell_centers: np.array = build_cell_centers_array( sub_grid )
    number_cells: int = sub_grid.GetNumberOfCells()
    mapping: np.array = np.empty( number_cells, dtype=np.int64 )
    for cell_id in range( number_cells ):
        _, index = kd_tree_grid_ref.query( cell_centers[ cell_id ] )
        mapping[ cell_id ] = index
    return mapping


def __analytic_field( mesh, support, name ) -> bool:
    if support == 'node':
        # example function: distance from mesh center
        nn = mesh.GetNumberOfPoints()
        coords = vtk_to_numpy( mesh.GetPoints().GetData() )
        center = ( coords.max( axis=0 ) + coords.min( axis=0 ) ) / 2
        data_arr = vtkDoubleArray()
        data_np = empty( nn )

        for i in range( nn ):
            val = 0
            pt = mesh.GetPoint( i )
            for j in range( len( pt ) ):
                val += ( pt[ j ] - center[ j ] ) * ( pt[ j ] - center[ j ] )
            val = sqrt( val )
            data_np[ i ] = val

        data_arr = numpy_to_vtk( data_np )
        data_arr.SetName( name )
        mesh.GetPointData().AddArray( data_arr )
        return True

    elif support == 'cell':
        # example function: random field
        ne = mesh.GetNumberOfCells()
        data_arr = vtkDoubleArray()
        data_np = rand( ne, 1 )

        data_arr = numpy_to_vtk( data_np )
        data_arr.SetName( name )
        mesh.GetCellData().AddArray( data_arr )
        return True
    else:
        logging.error( 'incorrect support option. Options are node, cell' )
        return False


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


def __transfer_field( mesh, support, field_name, source ) -> bool:
    from_mesh = read_mesh( source )
    same_mesh = __compatible_meshes( mesh, from_mesh )
    if not same_mesh:
        logging.error( 'meshes are not the same' )
        return False

    if support == 'cell':
        data = from_mesh.GetCellData().GetArray( field_name )
        if data == None:
            logging.error( 'Requested field does not exist on source mesh' )
            return False
        else:
            mesh.GetCellData().AddArray( data )
    elif support == 'node':
        data = from_mesh.GetPointData().GetArray( field_name )
        if data == None:
            logging.error( 'Requested field does not exist on source mesh' )
            return False
        else:
            mesh.GetPointData().AddArray( data )
            return False
    else:
        logging.error( 'incorrect support option. Options are node, cell' )
        return False
    return True


def perform_operation_on_array( global_array: np.array,
                                local_array: np.array,
                                mapping: np.array,
                                options: Options ) -> None:
    """Perform an operation that will fill the values of a global_array using the values contained in a local_array
    that is smaller or equal to the size as the global_array. A mapping is used to copy the values from the
    local_array to the right indexes in the global_array.

    Args:
        global_array (np.array): Array of size N.
        local_array (np.array): Array of size M <= N that is representing a subset of the global_array.
        mapping (np.array): Array of global indexes of size M.
        options (Options): Options chosen by the user.
    """
    size_global, size_local = global_array.shape, local_array.shape
    assert size_global[ 0 ] >= size_local[ 0 ], "The array to fill is smaller than the array to use."
    number_columns_global: int = size_global[ 1 ] if len( size_global ) == 2 else 1
    number_columns_local: int = size_local[ 1 ] if len( size_local ) == 2 else 1
    assert number_columns_global == number_columns_local, "The arrays do not have same number of columns."
    if options.operation == __OPERATION_CHOICES[ 0 ]:  # transfer
        if len(size_local) == 1:
            local_array = local_array.reshape(-1, 1)
        global_array[ mapping ] = local_array
    else:
        raise ValueError( f"Cannot perform operation '{options.operation}'. Only operations are {__OPERATION_CHOICES}" )


def implement_arrays( grid_ref: vtkUnstructuredGrid, global_arrays: dict[ str, np.array ], options: Options ) -> None:
    """Implement the arrays that are contained in global_arrays into the Data of a grid_ref.

    Args:
        grid_ref (vtkUnstructuredGrid): A vtk grid.
        global_arrays (dict[ str, np.array ]): { "array_name0": np.array, ..., "array_nameN": np.array }
        options (Options): Options chosen by the user.
    """
    if options.support == __SUPPORT_CHOICES[ 0 ]:
        data = grid_ref.GetPointData()
        number_elements: int = grid_ref.GetNumberOfPoints()
    elif options.support == __SUPPORT_CHOICES[ 1 ]:
        data = grid_ref.GetCellData()
        number_elements = grid_ref.GetNumberOfCells()
    else:
        raise ValueError( f"Support choices should be one of these: {__SUPPORT_CHOICES}." )

    for name, array in global_arrays.items():
        dimension: int = array.shape[ 1 ] if len( array.shape ) == 2 else 1
        if dimension > 1:  # Reshape the VTK array to match the original dimensions
            vtk_array = numpy_to_vtk( array.flatten() )
            vtk_array.SetNumberOfComponents( dimension )
            vtk_array.SetNumberOfTuples( number_elements )
        else:
            vtk_array = numpy_to_vtk( array )
        vtk_array.SetName( name )
        if options.operation == __OPERATION_CHOICES[ 0 ]:  # transfer
            data.AddArray( vtk_array )


def __check_on_points( grid_ref: vtkUnstructuredGrid, vtu_filepaths: tuple[ str ], options: Options ) -> None:
    # First part needs to create the empty arrays for each field name that we want to operate on.
    # The goal is then to fill them with the actual values from the different sub vtus on which we apply the operation.
    ...


def __check_on_cells( grid_ref: vtkUnstructuredGrid, vtu_filepaths: tuple[ str ], options: Options ) -> None:
    # First part needs to create the empty arrays for each field name that we want to operate on.
    # The goal is then to fill them with the actual values from the different sub vtus on which we apply the operation.
    global_arrays: dict[ str, np.array ] = dict()
    cell_centers_ref: np.array = build_cell_centers_array( grid_ref )
    kd_tree_ref: KDTree = KDTree( cell_centers_ref )
    for vtu_id in range( len( vtu_filepaths ) ):
        sub_grid: vtkUnstructuredGrid = read_mesh( vtu_filepaths[ vtu_id ] )
        sub_data = sub_grid.GetCellData()
        # We need to make sure that the arrays we are looking at exist in the sub grid
        arrays_available: list[ str ] = [ sub_data.GetArrayName( i ) for i in range( sub_data.GetNumberOfArrays() ) ]
        to_operate_on_indexes: list[ int ] = list()
        for name in options.field_names:
            if name not in arrays_available:
                logging.warning( f"The field named '{name}' does not exist in '{vtu_filepaths[ vtu_id ]}'." +
                                 " Cannot perform operation on it. Default values set to NaN." )
            else:
                array_index: int = arrays_available.index( name )
                to_operate_on_indexes.append( array_index )
                if not name in global_arrays:
                    dimension: int = sub_data.GetArray( array_index ).GetNumberOfComponents()
                    global_arrays[ name ] = np.full( ( grid_ref.GetNumberOfCells(), dimension ), np.nan )
        # If the arrays exist, we can perform the operation and fill the empty arrays
        if len( to_operate_on_indexes ) > 0:
            mapping: np.array = get_cells_reorder_mapping( kd_tree_ref, sub_grid )
            for index in to_operate_on_indexes:
                name = arrays_available[ index ]
                sub_array: np.array = vtk_to_numpy( sub_data.GetArray( index ) )
                perform_operation_on_array( global_arrays[ name ], sub_array, mapping, options )
    # the global arrays have been filled, so now we need to implement them in the grid_ref
    implement_arrays( grid_ref, global_arrays, options )


def __check( grid_ref: vtkUnstructuredGrid, options: Options ) -> Result:
    all_sub_vtu_filepaths: tuple[ str ] = get_vtu_filepaths( options )
    # create the output grid
    output_mesh: vtkUnstructuredGrid = grid_ref.NewInstance()
    output_mesh.CopyStructure( grid_ref )
    output_mesh.CopyAttributes( grid_ref )
    # perform operations on the grid
    if options.support == __SUPPORT_CHOICES[ 0 ]:
        __check_on_points( output_mesh, all_sub_vtu_filepaths, options )
    elif options.support == __SUPPORT_CHOICES[ 1 ]:
        __check_on_cells( output_mesh, all_sub_vtu_filepaths, options )
    write_mesh( output_mesh, options.out_vtk )
    return Result( info="OK" )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = read_mesh( vtk_input_file )
    return __check( mesh, options )
