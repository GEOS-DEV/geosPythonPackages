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
from ast import literal_eval
from enum import IntEnum
from lxml import etree as ElementTree  # type: ignore[import-untyped]
from lxml.etree import XMLSyntaxError  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
from os.path import expandvars
from pathlib import Path
from typing import NamedTuple
import vtk  # type: ignore[import-untyped]
from vtkmodules.util.numpy_support import numpy_to_vtk as numpy_to_vtk_
from geos.xml_tools import xml_processor

__doc__ = """
VTK Deck Builder for GEOS XML.

This module converts a processed GEOS XML element tree into a VTK data structure for visualization or analysis.
Features:
* Reads and processes XML decks using geos_xml_tools.xml_processor.
* Extracts geometric information (meshes, wells, boxes) and builds a vtkPartitionedDataSetCollection.
* Provides utilities for working with VTK and GEOS simulation data.

Typical usage:
    from geos.xml_tools.vtk_builder import create_vtk_deck
    vtk_collection = create_vtk_deck("input.xml")

Intended for use in visualization pipelines and as a backend for 3D viewers.
"""

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
    """A container for the path and parsed XML root of a simulation deck."""
    file_path: str
    xml_root: ElementTree.Element


class TreeViewNodeType( IntEnum ):
    """Enumeration for different types of nodes in the VTK data assembly."""
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
    """A wrapper for the vtk numpy_to_vtk utility to ensure deep copying."""
    return numpy_to_vtk_( a, deep=1 )


def read( xmlFilepath: str ) -> SimulationDeck:
    """Reads a GEOS xml file and processes it using the geos_xml_tools processor.

    This handles recursive includes, parameter substitution, unit conversion,
    and symbolic math.

    Args:
        xmlFilepath (str): The path to the top-level file to read.

    Returns:
        SimulationDeck: A named tuple containing the original file's directory
                        and the fully processed XML root element.
    """
    # 1. Resolve the original file path to get its parent directory. This is
    #    kept to ensure that relative paths to other files (like meshes)
    #    can be resolved correctly later.
    try:
        expanded_file = Path( expandvars( xmlFilepath ) ).expanduser().resolve( strict=True )
        original_file_directory = str( expanded_file.parent )
    except FileNotFoundError:
        print( f"\nCould not find input file: {xmlFilepath}" )
        raise

    # 2. Use the base processor to get a clean, fully resolved XML file.
    #    This single call replaces the manual include/merge logic and adds
    #    parameter/unit/math processing. The function returns the path to a
    #    new, temporary file.
    processed_xml_path = xml_processor.process( inputFiles=[ str( expanded_file ) ] )

    # 3. Parse the new, clean XML file produced by the processor to get the
    #    final XML tree.
    try:
        parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
        tree = ElementTree.parse( processed_xml_path, parser=parser )
        processed_root = tree.getroot()
    except XMLSyntaxError as err:
        print( f"\nCould not parse the processed file at: {processed_xml_path}" )
        print( "This may indicate an error in the structure of the source XML files." )
        print( f"Original error: {err.msg}" )
        raise Exception( "\nAn error occurred after processing the XML deck." ) from err

    # 4. Return the SimulationDeck, combining the original path with the
    #    fully processed XML root element.
    return SimulationDeck( file_path=original_file_directory, xml_root=processed_root )


def create_vtk_deck( xml_filepath: str, cell_attribute: str = "Region" ) -> vtk.vtkPartitionedDataSetCollection:
    """Processes a GEOS XML deck and converts it into a VTK partitioned dataset collection.

    This function serves as the primary entry point. It uses the standard `xml_processor`
    to handle file inclusions and other preprocessing, then builds the VTK model.

    Args:
        xml_filepath (str): Path to the top-level XML input deck.
        cell_attribute (str): The cell attribute name to use as a region marker for meshes.

    Returns:
        vtk.vtkPartitionedDataSetCollection: The fully constructed VTK data object.
    """
    print( "Step 1: Processing XML deck with geos_xml_tools processor..." )
    # Use the base processor to handle includes, parameters, units, etc.
    # This returns the path to a temporary, fully resolved XML file.
    processed_xml_path = xml_processor.process( inputFiles=[ xml_filepath ] )
    print( f"Processed deck saved to: {processed_xml_path}" )

    # Parse the final, clean XML file produced by the processor
    try:
        parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
        xml_tree = ElementTree.parse( processed_xml_path, parser=parser )
        root = xml_tree.getroot()
    except XMLSyntaxError as err:
        print( f"\nCould not load processed input file: {processed_xml_path}" )
        print( err.msg )
        raise Exception( "\nCheck processed XML file for errors!" ) from err

    # The `file_path` is the directory of the original XML file. This is crucial for
    # correctly resolving relative paths t
    # o mesh files (*.vtu, etc.) inside the XML.
    original_deck_dir = str( Path( xml_filepath ).parent.resolve() )
    deck = SimulationDeck( file_path=original_deck_dir, xml_root=root )

    # Build the VTK model from the fully processed XML tree
    print( "Step 2: Building VTK data model from processed XML..." )
    collection = vtk.vtkPartitionedDataSetCollection()
    build_model( deck, collection, cell_attribute )
    print( "VTK model built successfully." )

    return collection


