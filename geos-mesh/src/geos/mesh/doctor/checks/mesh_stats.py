import logging
import numpy as np
import numpy.typing as npt
from dataclasses import dataclass
from enum import Enum

from vtkmodules.util.numpy_support import (
    vtk_to_numpy, )

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, )

from . import vtk_utils


@dataclass( frozen=True )
class Options:
    info: str


ArrayGeneric = npt.NDArray[ np.generic ]


@dataclass( frozen=True )
class MeshComponentData:
    componentType: str
    scalar_names: list[ str ]
    scalar_min_values: list[ np.generic ]  # base class for all scalar types numpy
    scalar_max_values: list[ np.generic ]
    tensor_names: list[ str ]
    tensor_min_values: list[ ArrayGeneric ]
    tensor_max_values: list[ ArrayGeneric ]


@dataclass( frozen=True )
class Result:
    number_cells: int
    number_points: int
    number_cell_types: int
    cell_types: list[ str ]
    cell_type_counts: list[ int ]
    sum_number_cells_per_nodes: dict[ int, int ]
    disconnected_nodes: dict[ int, tuple[ float ] ]
    min_coords: np.ndarray
    max_coords: np.ndarray
    is_empty_point_global_ids: bool
    is_empty_cell_global_ids: bool
    point_data: MeshComponentData
    cell_data: MeshComponentData
    fields_validity_point_data: dict[ str, dict[ str, bool ] ]
    fields_validity_cell_data: dict[ str, dict[ str, bool ] ]


class MIN_FIELD( float, Enum ):  # SI Units
    PORO = 0.0
    PERM = 0.0
    FLUIDCOMP = 0.0
    PRESSURE = 0.0
    BHP = 0.0
    TEMPERATURE = 0.0
    DENSITY = 0.0
    COMPRESSIBILITY = 0.0
    VISCOSITY = 0.0
    NTG = 0.0
    BULKMOD = 0.0
    SHEARMOD = 0.0


class MAX_FIELD( float, Enum ):  # SI Units
    PORO = 1.0
    PERM = 1.0
    FLUIDCOMP = 1.0
    PRESSURE = 1.0e9
    BHP = 1.0e9
    TEMPERATURE = 2.0e3
    DENSITY = 2.5e4
    COMPRESSIBILITY = 1.0e-4
    VISCOSITY = 1.0e24
    NTG = 1.0
    BULKMOD = 1.0e12
    SHEARMOD = 1.0e12


def associate_min_max_field_values() -> dict[ str, tuple[ float ] ]:
    """Using MIN_FIELD and MAX_FIELD, associate the min and max value reachable for a
    property in GEOS to a property tag such as poro, perm etc...

    Returns:
        dict[ str, tuple[ float ] ]: { poro: (min_value, max_value), perm: (min_value, max_value), ... }
    """
    assoc_min_max_field_values: dict[ str, tuple[ float ] ] = {}
    for name in MIN_FIELD.__members__:
        mini = MIN_FIELD[ name ]
        maxi = MAX_FIELD[ name ]
        assoc_min_max_field_values[ name.lower() ] = ( mini.value, maxi.value )
    return assoc_min_max_field_values


def get_cell_types_and_counts( mesh: vtkUnstructuredGrid ) -> tuple[ int, int, list[ str ], list[ int ] ]:
    """From an unstructured grid, collects the number of cells,
    the number of cell types, the list of cell types and the counts
    of each cell element.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        tuple[int, int, list[str], list[int]]: In order,
        (number_cells, number_cell_types, cell_types, cell_type_counts)
    """
    number_cells: int = mesh.GetNumberOfCells()
    distinct_array_types = mesh.GetDistinctCellTypesArray()
    number_cell_types: int = distinct_array_types.GetNumberOfTuples()
    # Get the different cell types in the mesh
    cell_types: list[ str ] = []
    for cell_type in range( number_cell_types ):
        cell_types.append( vtk_utils.vtkid_to_string( distinct_array_types.GetTuple( cell_type )[ 0 ] ) )
    # Counts how many of each type are present
    cell_type_counts: list[ int ] = [ 0 ] * number_cell_types
    for cell in range( number_cells ):
        for cell_type in range( number_cell_types ):
            if vtk_utils.vtkid_to_string( mesh.GetCell( cell ).GetCellType() ) == cell_types[ cell_type ]:
                cell_type_counts[ cell_type ] += 1
                break
    return ( number_cells, number_cell_types, cell_types, cell_type_counts )


