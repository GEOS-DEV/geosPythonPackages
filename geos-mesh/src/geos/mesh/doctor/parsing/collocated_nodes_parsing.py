from geos.mesh.doctor.actions.collocated_nodes import Options, Result
from geos.mesh.doctor.parsing import COLLOCATES_NODES
from geos.utils.Logger import getLogger

logger = getLogger( "Collocated_nodes parsing" )

__TOLERANCE = "tolerance"
__TOLERANCE_DEFAULT = 0.

__COLLOCATED_NODES_DEFAULT = { __TOLERANCE: __TOLERANCE_DEFAULT }


def convert( parsed_options ) -> Options:
    return Options( parsed_options[ __TOLERANCE ] )


def fill_subparser( subparsers ) -> None:
    p = subparsers.add_parser( COLLOCATES_NODES, help="Checks if nodes are collocated." )
    p.add_argument( '--' + __TOLERANCE,
                    type=float,
                    metavar=__TOLERANCE_DEFAULT,
                    default=__TOLERANCE_DEFAULT,
                    required=True,
                    help="[float]: The absolute distance between two nodes for them to be considered collocated." )


def display_results( options: Options, result: Result ):
    all_collocated_nodes: list[ int ] = []
    for bucket in result.nodes_buckets:
        for node in bucket:
            all_collocated_nodes.append( node )
    all_collocated_nodes: frozenset[ int ] = frozenset( all_collocated_nodes )  # Surely useless
    if all_collocated_nodes:
        logger.error( f"You have {len(all_collocated_nodes)} collocated nodes (tolerance = {options.tolerance})." )

        logger.info( "Here are all the buckets of collocated nodes." )
        tmp: list[ str ] = []
        for bucket in result.nodes_buckets:
            tmp.append( f"({', '.join(map(str, bucket))})" )
        logger.info( f"({', '.join(tmp)})" )
    else:
        logger.error( f"You have no collocated node (tolerance = {options.tolerance})." )

    if result.wrong_support_elements:
        tmp: str = ", ".join( map( str, result.wrong_support_elements ) )
        logger.error( f"You have {len(result.wrong_support_elements)} elements with duplicated support nodes.\n" + tmp )
    else:
        logger.error( "You have no element with duplicated support nodes." )
