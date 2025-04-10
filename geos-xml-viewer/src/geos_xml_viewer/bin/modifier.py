# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import argparse
from pathlib import PurePath

from geos_xml_viewer.filters.geosDeckReader import GeosDeckReader

from vtkmodules.vtkIOXML import vtkXMLPartitionedDataSetCollectionReader
from vtkmodules.vtkCommonDataModel import vtkDataAssembly


def valid_file( param: str ) -> str:
    ext: str = PurePath( param ).suffix
    if ext.lower() != ".vtpc":
        raise argparse.ArgumentTypeError( "File must have a .vtpc extension" )
    return param


def parsing() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser( description="Rewrite wells into VTK file" )

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
        "-vtpc",
        type=str,
        default="",
        help="path to vtpc file.",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--outputName",
        type=valid_file,
        default="myModifiedPartionedDataSetCollection.vtpc",
        help="name of the output file.",
    )

    return parser


def main( args: argparse.Namespace ) -> None:
    reader = GeosDeckReader()
    reader.SetFileName( args.xmlFilepath )
    reader.SetAttributeName( args.attributeName )
    reader.Update()
    pdsc_xml = reader.GetOutputDataObject( 0 )

    vtpc = vtkXMLPartitionedDataSetCollectionReader()
    vtpc.SetFileName( args.vtpc )
    vtpc.Update()
    pdsc_file = vtpc.GetOutput()

    # look for xml root node name and wells node id
    assembly_xml: vtkDataAssembly = pdsc_xml.GetDataAssembly()
    root_name_xml: str = assembly_xml.GetNodeName( assembly_xml.GetRootNode() )
    wells_xml = assembly_xml.GetFirstNodeByPath( "//" + root_name_xml + "/Wells" )

    # look for vtpc root node name and wells node id
    assembly_file: vtkDataAssembly = pdsc_file.GetDataAssembly()
    wells_file = assembly_file.GetFirstNodeByPath( "//" + root_name_xml + "/Wells" )

    print( "assembly from vtpc file: ", wells_file )
    print( "wells id from vtpc file: ", wells_file )
    print( "remove dataset indices...." )
    # remove all well's subnode from file
    assembly_file.RemoveAllDataSetIndices( wells_file )
    print( "... finished" )
    print( "remove nodes..." )
    assembly_file.RemoveNode( wells_file )
    print( "... finished" )
    print( assembly_file )
    print( wells_xml )
    assembly_file.AddSubtree( assembly_file.GetRootNode(), assembly_xml, wells_xml )

    print( assembly_file )

    writer = vtkXMLPartitionedDataSetCollectionWriter()
    writer.SetInputData( pdsc_file )
    writer.SetFileName( args.outputName )
    writer.Write()


def run() -> None:
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main( args )


if __name__ == "__main__":
    run()