def get_number_cells_per_nodes( mesh: vtkUnstructuredGrid ) -> dict[ int, int ]:
    """Finds for each point_id the number of cells sharing that same node.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        dict[ int, int ]: { point_id0: 8, ..., point_idN: 4 }
    """
    number_cells_per_nodes: dict[ int, int ] = {}
    for point_id in range( mesh.GetNumberOfPoints() ):
        number_cells_per_nodes[ point_id ] = 0
    for cell_id in range( mesh.GetNumberOfCells() ):
        cell = mesh.GetCell( cell_id )
        for v in range( cell.GetNumberOfPoints() ):
            point_id = cell.GetPointId( v )
            number_cells_per_nodes[ point_id ] += 1
    return number_cells_per_nodes


def summary_number_cells_per_nodes( number_cells_per_nodes: dict[ int, int ] ) -> dict[ int, int ]:
    """Obtain the number of nodes that have X number of cells.

    Args:
        number_cells_per_nodes (dict[ int, int ]): { point_id0: 8, ..., point_idN: 4 }

    Returns:
        dict[ int, int ]: Connected to N cells as key, Number of nodes concerned as value
    """
    unique_number_cells = set( [ value for value in number_cells_per_nodes.values() ] )
    summary: dict[ int, int ] = {}
    for unique_number in unique_number_cells:
        summary[ unique_number ] = 0
    for number_cells in number_cells_per_nodes.values():
        summary[ number_cells ] += 1
    return summary


def get_coords_min_max( mesh: vtkUnstructuredGrid ) -> tuple[ np.ndarray ]:
    """From an unstructured mesh, returns the coordinates of
    the minimum and maximum points.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        tuple[np.ndarray]: Min and Max coordinates.
    """
    coords: np.ndarray = vtk_to_numpy( mesh.GetPoints().GetData() )
    min_coords: np.ndarray = coords.min( axis=0 )
    max_coords: np.ndarray = coords.max( axis=0 )
    return ( min_coords, max_coords )


def build_MeshComponentData( mesh: vtkUnstructuredGrid, componentType: str = "point" ) -> MeshComponentData:
    """Builds a MeshComponentData object for a specific component ("point", "cell")
    If the component type chosen is invalid, chooses "point" by default.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        meshCD (MeshComponentData): Object that gathers data regarding a mesh component.
    """
    if componentType not in [ "point", "cell" ]:
        componentType = "point"
        logging.error( f"Invalid component type chosen to build MeshComponentData. Defaulted to point." )

    if componentType == "point":
        number_arrays_data: int = mesh.GetPointData().GetNumberOfArrays()
    else:
        number_arrays_data = mesh.GetCellData().GetNumberOfArrays()

    scalar_names: list[ str ] = []
    scalar_min_values: list[ np.generic ] = []
    scalar_max_values: list[ np.generic ] = []
    tensor_names: list[ str ] = []
    tensor_min_values: list[ ArrayGeneric ] = []
    tensor_max_values: list[ ArrayGeneric ] = []
    for i in range( number_arrays_data ):
        if componentType == "point":
            data_array = mesh.GetPointData().GetArray( i )
        else:
            data_array = mesh.GetCellData().GetArray( i )
        data_array_name = data_array.GetName()
        data_np_array = vtk_to_numpy( data_array )
        if data_array.GetNumberOfComponents() == 1:  # assumes scalar cell data for max and min
            scalar_names.append( data_array_name )
            scalar_max_values.append( data_np_array.max() )
            scalar_min_values.append( data_np_array.min() )
        else:
            tensor_names.append( data_array_name )
            tensor_max_values.append( data_np_array.max( axis=0 ) )
            tensor_min_values.append( data_np_array.min( axis=0 ) )

    return MeshComponentData( componentType=componentType,
                              scalar_names=scalar_names,
                              scalar_min_values=scalar_min_values,
                              scalar_max_values=scalar_max_values,
                              tensor_names=tensor_names,
                              tensor_min_values=tensor_min_values,
                              tensor_max_values=tensor_max_values )


def field_values_validity( mcdata: MeshComponentData ) -> dict[ str, tuple[ bool, tuple[ float ] ] ]:
    """Check that for every min and max values found in the scalar and tensor fields,
    none of these values is out of bounds. If the value is out of bound, False validity flag
    is given to the field, True if no problem.

    Args:
        mcdata (MeshComponentData): Object that gathers data regarding a mesh component.

    Returns:
        dict[ str, bool ]: {poro: (True, Min_Max_poro), perm: (False, Min_Max_perm), ...}
    """
    field_values_validity: dict[ str, tuple[ bool, tuple[ float ] ] ] = {}
    assoc_min_max_field: dict[ str, tuple[ float ] ] = associate_min_max_field_values()
    # for scalar values
    for i in range( len( mcdata.scalar_names ) ):
        for field_param, min_max in assoc_min_max_field.items():
            if field_param in mcdata.scalar_names[ i ].lower():
                field_values_validity[ mcdata.scalar_names[ i ] ] = ( True, min_max )
                if mcdata.scalar_min_values[ i ] < min_max[ 0 ] or mcdata.scalar_max_values[ i ] > min_max[ 1 ]:
                    field_values_validity[ mcdata.scalar_names[ i ] ] = ( False, min_max )
                break
    # for tensor values
    for i in range( len( mcdata.tensor_names ) ):
        for field_param, min_max in assoc_min_max_field.items():
            if field_param in mcdata.tensor_names[ i ].lower():
                field_values_validity[ mcdata.tensor_names[ i ] ] = ( True, min_max )
                for sub_value_min, sub_value_max in zip( mcdata.tensor_min_values[ i ], mcdata.tensor_max_values[ i ] ):
                    if sub_value_min < min_max[ 0 ] or sub_value_max > min_max[ 1 ]:
                        field_values_validity[ mcdata.tensor_names[ i ] ] = ( False, min_max )
                        break
                break
    return field_values_validity


