from geos.mesh.doctor.actions.collocatedNodes import Options, Result
from geos.mesh.doctor.parsing import COLLOCATES_NODES
from geos.mesh.doctor.parsing._sharedChecksParsingLogic import getOptionsUsedMessage
from geos.mesh.doctor.parsing.cliParsing import setupLogger

__TOLERANCE = "tolerance"
__TOLERANCE_DEFAULT = 0.

__COLLOCATED_NODES_DEFAULT = { __TOLERANCE: __TOLERANCE_DEFAULT }


def convert( parsedOptions ) -> Options:
    return Options( parsedOptions[ __TOLERANCE ] )


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( COLLOCATES_NODES, help="Checks if nodes are collocated." )
    p.add_argument( '--' + __TOLERANCE,
                    type=float,
                    metavar=__TOLERANCE_DEFAULT,
                    default=__TOLERANCE_DEFAULT,
                    required=True,
                    help="[float]: The absolute distance between two nodes for them to be considered collocated." )


def displayResults( options: Options, result: Result ):
    setupLogger.results( getOptionsUsedMessage( options ) )
    allCollocatedNodes: list[ int ] = []
    for bucket in result.nodesBuckets:
        for node in bucket:
            allCollocatedNodes.append( node )
    allCollocatedNodes: frozenset[ int ] = frozenset( allCollocatedNodes )  # Surely useless
    if allCollocatedNodes:
        setupLogger.results( f"You have {len( allCollocatedNodes )} collocated nodes." )
        setupLogger.results( "Here are all the buckets of collocated nodes." )
        tmp: list[ str ] = []
        for bucket in result.nodesBuckets:
            tmp.append( f"({', '.join(map(str, bucket))})" )
        setupLogger.results( f"({', '.join(tmp)})" )
    else:
        setupLogger.results( "You have no collocated node." )

    if result.wrongSupportElements:
        tmp: str = ", ".join( map( str, result.wrongSupportElements ) )
        setupLogger.results(
            f"You have {len(result.wrongSupportElements)} elements with duplicated support nodes.\n" + tmp )
    else:
        setupLogger.results( "You have no element with duplicated support nodes." )
