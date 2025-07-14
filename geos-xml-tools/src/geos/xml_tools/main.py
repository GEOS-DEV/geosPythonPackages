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
import argparse
import os
import sys
import time
from typing import Callable, Any, Union, Iterable
from geos.xml_tools import ( attribute_coverage, command_line_parsers, pyvista_viewer, vtk_builder, xml_formatter,
                             xml_processor, xml_redundancy_check ) 

__doc__ = """Unified command line tools for geos-xml-tools package."""


def check_mpi_rank() -> int:
    """Check the MPI rank.

    Returns:
        int: MPI rank
    """
    rank = 0
    mpi_rank_key_options = [ 'OMPI_COMM_WORLD_RANK', 'PMI_RANK' ]
    for k in mpi_rank_key_options:
        if k in os.environ:
            rank = int( os.environ[ k ] )
    return rank


TFunc = Callable[..., Any ]


def wait_for_file_write_rank_0( target_file_argument: Union[ int, str ] = 0,
                                max_wait_time: float = 100,
                                max_startup_delay: float = 1 ) -> Callable[ [ TFunc ], TFunc ]:
    """Constructor for a function decorator that waits for a target file to be written on rank 0.

    Args:
        target_file_argument (int, str): Index or keyword of the filename argument in the decorated function
        max_wait_time (float): Maximum amount of time to wait (seconds)
        max_startup_delay (float): Maximum delay allowed for thread startup (seconds)

    Returns:
        Wrapped function
    """
    def wait_for_file_write_rank_0_inner( writer: TFunc ) -> TFunc:
        """Intermediate constructor for the function decorator.

        Args:
            writer (typing.Callable): A function that writes to a file
        """
        def wait_for_file_write_rank_0_decorator( *args, **kwargs ) -> Any:  # noqa: ANN002, ANN003
            """Apply the writer on rank 0, and wait for completion on other ranks."""
            # Check the target file status
            rank = check_mpi_rank()
            fname = ''
            if isinstance( target_file_argument, int ):
                fname = args[ target_file_argument ]
            else:
                fname = kwargs[ target_file_argument ]

            target_file_exists = os.path.isfile( fname )
            target_file_edit_time = 0.0
            if target_file_exists:
                target_file_edit_time = os.path.getmtime( fname )

                # Variations in thread startup times may mean the file has already been processed
                # If the last edit was done within the specified time, then allow the thread to proceed
                if ( abs( target_file_edit_time - time.time() ) < max_startup_delay ):
                    target_file_edit_time = 0.0

            # Go into the target process or wait for the expected file update
            if ( rank == 0 ):
                return writer( *args, **kwargs )
            else:
                ta = time.time()
                while ( time.time() - ta < max_wait_time ):
                    if target_file_exists:
                        if ( os.path.getmtime( fname ) > target_file_edit_time ):
                            break
                    else:
                        if os.path.isfile( fname ):
                            break
                    time.sleep( 0.1 )

        return wait_for_file_write_rank_0_decorator

    return wait_for_file_write_rank_0_inner


# Command registry for unified handling
COMMAND_REGISTRY: dict[ str, tuple[ str, str, Callable, Callable, str ] ] = {}


def register_command( name: str,
                      description: str,
                      handler: Callable,
                      parser_builder: Callable,
                      examples: str = "" ) -> None:
    """Register a command with its metadata and handlers.
    
    Args:
        name: Command name
        description: Command description
        handler: Function to handle the command
        parser_builder: Function to build the command's argument parser
        examples: Example usage for the command
    """
    COMMAND_REGISTRY[ name ] = ( description, name, handler, parser_builder, examples )


