# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import re
from typing import NamedTuple, List, Any, TextIO
from ast import literal_eval
from enum import IntEnum
from os.path import expandvars
from pathlib import Path
import io

import numpy as np
import numpy.typing as npt
import vtk  # type: ignore[import-untyped]
from lxml import etree as ElementTree  # type: ignore[import-untyped]
from lxml.etree import XMLSyntaxError  # type: ignore[import-untyped]
from vtk.util.numpy_support import numpy_to_vtk as numpy_to_vtk_

tr = str.maketrans( "{}", "[]" )

CLASS_READERS = {
    # Standard dataset readers:
    ".pvti": vtk.vtkXMLPImageDataReader,
    ".pvtr": vtk.vtkXMLPRectilinearGridReader,
    ".pvtu": vtk.vtkXMLPUnstructuredGridReader,
    ".vti": vtk.vtkXMLImageDataReader,
    ".vtp": vtk.vtkXMLPolyDataReader,
    ".vtr": vtk.vtkXMLRectilinearGridReader,
    ".vts": vtk.vtkXMLStructuredGridReader,
    ".vtu": vtk.vtkXMLUnstructuredGridReader,
}

COMPOSITE_DATA_READERS = {
    ".vtm": vtk.vtkXMLMultiBlockDataReader,
    ".vtmb": vtk.vtkXMLMultiBlockDataReader,
}


class SimulationDeck( NamedTuple ):
    file_path: str
    xml_root: ElementTree.Element


class TreeViewNodeType( IntEnum ):
    UNKNOWN = 1
    REPRESENTATION = 2
    PROPERTIES = 3
    WELLBORETRAJECTORY = 4
    WELLBOREFRAME = 5
    WELLBORECHANNEL = 6
    WELLBOREMARKER = 7
    WELLBORECOMPLETION = 8
    TIMESERIES = 9
    PERFORATION = 10


def numpy_to_vtk( a: npt.DTypeLike ) -> vtk.vtkDataArray:
    return numpy_to_vtk_( a, deep=1 )  # , array_type=get_vtk_array_type(a.dtype))


# def getBlockNameAndLabel(metadata: vtk.vtkInformation, defaultName: str) -> [str, str]:
#     if (
#         metadata is not None
#         and metadata.Has(vtk.vtkCompositeDataSet.NAME())
#         and metadata.Get(vtk.vtkCompositeDataSe.NAME())
#     ):
#         label: str = metadata.Get(vtk.vtkCompositeDataSet.NAME())
#         if not label.empty():
#             name: str = vtk.vtkDataAssembly.MakeValidNodeName(label)
#             return [name, label]

#     return [defaultName, ""]


def read( xmlFilepath: str ) -> SimulationDeck:
    """Reads an xml file (and recursively its included files) into memory

    Args:
        xmlFilepath (str): The path the file to read.

    Returns:
        SimulationDeck: The simulation deck
    """
    expanded_file = Path( expandvars( xmlFilepath ) ).expanduser().resolve()
    file_path = expanded_file.parent

    try:
        parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
        tree = ElementTree.parse( expanded_file, parser=parser )
        root = tree.getroot()
    except XMLSyntaxError as err:
        print( "\nCould not load input file: %s" % ( expanded_file ) )
        print( err.msg )
        raise Exception( "\nCheck input file!" ) from err

    includeCount = 0
    for include_node in root.findall( "Included" ):
        for f in include_node.findall( "File" ):
            _merge_included_xml_files( root, file_path, f.get( "name" ), includeCount )

    # Remove 'Included' nodes
    for include_node in root.findall( "Included" ):
        root.remove( include_node )

    for neighbor in root.iter():
        for key in neighbor.attrib.keys():
            s = re.sub( r"\s{2,}", " ", neighbor.get( key ) )
            neighbor.set( key, s )

    return SimulationDeck( file_path, root )


def build_model( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection, attr: str ) -> int:
    """_summary_

    Args:
        d (SimulationDeck): _description_
        collection (vtk.vtkPartitionedDataSetCollection): _description_
        attr (str): _description_

    Returns:
        _type_: _description_
    """
    assembly = vtk.vtkDataAssembly()
    # FIXME could be deck name
    assembly.SetRootNodeName( Path( d.file_path ).stem )
    collection.SetDataAssembly( assembly )

    # Step 1 - mesh
    # read the mesh as first child of root node
    if _read_mesh( d, collection, attr ) < 0:
        return 0

    # Step 2 - wells
    if _read_wells( d, collection ) < 0:
        return 0

    # Step 3 - boxes
    if _read_boxes( d, collection ) < 0:
        return 0

    return 1


