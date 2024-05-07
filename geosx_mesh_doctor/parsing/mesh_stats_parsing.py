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

    logging.info( f"Does the mesh have global point ids: {result.has_point_global_ids}" )
    logging.info( f"Does the mesh have global cell ids: {result.has_cell_global_ids}" )

    logging.info( f"There are {len(result.scalar_cell_data_names)} scalar fields on the cells:" )
    for i in range(len(result.scalar_cell_data_names)):
        logging.info( f"\t {result.scalar_cell_data_names[i]} \t min = {result.scalar_cell_data_mins[i]} \t max = {result.scalar_cell_data_maxs[i]}" )
    logging.info( f"There are {len(result.tensor_cell_data_names)} vector/tensor fields on the cells:" )
    for i in range(len(result.tensor_cell_data_names)):
        logging.info( f"\t {result.tensor_cell_data_names[i]}" )
    logging.info( f"There are {len(result.scalar_point_data_names)} scalar fields on the points:" )
    for i in range(len(result.scalar_point_data_names)):
        logging.info( f"\t {result.scalar_point_data_names[i]} \t min = {result.scalar_point_data_mins[i]} \t max = {result.scalar_point_data_maxs[i]}" )
    logging.info( f"There are {len(result.tensor_point_data_names)} vector/tensor fields on the points:" )
    for i in range(len(result.tensor_point_data_names)):
        logging.info( f"\t {result.tensor_point_data_names[i]}" )
