# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import argparse
from pathlib import PurePath

from geos_xml_viewer.filters.geosDeckReader import GeosDeckReader
from vtkmodules.vtkIOParallelXML import (
    vtkXMLPartitionedDataSetCollectionWriter,
)


def valid_file(param: str) -> str:
    """File validation function for argparse for .vtpc files.

    Args:
        param (str): filepath to a .vtpc

    Raises:
        argparse.ArgumentTypeError: Raises an error if the file does not have a .vtpc extension

    Returns:
        str: filepath to a.vtpc
    """
    ext: str = PurePath(param).suffix
    if ext.lower() != ".vtpc":
        raise argparse.ArgumentTypeError("File must have a .vtpc extension")
    return param


def parsing() -> argparse.ArgumentParser:
    """Argument parsing function.

    Returns:
        argparse.ArgumentParser: argument list
    """
    parser = argparse.ArgumentParser(
        description="Extract Internal wells into VTK files"
    )

    parser.add_argument(
        "-xp",
        "--xmlFilepath",
        type=str,
        default="",
        help="path to xml file.",
        required=True,
    )
    parser.add_argument(
        "-a",
        "--attributeName",
        type=str,
        default="attribute",
        help="Attribute name.",
        required=False,
    )
    parser.add_argument(
        "-o",
        "--outputName",
        type=valid_file,
        default="myPartionedDataSetCollection.vtpc",
        help="name of the output file.",
    )

    return parser


def main(args: argparse.Namespace) -> None:
    """Main function that reads the xml file and writes a PartiotionedDataSetCollection file.

    Args:
        args (argparse.Namespace): list of arguments
    """
    reader = GeosDeckReader()
    reader.SetFileName(args.xmlFilepath)
    reader.SetAttributeName(args.attributeName)
    writer = vtkXMLPartitionedDataSetCollectionWriter()
    writer.SetInputConnection(reader.GetOutputPort())
    writer.SetFileName(args.outputName)
    writer.Write()


def run() -> None:
    """Parses the arguments and runs the main function."""
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main(args)


if __name__ == "__main__":
    run()