def _read_boxes( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    geometric_objects = d.xml_root.find( "Geometry" )

    if geometric_objects is None:
        return 0

    boxes = geometric_objects.findall( "Box" )

    if not boxes:
        return 0

    count: int = collection.GetNumberOfPartitionedDataSets()

    assembly = collection.GetDataAssembly()
    node = assembly.AddNode( "Boxes" )

    for idx, box in enumerate( boxes ):
        p = vtk.vtkPartitionedDataSet()
        # geometry
        xmin = box.attrib[ "xMin" ]
        xmin_array = np.array( literal_eval( xmin.translate( tr ) ), dtype=np.float64 )
        xmax = box.attrib[ "xMax" ]
        xmax_array = np.array( literal_eval( xmax.translate( tr ) ), dtype=np.float64 )

        bounds = (
            xmin_array[ 0 ],
            xmax_array[ 0 ],
            xmin_array[ 1 ],
            xmax_array[ 1 ],
            xmin_array[ 2 ],
            xmax_array[ 2 ],
        )

        box = vtk.vtkTessellatedBoxSource()
        box.SetBounds( bounds )
        box.Update()
        b = box.GetOutput()

        p.SetPartition( 0, b )

        collection.SetPartitionedDataSet( count, p )
        collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), "Box" + str( idx ) )

        idbox = assembly.AddNode( "Box", node )
        assembly.SetAttribute( idbox, "label", "Box" + str( idx ) )
        assembly.SetAttribute( idbox, "type", TreeViewNodeType.REPRESENTATION )
        assembly.SetAttribute( idbox, "number_of_partitions", collection.GetNumberOfPartitions( count ) )
        assembly.AddDataSetIndex( idbox, count )
        count = count + 1

    return 1


