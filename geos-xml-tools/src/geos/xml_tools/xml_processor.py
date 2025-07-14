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
from lxml.etree import XMLSyntaxError  # type: ignore[import]
import os
import re
from typing import Iterable
from geos.xml_tools import regex_tools, unit_manager, xml_formatter

# Create an instance of the unit, parameter regex handlers
unitManager = unit_manager.UnitManager()
parameterHandler = regex_tools.DictRegexHandler()

__doc__ = """
Pre-processor for XML files in GEOS.
The main goal of this script is to process and simplify complex XML configurations.
It achieves this by performing several key actions in sequence:
* Merging Files: Combines multiple XML files into one.
* Substituting Variables: Replaces placeholders (like $pressure) with actual values.
* Handling Units: Converts values with units (like 100[psi]) into a standard base unit.
* Evaluating Math: Calculates mathematical expressions directly within the XML.
* Validation: Optionally checks if the final XML conforms to a master schema.
"""


def merge_xml_nodes( existingNode: ElementTree.Element, targetNode: ElementTree.Element, level: int ) -> None:
    """Merges two XML nodes. When it encounters a child node in the targetNode that has the same name.

    as one in the existingNode, it merges them recursively instead of just adding a duplicate.
    Otherwise, it appends new children.

    Args:
        existingNode (lxml.etree.Element): The current node in the base xml structure.
        targetNode (lxml.etree.Element): The node to insert.
        level (int): The xml file depth.
    """
    # Copy attributes on the current level
    for tk in targetNode.attrib:
        existingNode.set( tk, targetNode.get( tk ) )

    # Copy target children into the xml structure
    currentTag = ''
    matchingSubNodes = []

    for target in targetNode.getchildren():
        insertCurrentLevel = True

        # Check to see if a node with the appropriate type
        # exists at this level
        if ( currentTag != target.tag ):
            currentTag = target.tag
            matchingSubNodes = existingNode.findall( target.tag )

        if ( matchingSubNodes ):
            targetName = target.get( 'name' )

            # Special case for the root Problem node (which may be unnamed)
            if ( level == 0 ):
                insertCurrentLevel = False
                merge_xml_nodes( matchingSubNodes[ 0 ], target, level + 1 )

            # Handle named xml nodes
            elif ( targetName and ( currentTag not in [ 'Nodeset' ] ) ):
                for match in matchingSubNodes:
                    if ( match.get( 'name' ) == targetName ):
                        insertCurrentLevel = False
                        merge_xml_nodes( match, target, level + 1 )

        # Insert any unnamed nodes or named nodes that aren't present
        # in the current xml structure
        if ( insertCurrentLevel ):
            existingNode.insert( -1, target )


def merge_included_xml_files( root: ElementTree.Element, fname: str, includeCount: int, maxInclude: int = 100 ) -> None:
    """Opens an XML file specified in an <Included> tag, recursively calls itself for any includes within that file.

    and then uses merge_xml_nodes to merge the contents into the main XML tree.
    It includes a safety check to prevent infinite include loops.

    Args:
        root (lxml.etree.Element): The root node of the base xml structure.
        fname (str): The name of the target xml file to merge.
        includeCount (int): The current recursion depth.
        maxInclude (int): The maximum number of xml files to include (default = 100)
    """
    # Expand the input path
    pwd = os.getcwd()
    includePath, fname = os.path.split( os.path.abspath( os.path.expanduser( fname ) ) )
    os.chdir( includePath )

    # Check to see if the code has fallen into a loop
    includeCount += 1
    if ( includeCount > maxInclude ):
        raise Exception( 'Reached maximum recursive includes...  Is there an include loop?' )

    # Check to make sure the file exists
    if ( not os.path.isfile( fname ) ):
        print( 'Included file does not exist: %s' % ( fname ) )
        raise Exception( 'Check included file path!' )

    # Load target xml
    try:
        parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
        includeTree = ElementTree.parse( fname, parser )
        includeRoot = includeTree.getroot()
    except XMLSyntaxError as err:
        print( '\nCould not load included file: %s' % ( fname ) )
        print( err.msg )
        raise Exception( '\nCheck included file!' ) from err

    # Recursively add the includes:
    for includeNode in includeRoot.findall( 'Included' ):
        for f in includeNode.findall( 'File' ):
            merge_included_xml_files( root, f.get( 'name' ), includeCount )

    # Merge the results into the xml tree
    merge_xml_nodes( root, includeRoot, 0 )
    os.chdir( pwd )


