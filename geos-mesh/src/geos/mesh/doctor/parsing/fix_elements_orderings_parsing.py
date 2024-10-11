import logging
from geos.mesh.doctor.checks.fix_elements_orderings import Options, Result, NAME_TO_VTK_TYPE
from . import vtk_output_parsing, FIX_ELEMENTS_ORDERINGS

__CELL_NAMES = "cell_names"
__CELL_NAMES_CHOICES = list( NAME_TO_VTK_TYPE.keys() )

__VOLUME_TO_REORDER = "volume_to_reorder"
__VOLUME_TO_REORDER_DEFAULT = "negative"
__VOLUME_TO_REORDER_CHOICES = [ "all", "positive", "negative" ]


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( FIX_ELEMENTS_ORDERINGS, help="Reorders the support nodes for the given cell types." )
    p.add_argument( '--' + __CELL_NAMES,
                    type=str,
                    metavar=", ".join( map( str, __CELL_NAMES_CHOICES ) ),
                    default=", ".join( map( str, __CELL_NAMES_CHOICES ) ),
                    help=( "[list of str]: Cell names that can be reordered in your grid. You can use multiple names." +
                           " Defaults to all cell names being used." ) )
    p.add_argument( '--' + __VOLUME_TO_REORDER,
                    type=str,
                    default=__VOLUME_TO_REORDER_DEFAULT,
                    metavar=", ".join( __VOLUME_TO_REORDER_CHOICES ),
                    help=( "[str]: Select which element volume is invalid and needs reordering." +
                           " 'all' will allow reordering of nodes for every element, regarding of their volume." +
                           " 'positive' or 'negative' will only reorder the element with the corresponding volume." +
                           " Defaults to 'negative'." ) )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    """
    From the parsed cli options, return the converted options for self intersecting elements check.
    :param options_str: Parsed cli options.
    :return: Options instance.
    """
    raw_mapping = parsed_options[ __CELL_NAMES ]
    cell_names_to_reorder = tuple( raw_mapping.split( "," ) )
    for cell_name in cell_names_to_reorder:
        if cell_name not in __CELL_NAMES_CHOICES:
            raise ValueError( f"Please choose names between these options for --{__CELL_NAMES}:" +
                              f" {__CELL_NAMES_CHOICES}." )
    vtk_output = vtk_output_parsing.convert( parsed_options )
    volume_to_reorder: str = parsed_options[ __VOLUME_TO_REORDER ]
    if volume_to_reorder.lower() not in __VOLUME_TO_REORDER_CHOICES:
        raise ValueError( f"Please use one of these options for --{__VOLUME_TO_REORDER}:" +
                          f" {__VOLUME_TO_REORDER_CHOICES}." )
    return Options( vtk_output=vtk_output,
                    cell_names_to_reorder=cell_names_to_reorder,
                    volume_to_reorder=volume_to_reorder )


def display_results( options: Options, result: Result ):
    if result.output:
        logging.info( f"New mesh was written to file '{result.output}'" )
    else:
        logging.info( "No output file was written." )
    if len( result.reordering_stats[ "Types reordered" ] ) > 0:
        logging.info( "Number of cells reordered:" )
        logging.info( "\tCellType\tNumber" )
        for i in range( len( result.reordering_stats[ "Types reordered" ] ) ):
            type_r = result.reordering_stats[ "Types reordered" ][ i ]
            number = result.reordering_stats[ "Number of cells reordered" ][ i ]
            logging.info( f"\t{type_r}\t\t{number}" )
    if len( result.reordering_stats[ "Types non reordered because ordering is already correct" ] ) > 0:
        logging.info( "Number of cells non reordered because ordering is already correct:" )
        logging.info( "\tCellType\tNumber" )
        for i in range( len( result.reordering_stats[ "Types non reordered because ordering is already correct" ] ) ):
            type_nr = result.reordering_stats[ "Types non reordered because ordering is already correct" ][ i ]
            number = result.reordering_stats[ "Number of cells non reordered because ordering is already correct" ][ i ]
            logging.info( f"\t{type_nr}\t\t{number}" )
    if len( result.reordering_stats[ "Types non reordered because of errors" ] ) > 0:
        logging.info( "Number of cells non reordered because of errors:" )
        logging.info( "\tCellType\tNumber" )
        for i in range( len( result.reordering_stats[ "Types non reordered because of errors" ] ) ):
            type_nr = result.reordering_stats[ "Types non reordered because of errors" ][ i ]
            number = result.reordering_stats[ "Number of cells non reordered because of errors" ][ i ]
            err_msg = result.reordering_stats[ "Error message given" ][ i ]
            logging.info( f"\t{type_nr}\t\t{number}" )
            logging.info( f"\tError message: {err_msg}" )