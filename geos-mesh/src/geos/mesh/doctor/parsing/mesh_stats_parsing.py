import logging
import os
from datetime import datetime
from io import StringIO
from numpy import unique, where
from typing import Iterable
from geos.mesh.doctor.checks.mesh_stats import Options, Result
from geos.mesh.doctor.parsing import MESH_STATS

__WRITE_STATS = "write_stats"
__WRITE_STATS_DEFAULT = 0

__OUTPUT = "output"

__DISCONNECTED = "disconnected"
__DISCONNECTED_DEFAULT = 0

__FIELD_VALUES = "field_values"
__FIELD_VALUES_DEFAULT = 0


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( MESH_STATS, help=f"Outputs basic properties of a mesh." )
    p.add_argument( '--' + __WRITE_STATS,
                    type=int,
                    required=True,
                    metavar=[ 0, 1 ],
                    default=__WRITE_STATS_DEFAULT,
                    help=( f"\t[int]: The stats of the mesh will be printed in a file" +
                           " to the folder specified in --output." ) )
    p.add_argument( '--' + __DISCONNECTED,
                    type=int,
                    required=False,
                    metavar=[ 0, 1 ],
                    default=__DISCONNECTED_DEFAULT,
                    help=f"\t[int]: Display all disconnected nodes ids and disconnected cell ids." )
    p.add_argument( '--' + __FIELD_VALUES,
                    type=int,
                    required=False,
                    metavar=[ 0, 1 ],
                    default=__FIELD_VALUES_DEFAULT,
                    help=f"\t[int]: Display all range of field values that seem not realistic." )
    p.add_argument( '--' + __OUTPUT,
                    type=str,
                    required=False,
                    help=f"[string]: The output folder destination where the stats will be written." )


def convert( parsed_options ) -> Options:
    # input_filepath will be defined in check function before calling __check
    return Options( write_stats=parsed_options[ __WRITE_STATS ],
                    output_folder=parsed_options[ __OUTPUT ],
                    input_filepath="",
                    disconnected=parsed_options[ __DISCONNECTED ],
                    field_values=parsed_options[ __FIELD_VALUES ] )


