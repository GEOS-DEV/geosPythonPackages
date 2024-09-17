import logging
import random
from geos.mesh.doctor.checks.fix_elements_orderings import Options, Result
from . import vtk_output_parsing, FIX_ELEMENTS_ORDERINGS

__CELL_NAME_WITH_NUMBER_NODES = {
    "Tetrahedron": 4,
    "Pyramid": 5,
    "Wedge": 6,
    "Hexahedron": 8,
    "Prism5": 10,
    "Prism6": 12
}

__VOLUME_TO_REORDER = "volume_to_reorder"
__VOLUME_TO_REORDER_DEFAULT = "all"
__VOLUME_TO_REORDER_CHOICES = [ "all", "positive", "negative" ]


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( FIX_ELEMENTS_ORDERINGS, help="Reorders the support nodes for the given cell types." )
    for element_name, size in __CELL_NAME_WITH_NUMBER_NODES.items():
        tmp = list( range( size ) )
        random.Random( 4 ).shuffle( tmp )
        p.add_argument( '--' + element_name,
                        type=str,
                        metavar=",".join( map( str, tmp ) ),
                        default=None,
                        required=False,
                        help=f"[list of integers]: node permutation for \"{element_name}\"." )
    p.add_argument( '--' + __VOLUME_TO_REORDER,
                    type=str,
                    default=__VOLUME_TO_REORDER_DEFAULT,
                    metavar=",".join( map( str, __VOLUME_TO_REORDER_CHOICES ) ),
                    required=True,
                    help="[str]: Select which element volume is invalid and needs reordering." +
                    " 'all' will allow reordering of nodes for every element, regarding of their volume." +
                    " 'positive' or 'negative' will only reorder the element with the corresponding volume." )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    """
    From the parsed cli options, return the converted options for self intersecting elements check.
    :param options_str: Parsed cli options.
    :return: Options instance.
    """
    cell_name_to_ordering: dict[ str, list[ int ] ] = {}
    for element_name, size in __CELL_NAME_WITH_NUMBER_NODES.items():
        raw_mapping = parsed_options[ element_name ]
        if raw_mapping:
            nodes_ordering = tuple( map( int, raw_mapping.split( "," ) ) )
            if not set( nodes_ordering ) == set( range( size ) ):
                err_msg: str = f"Permutation {raw_mapping} for type {element_name} is not valid."
                logging.error( err_msg )
                raise ValueError( err_msg )
            cell_name_to_ordering[ element_name ] = nodes_ordering
    vtk_output = vtk_output_parsing.convert( parsed_options )
    volume_to_reorder: str = parsed_options[ __VOLUME_TO_REORDER ]
    if volume_to_reorder.lower() not in __VOLUME_TO_REORDER_CHOICES:
        raise ValueError( f"Please use one of these options for --volume_to_reorder: {__VOLUME_TO_REORDER_CHOICES}." )
    return Options( vtk_output=vtk_output,
                    cell_name_to_ordering=cell_name_to_ordering,
                    volume_to_reorder=volume_to_reorder )


def display_results( options: Options, result: Result ):
    if result.output:
        logging.info( f"New mesh was written to file '{result.output}'" )
    else:
        logging.info( "No output file was written." )
    logging.info( f"Number of cells reordered:" )
    logging.info( f"\tCellType\tNumber" )
    for i in range( len( result.reordering_stats[ "Types reordered" ] ) ):
        logging.info( f"\t{result.reordering_stats[ 'Types reordered' ][ i ]}" +
                      f"\t\t{result.reordering_stats[ 'Number of cells reordered' ][ i ]}" )
    logging.info( f"Number of cells non reordered:" )
    logging.info( f"\tCellType\tNumber" )
    for i in range( len( result.reordering_stats[ "Types non reordered" ] ) ):
        logging.info( f"\t{result.reordering_stats[ 'Types non reordered' ][ i ]}" +
                      f"\t\t{result.reordering_stats[ 'Number of cells non reordered' ][ i ]}" )
