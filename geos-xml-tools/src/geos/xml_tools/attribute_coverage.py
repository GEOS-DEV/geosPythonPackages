# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
from lxml import etree as ElementTree  # type: ignore[import]
import os
from pathlib import Path
from typing import Any, Iterable
from geos.xml_tools import command_line_parsers

__doc__ = """
Tool designed to analyze how well a project's XML files cover the possibilities defined in an XML Schema Definition (.xsd) file.
It checks which attributes are used in a codebase and generates a report.
The script works in three main stages:
* Parse the Schema: It reads the master .xsd file to understand all possible elements, attributes, and their default values.
* Collect Usage Data: It scans through all .xml files in specified folders (like src and examples) and records every attribute value it finds.
* Generate a Report: It creates a new XML file that summarizes the findings, showing which attributes were used, what values they were given, and their default values from the schema.
"""

record_type = dict[ str, dict[ str, Any ] ]


def parse_schema_element( root: ElementTree.Element,
                          node: ElementTree.Element,
                          xsd: str = '{http://www.w3.org/2001/XMLSchema}',
                          recursive_types: Iterable[ str ] = [ 'PeriodicEvent', 'SoloEvent', 'HaltEvent' ],
                          folders: Iterable[ str ] = [ 'src', 'examples' ] ) -> record_type:
    """Parse the xml schema at the current level.
    Recursively builds a nested dictionary that mirrors the schema's structure.
    For each element, it records the names of its valid attributes and children.
    If an attribute has a default value defined in the schema, it stores that as well.

    Args:
        root (lxml.etree.Element): the root schema node
        node (lxml.etree.Element): current schema node
        xsd (str): the file namespace
        recursive_types (list): node tags that allow recursive nesting
        folders (list): folders to sort xml attribute usage into

    Returns:
        dict: Dictionary of attributes and children for the current node
    """
    element_type = node.get( 'type' )
    element_name = node.get( 'name' )
    element_def = root.find( "%scomplexType[@name='%s']" % ( xsd, element_type ) )
    local_types: record_type = { 'attributes': {}, 'children': {} }

    # Parse attributes
    for attribute in element_def.findall( '%sattribute' % ( xsd ) ):
        attribute_name = attribute.get( 'name' )
        local_types[ 'attributes' ][ attribute_name ] = { ka: [] for ka in folders }
        if ( 'default' in attribute.attrib ):
            local_types[ 'attributes' ][ attribute_name ][ 'default' ] = attribute.get( 'default' )

    # Parse children
    choice_node = element_def.findall( '%schoice' % ( xsd ) )
    if choice_node:
        for child in choice_node[ 0 ].findall( '%selement' % ( xsd ) ):
            child_name = child.get( 'name' )
            if not ( ( child_name in recursive_types ) and ( element_name in recursive_types ) ):
                local_types[ 'children' ][ child_name ] = parse_schema_element( root, child )

    return local_types


def parse_schema( fname: str ) -> record_type:
    """Parse the schema file into the xml attribute usage dict.

    Args:
        fname (str): schema name

    Returns:
        dict: Dictionary of attributes and children for the entire schema
    """
    xml_tree = ElementTree.parse( fname )
    xml_root = xml_tree.getroot()
    problem_node = xml_root.find( "{http://www.w3.org/2001/XMLSchema}element" )
    return { 'Problem': parse_schema_element( xml_root, problem_node ) }


def collect_xml_attributes_level( local_types: record_type, node: ElementTree.Element, folder: str ) -> None:
    """Collect xml attribute usage at the current level by going through the XML file's elements.
    When it finds an attribute, it appends its value to the appropriate list
    in the data structure created by parse_schema.

    Args:
        local_types (dict): dictionary containing attribute usage
        node (lxml.etree.Element): current xml node
        folder (str): the source folder for the current file
    """
    for ka in node.attrib:
        local_types[ 'attributes' ][ ka ][ folder ].append( node.get( ka ) )

    for child in node:
        if child.tag in local_types[ 'children' ]:
            collect_xml_attributes_level( local_types[ 'children' ][ child.tag ], child, folder )


