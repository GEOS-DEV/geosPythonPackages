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
from typing import Iterable


def build_preprocessor_input_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        argparse.ArgumentParser: The parser
    """
    # Parse the user arguments
    parser = argparse.ArgumentParser()
    parser.add_argument( '-i', '--input', type=str, action='append', help='Input file name (multiple allowed)' )
    parser.add_argument( '-c',
                         '--compiled-name',
                         type=str,
                         help='Compiled xml file name (otherwise, it is randomly genrated)',
                         default='' )
    parser.add_argument( '-s', '--schema', type=str, help='GEOS schema to use for validation', default='' )
    parser.add_argument( '-v', '--verbose', type=int, help='Verbosity of outputs', default=0 )
    parser.add_argument( '-p',
                         '--parameters',
                         nargs='+',
                         action='append',
                         help='Parameter overrides (name value, multiple allowed)',
                         default=[] )

    return parser


def parse_xml_preprocessor_arguments() -> tuple[ argparse.Namespace, Iterable[ str ] ]:
    """Parse user arguments.

    Returns:
        list: The remaining unparsed argument strings
    """
    parser = build_preprocessor_input_parser()
    return parser.parse_known_args()


def build_vtk_parser() -> argparse.ArgumentParser:
    """Build VTK parser for help display.

    Returns:
        argparse.ArgumentParser: the parser instance
    """
    parser = argparse.ArgumentParser( description="Build VTK deck from XML configuration" )
    parser.add_argument( 'input', type=str, help='Input XML file' )
    parser.add_argument( '-a',
                         '--attribute',
                         type=str,
                         default='Region',
                         help='Cell attribute name to use as region marker' )
    parser.add_argument( '-o', '--output', type=str, help='Output VTK file (optional)' )
    return parser


def build_xml_formatter_input_parser() -> argparse.ArgumentParser:
    """Build the argument parser.

    Returns:
        argparse.ArgumentParser: the parser instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument( 'input', type=str, help='Input file name' )
    parser.add_argument( '-i', '--indent', type=int, help='Indent size', default=2 )
    parser.add_argument( '-s', '--style', type=int, help='Indent style', default=0 )
    parser.add_argument( '-d', '--depth', type=int, help='Block separation depth', default=2 )
    parser.add_argument( '-a', '--alphebitize', type=int, help='Alphebetize attributes', default=0 )
    parser.add_argument( '-c', '--close', type=int, help='Close tag style', default=0 )
    parser.add_argument( '-n', '--namespace', type=int, help='Include namespace', default=0 )
    return parser


def build_attribute_coverage_input_parser() -> argparse.ArgumentParser:
    """Build attribute coverage redundancy input parser.

    Returns:
        argparse.ArgumentParser: parser instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument( '-r', '--root', type=str, help='GEOS root', default='' )
    parser.add_argument( '-o', '--output', type=str, help='Output file name', default='attribute_test.xml' )
    return parser


def build_xml_redundancy_input_parser() -> argparse.ArgumentParser:
    """Build xml redundancy input parser.

    Returns:
        argparse.ArgumentParser: parser instance
    """
    parser = argparse.ArgumentParser()
    parser.add_argument( '-r', '--root', type=str, help='GEOS root', default='' )
    return parser