def build_main_parser() -> argparse.ArgumentParser:
    """Build the main argument parser for geos-xml-tools.

    Returns:
        argparse.ArgumentParser: The main parser
    """
    parser = argparse.ArgumentParser( description="Unified command line tools for geos-xml-tools package",
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      epilog="""
Available Commands and Options:

PREPROCESS - XML preprocessing and variable substitution
  geos-xml-tools preprocess [OPTIONS]
  
  Options:
    -i, --input FILE          Input XML file(s) (multiple allowed)
    -c, --compiled-name FILE  Output compiled XML file name
    -s, --schema FILE         GEOS schema file for validation
    -v, --verbose LEVEL       Verbosity level (0-3, default: 0)
    -p, --parameters NAME VALUE  Parameter overrides (multiple allowed)
  
  Examples:
    geos-xml-tools preprocess -i input.xml -c output.xml
    geos-xml-tools preprocess -i input.xml -c output.xml -v 2 -p pressure 1000

FORMAT - XML formatting and structure cleanup
  geos-xml-tools format FILE [OPTIONS]
  
  Options:
    -i, --indent SIZE         Indent size (default: 2)
    -s, --style STYLE         Indent style (0=fixed, 1=hanging, default: 0)
    -d, --depth DEPTH         Block separation depth (default: 2)
    -a, --alphebitize LEVEL   Alphabetize attributes (0=no, 1=yes, default: 0)
    -c, --close STYLE         Close tag style (0=same line, 1=new line, default: 0)
    -n, --namespace LEVEL     Include namespace (0=no, 1=yes, default: 0)
  
  Examples:
    geos-xml-tools format input.xml -i 4
    geos-xml-tools format input.xml -i 2 -a 1 -c 1

COVERAGE - XML attribute coverage analysis
  geos-xml-tools coverage [OPTIONS]
  
  Options:
    -r, --root PATH           GEOS root directory
    -o, --output FILE         Output file name (default: attribute_test.xml)
  
  Examples:
    geos-xml-tools coverage -r /path/to/geos/root
    geos-xml-tools coverage -r /path/to/geos/root -o coverage_report.xml

REDUNDANCY - XML redundancy checking
  geos-xml-tools redundancy [OPTIONS]
  
  Options:
    -r, --root PATH           GEOS root directory
  
  Examples:
    geos-xml-tools redundancy -r /path/to/geos/root

VTK-BUILD - Build VTK deck from XML configuration
  geos-xml-tools vtk-build FILE [OPTIONS]
  
  Options:
    -a, --attribute NAME      Cell attribute name for region marker (default: Region)
    -o, --output FILE         Output VTK file (optional)
  
  Examples:
    geos-xml-tools vtk-build input.xml -a Region
    geos-xml-tools vtk-build input.xml -a Region -o output.vtm

VIEWER - 3D visualization viewer for GEOS data
  geos-xml-tools viewer [OPTIONS]
  
  Options:
    -xp, --xmlFilepath FILE   Path to XML file (required)
    -vtpc, --vtpcFilepath FILE Path to .vtpc file (optional)
    --showmesh BOOL           Show mesh (default: True)
    --showsurfaces BOOL       Show surfaces (default: True)
    --showboxes BOOL          Show boxes (default: True)
    --showwells BOOL          Show wells (default: True)
    --showperforations BOOL   Show well perforations (default: True)
    --clipToBoxes BOOL        Show only mesh elements inside boxes (default: True)
    --Zamplification FACTOR   Z amplification factor (default: 1.0)
    --attributeName NAME      Attribute name (default: attribute)
  
  Examples:
    geos-xml-tools viewer -xp input.xml --showmesh --showwells
    geos-xml-tools viewer -xp input.xml --Zamplification 2.0 --attributeName Region

For detailed help on any command, use:
  geos-xml-tools <command> --help
        """ )

    parser.add_argument( 'command', choices=list( COMMAND_REGISTRY.keys() ), help='Command to execute' )

    return parser


def handle_preprocess() -> None:
    """Handle XML preprocessing command."""
    # Process the xml file
    preprocess_args, unknown_args = command_line_parsers.parse_xml_preprocessor_arguments()

    # Attempt to only process the file on rank 0
    # Note: The rank here is determined by inspecting the system environment variables
    #       While this is not the preferred way of doing so, it avoids mpi environment errors
    #       If the rank detection fails, then it will preprocess the file on all ranks, which
    #       sometimes cause a (seemingly harmless) file write conflict.
    processor = wait_for_file_write_rank_0( target_file_argument='outputFile',
                                            max_wait_time=100 )( xml_processor.process )

    compiled_name = processor( preprocess_args.input,
                               outputFile=preprocess_args.compiled_name,
                               schema=preprocess_args.schema,
                               verbose=preprocess_args.verbose,
                               parameter_override=preprocess_args.parameters )
    if not compiled_name:
        if preprocess_args.compiled_name:
            compiled_name = preprocess_args.compiled_name
        else:
            raise Exception( 'When applying the preprocessor in parallel (outside of pygeos), '
                             'the --compiled_name argument is required' )

    print( f"XML preprocessing completed successfully!" )
    print( f"Output file: {compiled_name}" )


