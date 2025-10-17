from geos.mesh.doctor.actions.collocated_nodes import Options, Result
from geos.mesh.doctor.parsing import COLLOCATES_NODES
from geos.mesh.doctor.parsing._shared_checks_parsing_logic import get_options_used_message
from geos.mesh.doctor.parsing.cli_parsing import setup_logger

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
    setup_logger.results( get_options_used_message( options ) )
    logger_results( setup_logger, result.nodes_buckets, result.wrong_support_elements )


def logger_results( logger, nodes_buckets: list[ tuple[ int ] ], wrong_support_elements: list[ int ] ):
    """Log the results of the collocated nodes check.

    Args:
        logger: Logger instance for output.
        nodes_buckets (list[ tuple[ int ] ]): List of collocated nodes buckets.
        wrong_support_elements (list[ int ]): List of elements with wrong support nodes.
    """
    # Accounts for external logging object that would not contain 'results' attribute
    log_method = logger.info
    if hasattr( logger, 'results' ):
        log_method = logger.results

    all_collocated_nodes: list[ int ] = []
    for bucket in nodes_buckets:
        for node in bucket:
            all_collocated_nodes.append( node )
    all_collocated_nodes = list( set( all_collocated_nodes ) )
    if all_collocated_nodes:
        log_method( f"You have {len( all_collocated_nodes )} collocated nodes." )
        log_method( "Here are all the buckets of collocated nodes." )
        tmp: list[ str ] = []
        for bucket in nodes_buckets:
            tmp.append( f"({', '.join(map(str, bucket))})" )
        log_method( f"({', '.join(tmp)})" )
    else:
        log_method( "You have no collocated node." )

    if wrong_support_elements:
        tmp: str = ", ".join( map( str, wrong_support_elements ) )
        log_method( f"You have {len(wrong_support_elements)} elements with duplicated support nodes.\n" + tmp )
    else:
        log_method( "You have no element with duplicated support nodes." )
