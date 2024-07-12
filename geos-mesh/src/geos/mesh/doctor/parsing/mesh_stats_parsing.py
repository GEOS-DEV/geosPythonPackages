import logging

from checks.mesh_stats import Options, Result

from . import MESH_STATS

def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( MESH_STATS,
                               help=f"Outputs basic properties of a mesh." )
    
def convert( parsed_options ) -> Options:
    """
    """
    return Options( info="test" )
    
def display_results( options: Options, result: Result ):
    logging.info( f"The mesh has {result.num_elements} elements and {result.num_nodes} nodes." )
    logging.info( f"There are {result.num_cell_types} different types of cell in the mesh:" )
    for i in range(result.num_cell_types):
        logging.info( f"\t {result.cell_types[i]} \t ({result.cell_type_counts[i]} cells)" )
    
    logging.info( f"The domain is contained in {result.min_coords[0]} <= x <= {result.max_coords[0]}")
    logging.info( f"                           {result.min_coords[1]} <= y <= {result.max_coords[1]}")
    logging.info( f"                           {result.min_coords[2]} <= z <= {result.max_coords[2]}")

    logging.info( f"Does the mesh have global point ids: {not result.is_empty_point_global_ids}" )
    logging.info( f"Does the mesh have global cell ids: {not result.is_empty_cell_global_ids}" )

    logging.info( f"There are {len(result.cell_data.scalar_names)} scalar fields on the cells:" )
    for i in range(len(result.cell_data.scalar_names)):
        logging.info(   f"\t {result.cell_data.scalar_names[i]}"
                      + f" \t min = {result.cell_data.scalar_min_values[i]}"
                      + f" \t max = {result.cell_data.scalar_max_values[i]}" )
    logging.info( f"There are {len(result.cell_data.tensor_names)} vector/tensor fields on the cells:" )
    for i in range(len(result.cell_data.tensor_names)):
        logging.info(   f"\t {result.cell_data.tensor_names[i]}"
                      + f" \t min = {result.cell_data.tensor_min_values[i]}"
                      + f" \t max = {result.cell_data.tensor_max_values[i]}" )
    
    logging.info( f"There are {len(result.point_data.scalar_names)} scalar fields on the points:" )
    for i in range(len(result.point_data.scalar_names)):
        logging.info(   f"\t {result.point_data.scalar_names[i]}"
                      + f" \t min = {result.point_data.scalar_min_values[i]}"
                      + f" \t max = {result.point_data.scalar_max_values[i]}" )
    logging.info( f"There are {len(result.point_data.tensor_names)} vector/tensor fields on the points:" )
    for i in range(len(result.point_data.tensor_names)):
        logging.info(   f"\t {result.point_data.tensor_names[i]}"
                      + f" \t min = {result.point_data.tensor_min_values[i]}"
                      + f" \t max = {result.point_data.tensor_max_values[i]}" )