def get_disconnected_nodes_id( mesh: vtkUnstructuredGrid ) -> list[ int ]:
    """Checks the nodes of the mesh to see if they are disconnected.
    If a node does not appear in connectivity graph, we can assume that it is disconnected.
    Returns the list of node ids that are disconnected.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        list[ int ]: [nodeId0, nodeId23, ..., nodeIdM]
    """
    disconnected_nodes_id: list[ int ] = []
    connectivity = mesh.GetCells().GetConnectivityArray()
    connectivity_unique_points: set = set()
    for i in range( connectivity.GetNumberOfValues() ):
        connectivity_unique_points.add( connectivity.GetValue( i ) )
    for v in range( mesh.GetNumberOfPoints() ):
        if v in connectivity_unique_points:
            connectivity_unique_points.remove( v )
        else:
            disconnected_nodes_id.append( v )
    return disconnected_nodes_id


def get_disconnected_nodes_coords( mesh: vtkUnstructuredGrid ) -> dict[ int, tuple[ float ] ]:
    """Checks the nodes of the mesh to see if they are disconnected.
    If a node does not appear in connectivity graph, we can assume that it is disconnected.
    Returns a dict zhere the keys are the node id of disconnected nodes and the values are their coordinates.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        dict[ int, tuple[ float ] ]: {nodeId0: (x0, y0, z0), nodeId23: (x23, y23, z23), ..., nodeIdM: (xM, yM, zM)}
    """
    disconnected_nodes_id: list[ int ] = get_disconnected_nodes_id( mesh )
    disconnected_nodes_coords: dict[ int, tuple[ float ] ] = {}
    points = mesh.GetPoints()
    for node_id in disconnected_nodes_id:
        node_coords: tuple[ float ] = points.GetPoint( node_id )
        disconnected_nodes_coords[ node_id ] = node_coords
    return disconnected_nodes_coords


def __check( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    number_points: int = mesh.GetNumberOfPoints()
    cells_info = get_cell_types_and_counts( mesh )
    number_cells: int = cells_info[ 0 ]
    number_cell_types: int = cells_info[ 1 ]
    cell_types: int = cells_info[ 2 ]
    cell_type_counts: int = cells_info[ 3 ]
    number_cells_per_nodes: dict[ int, int ] = get_number_cells_per_nodes( mesh )
    sum_number_cells_per_nodes: dict[ int, int ] = summary_number_cells_per_nodes( number_cells_per_nodes )
    disconnected_nodes: dict[ int, tuple[ float ] ] = get_disconnected_nodes_coords( mesh )
    min_coords, max_coords = get_coords_min_max( mesh )
    point_ids: bool = not bool( mesh.GetPointData().GetGlobalIds() )
    cell_ids: bool = not bool( mesh.GetCellData().GetGlobalIds() )
    point_data: MeshComponentData = build_MeshComponentData( mesh, "point" )
    cell_data: MeshComponentData = build_MeshComponentData( mesh, "cell" )
    fields_validity_point_data: dict[ str, tuple[ bool, tuple[ float ] ] ] = field_values_validity( point_data )
    fields_validity_cell_data: dict[ str, tuple[ bool, tuple[ float ] ] ] = field_values_validity( cell_data )

    return Result( number_points=number_points,
                   number_cells=number_cells,
                   number_cell_types=number_cell_types,
                   cell_types=cell_types,
                   cell_type_counts=cell_type_counts,
                   sum_number_cells_per_nodes=sum_number_cells_per_nodes,
                   disconnected_nodes=disconnected_nodes,
                   min_coords=min_coords,
                   max_coords=max_coords,
                   is_empty_point_global_ids=point_ids,
                   is_empty_cell_global_ids=cell_ids,
                   point_data=point_data,
                   cell_data=cell_data,
                   fields_validity_point_data=fields_validity_point_data,
                   fields_validity_cell_data=fields_validity_cell_data )


def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )
