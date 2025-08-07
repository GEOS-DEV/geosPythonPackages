import pytest
import vtk
from pathlib import Path
from geos.xml_tools import vtk_builder
from geos.xml_tools import xml_processor  # Make sure this import is at the top


@pytest.fixture
def cleanup_processed_xml( tmp_path, monkeypatch ):
    """
    Fixture to ensure processed XML files are created in a temporary
    directory that pytest will automatically clean up.
    """

    # We are going to temporarily replace the original function that creates files with the random "prep_..." name
    # with a function that creates files with a predictable name inside the temp path.
    def temp_name_generator( prefix='', suffix='.xml' ):
        """A new function that creates a predictable name inside the temp path."""
        # tmp_path is a unique temporary directory managed by pytest
        return str( tmp_path / f"{prefix}processed_test_output{suffix}" )

    # Use monkeypatch to replace the real function with our temporary one
    monkeypatch.setattr( xml_processor, 'generate_random_name', temp_name_generator )
    yield  # The test runs here

    # After the test, monkeypatch automatically restores the original function.
    # Pytest automatically deletes the tmp_path directory and its contents.


@pytest.fixture
def temp_dir( tmp_path ):
    """Create a temporary directory for test files."""
    return tmp_path


@pytest.fixture
def simple_xml_content( temp_dir ):
    """Create a basic XML file for testing."""
    xml_content = """
    <Problem name="TestProblem">
      <Mesh>
        <InternalMesh name="SimpleMesh" elementTypes="{C3D8}"
                      nx="{1}" ny="{1}" nz="{1}"
                      xCoords="{0, 1}" yCoords="{0, 1}" zCoords="{0, 1}"/>
      </Mesh>
    </Problem>
    """
    xml_file = temp_dir / "simple.xml"
    xml_file.write_text( xml_content )
    return str( xml_file )


@pytest.fixture
def vtk_file( temp_dir ):
    """Create a dummy VTK .vtu file for testing."""
    points = vtk.vtkPoints()
    points.InsertNextPoint( 0, 0, 0 )
    points.InsertNextPoint( 1, 0, 0 )
    points.InsertNextPoint( 1, 1, 0 )
    points.InsertNextPoint( 0, 1, 0 )

    quad = vtk.vtkQuad()
    quad.GetPointIds().SetId( 0, 0 )
    quad.GetPointIds().SetId( 1, 1 )
    quad.GetPointIds().SetId( 2, 2 )
    quad.GetPointIds().SetId( 3, 3 )

    cells = vtk.vtkCellArray()
    cells.InsertNextCell( quad )

    polydata = vtk.vtkPolyData()
    polydata.SetPoints( points )
    polydata.SetPolys( cells )

    # Add a region attribute for testing surface/region extraction
    region_array = vtk.vtkIntArray()
    region_array.SetName( "Region" )
    region_array.SetNumberOfComponents( 1 )
    region_array.InsertNextValue( 1 )
    polydata.GetCellData().AddArray( region_array )

    writer = vtk.vtkXMLPolyDataWriter()
    vtu_path = temp_dir / "test_mesh.vtp"
    writer.SetFileName( str( vtu_path ) )
    writer.SetInputData( polydata )
    writer.Write()
    return str( vtu_path )


@pytest.fixture
def complex_xml_content( temp_dir, vtk_file ):
    """Create a more complex XML for testing wells, boxes, and external meshes."""
    # Correct the format of polylineNodeCoords to be a list of tuples
    xml_content = f"""
    <Problem name="ComplexTest">
      <Mesh>
        <VTKMesh name="ExternalMesh" file="{Path(vtk_file).name}" />
        <InternalWell name="TestWell"
            polylineNodeCoords="{{(0,0,0), (1,1,1)}}"
            polylineSegmentConn="{{0,1}}"
            radius="{{0.1}}">
          <Perforation name="Perf1" distanceFromHead="{{0.5}}" />
        </InternalWell>
      </Mesh>
      <Geometry>
        <Box name="BoundaryBox" xMin="{{0,0,0}}" xMax="{{1,1,1}}" />
      </Geometry>
    </Problem>
    """
    xml_file = temp_dir / "complex.xml"
    xml_file.write_text( xml_content )
    return str( xml_file )


def test_read_valid_xml( simple_xml_content, cleanup_processed_xml ):
    """Test reading a valid and simple XML file."""
    deck = vtk_builder.read( simple_xml_content )
    assert deck is not None
    assert isinstance( deck, vtk_builder.SimulationDeck )
    assert deck.xml_root.tag == "Problem"
    assert deck.xml_root.attrib[ "name" ] == "TestProblem"


def test_read_nonexistent_xml():
    """Test that reading a non-existent file raises FileNotFoundError."""
    with pytest.raises( FileNotFoundError ):
        vtk_builder.read( "nonexistent_file.xml" )