def handle_format() -> None:
    """Handle XML formatting command."""
    # Parse remaining arguments for formatting
    format_parser = command_line_parsers.build_xml_formatter_input_parser()
    format_args, _ = format_parser.parse_known_args()

    xml_formatter.format_file( format_args.input,
                               indent_size=format_args.indent,
                               indent_style=format_args.style,
                               block_separation_max_depth=format_args.depth,
                               alphebitize_attributes=format_args.alphebitize,
                               close_style=format_args.close,
                               namespace=format_args.namespace )

    print( f"XML formatting completed successfully!" )
    print( f"Formatted file: {format_args.input}" )


def handle_coverage() -> None:
    """Handle XML attribute coverage command."""
    # Parse remaining arguments for coverage checking
    coverage_parser = command_line_parsers.build_attribute_coverage_input_parser()
    coverage_args, _ = coverage_parser.parse_known_args()

    attribute_coverage.process_xml_files( coverage_args.root, coverage_args.output )

    print( f"XML attribute coverage analysis completed successfully!" )
    print( f"Output file: {coverage_args.output}" )


def handle_redundancy() -> None:
    """Handle XML redundancy checking command."""
    # Parse remaining arguments for redundancy checking
    redundancy_parser = command_line_parsers.build_xml_redundancy_input_parser()
    redundancy_args, _ = redundancy_parser.parse_known_args()

    xml_redundancy_check.process_xml_files( redundancy_args.root )

    print( f"XML redundancy analysis completed successfully!" )
    print( f"Analysis performed on: {redundancy_args.root}" )


def handle_vtk_build() -> None:
    """Handle VTK deck building command."""
    # Build a simple parser for VTK building arguments
    vtk_parser = argparse.ArgumentParser()
    vtk_parser.add_argument( 'input', type=str, help='Input XML file' )
    vtk_parser.add_argument( '-a',
                             '--attribute',
                             type=str,
                             default='Region',
                             help='Cell attribute name to use as region marker' )
    vtk_parser.add_argument( '-o', '--output', type=str, help='Output VTK file (optional)' )

    vtk_args, _ = vtk_parser.parse_known_args()

    # Build the VTK deck
    collection = vtk_builder.create_vtk_deck( vtk_args.input, cell_attribute=vtk_args.attribute )

    if vtk_args.output:
        # Save to file if output specified
        import vtk
        writer = vtk.vtkXMLPartitionedDataSetCollectionWriter()
        writer.SetFileName( vtk_args.output )
        writer.SetInputData( collection )
        writer.Write()
        print( f"VTK deck building completed successfully!" )
        print( f"Output file: {vtk_args.output}" )
        print( f"Number of datasets: {collection.GetNumberOfPartitionedDataSets()}" )
    else:
        print( f"VTK deck building completed successfully!" )
        print( f"Number of datasets: {collection.GetNumberOfPartitionedDataSets()}" )


def handle_viewer() -> None:
    """Handle 3D viewer command."""
    # Use the existing pyvista_viewer argument parser
    viewer_parser = pyvista_viewer.parsing()
    viewer_args, _ = viewer_parser.parse_known_args()

    print( f"Launching 3D visualization viewer..." )
    pyvista_viewer.main( viewer_args )


# Register all commands
register_command( "preprocess", "XML preprocessing and variable substitution", handle_preprocess,
                  command_line_parsers.build_preprocessor_input_parser,
                  "geos-xml-tools preprocess -i input.xml -c output.xml\n"
                  "geos-xml-tools preprocess -i input.xml -c output.xml -v 2 -p pressure 1000" )