def display_results( options: Options, result: Result ):
    log_stream = StringIO()
    stream_handler = logging.StreamHandler( log_stream )
    stream_handler.setLevel( logging.INFO )

    # Get the root logger and add the StreamHandler to it to possibly output the log to an external file
    logger = logging.getLogger()
    logger.addHandler( stream_handler )
    logger.setLevel( logging.INFO )

    logging.info( f"The mesh has {result.number_cells} cells and {result.number_points} points." )
    logging.info( f"There are {result.number_cell_types} different types of cells in the mesh:" )
    for cell_type, type_count in zip( result.cell_types, result.cell_type_counts ):
        logging.info( f"\t{cell_type}\t\t({type_count} cells)" )

    logging.info( f"Number of cells that have exactly N neighbors:" )
    unique_numbers_neighbors, counts = unique( result.cells_neighbors_number, return_counts=True )
    logging.info( "\tNeighbors\tNumber of cells concerned" )
    for number_neighbors, count in zip( unique_numbers_neighbors, counts ):
        logging.info( f"\t{number_neighbors}\t\t{count}" )

    logging.info( "Number of nodes being shared by exactly N cells:" )
    logging.info( "\tCells\t\tNumber of nodes" )
    for number_cells_per_node, number_of_occurences in result.sum_number_cells_per_nodes.items():
        logging.info( f"\t{number_cells_per_node}\t\t{number_of_occurences}" )

    #  unique_numbers_neighbors sorted in ascending order from minimum positive number
    number_cells_disconnected: int = unique_numbers_neighbors[ 0 ] if 0 in unique_numbers_neighbors else 0
    logging.info( f"Number of disconnected cells in the mesh: {number_cells_disconnected}" )
    if number_cells_disconnected > 0:
        logging.info( "\tIndexes of disconnected cells" )
        indexes = where( result.cells_neighbors_number == 0 )
        logging.info( f"{indexes[ 0 ]}" )

    logging.info( f"Number of disconnected nodes in the mesh: {len( result.disconnected_nodes )}" )
    if len( result.disconnected_nodes ) > 0:
        logging.info( "\tNodeId\t\tCoordinates" )
        for node_id, coordinates in result.disconnected_nodes.items():
            logging.info( f"\t{node_id}\t\t{coordinates}" )

    logging.info( "The domain is contained in:" )
    logging.info( f"\t{result.min_coords[ 0 ]} <= x <= {result.max_coords[ 0 ]}" )
    logging.info( f"\t{result.min_coords[ 1 ]} <= y <= {result.max_coords[ 1 ]}" )
    logging.info( f"\t{result.min_coords[ 2 ]} <= z <= {result.max_coords[ 2 ]}" )

    logging.info( f"Does the mesh have global point ids: {not result.is_empty_point_global_ids}" )
    logging.info( f"Does the mesh have global cell ids: {not result.is_empty_cell_global_ids}" )

    logging.info( f"Number of fields data containing NaNs values: {len( result.fields_with_NaNs )}" )
    if len( result.fields_with_NaNs ) > 0:
        logging.info( "\tFieldName\tNumber of NaNs" )
        for field_name, number_NaNs in result.fields_with_NaNs.items():
            logging.info( f"\t{field_name}\t{number_NaNs}" )

    space_size: int = 3
    data_types: dict[ str, any ] = {
        "CellData": result.cell_data,
        "PointData": result.point_data,
        "FieldData": result.field_data
    }
    for data_type, data in data_types.items():
        logging.info( f"There are {len( data.scalar_names )} scalar fields from the {data_type}:" )
        for i in range( len( data.scalar_names ) ):
            logging.info( f"\t{data.scalar_names[i]}" + harmonious_spacing( data.scalar_names, i, space_size ) +
                          f"min = {data.scalar_min_values[ i ]}" + " " * space_size +
                          f"max = {data.scalar_max_values[ i ]}" )

        logging.info( f"There are {len( data.tensor_names )} vector/tensor fields from the {data_type}:" )
        for i in range( len( data.tensor_names ) ):
            logging.info( f"\t{data.tensor_names[ i ]}" + harmonious_spacing( data.tensor_names, i, space_size ) +
                          f"min = {data.tensor_min_values[ i ]}" + " " * space_size +
                          f"max = {data.tensor_max_values[ i ]}" )

    fields_validity_types: dict[ str, any ] = {
        "CellData": result.fields_validity_cell_data,
        "PointData": result.fields_validity_point_data,
        "FieldData": result.fields_validity_field_data
    }
    for field_vailidity_type, data in fields_validity_types.items():
        logging.info( f"Unexpected range of values for vector/tensor fields from the {field_vailidity_type}:" )
        for field_name, ( is_valid, min_max ) in data.items():
            if not is_valid:
                logging.info( f"{field_name} expected to be between {min_max[ 0 ]} and {min_max[ 1 ]}." )

    if options.write_stats and is_valid_to_write_folder( options.output_folder ):
        filepath: str = build_filepath_output_file( options )
        with open( filepath, 'w' ) as file:
            file.writelines( log_stream.getvalue() )


def harmonious_spacing( iterable_objs: Iterable[ Iterable ], indexIter: int, space_size: int = 3 ) -> str:
    longest_element: Iterable = max( iterable_objs, key=len )
    ideal_space: int = len( longest_element ) - len( iterable_objs[ indexIter ] ) + space_size
    return " " * ideal_space


def is_valid_to_write_folder( folder_path: str ) -> bool:
    """Checks if a folder path is valid to write a file within it.

    Args:
        folder_path (str): Path to a folder.

    Returns:
        bool:
    """
    if not os.path.exists( folder_path ):
        logging.error( f"The folder path given '{folder_path}' to write the log in does not exist. No file written." )
        return False
    if not os.path.isdir( folder_path ):
        logging.error( f"The path given '{folder_path}' to write the log is not a directory path. No file written." )
        return False
    if not os.access( folder_path, os.W_OK ):
        logging.error( f"You do not have writing access to the folder chosen '{folder_path}' to write the log." +
                       " No file written." )
        return False
    return True


def build_filepath_output_file( options: Options ) -> str:
    """Knowing the filepath of the mesh on which the stats will be gathered, and the directory path to where the user
    wants to save the stats, builds a unique filename.

    Args:
        options (Options): Options given by the user.

    Returns:
        str: Complete filepath for the creation of the output file.
    """
    base_name = os.path.basename( options.input_filepath )
    # Split the base name into a mesh name and extension
    mesh_name, _ = os.path.splitext( base_name )
    current_time = datetime.now()
    time = current_time.strftime( "%Y%m%d_%H%M%S" )
    filename: str = mesh_name + "_stats_" + time + ".txt"
    filepath: str = os.path.join( options.output_folder, filename )
    return filepath
