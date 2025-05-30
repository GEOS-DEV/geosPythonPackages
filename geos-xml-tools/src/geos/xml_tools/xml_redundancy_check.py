from geos.xml_tools.attribute_coverage import parse_schema
from geos.xml_tools.xml_formatter import format_file
from lxml import etree as ElementTree  # type: ignore[import]
import os
from pathlib import Path
from geos.xml_tools import command_line_parsers
from typing import Iterable, Dict, Any


def check_redundancy_level( local_schema: Dict[ str, Any ],
                            node: ElementTree.Element,
                            whitelist: Iterable[ str ] = [ 'component' ] ) -> int:
    """Check xml redundancy at the current level.

    Args:
        local_schema (dict): Schema definitions
        node (lxml.etree.Element): current xml node
        whitelist (list): always match nodes containing these attributes

    Returns:
        int: Number of required attributes in the node and its children
    """
    node_is_required = 0
    for ka in node.attrib:
        if ( ka in whitelist ) or ( ka not in local_schema[ 'attributes' ] ) or (
                'default'
                not in local_schema[ 'attributes' ][ ka ] ) or ( node.get( ka )
                                                                 != local_schema[ 'attributes' ][ ka ][ 'default' ] ):
            node_is_required += 1
        else:
            node.attrib.pop( ka )

    for child in node:
        # Comments will not appear in the schema
        if child.tag in local_schema[ 'children' ]:
            child_is_required = check_redundancy_level( local_schema[ 'children' ][ child.tag ], child )
            node_is_required += child_is_required
            if not child_is_required:
                node.remove( child )

    return node_is_required


def check_xml_redundancy( schema: Dict[ str, Any ], fname: str ) -> None:
    """Check redundancy in an xml file.

    Args:
        schema (dict): Schema definitions
        fname (str): Name of the target file
    """
    xml_tree = ElementTree.parse( fname )
    xml_root = xml_tree.getroot()
    check_redundancy_level( schema[ 'Problem' ], xml_root )
    xml_tree.write( fname )
    format_file( fname )


def process_xml_files( geosx_root: str ) -> None:
    """Test for xml redundancy.

    Args:
        geosx_root (str): GEOSX root directory
    """
    # Parse the schema
    geosx_root = os.path.expanduser( geosx_root )
    schema_fname = '%ssrc/coreComponents/schema/schema.xsd' % ( geosx_root )
    schema = parse_schema( schema_fname )

    # Find all xml files, collect their attributes
    for folder in [ 'src', 'examples' ]:
        print( folder )
        xml_files = Path( os.path.join( geosx_root, folder ) ).rglob( '*.xml' )
        for f in xml_files:
            print( '  %s' % ( str( f ) ) )
            check_xml_redundancy( schema, str( f ) )


def main() -> None:
    """Entry point for the xml attribute usage test script.

    Args:
        -r/--root (str): GEOSX root directory
    """
    # Parse the user arguments
    parser = command_line_parsers.build_xml_redundancy_input_parser()
    args = parser.parse_args()

    # Parse the xml files
    process_xml_files( args.root )


if __name__ == "__main__":
    main()