# --- Core VTK Building Logic (Kept from original, now operates on a clean XML tree) ---


def build_model( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection, attr: str ) -> int:
    """Populates a VTK data collection from a processed SimulationDeck."""
    print( "Building VTKDataAssembly...", flush=True )
    assembly = vtk.vtkDataAssembly()
    # Use the original file's name for the root node, not the temporary processed file
    root_name = Path( d.xml_root.get( "name", "Deck" ) ).stem
    assembly.SetRootNodeName( root_name )
    collection.SetDataAssembly( assembly )

    # Step 1 - mesh
    print( "Performing _read_mesh...", flush=True )
    if _read_mesh( d, collection, attr ) < 0:
        return 0
    # Step 2 - wells
    print( "Performing _read_wells...", flush=True )
    if _read_wells( d, collection ) < 0:
        return 0
    # Step 3 - boxes
    print( "Performing _read_boxes...", flush=True )
    if _read_boxes( d, collection ) < 0:
        return 0

    return 1


def _read_boxes( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    # (This function is identical to the original implementation)
    geometric_objects = d.xml_root.find( "Geometry" )
    if geometric_objects is None:
        return 0
    boxes = geometric_objects.findall( "Box" )
    if not boxes:
        return 0

    count: int = collection.GetNumberOfPartitionedDataSets()
    assembly = collection.GetDataAssembly()
    node = assembly.AddNode( "Boxes" )

    for idx, box_node in enumerate( boxes ):
        p = vtk.vtkPartitionedDataSet()
        xmin = np.array( literal_eval( box_node.attrib[ "xMin" ].translate( tr ) ), dtype=np.float64 )
        xmax = np.array( literal_eval( box_node.attrib[ "xMax" ].translate( tr ) ), dtype=np.float64 )
        bounds = ( xmin[ 0 ], xmax[ 0 ], xmin[ 1 ], xmax[ 1 ], xmin[ 2 ], xmax[ 2 ] )

        box_source = vtk.vtkTessellatedBoxSource()
        box_source.SetBounds( bounds )
        box_source.Update()
        b = box_source.GetOutput()
        p.SetPartition( 0, b )

        collection.SetPartitionedDataSet( count, p )
        box_name = box_node.get( "name", f"Box{idx}" )
        collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), box_name )

        idbox = assembly.AddNode( "Box", node )
        assembly.SetAttribute( idbox, "label", box_name )
        assembly.SetAttribute( idbox, "type", TreeViewNodeType.REPRESENTATION )
        assembly.AddDataSetIndex( idbox, count )
        count += 1
    return 1