def collect_xml_attributes( xml_types: record_type, fname: str, folder: str ) -> None:
    """Collect xml attribute usage in a file.

    Args:
        xml_types (dict): dictionary containing attribute usage
        fname (str): name of the target file
        folder (str): the source folder for the current file
    """
    parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
    xml_tree = ElementTree.parse( fname, parser=parser )
    xml_root = xml_tree.getroot()

    collect_xml_attributes_level( xml_types[ 'Problem' ], xml_root, folder )


def write_attribute_usage_xml_level( local_types: record_type,
                                     node: ElementTree.Element,
                                     folders: Iterable[ str ] = [ 'src', 'examples' ] ) -> None:
    """Recursively builds a report called attribute usage file.
    For each element and attribute from the schema, it creates a new XML element.
    It sets attributes on this new element to show the collected values from the src and examples folders,
    the default value, and a count of unique values found.

    Args:
        local_types (dict): dict containing attribute usage at the current level
        node (lxml.etree.Element): current xml node
        folders (Iterable[ str ]): folders. Defaults to [ 'src', 'examples' ].
    """
    # Write attributes
    for ka in local_types[ 'attributes' ]:
        attribute_node = ElementTree.Element( ka )
        node.append( attribute_node )

        if ( 'default' in local_types[ 'attributes' ][ ka ] ):
            attribute_node.set( 'default', local_types[ 'attributes' ][ ka ][ 'default' ] )

        unique_values = []
        for f in folders:
            sub_values = list( set( local_types[ 'attributes' ][ ka ][ f ] ) )
            unique_values.extend( sub_values )
            attribute_node.set( f, ' | '.join( sub_values ) )

        unique_length = len( set( unique_values ) )
        attribute_node.set( 'unique_values', str( unique_length ) )

    # Write children
    for ka in sorted( local_types[ 'children' ] ):
        child = ElementTree.Element( ka )
        node.append( child )
        write_attribute_usage_xml_level( local_types[ 'children' ][ ka ], child )


def write_attribute_usage_xml( xml_types: record_type, fname: str ) -> None:
    """Write xml attribute usage file.

    Args:
        xml_types (dict): dictionary containing attribute usage by xml type
        fname (str): output file name
    """
    xml_root = ElementTree.Element( 'Problem' )
    xml_tree = ElementTree.ElementTree( xml_root )

    write_attribute_usage_xml_level( xml_types[ 'Problem' ], xml_root )
    xml_tree.write( fname, pretty_print=True )


def process_xml_files( geos_root: str, output_name: str ) -> None:
    """Test for xml attribute usage.

    Args:
        geos_root (str): GEOS root directory
        output_name (str): output file name
    """
    # Parse the schema
    geos_root = os.path.expanduser( geos_root )
    schema = '%ssrc/coreComponents/schema/schema.xsd' % ( geos_root )
    xml_types = parse_schema( schema )

    # Find all xml files, collect their attributes
    for folder in [ 'src', 'examples' ]:
        print( folder )
        xml_files = Path( os.path.join( geos_root, folder ) ).rglob( '*.xml' )
        for f in xml_files:
            print( '  %s' % ( str( f ) ) )
            collect_xml_attributes( xml_types, str( f ), folder )

    # Consolidate attributes
    write_attribute_usage_xml( xml_types, output_name )


def main() -> None:
    """Entry point for the xml attribute usage test script.

    Args:
        -r/--root (str): GEOS root directory
        -o/--output (str): output file name
    """
    # Parse the user arguments
    parser = command_line_parsers.build_attribute_coverage_input_parser()
    args = parser.parse_args()

    # Parse the xml files
    process_xml_files( args.root, args.output )


if __name__ == "__main__":
    main()
