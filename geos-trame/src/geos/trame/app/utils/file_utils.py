# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import os
import re
from io import StringIO
from typing import Any, List, TextIO
from lxml import etree as ElementTree  # type: ignore[import-untyped]


def normalize_path( x: str ) -> str:
    """Normalize the given path."""
    tmp = os.path.expanduser( x )
    tmp = os.path.abspath( tmp )
    if os.path.isfile( tmp ):
        x = tmp
    return x


def format_attribute( attribute_indent: str, ka: str, attribute_value: str ) -> str:
    """Format xml attribute strings.

    Args:
        attribute_indent (str): Attribute indent string
        ka (str): Attribute name
        attribute_value (str): Attribute value

    Returns:
        str: Formatted attribute value
    """
    # Make sure that a space follows commas
    attribute_value = re.sub( r",\s*", ", ", attribute_value )

    # Handle external brackets
    attribute_value = re.sub( r"{\s*", "{ ", attribute_value )
    attribute_value = re.sub( r"\s*}", " }", attribute_value )

    # Consolidate whitespace
    attribute_value = re.sub( r"\s+", " ", attribute_value )

    # Identify and split multi-line attributes
    if re.match( r"\s*{\s*({[-+.,0-9a-zA-Z\s]*},?\s*)*\s*}", attribute_value ):
        split_positions: List[ Any ] = [ match.end() for match in re.finditer( r"}\s*,", attribute_value ) ]
        newline_indent = "\n%s" % ( " " * ( len( attribute_indent ) + len( ka ) + 4 ) )
        new_values = []
        for a, b in zip( [ None ] + split_positions, split_positions + [ None ] ):
            new_values.append( attribute_value[ a:b ].strip() )
        if new_values:
            attribute_value = newline_indent.join( new_values )

    return attribute_value


def format_xml_level(
    output: TextIO,
    node: ElementTree.Element,
    level: int,
    indent: str = " " * 2,
    block_separation_max_depth: int = 2,
    modify_attribute_indent: bool = False,
    sort_attributes: bool = False,
    close_tag_newline: bool = False,
    include_namespace: bool = False,
) -> None:
    """Iteratively format the xml file.

    Args:
        output (file): the output text file handle
        node (lxml.etree.Element): the current xml element
        level (int): the xml depth
        indent (str): the xml indent style
        block_separation_max_depth (int): the maximum depth to separate adjacent elements
        modify_attribute_indent (bool): option to have flexible attribute indentation
        sort_attributes (bool): option to sort attributes alphabetically
        close_tag_newline (bool): option to place close tag on a separate line
        include_namespace (bool): option to include the xml namespace in the output
    """
    # Handle comments
    if node.tag is ElementTree.Comment:
        output.write( "\n%s<!--%s-->" % ( indent * level, node.text ) )

    else:
        # Write opening line
        opening_line = "\n%s<%s" % ( indent * level, node.tag )
        output.write( opening_line )

        # Write attributes
        if len( node.attrib ) > 0:
            # Choose indentation
            attribute_indent = "%s" % ( indent * ( level + 1 ) )
            if modify_attribute_indent:
                attribute_indent = " " * ( len( opening_line ) )

            # Get a copy of the attributes
            attribute_dict = node.attrib

            # Sort attribute names
            akeys = list( attribute_dict.keys() )
            if sort_attributes:
                akeys = sorted( akeys )

            # Format attributes
            for ka in akeys:
                # Avoid formatting mathpresso expressions
                if not ( node.tag in [ "SymbolicFunction", "CompositeFunction" ] and ka == "expression" ):
                    attribute_dict[ ka ] = format_attribute( attribute_indent, ka, attribute_dict[ ka ] )

            for ii in range( 0, len( akeys ) ):
                k = akeys[ ii ]
                if ( ii == 0 ) & modify_attribute_indent:
                    # TODO: attrib_ute_dict isn't define here which leads to an error
                    # output.write(' %s="%s"' % (k, attrib_ute_dict[k]))
                    pass
                else:
                    output.write( '\n%s%s="%s"' % ( attribute_indent, k, attribute_dict[ k ] ) )

        # Write children
        if len( node ):
            output.write( ">" )
            Nc = len( node )
            for ii, child in zip( range( Nc ), node ):
                format_xml_level(
                    output,
                    child,
                    level + 1,
                    indent,
                    block_separation_max_depth,
                    modify_attribute_indent,
                    sort_attributes,
                    close_tag_newline,
                    include_namespace,
                )

                # Add space between blocks
                if ( ( level < block_separation_max_depth )
                     & ( ii < Nc - 1 )
                     & ( child.tag is not ElementTree.Comment ) ):
                    output.write( "\n" )

            # Write the end tag
            output.write( "\n%s</%s>" % ( indent * level, node.tag ) )
        else:
            if close_tag_newline:
                output.write( "\n%s/>" % ( indent * level ) )
            else:
                output.write( "/>" )


def format_xml(
    input_str: str,
    indent_size: int = 2,
    indent_style: bool = False,
    block_separation_max_depth: int = 2,
    alphabetize_attributes: bool = False,
    close_style: bool = False,
    namespace: bool = False,
) -> str:
    """Script to format xml files.

    Args:
        input_str (str): Input str
        indent_size (int): Indent size
        indent_style (bool): Style of indentation (0=fixed, 1=hanging)
        block_separation_max_depth (int): Max depth to separate xml blocks
        alphabetize_attributes (bool): Alphebitize attributes
        close_style (bool): Style of close tag (0=same line, 1=new line)
        namespace (bool): Insert this namespace in the xml description
    """
    try:
        root = ElementTree.fromstring( input_str )
        prologue_comments = [ tmp.text for tmp in root.itersiblings( preceding=True ) ]
        epilog_comments = [ tmp.text for tmp in root.itersiblings() ]

        f = StringIO()
        f.write( '<?xml version="1.0" ?>\n' )

        for comment in reversed( prologue_comments ):
            f.write( "\n<!--%s-->" % comment )

        format_xml_level(
            f,
            root,
            0,
            indent=" " * indent_size,
            block_separation_max_depth=block_separation_max_depth,
            modify_attribute_indent=indent_style,
            sort_attributes=alphabetize_attributes,
            close_tag_newline=close_style,
            include_namespace=namespace,
        )

        for comment in epilog_comments:
            f.write( "\n<!--%s-->" % comment )
        f.write( "\n" )

        return f.getvalue()

    except ElementTree.ParseError as err:
        print( err.msg )
        raise Exception( "Failed to format xml file" ) from err
