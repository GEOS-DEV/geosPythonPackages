import pytest
import numpy as np
import pyvista as pv
from unittest.mock import patch
import vtk
# Import the module to be tested
from geos.xml_tools import vtk_builder


@pytest.fixture
def real_project_files(tmp_path):
    """
    Creates a real set of files, including a VTK mesh file (.vtu),
    for integration testing.
    """
    # Create a mesh representing a cube, which has 6 cells (faces)
    mesh = pv.Cube().cast_to_unstructured_grid()
    mesh.cell_data["Region"] = [1, 1, 1, 1, 1, 1]
    mesh_path = tmp_path / "mesh.vtu"
    mesh.save(str(mesh_path))

    xml_content = f"""
    <Problem name="IntegrationTestDeck">
        <Mesh>
            <VTKMesh name="main_mesh" file="{mesh_path.name}"/>
            <InternalWell name="Well-A" radius="{{0.1}}"
                          polylineNodeCoords="{{1,1,10}}, {{1,1,0}}"
                          polylineSegmentConn="{{0,1}}" />
        </Mesh>
        <Geometry>
            <Box name="ReservoirBox" xMin="{{0,0,0}}" xMax="{{1,1,1}}"/>
        </Geometry>
    </Problem>
    """
    xml_path = tmp_path / "deck.xml"
    xml_path.write_text(xml_content)

    return {"xml_path": str(xml_path), "mesh_path": str(mesh_path)}


class TestVtkBuilderIntegration:
    """An integration test suite for the vtk_builder module."""

    @patch("geos.xml_tools.xml_processor.process")
    def test_create_vtk_deck_integration(self, mock_process, real_project_files):
        """
        Tests the entire vtk_builder workflow using real files and VTK objects.
        """
        xml_path = real_project_files["xml_path"]

        # Mock the pre-processor to return the path to our test XML
        mock_process.return_value = xml_path
        
        # Execute the function under test
        collection = vtk_builder.create_vtk_deck(xml_path, cell_attribute="Region")
        
        # 1. Check the overall object type
        assert isinstance(collection, vtk.vtkPartitionedDataSetCollection)

        # 2. Check the data assembly structure
        assembly = collection.GetDataAssembly()
        assert assembly is not None
        assert assembly.GetRootNodeName() == "IntegrationTestDeck"
        
        # Verify that nodes for Mesh, Wells, and Boxes were created
        assert assembly.GetFirstNodeByPath("//IntegrationTestDeck/Mesh") > 0
        assert assembly.GetFirstNodeByPath("//IntegrationTestDeck/Wells/Well") > 0
        assert assembly.GetFirstNodeByPath("//IntegrationTestDeck/Boxes/Box") > 0

        # 3. Verify the data content of a specific part (the Box)
        box_node_id = assembly.GetFirstNodeByPath("//IntegrationTestDeck/Boxes/Box")
        dataset_indices = assembly.GetDataSetIndices(box_node_id, False)
        assert len(dataset_indices) == 1
        
        partitioned_dataset = collection.GetPartitionedDataSet(dataset_indices[0])
        box_polydata = partitioned_dataset.GetPartition(0)
        
        # Get the bounds of the created VTK box and check them
        bounds = box_polydata.GetBounds()
        expected_bounds = (0.0, 1.0, 0.0, 1.0, 0.0, 1.0)
        np.testing.assert_allclose(bounds, expected_bounds)