register_command( "format", "XML formatting and structure cleanup", handle_format,
                  command_line_parsers.build_xml_formatter_input_parser,
                  "geos-xml-tools format input.xml -i 4\ngeos-xml-tools format input.xml -i 2 -a 1 -c 1" )
register_command( "coverage", "XML attribute coverage analysis", handle_coverage,
                  command_line_parsers.build_attribute_coverage_input_parser,
                  "geos-xml-tools coverage -r /path/to/geos/root -o coverage_report.xml" )
register_command( "redundancy", "XML redundancy checking", handle_redundancy,
                  command_line_parsers.build_xml_redundancy_input_parser,
                  "geos-xml-tools redundancy -r /path/to/geos/root" )
register_command( "vtk-build", "Build VTK deck from XML configuration", handle_vtk_build,
                  command_line_parsers.build_vtk_parser, "geos-xml-tools vtk-build input.xml -a Region -o file.vtm" )
register_command( "viewer", "3D visualization viewer for GEOS data", handle_viewer, pyvista_viewer.parsing,
                  "geos-xml-tools viewer -xp input.xml --showmesh --showwells\n"
                  "geos-xml-tools viewer -xp input.xml --Zamplification 2.0 --attributeName Region" )


def show_command_help( command: str ) -> None:
    """Show help for a specific command.
    
    Args:
        command: Command name to show help for
    """
    if command not in COMMAND_REGISTRY:
        print( f"Unknown command: {command}" )
        return

    description, name, _, parser_builder, examples = COMMAND_REGISTRY[ command ]

    # Print header
    print( f"{name.upper()} - {description}" )
    print( "=" * ( len( name ) + len( description ) + 3 ) + "\n" )

    # Show command-specific help
    parser = parser_builder()
    parser.print_help()
    if examples:
        print( "\nExamples:" )
        print( "-" * 9 )
        print( examples )


def preprocess_parallel() -> Iterable[ str ]:
    """MPI aware xml preprocessing."""
    # Process the xml file
    from mpi4py import MPI  # type: ignore[import]
    comm = MPI.COMM_WORLD
    rank = comm.Get_rank()

    args, unknown_args = command_line_parsers.parse_xml_preprocessor_arguments()
    compiled_name = ''
    if ( rank == 0 ):
        compiled_name = xml_processor.process( args.input,
                                               outputFile=args.compiled_name,
                                               schema=args.schema,
                                               verbose=args.verbose,
                                               parameter_override=args.parameters )
    compiled_name = comm.bcast( compiled_name, root=0 )
    return format_geos_arguments( compiled_name, unknown_args )


def format_geos_arguments( compiled_name: str, unknown_args: Iterable[ str ] ) -> Iterable[ str ]:
    """Format GEOS arguments.

    Args:
        compiled_name (str): Name of the compiled xml file
        unknown_args (list): List of unprocessed arguments

    Returns:
        list: List of arguments to pass to GEOS
    """
    geos_args = [ sys.argv[ 0 ], '-i', compiled_name ]
    if unknown_args:
        geos_args.extend( unknown_args )

    # Print the output name for use in bash scripts
    print( compiled_name )
    return geos_args


def main() -> None:
    """Main entry point for geos-xml-tools."""
    # Check if this is a help request for a specific command
    if len( sys.argv ) > 2 and sys.argv[ 2 ] in [ '--help', '-h' ]:
        command = sys.argv[ 1 ]
        show_command_help( command )
        return

    # Normal command processing
    parser = build_main_parser()
    args, remaining = parser.parse_known_args()

    # Update sys.argv to pass remaining arguments to sub-commands
    sys.argv = [ sys.argv[ 0 ] ] + remaining

    try:
        if args.command in COMMAND_REGISTRY:
            handler = COMMAND_REGISTRY[ args.command ][ 2 ]
            handler()
        else:
            print( f"Unknown command: {args.command}" )
            sys.exit( 1 )
    except Exception as e:
        print( f"Error executing {args.command}: {e}" )
        sys.exit( 1 )


if __name__ == "__main__":
    main()
