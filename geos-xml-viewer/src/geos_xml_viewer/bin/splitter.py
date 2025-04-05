# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import argparse
from pathlib import PurePath

from geos_xml_viewer.algorithms.deck import SimulationDeck, read, format_xml
from lxml import etree as ElementTree  # type: ignore[import-untyped]


def valid_file( param: str ) -> str:
    """File validation function for argparse for .vtpc files.

    Args:
        param (str): filepath to a .vtpc

    Raises:
        argparse.ArgumentTypeError: Raises an error if the file does not have a .vtpc extension

    Returns:
        str: filepath to a.vtpc
    """
    ext: str = PurePath( param ).suffix
    if ext.lower() != ".vtpc":
        raise argparse.ArgumentTypeError( "File must have a .vtpc extension" )
    return param


def parsing() -> argparse.ArgumentParser:
    """Argument parsing function.

    Returns:
        argparse.ArgumentParser: argument list
    """
    parser = argparse.ArgumentParser( description="Extract Internal wells into VTK files" )

    parser.add_argument(
        "-xp",
        "--xmlFilepath",
        type=str,
        default="",
        help="path to xml file.",
        required=True,
    )

    parser.add_argument(
        "--deckName",
        type=str,
        default="test",
        help="name of the deck.",
        required=True,
    )

    return parser


def split_by_components( simulation_deck: SimulationDeck, deck_name: str ) -> None:
    # Top-level elements
    top_elements = simulation_deck.xml_root.findall( "./" )

    # create root document
    output_root = ElementTree.Element( "Problem" )

    includes = ElementTree.SubElement( output_root, "Included" )
    for t in top_elements:
        ElementTree.SubElement( includes, "File", attrib={ "name": deck_name + "_" + t.tag + ".xml" } )

    tree = ElementTree.ElementTree( output_root )
    ElementTree.indent( tree )

    # create files for top elements
    for f in top_elements:
        subtree_root = ElementTree.Element( "Problem" )
        subtree_root.append( f )

        subtree = ElementTree.ElementTree( subtree_root )

        ElementTree.indent( subtree )
        filename = deck_name + "_" + f.tag + ".xml"
        with open( filename, "wb" ) as files:
            # format_xml(subtree)
            subtree.write( files, encoding="UTF-8", xml_declaration=True, pretty_print=True )

    filename = deck_name + ".xml"
    with open( filename, "wb" ) as files:
        # tree = format_xml(tree)
        tree.write( files, encoding="UTF-8", xml_declaration=True, pretty_print=True )


def main( args: argparse.Namespace ) -> None:
    """Main function that reads the xml file and writes a PartiotionedDataSetCollection file.

    Args:
        args (argparse.Namespace): list of arguments
    """
    simulation_deck: SimulationDeck = read( args.xmlFilepath )
    split_by_components( simulation_deck, args.deckName )


def run() -> None:
    """Parses the arguments and runs the main function."""
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main( args )


if __name__ == "__main__":
    run()
