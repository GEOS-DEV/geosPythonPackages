import sys
from unittest.mock import MagicMock, patch

# Mock the heavy external libraries BEFORE they are imported by the module we are testing.
# This allows tests to run without needing pyvista or vtk installed.
MOCK_PV = MagicMock()
MOCK_VTK = MagicMock()
MOCK_LXML = MagicMock()
MOCK_CC = MagicMock()

# --- The Fix is Here ---
# We must mock the top-level package AND every specific sub-module path that is imported.
sys.modules[ "vtk" ] = MOCK_VTK
sys.modules[ "pyvista" ] = MOCK_PV
sys.modules[ "colorcet" ] = MOCK_CC
sys.modules[ "lxml" ] = MOCK_LXML
sys.modules[ "lxml.etree" ] = MOCK_LXML

# Mock all vtkmodules paths used in the source files
sys.modules[ "vtkmodules" ] = MOCK_VTK
sys.modules[ "vtkmodules.vtkIOXML" ] = MOCK_VTK
sys.modules[ "vtkmodules.vtkCommonCore" ] = MOCK_VTK
sys.modules[ "vtkmodules.vtkCommonDataModel" ] = MOCK_VTK
sys.modules[ "vtkmodules.vtkRenderingCore" ] = MOCK_VTK
sys.modules[ "vtkmodules.vtkFiltersCore" ] = MOCK_VTK
sys.modules[ "vtkmodules.util" ] = MOCK_VTK  # Added this line
sys.modules[ "vtkmodules.util.numpy_support" ] = MOCK_VTK  # Added this line

# Now we can import the module to be tested, and all its imports will be satisfied by our mocks.
from geos.xml_tools import pyvista_viewer


# --- Tests for the Argument Parser ---
class TestParsing:

    def test_parser_defaults( self ):
        """Verify the parser's default values."""
        parser = pyvista_viewer.parsing()
        # Providing only the required argument
        args = parser.parse_args( [ "--xmlFilepath", "file.xml" ] )
        assert args.xmlFilepath == "file.xml"
        assert args.vtpcFilepath == ""
        assert args.showmesh is True
        assert args.Zamplification == 1.0

    def test_parser_custom_args( self ):
        """Verify custom arguments are parsed correctly."""
        parser = pyvista_viewer.parsing()
        cmd_args = [
            "--xmlFilepath", "my.xml", "--vtpcFilepath", "my.vtpc", "--no-showmesh", "--Zamplification", "5.5"
        ]
        args = parser.parse_args( cmd_args )
        assert args.xmlFilepath == "my.xml"
        assert args.vtpcFilepath == "my.vtpc"
        assert args.showmesh is False
        assert args.Zamplification == 5.5


# --- Tests for Viewer Logic Classes ---


class TestWellViewer:

    def test_well_viewer_add_and_update( self ):
        """Test that WellViewer creates and updates tubes correctly."""
        viewer = pyvista_viewer.WellViewer( size=200.0, amplification=1.0 )

        # FIX: Remove the spec argument. A plain MagicMock is all that's needed.
        mock_mesh = MagicMock()

        # The tube() method should still return another mock object
        mock_mesh.tube.return_value = MagicMock()

        # Test add_mesh
        viewer.add_mesh( mock_mesh )
        assert len( viewer.input ) == 1
        assert len( viewer.tubes ) == 1
        mock_mesh.tube.assert_called_with( radius=10.0, n_sides=50 )

        # Test update
        viewer.update( value=50.0 )
        mock_mesh.tube.assert_called_with( radius=100.0, n_sides=50 )
        assert viewer.tubes[ 0 ].copy_from.called


class TestPerforationViewer:

    def test_perforation_viewer_add_and_update( self ):
        """Test that PerforationViewer creates and updates spheres correctly."""
        viewer = pyvista_viewer.PerforationViewer( size=100.0 )

        # FIX: Remove the spec argument. A plain MagicMock is all that's needed.
        mock_mesh = MagicMock()
        mock_mesh.center = [ 1, 2, 3 ]

        # Test add_mesh
        viewer.add_mesh( mock_mesh )
        assert len( viewer.input ) == 1
        assert len( viewer.spheres ) == 1
        MOCK_PV.Sphere.assert_called_with( center=[ 1, 2, 3 ], radius=5.0 )

        # Test update
        viewer.update( value=20.0 )
        MOCK_PV.Sphere.assert_called_with( center=[ 1, 2, 3 ], radius=20.0 )
        assert viewer.spheres[ 0 ].copy_from.called


# --- Tests for Callback Classes ---


class TestCallbacks:

    def test_set_visibility_callback( self ):
        """Test the single actor visibility callback."""
        # FIX: Remove the spec argument.
        mock_actor = MagicMock()
        callback = pyvista_viewer.SetVisibilityCallback( mock_actor )

        callback( True )
        mock_actor.SetVisibility.assert_called_with( True )

        callback( False )
        mock_actor.SetVisibility.assert_called_with( False )

    def test_set_visibilities_callback( self ):
        """Test the multiple actor visibility callback."""
        # FIX: Remove the spec argument.
        mock_actor1 = MagicMock()
        mock_actor2 = MagicMock()

        callback = pyvista_viewer.SetVisibilitiesCallback()
        callback.add_actor( mock_actor1 )
        callback.add_actor( mock_actor2 )

        callback( True )
        mock_actor1.SetVisibility.assert_called_with( True )
        mock_actor2.SetVisibility.assert_called_with( True )


# --- Test for XML Parsing Function ---


class TestFindSurfaces:

    def test_find_surfaces_from_xml( self, tmp_path, monkeypatch ):
        """
        Tests that find_surfaces correctly parses an XML file and extracts surface names.
        """
        xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<Problem>
    <FieldSpecifications>
        <FieldSpecification name="pressure" setNames="{Surface1, Surface2, all}" />
        <FieldSpecification name="temperature" setNames="{Surface3}" />
    </FieldSpecifications>
</Problem>"""
        xml_file = tmp_path / "test.xml"
        xml_file.write_text( xml_content )

        # Mock the xml_processor.process function
        mock_processed_path = str( tmp_path / "processed.xml" )
        with patch( 'geos.xml_tools.pyvista_viewer.process', return_value=mock_processed_path ) as mock_process:

            # Mock the lxml parsing
            mock_root = MagicMock()
            mock_field_spec1 = MagicMock()
            mock_field_spec1.get.return_value = "{Surface1, Surface2, all}"
            mock_field_spec2 = MagicMock()
            mock_field_spec2.get.return_value = "{Surface3}"

            mock_root.findall.return_value = [ mock_field_spec1, mock_field_spec2 ]

            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root

            mock_parser = MagicMock()
            mock_parse = MagicMock()
            mock_parse.return_value = mock_tree

            with patch('geos.xml_tools.pyvista_viewer.ElementTree.XMLParser', return_value=mock_parser), \
                 patch('geos.xml_tools.pyvista_viewer.ElementTree.parse', return_value=mock_tree):

                # --- Run the function ---
                surfaces = pyvista_viewer.find_surfaces( str( xml_file ) )

                # --- Assert the results ---
                mock_process.assert_called_once_with( inputFiles=[ str( xml_file ) ],
                                                      keep_parameters=True,
                                                      keep_includes=True )
                assert sorted( surfaces ) == sorted( [ "Surface1", "Surface2", "Surface3" ] )