def apply_regex_to_node( node: ElementTree.Element ) -> None:
    """Recursively going through every element in the XML tree and inspects its attributes.

    For each attribute value, it sequentially applies regular expressions to:
    * Replace parameter variables ($variable) with their values.
    * Convert physical units (value[unit]) into base SI values.
    * Evaluate symbolic math expressions (`1+2*3`) into a single number.

    Args:
        node (lxml.etree.Element): The target node in the xml structure.
    """
    for k in node.attrib:
        value = node.get( k )

        # Parameter format:  $Parameter or $:Parameter
        ii = 0
        while ( '$' in value ):
            value = re.sub( regex_tools.patterns[ 'parameters' ], parameterHandler, value )
            ii += 1
            if ( ii > 100 ):
                raise Exception( 'Reached maximum parameter expands (Node=%s, value=%s)' % ( node.tag, value ) )

        # Unit format:       9.81[m**2/s] or 1.0 [bbl/day]
        if ( '[' in value ):
            value = re.sub( regex_tools.patterns[ 'units' ], unitManager.regexHandler, value )

        # Symbolic format:   `1 + 2.34e5*2 * ...`
        ii = 0
        while ( '`' in value ):
            value = re.sub( regex_tools.patterns[ 'symbolic' ], regex_tools.SymbolicMathRegexHandler, value )
            ii += 1
            if ( ii > 100 ):
                raise Exception( 'Reached maximum symbolic expands (Node=%s, value=%s)' % ( node.tag, value ) )

        node.set( k, value )

    for subNode in node.getchildren():
        apply_regex_to_node( subNode )


def generate_random_name( prefix: str = '', suffix: str = '.xml' ) -> str:
    """If the target name is not specified, generate a random name for the compiled xml.

    Args:
        prefix (str): The file prefix (default = '').
        suffix (str): The file suffix (default = '.xml')

    Returns:
        str: Random file name
    """
    from hashlib import md5
    from time import time
    from os import getpid

    tmp = str( time() ) + str( getpid() )
    return '%s%s%s' % ( prefix, md5( tmp.encode( 'utf-8' ) ).hexdigest(), suffix )


