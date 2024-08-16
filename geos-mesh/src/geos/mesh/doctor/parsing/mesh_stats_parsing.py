import logging
from typing import Iterable
from numpy import unique, where

from geos.mesh.doctor.checks.mesh_stats import Options, Result

from . import MESH_STATS


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( MESH_STATS, help=f"Outputs basic properties of a mesh." )


def convert( parsed_options ) -> Options:
    """
    """
    return Options( info="test" )


def display_results( options: Options, result: Result ):
    logging.critical( f"The mesh has {result.number_cells} cells and {result.number_points} points." )
    logging.critical( f"There are {result.number_cell_types} different types of cells in the mesh:" )
    for i in range( result.number_cell_types ):
        logging.critical( f"\t{result.cell_types[ i ]}\t\t({result.cell_type_counts[ i ]} cells)" )

    logging.critical( f"Number of cells that have exactly N neighbors:" )
    unique_numbers_neighbors, counts = unique( result.cells_neighbors_number, return_counts=True )
    logging.critical( "\tNeighbors\tNumber of cells concerned" )
    for number_neighbors, count in zip( unique_numbers_neighbors, counts ):
        logging.critical( f"\t{number_neighbors}\t\t{count}" )
    
    logging.critical( "Number of nodes being shared by exactly N cells:" )
    logging.critical( "\tCells\t\tNumber of nodes" )
    for number_cells_per_node, number_of_occurences in result.sum_number_cells_per_nodes.items():
        logging.critical( f"\t{number_cells_per_node}\t\t{number_of_occurences}" )

    if 0 in unique_numbers_neighbors: #  unique_numbers_neighbors sorted in ascending order from minimum positive number
        number_cells_disconnected: int = unique_numbers_neighbors[ 0 ]
    else:
        number_cells_disconnected = 0
    logging.critical( f"Number of disconnected cells in the mesh: {number_cells_disconnected}" )
    if number_cells_disconnected > 0:
        logging.info( "\tIndexes of disconnected cells" )
        indexes = where(result.cells_neighbors_number == 0)
        logging.info( f"{indexes[ 0 ]}" )

    logging.critical( f"Number of disconnected nodes in the mesh: {len( result.disconnected_nodes )}" )
    if len( result.disconnected_nodes ) > 0:
        logging.info( "\tNodeId\t\tCoordinates" )
        for node_id, coordinates in result.disconnected_nodes.items():
            logging.info( f"\t{node_id}\t\t{coordinates}" )

    logging.critical( "The domain is contained in:" )
    logging.critical( f"\t{result.min_coords[ 0 ]} <= x <= {result.max_coords[ 0 ]}" )
    logging.critical( f"\t{result.min_coords[ 1 ]} <= y <= {result.max_coords[ 1 ]}" )
    logging.critical( f"\t{result.min_coords[ 2 ]} <= z <= {result.max_coords[ 2 ]}" )

    logging.critical( f"Does the mesh have global point ids: {not result.is_empty_point_global_ids}" )
    logging.critical( f"Does the mesh have global cell ids: {not result.is_empty_cell_global_ids}" )

    logging.critical( f"Number of fields data containing NaNs values: {len( result.fields_with_NaNs )}" )
    if len( result.fields_with_NaNs ) > 0:
        logging.critical( "\tFieldName\tNumber of NaNs" )
        for field_name, number_NaNs in result.fields_with_NaNs.items():
            logging.critical( f"\t{field_name}\t{number_NaNs}" )

    space_size: int = 3
    data_types: dict[ str, any ] = {
        "CellData": result.cell_data,
        "PointData": result.point_data,
        "FieldData": result.field_data
    }
    for data_type, data in data_types.items():
        logging.critical( f"There are {len( data.scalar_names )} scalar fields from the {data_type}:" )
        for i in range( len( data.scalar_names ) ):
            logging.critical( f"\t{data.scalar_names[i]}" + harmonious_spacing( data.scalar_names, i, space_size ) +
                              f"min = {data.scalar_min_values[ i ]}" + " " * space_size +
                              f"max = {data.scalar_max_values[ i ]}" )

        logging.critical( f"There are {len( data.tensor_names )} vector/tensor fields from the {data_type}:" )
        for i in range( len( data.tensor_names ) ):
            logging.critical( f"\t{data.tensor_names[ i ]}" + harmonious_spacing( data.tensor_names, i, space_size ) +
                              f"min = {data.tensor_min_values[ i ]}" + " " * space_size +
                              f"max = {data.tensor_max_values[ i ]}" )

    fields_validity_types: dict[ str, any ] = {
        "CellData": result.fields_validity_cell_data,
        "PointData": result.fields_validity_point_data,
        "FieldData": result.fields_validity_field_data
    }
    for field_vailidity_type, data in fields_validity_types.items():
        logging.warning( f"Unexpected range of values for vector/tensor fields from the {field_vailidity_type}:" )
        for field_name, validity_range in data.items():
            is_valid: bool = validity_range[ 0 ]
            min_max: tuple[ float ] = validity_range[ 1 ]
            if not is_valid:
                logging.warning( f"{field_name} expected to be between {min_max[ 0 ]} and {min_max[ 1 ]}." )


def harmonious_spacing( iterable_objs: Iterable[ Iterable ], indexIter: int, space_size: int = 3 ) -> str:
    longest_element: Iterable = max( iterable_objs, key=len )
    ideal_space: int = len( longest_element ) - len( iterable_objs[ indexIter ] ) + space_size
    return " " * ideal_space