def _read_wells( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    meshes = d.xml_root.find( "Mesh" )

    if meshes is None:
        raise Exception( "\nMesh node not found" )

    wells = meshes.findall( ".//InternalWell" )

    if not wells:
        return 0

    count: int = collection.GetNumberOfPartitionedDataSets()

    assembly = collection.GetDataAssembly()
    node = assembly.AddNode( "Wells" )

    for idx, well in enumerate( wells ):
        # geometry
        s = well.attrib[ "polylineNodeCoords" ]
        points = np.array( literal_eval( s.translate( tr ) ), dtype=np.float64 )
        tip = points[ 0 ]

        # combinatorics
        s = well.attrib[ "polylineSegmentConn" ]
        lines = np.array( literal_eval( s.translate( tr ) ), dtype=np.int64 )
        v_indices = np.unique( lines.flatten() )

        r = literal_eval( well.attrib[ "radius" ].translate( tr ) )
        radius = np.repeat( r, points.shape[ 0 ] )

        vpoints = vtk.vtkPoints()
        vpoints.SetNumberOfPoints( points.shape[ 0 ] )
        vpoints.SetData( numpy_to_vtk( points ) )

        polyLine = vtk.vtkPolyLine()
        polyLine.GetPointIds().SetNumberOfIds( len( v_indices ) )

        for iline, vidx in enumerate( v_indices ):
            polyLine.GetPointIds().SetId( iline, vidx )

        cells = vtk.vtkCellArray()
        cells.InsertNextCell( polyLine )

        vradius = vtk.vtkDoubleArray()
        vradius.SetName( "radius" )
        vradius.SetNumberOfComponents( 1 )
        vradius.SetNumberOfTuples( points.shape[ 0 ] )
        vradius.SetVoidArray( numpy_to_vtk( radius ), points.shape[ 0 ], 1 )

        polyData = vtk.vtkPolyData()
        polyData.SetPoints( vpoints )
        polyData.SetLines( cells )
        polyData.GetPointData().AddArray( vradius )
        polyData.GetPointData().SetActiveScalars( "radius" )

        p = vtk.vtkPartitionedDataSet()
        p.SetPartition( 0, polyData )
        collection.SetPartitionedDataSet( count, p )

        collection.GetMetaData( count ).Set(
            vtk.vtkCompositeDataSet.NAME(),
            well.attrib[ "name" ],
        )

        idwell = assembly.AddNode( "Well", node )
        assembly.SetAttribute( idwell, "label", well.attrib[ "name" ] )

        well_mesh_node = assembly.AddNode( "Mesh", idwell )
        assembly.SetAttribute( well_mesh_node, "type", TreeViewNodeType.REPRESENTATION )
        assembly.SetAttribute(
            well_mesh_node,
            "number_of_partitions",
            collection.GetNumberOfPartitions( count ),
        )
        assembly.AddDataSetIndex( well_mesh_node, count )
        count = count + 1

        perforations = well.findall( "Perforation" )
        perf_node = assembly.AddNode( "Perforations", idwell )
        assembly.SetAttribute( perf_node, "label", "Perforations" )
        for idxp, perfo in enumerate( perforations ):
            pp = vtk.vtkPartitionedDataSet()
            name = perfo.attrib[ "name" ]
            z = literal_eval( perfo.attrib[ "distanceFromHead" ].translate( tr ) )

            ppoints = vtk.vtkPoints()
            ppoints.SetNumberOfPoints( 1 )
            perfo_point = np.array( [ tip[ 0 ], tip[ 1 ], tip[ 2 ] - z ], dtype=np.float64 )
            ppoints.SetPoint( 0, perfo_point )

            polyData = vtk.vtkPolyData()
            polyData.SetPoints( ppoints )

            pp.SetPartition( 0, polyData )
            collection.SetPartitionedDataSet( count, pp )
            collection.GetMetaData( count ).Set(
                vtk.vtkCompositeDataSet.NAME(),
                name,
            )

            idperf = assembly.AddNode( "Perforation", perf_node )
            assembly.SetAttribute( idperf, "label", name )
            assembly.SetAttribute( idperf, "type", TreeViewNodeType.REPRESENTATION )
            assembly.AddDataSetIndex( idperf, count )
            count = count + 1

    return 1


def _read_mesh(
    d: SimulationDeck,
    collection: vtk.vtkPartitionedDataSetCollection,
    attr: str,
) -> int:
    """Reads the mesh from the simulation deck

    Args:
        d (SimulationDeck): _description_
        collection (vtk.vtkPartitionedDataSetCollection): _description_

    Raises:
        Exception: _description_
        Exception: _description_

    Returns:
        vtk.vtkPartitionedDataSet: the mesh as a partition of the data from the deck
    """
    meshes = d.xml_root.find( "Mesh" )

    if meshes is None:
        raise Exception( "\nMesh node not found" )

    mesh = meshes.find( "VTKMesh" )
    if mesh is not None:
        if _read_vtk_data_repository( d.file_path, mesh, collection, attr ) < 1:
            return 0

    mesh = meshes.find( "InternalMesh" )
    if mesh is not None:
        _generate_grid( mesh, collection )

    return 1
    # else:
    #     raise Exception("\nNeither VTKMesh or InternalMesh node were found")


def _read_vtk_data_repository(
    file_path: str,
    mesh: ElementTree.Element,
    collection: vtk.vtkPartitionedDataSetCollection,
    attr: str,
) -> int:
    """Reads the mesh added in the simulation deck and builds adds it as a partition

    Args:
        file_path (str): Path where the mesh is
        mesh (ElementTree.Element): XML node of the mesh
        collection (vtk.vtkPartitionedDataSetCollection): Current collection to update
        attr (str): Cell attribute name to use as region marker

    Returns:
        int: Updated global dataset index
    """
    path = Path( file_path ) / mesh.attrib[ "file" ]

    count: int = collection.GetNumberOfPartitionedDataSets()
    assembly = collection.GetDataAssembly()

    id_mesh = assembly.AddNode( "Mesh" )
    assembly.SetAttribute( id_mesh, "label", mesh.attrib[ "name" ] )
    assembly.SetAttribute( id_mesh, "type", TreeViewNodeType.REPRESENTATION )

    id_surf = assembly.AddNode( "Surfaces" )

    if path.suffix in CLASS_READERS:
        try:
            Reader = CLASS_READERS[ path.suffix ]
        except KeyError as err:
            # raise ValueError(
            #     f"`read` does not support a file with the {path.suffix} extension"
            # ) from err

            return 0

        reader = Reader()
        reader.SetFileName( path )
        reader.Update()

        ugrid: vtk.vtkUnstructuredGrid = reader.GetOutputDataObject( 0 )  # use pv.wrap()

        attr_array = ugrid.GetCellData().GetArray( attr )
        [ attr_min, attr_max ] = attr_array.GetRange()

        # load surfaces
        for i in range( int( attr_min ), int( attr_max + 1 ) ):
            threshold = vtk.vtkThreshold()
            threshold.SetInputData( ugrid )
            threshold.SetUpperThreshold( i )
            threshold.SetLowerThreshold( i )
            threshold.SetInputArrayToProcess( 0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, attr )

            extract = vtk.vtkExtractCellsByType()
            extract.SetInputConnection( threshold.GetOutputPort() )
            extract.AddCellType( vtk.VTK_QUAD )
            extract.AddCellType( vtk.VTK_TRIANGLE )
            extract.AddCellType( vtk.VTK_POLYGON )
            extract.Update()

            if extract.GetOutputDataObject( 0 ).GetNumberOfCells() != 0:
                p = vtk.vtkPartitionedDataSet()
                p.SetNumberOfPartitions( 1 )
                p.SetPartition( 0, extract.GetOutputDataObject( 0 ) )
                collection.SetPartitionedDataSet( count, p )

                collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), "Surface" + str( i - 1 ) )

                node = assembly.AddNode( "Surface", id_surf )  # + str(i - 1)
                assembly.SetAttribute( node, "label", "Surface" + str( i - 1 ) )
                # assembly.SetAttribute(id_surf_i, "type", TreeViewNodeType.REPRESENTATION)
                # assembly.SetAttribute(id_surf_i, "number_of_partitions", collection.GetNumberOfPartitions(count));
                assembly.AddDataSetIndex( node, count )
                count = count + 1

        # load regions
        for i in range( int( attr_min ), int( attr_max + 1 ) ):
            threshold = vtk.vtkThreshold()
            threshold.SetInputData( ugrid )
            threshold.SetUpperThreshold( i )
            threshold.SetLowerThreshold( i )
            threshold.SetInputArrayToProcess( 0, 0, 0, vtk.vtkDataObject.FIELD_ASSOCIATION_CELLS, attr )

            extract = vtk.vtkExtractCellsByType()
            extract.SetInputConnection( threshold.GetOutputPort() )
            extract.AddCellType( vtk.VTK_HEXAHEDRON )
            extract.AddCellType( vtk.VTK_TETRA )
            extract.AddCellType( vtk.VTK_WEDGE )
            extract.AddCellType( vtk.VTK_PYRAMID )
            extract.AddCellType( vtk.VTK_VOXEL )
            extract.AddCellType( vtk.VTK_PENTAGONAL_PRISM )
            extract.AddCellType( vtk.VTK_HEXAGONAL_PRISM )
            extract.AddCellType( vtk.VTK_POLYHEDRON )
            extract.Update()

            if extract.GetOutputDataObject( 0 ).GetNumberOfCells() != 0:
                p = vtk.vtkPartitionedDataSet()
                p.SetNumberOfPartitions( 1 )
                p.SetPartition( 0, extract.GetOutputDataObject( 0 ) )
                collection.SetPartitionedDataSet( count, p )

                collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), "Region" + str( i - 1 ) )

                node = assembly.AddNode( "Region", id_mesh )  # + str(i - 1)
                assembly.SetAttribute( node, "label", "Region" + str( i - 1 ) )
                # assembly.SetAttribute(node, "type", TreeViewNodeType.REPRESENTATION)
                # assembly.SetAttribute(node, "number_of_partitions", collection.GetNumberOfPartitions(count));
                assembly.AddDataSetIndex( node, count )
                count = count + 1

    elif path.suffix in COMPOSITE_DATA_READERS:
        try:
            Reader = COMPOSITE_DATA_READERS[ path.suffix ]
        except KeyError as err:
            # raise ValueError(
            #     f"`read` does not support a file with the {path.suffix} extension"
            # ) from err
            return 0

        reader = Reader()
        reader.SetFileName( path )
        reader.Update()

        mb = reader.GetOutput()

        mainBlockName = "main"
        faceBlocks = []
        if "mainBlockName" in mesh.attrib:
            mainBlockName = mesh.attrib[ "mainBlockName" ]

        # if "faceBlocks" in mesh.attrib:
        #     names = mesh.attrib["faceBlocks"]
        #     names = names.replace("{", "[").replace("}", "]")
        #     e = names.strip("][").split(",")
        #     e = [element.strip() for element in e]
        #     faceBlocks = e

        for i in range( mb.GetNumberOfBlocks() ):
            if mb.HasMetaData( i ):
                unstructuredGrid = vtk.vtkUnstructuredGrid.SafeDownCast( mb.GetBlock( i ) )
                if unstructuredGrid and unstructuredGrid.GetNumberOfPoints():
                    blockName = mb.GetMetaData( i ).Get( vtk.vtkCompositeDataSet.NAME() )

                    p = vtk.vtkPartitionedDataSet()
                    p.SetNumberOfPartitions( 1 )
                    p.SetPartition( 0, unstructuredGrid )
                    collection.SetPartitionedDataSet( count, p )

                    collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), blockName )

                    node = None
                    if blockName == mainBlockName:
                        node = assembly.AddNode( "Region", id_mesh )  #
                    else:
                        node = assembly.AddNode( "Surface", id_surf )  # + str(i - 1)

                    assembly.SetAttribute( node, "label", blockName )
                    # assembly.SetAttribute(id_surf_i, "type", TreeViewNodeType.REPRESENTATION)
                    # assembly.SetAttribute(id_surf_i, "number_of_partitions", collection.GetNumberOfPartitions(count));
                    assembly.AddDataSetIndex( node, count )
                    count = count + 1

    return 1