def _read_wells( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    # (This function is identical to the original implementation)
    meshes = d.xml_root.find( "Mesh" )
    if meshes is None:
        raise Exception( "\nMesh node not found in XML deck" )
    wells = meshes.findall( ".//InternalWell" )
    if not wells:
        return 0

    print( "Found number of wells:", len( wells ), flush=True )
    count: int = collection.GetNumberOfPartitionedDataSets()
    print( f"Number of partitioned data sets: {count}", flush=True )
    assembly = collection.GetDataAssembly()
    print( "Got data assembly from collection.", flush=True )
    node = assembly.AddNode( "Wells" )

    for well in wells:
        points = np.array( literal_eval( well.attrib[ "polylineNodeCoords" ].translate( tr ) ), dtype=np.float64 )
        lines = np.array( literal_eval( well.attrib[ "polylineSegmentConn" ].translate( tr ) ), dtype=np.int64 )
        v_indices = np.unique( lines.flatten() )
        r = literal_eval( well.attrib[ "radius" ].translate( tr ) )
        radius = np.repeat( r, points.shape[ 0 ] )

        vpoints = vtk.vtkPoints()
        vpoints.SetData( numpy_to_vtk( points ) )

        polyLine = vtk.vtkPolyLine()
        polyLine.GetPointIds().SetNumberOfIds( len( v_indices ) )
        for i, vidx in enumerate( v_indices ):
            polyLine.GetPointIds().SetId( i, vidx )
        cells = vtk.vtkCellArray()
        cells.InsertNextCell( polyLine )

        vradius = vtk.vtkDoubleArray()
        vradius.SetName( "radius" )
        vradius.SetNumberOfComponents( 1 )
        vradius.SetArray( numpy_to_vtk( radius ), len( radius ), 1 )

        polyData = vtk.vtkPolyData()
        polyData.SetPoints( vpoints )
        polyData.SetLines( cells )
        polyData.GetPointData().AddArray( vradius )
        polyData.GetPointData().SetActiveScalars( "radius" )

        p = vtk.vtkPartitionedDataSet()
        p.SetPartition( 0, polyData )
        collection.SetPartitionedDataSet( count, p )
        well_name = well.attrib[ "name" ]
        collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), well_name )

        idwell = assembly.AddNode( "Well", node )
        assembly.SetAttribute( idwell, "label", well_name )
        well_mesh_node = assembly.AddNode( "Mesh", idwell )
        assembly.SetAttribute( well_mesh_node, "type", TreeViewNodeType.REPRESENTATION )
        assembly.AddDataSetIndex( well_mesh_node, count )
        count += 1

        # Handle perforations
        perforations = well.findall( "Perforation" )
        if perforations:
            perf_node = assembly.AddNode( "Perforations", idwell )
            assembly.SetAttribute( perf_node, "label", "Perforations" )
            tip = points[ 0 ]
            for perfo in perforations:
                pp = vtk.vtkPartitionedDataSet()
                name = perfo.attrib[ "name" ]
                z = literal_eval( perfo.attrib[ "distanceFromHead" ].translate( tr ) )
                # Handle case where z might be a list (e.g., from "{5.0}" -> [5.0])
                if isinstance( z, list ):
                    z = z[ 0 ]
                perfo_point = np.array( [ float(
                    tip[ 0 ] ), float( tip[ 1 ] ), float( tip[ 2 ] ) - z ],
                                        dtype=np.float64 )

                ppoints = vtk.vtkPoints()
                ppoints.SetNumberOfPoints( 1 )
                ppoints.SetPoint( 0, perfo_point.tolist() )

                pperfo_poly = vtk.vtkPolyData()
                pperfo_poly.SetPoints( ppoints )
                pp.SetPartition( 0, pperfo_poly )

                collection.SetPartitionedDataSet( count, pp )
                collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), name )
                idperf = assembly.AddNode( "Perforation", perf_node )
                assembly.SetAttribute( idperf, "label", name )
                assembly.SetAttribute( idperf, "type", TreeViewNodeType.REPRESENTATION )
                assembly.AddDataSetIndex( idperf, count )
                count += 1
    return 1


def _read_mesh( d: SimulationDeck, collection: vtk.vtkPartitionedDataSetCollection, attr: str ) -> int:
    """Reads the mesh from the simulation deck and completes the collection with mesh information.

    Args:
        d (SimulationDeck): A container for the path and parsed XML root of a simulation deck.
        collection (vtk.vtkPartitionedDataSetCollection): Current collection to update
        attr (str): Cell attribute name to use as region marker

    Returns:
        vtk.vtkPartitionedDataSet: the mesh as a partition of the data from the deck
    """
    meshes = d.xml_root.find( "Mesh" )
    if meshes is None:
        raise Exception( "\nMesh node not found in XML deck" )

    # Check for VTKMesh (external file)
    vtk_mesh_node = meshes.find( "VTKMesh" )
    if vtk_mesh_node is not None and _read_vtk_data_repository( d.file_path, vtk_mesh_node, collection, attr ) < 1:
        return 0

    # Check for InternalMesh (generated grid)
    internal_mesh_node = meshes.find( "InternalMesh" )
    if internal_mesh_node is not None:
        print( "Performing _generate_grid...", flush=True )
        _generate_grid( internal_mesh_node, collection )

    return 1