def process(
        inputFiles: Iterable[ str ],
        outputFile: str = '',
        schema: str = '',
        verbose: int = 0,
        parameter_override: list[ tuple[ str, str ] ] = [],  # noqa: B006
        keep_parameters: bool = True,
        keep_includes: bool = True ) -> str:
    """Process an xml file following these steps.

    1) Merging multiple input files specified via <Included> tags into a single one.
    2) Building a map of variables from <Parameters> blocks.
    3) Applying regex substitutions for parameters ($variable), units (10[m/s]), symbolic math expressions (`1+2*3`).
    4) Write the XML after these first 3 steps as a new file.
    4) Optionally validates the final XML against a schema.

    Args:
        inputFiles (list): Input file names.
        outputFile (str): Output file name (if not specified, then generate randomly).
        schema (str): Schema file name to validate the final xml (if not specified, then do not validate).
        verbose (int): Verbosity level.
        parameter_override (list): Parameter value overrides
        keep_parameters (bool): If True, then keep parameters in the compiled file (default = True)
        keep_includes (bool): If True, then keep includes in the compiled file (default = True)

    Returns:
        str: Output file name.
    """
    if verbose:
        print( '\nReading input xml parameters and parsing symbolic math...' )

    # Check the type of inputFiles
    if isinstance( inputFiles, str ):
        inputFiles = [ inputFiles ]

    # Expand the input path
    pwd = os.getcwd()
    expanded_files = [ os.path.abspath( os.path.expanduser( f ) ) for f in inputFiles ]
    single_path, single_input = os.path.split( expanded_files[ 0 ] )
    os.chdir( single_path )

    # Handle single vs. multiple command line inputs
    root = ElementTree.Element( "Problem" )
    tree = ElementTree.ElementTree()
    if ( len( expanded_files ) == 1 ):
        # Load single files directly
        try:
            parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
            tree = ElementTree.parse( single_input, parser=parser )
            root = tree.getroot()
        except XMLSyntaxError as err:
            print( '\nCould not load input file: %s' % ( single_input ) )
            print( err.msg )
            raise Exception( '\nCheck input file!' ) from err

    else:
        # For multiple inputs, create a simple xml structure to hold
        # the included files.  These will be saved as comments in the compiled file
        root = ElementTree.Element( 'Problem' )
        tree = ElementTree.ElementTree( root )
        included_node = ElementTree.Element( "Included" )
        root.append( included_node )
        for f in expanded_files:
            included_file = ElementTree.Element( "File" )
            included_file.set( 'name', f )
            included_node.append( included_file )

    # Add the included files to the xml structure
    # Note: doing this first assumes that parameters aren't used in Included block
    includeCount = 0
    for includeNode in root.findall( 'Included' ):
        for f in includeNode.findall( 'File' ):
            merge_included_xml_files( root, f.get( 'name' ), includeCount )  # type: ignore[attr-defined]
    os.chdir( pwd )

    # Build the parameter map
    Pmap = {}
    for parameters in root.findall( 'Parameters' ):
        for p in parameters.findall( 'Parameter' ):
            Pmap[ p.get( 'name' ) ] = p.get( 'value' )

    # Apply any parameter overrides
    if len( parameter_override ):
        # Save overriden values to a new xml element
        command_override_node = ElementTree.Element( "CommandLineOverride" )
        root.append( command_override_node )
        for ii in range( len( parameter_override ) ):
            pname = parameter_override[ ii ][ 0 ]
            pval = ' '.join( parameter_override[ ii ][ 1: ] )
            Pmap[ pname ] = pval
            override_parameter = ElementTree.Element( "Parameter" )
            override_parameter.set( 'name', pname )
            override_parameter.set( 'value', pval )
            command_override_node.append( override_parameter )

    # Add the parameter map to the handler
    parameterHandler.target = Pmap

    # Process any parameters, units, and symbolic math in the xml
    apply_regex_to_node( root )

    # A dictionary to map element tags to their cleanup flags
    nodes_to_cleanup = {
        'Included': keep_includes,
        'Parameters': keep_parameters,
        'CommandLineOverride': keep_parameters
    }

    # Iterate over a static copy of the children to safely modify the tree
    for node in list( root ):
        # Check if the node's tag is one we need to process
        if node.tag in nodes_to_cleanup:
            # If the cleanup flag is True, create and append a comment
            if nodes_to_cleanup[ node.tag ]:
                root.insert( -1, ElementTree.Comment( ElementTree.tostring( node ) ) )
            # We remove the original node
            root.remove( node )

    # Generate a random output name if not specified
    if not outputFile:
        outputFile = generate_random_name( prefix='prep_' )

    # Write the output file
    tree.write( outputFile, pretty_print=True )

    # Check for un-matched special characters
    with open( outputFile, 'r' ) as ofile:
        for line in ofile:
            if any( [ sc in line for sc in [ '$', '[', ']', '`' ] ] ):  #noqa: C419
                raise Exception( 'Found un-matched special characters in the pre-processed input file on line:\n%s\n '
                                 'Check your input xml for errors!' % ( line ) )

    # Apply formatting to the file
    xml_formatter.format_file( outputFile )

    if verbose:
        print( 'Preprocessed xml file stored in %s' % ( outputFile ) )

    if schema:
        validate_xml( outputFile, schema, verbose )

    return outputFile


def validate_xml( fname: str, schema: str, verbose: int ) -> None:
    """Validate an xml file, and parse the warnings.

    Args:
        fname (str): Target xml file name.
        schema (str): Schema file name.
        verbose (int): Verbosity level.
    """
    if verbose:
        print( 'Validating the xml against the schema...' )
    try:
        ofile = ElementTree.parse( fname )
        sfile = ElementTree.XMLSchema( ElementTree.parse( os.path.expanduser( schema ) ) )
        sfile.assertValid( ofile )
    except ElementTree.DocumentInvalid as err:
        print( err )
        print( '\nWarning: input XML contains potentially invalid input parameters:' )
        print( '-' * 20 + '\n' )
        print( sfile.error_log )
        print( '\n' + '-' * 20 )
        print( '(Total schema warnings: %i)\n' % ( len( sfile.error_log ) ) )

    if verbose:
        print( 'Done!' )