def _read_vtkmesh(
    file_path: str,
    mesh: ElementTree.Element,
    collection: vtk.vtkPartitionedDataSetCollection,
    attr: str,
) -> int:
    """Reads the mesh added in the simulation deck and builds adds it as a partition

    Args:
        file_path (str): Path where the mesh is
        mesh (ElementTree.Element): XML node of the mesh
        collection (vtk.vtkPartitionedDataSetCollection): current DataAssembly

    Returns:
        vtk.vtkPartitionedDataSet: The vtk mesh as a partition
    """
    assembly = collection.GetDataAssembly()

    path = Path( file_path )
    reader = pv.get_reader( path / mesh.attrib[ "file" ] )

    idNode = assembly.AddNode( "Mesh" )

    assembly.SetAttribute( idNode, "label", mesh.attrib[ "name" ] )
    assembly.SetAttribute( idNode, "type", TreeViewNodeType.REPRESENTATION )

    # add vtu file as a partition of a partionedDataSet
    p = vtk.vtkPartitionedDataSet()
    p.SetPartition( 0, reader.read() )
    assembly.AddDataSetIndex( idNode, 0 )

    # add partitionedDataSet to collection
    collection.SetPartitionedDataSet( 0, p )

    return 1


def _generate_grid( mesh: ElementTree.Element, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    """Generates the grid depending on the parameters read from the deck

    Args:
        mesh (ElementTree.Element): XML node of the mesh
        assembly (vtk.vtkDataAssembly): current DataAssembly

    Returns:
        vtk.vtkPartitionedDataSet: The collection updated with the grid
    """
    count: int = collection.GetNumberOfPartitionedDataSets()

    elem_type = mesh.attrib[ "elementTypes" ].strip( "}{ " )

    if elem_type == "C3D8":
        xcoords = mesh.attrib[ "xCoords" ]
        ycoords = mesh.attrib[ "yCoords" ]
        zcoords = mesh.attrib[ "zCoords" ]
        xcoords_array = np.array( literal_eval( xcoords.translate( tr ) ), dtype=np.float64 )
        ycoords_array = np.array( literal_eval( ycoords.translate( tr ) ), dtype=np.float64 )
        zcoords_array = np.array( literal_eval( zcoords.translate( tr ) ), dtype=np.float64 )
        nx = literal_eval( mesh.attrib[ "nx" ].translate( tr ) )
        ny = literal_eval( mesh.attrib[ "ny" ].translate( tr ) )
        nz = literal_eval( mesh.attrib[ "nz" ].translate( tr ) )

        grid = vtk.vtkImageData()

        grid.dimensions = np.array( ( nx[ 0 ] + 1, ny[ 0 ] + 1, nz[ 0 ] + 1 ), dtype=np.int64 )

        xspacing = ( xcoords_array[ 1 ] - xcoords_array[ 0 ] ) / grid.dimensions[ 0 ]
        yspacing = ( ycoords_array[ 1 ] - ycoords_array[ 0 ] ) / grid.dimensions[ 1 ]
        zspacing = ( zcoords_array[ 1 ] - zcoords_array[ 0 ] ) / grid.dimensions[ 2 ]

        # # Edit the spatial reference
        grid.origin = (
            xcoords_array[ 0 ],
            ycoords_array[ 0 ],
            zcoords_array[ 0 ],
        )  # The bottom left corner of the data set
        grid.spacing = (
            xspacing,
            yspacing,
            zspacing,
        )  # These are the cell sizes along each axis

        # idNode = assembly.AddNode("Mesh")

        # assembly.SetAttribute(idNode, "label", mesh.attrib["name"])
        # assembly.SetAttribute(idNode, "type", TreeViewNodeType.REPRESENTATION)

        # add vtu file as a partition of a partionedDataSet
        p = vtk.vtkPartitionedDataSet()
        p.SetPartition( 0, grid )
        collection.SetPartitionedDataSet( count, p )
        count = count + 1
        # assembly.AddDataSetIndex(idNode, 0)

        return 1

    else:
        raise Exception( "\nElem type {elem_type} of InternalMesh not handle yet" )


def _merge_xml_nodes( existingNode: ElementTree.Element, targetNode: ElementTree.Element, level: int ) -> None:
    """Merge nodes in an included file into the current structure level by level.

    Args:
        existingNode (lxml.etree.Element): The current node in the base xml structure.
        targetNode (lxml.etree.Element): The node to insert.
        level (int): The xml file depth.
    """
    # Copy attributes on the current level
    for tk in targetNode.attrib.keys():
        existingNode.set( tk, targetNode.get( tk ) )

    # Copy target children into the xml structure
    currentTag = ""
    matchingSubNodes = []

    for target in targetNode.getchildren():
        insertCurrentLevel = True

        # Check to see if a node with the appropriate type
        # exists at this level
        if currentTag != target.tag:
            currentTag = target.tag
            matchingSubNodes = existingNode.findall( target.tag )

        if matchingSubNodes:
            targetName = target.get( "name" )

            # Special case for the root Problem node (which may be unnamed)
            if level == 0:
                insertCurrentLevel = False
                _merge_xml_nodes( matchingSubNodes[ 0 ], target, level + 1 )

            # Handle named xml nodes
            elif targetName and ( currentTag not in [ "Nodeset" ] ):
                for match in matchingSubNodes:
                    if match.get( "name" ) == targetName:
                        insertCurrentLevel = False
                        _merge_xml_nodes( match, target, level + 1 )

        # Insert any unnamed nodes or named nodes that aren't present
        # in the current xml structure
        if insertCurrentLevel:
            existingNode.insert( -1, target )


def _merge_included_xml_files(
    root: ElementTree.Element,
    file_path: str,
    fname: str,
    includeCount: int,
    maxInclude: int = 100,
) -> None:
    """Recursively merge included files into the current structure.

    Args:
        root (lxml.etree.Element): The root node of the base xml structure.
        fname (str): The name of the target xml file to merge.
        includeCount (int): The current recursion depth.
        maxInclude (int): The maximum number of xml files to include (default = 100)
    """
    included_file_path = Path( expandvars( file_path ), fname )
    expanded_file = included_file_path.expanduser().resolve()

    # Check to see if the code has fallen into a loop
    includeCount += 1
    if includeCount > maxInclude:
        raise Exception( "Reached maximum recursive includes...  Is there an include loop?" )

    # Check to make sure the file exists
    if not included_file_path.is_file():
        print( "Included file does not exist: %s" % ( included_file_path ) )
        raise Exception( "Check included file path!" )

    # Load target xml
    try:
        parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
        includeTree = ElementTree.parse( included_file_path, parser )
        includeRoot = includeTree.getroot()
    except XMLSyntaxError as err:
        print( "\nCould not load included file: %s" % ( included_file_path ) )
        print( err.msg )
        raise Exception( "\nCheck included file!" ) from err

    # Recursively add the includes:
    for include_node in includeRoot.findall( "Included" ):
        for f in include_node.findall( "File" ):
            _merge_included_xml_files( root, expanded_file.parent, f.get( "name" ), includeCount )

    # Merge the results into the xml tree
    _merge_xml_nodes( root, includeRoot, 0 )


def format_attribute( attribute_indent: str, ka: str, attribute_value: str ) -> str:
    """Format xml attribute strings

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
    """Iteratively format the xml file

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
            attribute_dict = {}
            if ( level == 0 ) & include_namespace:
                # Handle the optional namespace information at the root level
                # Note: preferably, this would point to a schema we host online
                attribute_dict[ "xmlns:xsi" ] = "http://www.w3.org/2001/XMLSchema-instance"
                attribute_dict[ "xsi:noNamespaceSchemaLocation" ] = "/usr/gapps/GEOS/schema/schema.xsd"
            elif level > 0:
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
                    output.write( ' %s="%s"' % ( k, attribute_dict[ k ] ) )
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
    tree: ElementTree.ElementTree,
    indent_size: int = 2,
    indent_style: bool = False,
    block_separation_max_depth: int = 2,
    alphebitize_attributes: bool = False,
    close_style: bool = False,
    namespace: bool = False,
) -> io.StringIO:
    # tree = ElementTree.parse(fname)
    root = tree.getroot()
    prologue_comments = [ tmp.text for tmp in root.itersiblings( preceding=True ) ]
    epilog_comments = [ tmp.text for tmp in root.itersiblings() ]

    # with open(fname, "w") as f:
    f = io.StringIO()
    f.write( '<?xml version="1.0" ?>\n' )

    for comment in reversed( prologue_comments ):
        f.write( "\n<!--%s-->" % ( comment ) )

    format_xml_level(
        f,
        root,
        0,
        indent=" " * indent_size,
        block_separation_max_depth=block_separation_max_depth,
        modify_attribute_indent=indent_style,
        sort_attributes=alphebitize_attributes,
        close_tag_newline=close_style,
        include_namespace=namespace,
    )

    for comment in epilog_comments:
        f.write( "\n<!--%s-->" % ( comment ) )
    f.write( "\n" )

    return f