def _read_vtk_data_repository( file_path: str, mesh: ElementTree.Element,
                               collection: vtk.vtkPartitionedDataSetCollection, attr: str ) -> int:
    """Reads the mesh added in the simulation deck and builds adds it as a partition.

    Args:
        file_path (str): Path where the mesh is
        mesh (ElementTree.Element): XML node of the mesh
        collection (vtk.vtkPartitionedDataSetCollection): Current collection to update
        attr (str): Cell attribute name to use as region marker

    Returns:
        int: Updated global dataset index
    """
    # The file_path argument is the fully-resolved path to the original deck's directory.
    path = Path( file_path ) / mesh.attrib[ "file" ]
    if not path.is_file():
        raise FileNotFoundError( f"Mesh file not found at resolved path: {path}" )

    try:
        # Consolidated lookup for the correct VTK reader
        Reader = ( CLASS_READERS | COMPOSITE_DATA_READERS )[ path.suffix ]
    except KeyError:
        # Active error message for unsupported file types
        print( f"Error: Unsupported VTK file extension: {path.suffix}" )
        return 0

    reader = Reader()
    reader.SetFileName( str( path ) )
    reader.Update()

    count: int = collection.GetNumberOfPartitionedDataSets()
    assembly = collection.GetDataAssembly()

    id_mesh = assembly.AddNode( "Mesh" )
    assembly.SetAttribute( id_mesh, "label", mesh.attrib[ "name" ] )
    assembly.SetAttribute( id_mesh, "type", TreeViewNodeType.REPRESENTATION )

    id_surf = assembly.AddNode( "Surfaces" )

    # This logic handles standard VTK files like .vtu, .vti, etc.
    if path.suffix in CLASS_READERS:
        ugrid: vtk.vtkUnstructuredGrid = reader.GetOutputDataObject( 0 )
        attr_array = ugrid.GetCellData().GetArray( attr )
        if not attr_array:
            print( f"Attribute '{attr}' not found. Treating the entire mesh as a single region named 'domain'." )
            # Add the entire unstructured grid as a single region
            p = vtk.vtkPartitionedDataSet()
            p.SetNumberOfPartitions( 1 )
            p.SetPartition( 0, ugrid )
            collection.SetPartitionedDataSet( count, p )
            collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), "domain" )
            # Add a corresponding "Region" node to the assembly
            node = assembly.AddNode( "Region", id_mesh )
            assembly.SetAttribute( node, "label", "domain" )
            assembly.AddDataSetIndex( node, count )
            count += 1
            return 1

        [ attr_min, attr_max ] = attr_array.GetRange()

        # Load surfaces
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
                collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), f"Surface{i - 1}" )

                node = assembly.AddNode( "Surface", id_surf )
                assembly.SetAttribute( node, "label", f"Surface{i - 1}" )
                assembly.AddDataSetIndex( node, count )
                count += 1

        # Load regions
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
                collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), f"Region{i - 1}" )

                node = assembly.AddNode( "Region", id_mesh )
                assembly.SetAttribute( node, "label", f"Region{i - 1}" )
                assembly.AddDataSetIndex( node, count )
                count += 1

    # This logic handles composite VTK files like .vtm
    elif path.suffix in COMPOSITE_DATA_READERS:
        mb = reader.GetOutput()
        mainBlockName = mesh.attrib.get( "mainBlockName", "main" )

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
                        node = assembly.AddNode( "Region", id_mesh )
                    else:
                        node = assembly.AddNode( "Surface", id_surf )

                    assembly.SetAttribute( node, "label", blockName )
                    assembly.AddDataSetIndex( node, count )
                    count += 1

    return 1