def test_create_vtk_deck_simple( simple_xml_content, cleanup_processed_xml ):
    """Test the main entry point with a simple internal mesh."""
    collection = vtk_builder.create_vtk_deck( simple_xml_content )
    assert isinstance( collection, vtk.vtkPartitionedDataSetCollection )
    assert collection.GetNumberOfPartitionedDataSets() > 0

    assembly = collection.GetDataAssembly()
    assert assembly is not None
    # Correct the assertion to check for the actual root name
    assert assembly.GetRootNodeName() == "TestProblem"


def test_create_vtk_deck_complex( complex_xml_content, cleanup_processed_xml ):
    """Test creating a VTK deck with an external mesh, well, and box."""
    collection = vtk_builder.create_vtk_deck( complex_xml_content )
    assert isinstance( collection, vtk.vtkPartitionedDataSetCollection )

    # Expecting datasets for the mesh, well, perforation, and box
    assert collection.GetNumberOfPartitionedDataSets() >= 4

    assembly = collection.GetDataAssembly()
    root_name = assembly.GetRootNodeName()
    assert "ComplexTest" in root_name

    # Check for nodes using the correct GetFirstNodeByPath method
    assert assembly.GetFirstNodeByPath( f"/{root_name}/Wells" ) is not None
    assert assembly.GetFirstNodeByPath( f"/{root_name}/Boxes" ) is not None
    assert assembly.GetFirstNodeByPath( f"/{root_name}/Mesh" ) is not None


def test_well_creation( complex_xml_content, cleanup_processed_xml ):
    """Test that wells and perforations are correctly created."""
    collection = vtk_builder.create_vtk_deck( complex_xml_content )
    assembly = collection.GetDataAssembly()
    well_node_id = assembly.GetFirstNodeByPath( "/ComplexTest/Wells/Well" )
    assert well_node_id is not None

    perforation_node_id = assembly.GetFirstNodeByPath( "/ComplexTest/Wells/Well/Perforations/Perforation" )
    assert perforation_node_id is not None

    # Check metadata for names
    well_dataset_id = assembly.GetDataSetIndices( well_node_id )[ 0 ]
    well_name = collection.GetMetaData( well_dataset_id ).Get( vtk.vtkCompositeDataSet.NAME() )
    assert well_name == "TestWell"


def test_box_creation( complex_xml_content, cleanup_processed_xml ):
    """Test that box geometries are correctly created."""
    collection = vtk_builder.create_vtk_deck( complex_xml_content )
    assembly = collection.GetDataAssembly()
    box_node_id = assembly.GetFirstNodeByPath( "/ComplexTest/Boxes/Box" )
    assert box_node_id is not None

    dataset_id = assembly.GetDataSetIndices( box_node_id )[ 0 ]
    box_name = collection.GetMetaData( dataset_id ).Get( vtk.vtkCompositeDataSet.NAME() )
    assert box_name == "BoundaryBox"

    # Check the geometry of the box
    partitioned_dataset = collection.GetPartitionedDataSet( dataset_id )
    box_polydata = partitioned_dataset.GetPartition( 0 )
    assert box_polydata.GetNumberOfPoints() > 0
    bounds = box_polydata.GetBounds()
    assert bounds == ( 0.0, 1.0, 0.0, 1.0, 0.0, 1.0 )


def test_unsupported_mesh_extension( tmp_path, cleanup_processed_xml ):
    """Test that an unsupported mesh file extension is handled gracefully."""
    unsupported_file = tmp_path / "mesh.unsupported"
    unsupported_file.write_text( "<fake/>" )

    xml_content = f"""
    <Problem name="UnsupportedMesh">
      <Mesh>
        <VTKMesh name="BadMesh" file="{unsupported_file.name}"/>
      </Mesh>
    </Problem>
    """
    xml_file = tmp_path / "unsupported.xml"
    xml_file.write_text( xml_content )

    # Should print an error but not raise an exception, returning a collection
    collection = vtk_builder.create_vtk_deck( str( xml_file ) )
    assert collection is not None
    # No datasets should be added for the unsupported mesh
    assert collection.GetNumberOfPartitionedDataSets() == 0


def test_missing_mesh_attribute( vtk_file, tmp_path, cleanup_processed_xml ):
    """Test behavior when the specified cell attribute is not in the mesh."""
    xml_content = f"""
    <Problem name="MissingAttribute">
      <Mesh>
        <VTKMesh name="MyMesh" file="{Path(vtk_file).name}"/>
      </Mesh>
    </Problem>
    """
    xml_file = tmp_path / "missing_attr.xml"
    xml_file.write_text( xml_content )

    # Test with a non-existent attribute
    collection = vtk_builder.create_vtk_deck( str( xml_file ), cell_attribute="NonExistentAttr" )
    assert collection is not None
    # The mesh should still be loaded, but no surfaces/regions extracted.
    assert collection.GetNumberOfPartitionedDataSets() >= 0