def format_deck(
    input_fname: str,
    indent_size: int = 2,
    indent_style: bool = False,
    block_separation_max_depth: int = 2,
    alphebitize_attributes: bool = False,
    close_style: bool = False,
    namespace: bool = False,
) -> None:
    """Script to format xml files

    Args:
        input_fname (str): Input file name
        indent_size (int): Indent size
        indent_style (bool): Style of indentation (0=fixed, 1=hanging)
        block_separation_max_depth (int): Max depth to separate xml blocks
        alphebitize_attributes (bool): Alphebitize attributes
        close_style (bool): Style of close tag (0=same line, 1=new line)
        namespace (bool): Insert this namespace in the xml description
    """
    fname = os.path.expanduser( input_fname )
    try:
        tree = ElementTree.parse( fname )
        root = tree.getroot()
        prologue_comments = [ tmp.text for tmp in root.itersiblings( preceding=True ) ]
        epilog_comments = [ tmp.text for tmp in root.itersiblings() ]

        with open( fname, "w" ) as f:
            f.write( '<?xml version="1.0" ?>\n' )

            for comment in reversed( prologue_comments ):
                f.write( "\n<!--%s-->" % ( comment ) )

            format_xml_level(
                f,
                root,
                0,
                indent=" " * indent_size,
                block_separation_max_depth=block_separation_max_depth,
                modify_attribute_indent=indent_style,
                sort_attributes=alphebitize_attributes,
                close_tag_newline=close_style,
                include_namespace=namespace,
            )

            for comment in epilog_comments:
                f.write( "\n<!--%s-->" % ( comment ) )
            f.write( "\n" )

    except ElementTree.ParseError as err:
        print( "\nCould not load file: %s" % ( fname ) )
        print( err.msg )
        raise Exception( "\nCheck input file!" )