def _generate_grid( mesh: ElementTree.Element, collection: vtk.vtkPartitionedDataSetCollection ) -> int:
    count: int = collection.GetNumberOfPartitionedDataSets()
    print( f"Number of partitioned data sets: {count}", flush=True )
    elem_type = mesh.attrib[ "elementTypes" ].strip( "}{ " )

    if elem_type == "C3D8":
        xs = literal_eval( mesh.attrib[ "xCoords" ].translate( tr ) )
        ys = literal_eval( mesh.attrib[ "yCoords" ].translate( tr ) )
        zs = literal_eval( mesh.attrib[ "zCoords" ].translate( tr ) )
        nxs = literal_eval( mesh.attrib[ "nx" ].translate( tr ) )
        nys = literal_eval( mesh.attrib[ "ny" ].translate( tr ) )
        nzs = literal_eval( mesh.attrib[ "nz" ].translate( tr ) )

        def buildCoordinates( positions, numElements ):
            result = []
            it = zip( zip( positions, positions[ 1: ] ), numElements )
            for idx, (coords, n) in enumerate( it ):
                start, stop = coords
                # For all segments except the last, exclude the endpoint to avoid duplicates
                # The endpoint of one segment is the start of the next
                if idx == 0:
                    # First segment: include all points
                    tmp = np.linspace( start=start, stop=stop, num=n + 1, endpoint=True )
                else:
                    # Subsequent segments: exclude the start point (it's the endpoint of the previous segment)
                    tmp = np.linspace( start=start, stop=stop, num=n + 1, endpoint=True )[ 1: ]
                result.append( tmp )
            return np.concatenate( result )

        x_coords = buildCoordinates( xs, nxs )
        y_coords = buildCoordinates( ys, nys )
        z_coords = buildCoordinates( zs, nzs )

        # Ensure arrays are contiguous and correct type
        x_coords = np.ascontiguousarray( x_coords, dtype=np.float64 )
        y_coords = np.ascontiguousarray( y_coords, dtype=np.float64 )
        z_coords = np.ascontiguousarray( z_coords, dtype=np.float64 )

        # Create an unstructured grid from the rectilinear coordinates
        print( "Creating VTK Unstructured Grid from coordinates...", flush=True )

        # Generate all grid points
        nx, ny, nz = len( x_coords ), len( y_coords ), len( z_coords )
        points = vtk.vtkPoints()
        points.SetNumberOfPoints( nx * ny * nz )

        idx = 0
        for k in range( nz ):
            for j in range( ny ):
                for i in range( nx ):
                    points.SetPoint( idx, x_coords[ i ], y_coords[ j ], z_coords[ k ] )
                    idx += 1

        # Create hexahedral cells
        ugrid = vtk.vtkUnstructuredGrid()
        ugrid.SetPoints( points )

        # Number of cells in each direction
        ncx, ncy, ncz = nx - 1, ny - 1, nz - 1
        for k in range( ncz ):
            for j in range( ncy ):
                for i in range( ncx ):
                    # Calculate the 8 corner point indices for this hexahedron
                    # VTK hexahedron ordering: bottom face (CCW), then top face (CCW)
                    i0 = i + j * nx + k * nx * ny
                    i1 = ( i + 1 ) + j * nx + k * nx * ny
                    i2 = ( i + 1 ) + ( j + 1 ) * nx + k * nx * ny
                    i3 = i + ( j + 1 ) * nx + k * nx * ny
                    i4 = i + j * nx + ( k + 1 ) * nx * ny
                    i5 = ( i + 1 ) + j * nx + ( k + 1 ) * nx * ny
                    i6 = ( i + 1 ) + ( j + 1 ) * nx + ( k + 1 ) * nx * ny
                    i7 = i + ( j + 1 ) * nx + ( k + 1 ) * nx * ny

                    hex_cell = vtk.vtkHexahedron()
                    hex_cell.GetPointIds().SetId( 0, i0 )
                    hex_cell.GetPointIds().SetId( 1, i1 )
                    hex_cell.GetPointIds().SetId( 2, i2 )
                    hex_cell.GetPointIds().SetId( 3, i3 )
                    hex_cell.GetPointIds().SetId( 4, i4 )
                    hex_cell.GetPointIds().SetId( 5, i5 )
                    hex_cell.GetPointIds().SetId( 6, i6 )
                    hex_cell.GetPointIds().SetId( 7, i7 )

                    ugrid.InsertNextCell( hex_cell.GetCellType(), hex_cell.GetPointIds() )

        print( "Unstructured grid created successfully.", flush=True )

        # --- Start of Added Assembly Logic ---
        # Get the data assembly from the collection BEFORE creating the partitioned dataset
        print( "Getting data assembly from collection...", flush=True )
        assembly = collection.GetDataAssembly()

        # Add a parent node for this mesh, using its name from the XML
        print( "Add Mesh node...", flush=True )
        mesh_name = mesh.get( "name", "InternalMesh" )
        id_mesh = assembly.AddNode( "Mesh" )
        assembly.SetAttribute( id_mesh, "label", mesh_name )
        assembly.SetAttribute( id_mesh, "type", TreeViewNodeType.REPRESENTATION )

        # Add a "Region" node under the "Mesh" node for the generated grid
        print( "Add Region node...", flush=True )
        region_name = f"{mesh_name}_Region"
        node = assembly.AddNode( "Region", id_mesh )
        assembly.SetAttribute( node, "label", region_name )

        # Associate the new assembly node with the actual dataset index
        print( "Add Dataset index...", flush=True )
        assembly.AddDataSetIndex( node, count )
        # --- End of Added Assembly Logic ---

        print( "Creating VTK Partitioned DataSet...", flush=True )
        p = vtk.vtkPartitionedDataSet()
        p.SetPartition( 0, ugrid )
        collection.SetPartitionedDataSet( count, p )

        # Set the dataset's name metadata for consistency
        collection.GetMetaData( count ).Set( vtk.vtkCompositeDataSet.NAME(), region_name )

        return 1
    else:
        raise NotImplementedError( f"\nElement type '{elem_type}' for InternalMesh not handled yet" )
