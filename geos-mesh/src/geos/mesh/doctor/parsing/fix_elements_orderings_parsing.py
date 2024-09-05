import logging
import random

from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAGONAL_PRISM,
    VTK_HEXAHEDRON,
    VTK_PENTAGONAL_PRISM,
    VTK_PYRAMID,
    VTK_TETRA,
    VTK_VOXEL,
    VTK_WEDGE,
)
from geos.mesh.doctor.checks.fix_elements_orderings import Options, Result
from . import vtk_output_parsing, FIX_ELEMENTS_ORDERINGS

__CELL_TYPE_MAPPING = {
    "Hexahedron": VTK_HEXAHEDRON,
    "Prism5": VTK_PENTAGONAL_PRISM,
    "Prism6": VTK_HEXAGONAL_PRISM,
    "Pyramid": VTK_PYRAMID,
    "Tetrahedron": VTK_TETRA,
    "Wedge": VTK_WEDGE,
}

__CELL_TYPE_SUPPORT_SIZE = {
    VTK_HEXAHEDRON: 8,
    VTK_PENTAGONAL_PRISM: 10,
    VTK_HEXAGONAL_PRISM: 12,
    VTK_PYRAMID: 5,
    VTK_TETRA: 4,
    VTK_VOXEL: 8,
    VTK_WEDGE: 6,
}

__VOLUME_TO_REORDER = "volume_to_reorder"
__VOLUME_TO_REORDER_DEFAULT = "all"
__VOLUME_TO_REORDER_CHOICES = [ "all", "positive", "negative" ] 


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( FIX_ELEMENTS_ORDERINGS, help="Reorders the support nodes for the given cell types." )
    for key, vtk_key in __CELL_TYPE_MAPPING.items():
        tmp = list( range( __CELL_TYPE_SUPPORT_SIZE[ vtk_key ] ) )
        random.Random( 4 ).shuffle( tmp )
        p.add_argument( '--' + key,
                        type=str,
                        metavar=",".join( map( str, tmp ) ),
                        default=None,
                        required=False,
                        help=f"[list of integers]: node permutation for \"{key}\"." )
    p.add_argument( '--' + __VOLUME_TO_REORDER,
                    type=str,
                    metavar=__VOLUME_TO_REORDER_DEFAULT,
                    default=__VOLUME_TO_REORDER_DEFAULT,
                    choices=__VOLUME_TO_REORDER_CHOICES,
                    required=True,
                    help= "[str]: Select which element volume is invalid and needs reordering."
                          + "'all' will allow reordering of nodes for every element, regarding of their volume."
                          + "'positive' or 'negative' will only reorder the element with the corresponding volume." )
    vtk_output_parsing.fill_vtk_output_subparser( p )


def convert( parsed_options ) -> Options:
    """
    From the parsed cli options, return the converted options for self intersecting elements check.
    :param options_str: Parsed cli options.
    :return: Options instance.
    """
    cell_type_to_ordering = {}
    for key, vtk_key in __CELL_TYPE_MAPPING.items():
        raw_mapping = parsed_options[ key ]
        if raw_mapping:
            tmp = tuple( map( int, raw_mapping.split( "," ) ) )
            if not set( tmp ) == set( range( __CELL_TYPE_SUPPORT_SIZE[ vtk_key ] ) ):
                err_msg = f"Permutation {raw_mapping} for type {key} is not valid."
                logging.error( err_msg )
                raise ValueError( err_msg )
            cell_type_to_ordering[ vtk_key ] = tmp
    vtk_output = vtk_output_parsing.convert( parsed_options )
    volume_to_reorder: str = parsed_options[ __VOLUME_TO_REORDER ]
    if volume_to_reorder.lower() not in __VOLUME_TO_REORDER_CHOICES:
        raise ValueError( f"Please use one of these options for --volume_to_reorder: {__VOLUME_TO_REORDER_CHOICES}." )
    return Options( vtk_output=vtk_output, cell_type_to_ordering=cell_type_to_ordering,
                    volume_to_reorder=volume_to_reorder )


def display_results( options: Options, result: Result ):
    if result.output:
        logging.info( f"New mesh was written to file '{result.output}'" )
    else:
        logging.info( "No output file was written." )
    logging.info( f"Number of cells reordered:" )
    logging.info( f"\tCellType\tNumber" )
    for i in range( len( result.reordering_stats[ "Types reordered" ] ) ):
        logging.info( f"\t{result.reordering_stats[ "Types reordered" ][ i ]}" +
                      f"\t\t{result.reordering_stats[ "Number of cells reordered" ][ i ]}" )
    logging.info( f"Number of cells non reordered:" )
    logging.info( f"\tCellType\tNumber" )
    for i in range( len( result.reordering_stats[ "Types non reordered" ] ) ):
        logging.info( f"\t{result.reordering_stats[ "Types non reordered" ][ i ]}" +
                      f"\t\t{result.reordering_stats[ "Number of cells non reordered" ][ i ]}" )
