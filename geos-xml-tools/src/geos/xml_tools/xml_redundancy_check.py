# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2025 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2025 TotalEnergies
# Copyright (c) 2018-2025 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2025 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
from lxml import etree as ElementTree  # type: ignore[import]
import os
from pathlib import Path
from typing import Iterable, Any
from geos.xml_tools import command_line_parsers
from geos.xml_tools.attribute_coverage import parse_schema
from geos.xml_tools.xml_formatter import format_file

__doc__ = """
XML Redundancy Checker for GEOS.

This module analyzes XML files for redundant attributes and elements by comparing them to a schema.
Features:
* Removes attributes that match schema defaults.
* Prunes unused or redundant XML elements.
* Provides command-line and programmatic interfaces for batch processing.

Typical usage:
    from geos.xml_tools.xml_redundancy_check import check_xml_redundancy

Intended for cleaning and optimizing GEOS XML input files.
"""


def check_redundancy_level( local_schema: dict[ str, Any ],
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
        # An attribute is considered essential and is kept if it meets any of these conditions:
        # * It's on the special whitelist (like component).
        # * It's not defined in the schema (so we can't know if it's a default).
        # * The schema doesn't specify a default value for it.
        # * Its value is different from the schema's default value.
        if ka in whitelist or \
           ka not in local_schema[ 'attributes' ] or \
           'default' not in local_schema[ 'attributes' ][ ka ] or \
           node.get( ka ) != local_schema[ 'attributes' ][ ka ][ 'default' ]:
            node_is_required += 1
        else:
            # If an attribute is not essential (meaning its value is exactly the same as the default in the schema),
            # it's considered redundant and gets deleted from the node.
            node.attrib.pop( ka )

    for child in node:
        # Comments will not appear in the schema
        if child.tag in local_schema[ 'children' ]:
            child_is_required = check_redundancy_level( local_schema[ 'children' ][ child.tag ], child )
            node_is_required += child_is_required
            if not child_is_required:
                node.remove( child )

    return node_is_required


def check_xml_redundancy( schema: dict[ str, Any ], fname: str ) -> None:
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
        geosx_root (str): GEOS root directory
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
        -r/--root (str): GEOS root directory
    """
    # Parse the user arguments
    parser = command_line_parsers.build_xml_redundancy_input_parser()
    args = parser.parse_args()

    # Parse the xml files
    process_xml_files( args.root )


if __name__ == "__main__":
    main()
