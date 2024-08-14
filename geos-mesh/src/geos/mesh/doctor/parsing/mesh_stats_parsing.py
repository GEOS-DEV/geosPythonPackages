import logging
from typing import Iterable

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
    logging.critical( f"There are {result.number_cell_types} different types of cell in the mesh:" )
    for i in range( result.number_cell_types ):
        logging.critical( f"\t{result.cell_types[ i ]}\t({result.cell_type_counts[ i ]} cells)" )

    logging.critical( "Number of nodes being shared between exactly N cells:" )
    logging.critical( "\tCells\tNodes" )
    for number_cells_per_node, number_of_occurences in result.sum_number_cells_per_nodes.items():
        logging.critical( f"\t{number_cells_per_node}\t{number_of_occurences}" )

    logging.critical( "The domain is contained in:" )
    logging.critical( f"\t{result.min_coords[ 0 ]} <= x <= {result.max_coords[ 0 ]}" )
    logging.critical( f"\t{result.min_coords[ 1 ]} <= y <= {result.max_coords[ 1 ]}" )
    logging.critical( f"\t{result.min_coords[ 2 ]} <= z <= {result.max_coords[ 2 ]}" )

    logging.critical( f"Does the mesh have global point ids: {not result.is_empty_point_global_ids}" )
    logging.critical( f"Does the mesh have global cell ids: {not result.is_empty_cell_global_ids}" )

    space_size: int = 3
    logging.critical( f"There are {len( result.cell_data.scalar_names )} scalar fields on the cells:" )
    for i in range( len( result.cell_data.scalar_names ) ):
        logging.critical( f"\t{result.cell_data.scalar_names[i]}" +
                          harmonious_spacing( result.cell_data.scalar_names, i, space_size ) +
                          f"min = {result.cell_data.scalar_min_values[ i ]}" + " " * space_size +
                          f"max = {result.cell_data.scalar_max_values[ i ]}" )

    logging.critical( f"There are {len( result.cell_data.tensor_names )} vector/tensor fields on the cells:" )
    for i in range( len( result.cell_data.tensor_names ) ):
        logging.critical( f"\t{result.cell_data.tensor_names[ i ]}" +
                          harmonious_spacing( result.cell_data.tensor_names, i, space_size ) +
                          f"min = {result.cell_data.tensor_min_values[ i ]}" + " " * space_size +
                          f"max = {result.cell_data.tensor_max_values[ i ]}" )

    logging.critical( f"There are {len( result.point_data.scalar_names )} scalar fields on the points:" )
    for i in range( len( result.point_data.scalar_names ) ):
        logging.critical( f"\t{result.point_data.scalar_names[ i ]}" +
                          harmonious_spacing( result.point_data.scalar_names, i, space_size ) +
                          f"min = {result.point_data.scalar_min_values[ i ]}" + " " * space_size +
                          f"max = {result.point_data.scalar_max_values[ i ]}" )

    logging.critical( f"There are {len( result.point_data.tensor_names )} vector/tensor fields on the points:" )
    for i in range( len( result.point_data.tensor_names ) ):
        logging.critical( f"\t{result.point_data.tensor_names[ i ]}" +
                          harmonious_spacing( result.point_data.tensor_names, i, space_size ) +
                          f"min = {result.point_data.tensor_min_values[ i ]}" + " " * space_size +
                          f"max = {result.point_data.tensor_max_values[ i ]}" )

    logging.warning( f"Unexpected range of values for vector/tensor fields on the cells :" )
    for field_name, validity_range in result.fields_validity_cell_data.items():
        is_valid: bool = validity_range[ 0 ]
        min_max: tuple[ float ] = validity_range[ 1 ]
        if not is_valid:
            logging.warning( f"{field_name} expected to be between {min_max[ 0 ]} and {min_max[ 1 ]}." )

    logging.warning( f"Unexpected range of values for vector/tensor fields on the points :" )
    for field_name, validity_range in result.fields_validity_point_data.items():
        is_valid: bool = validity_range[ 0 ]
        min_max: tuple[ float ] = validity_range[ 1 ]
        if not is_valid:
            logging.warning( f"{field_name} expected to be between {min_max[ 0 ]} and {min_max[ 1 ]}." )


def harmonious_spacing( iterable_objs: Iterable[ Iterable ], indexIter: int, space_size: int = 3 ) -> str:
    longest_element: Iterable = max( iterable_objs, key=len )
    ideal_space: int = len( longest_element ) - len( iterable_objs[ indexIter ] ) + space_size
    return " " * ideal_space
