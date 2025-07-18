import sys
from unittest.mock import MagicMock, patch
import pytest

# Define mocks at the module level so they are accessible in all tests
MOCK_PV = MagicMock()
MOCK_VTK = MagicMock()
MOCK_LXML = MagicMock()
MOCK_CC = MagicMock()


# Move all sys.modules mocking into a fixture
@pytest.fixture( autouse=True )
def mock_heavy_modules( monkeypatch ):
    monkeypatch.setitem( sys.modules, "vtk", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "pyvista", MOCK_PV )
    monkeypatch.setitem( sys.modules, "colorcet", MOCK_CC )
    monkeypatch.setitem( sys.modules, "lxml", MOCK_LXML )
    monkeypatch.setitem( sys.modules, "lxml.etree", MOCK_LXML )
    monkeypatch.setitem( sys.modules, "vtkmodules", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.vtkIOXML", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.vtkCommonCore", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.vtkCommonDataModel", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.vtkRenderingCore", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.vtkFiltersCore", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.util", MOCK_VTK )
    monkeypatch.setitem( sys.modules, "vtkmodules.util.numpy_support", MOCK_VTK )
    # No yield needed; monkeypatch handles cleanup


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
        mock_mesh = MagicMock()
        mock_mesh.tube.return_value = MagicMock()

        # Test add_mesh
        viewer.add_mesh( mock_mesh )
        assert len( viewer.input ) == 1
        assert len( viewer.tubes ) == 1
        mock_mesh.tube.assert_called_with( radius=10.0, capping=True )

        # Test update
        viewer.update( value=50.0 )
        mock_mesh.tube.assert_called_with( radius=100.0, capping=True )


class TestPerforationViewer:

    def test_perforation_viewer_add_and_update( self ):
        """Test that PerforationViewer creates and updates spheres correctly."""
        viewer = pyvista_viewer.PerforationViewer( size=100.0 )
        mock_mesh = MagicMock()
        mock_mesh.points.__getitem__.return_value = [ 1, 2, 3 ]

        with patch( 'geos.xml_tools.pyvista_viewer.pv.Sphere' ) as mock_sphere:
            # Test add_mesh
            viewer.add_mesh( mock_mesh )
            assert len( viewer.input ) == 1
            assert len( viewer.spheres ) == 1
            mock_sphere.assert_called_with( center=[ 1, 2, 3 ], radius=5.0 )

            # Test update
            viewer.update( value=20.0 )
            mock_sphere.assert_called_with( center=[ 1, 2, 3 ], radius=20.0 )


# --- Tests for Callback Classes ---


class TestCallbacks:

    def test_set_visibility_callback( self ):
        """Test the single actor visibility callback."""
        mock_actor = MagicMock()
        callback = pyvista_viewer.SetVisibilityCallback( mock_actor )

        callback( True )
        mock_actor.SetVisibility.assert_called_with( True )

        callback( False )
        mock_actor.SetVisibility.assert_called_with( False )

    def test_set_visibilities_callback( self ):
        """Test the multiple actor visibility callback."""
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
        xml_file = tmp_path / "test.xml"
        # This content isn't actually parsed, but it's good practice to have it.
        xml_file.write_text( "<Problem/>" )

        # Mock the xml_processor.process function to return a dummy path
        mock_processed_path = str( tmp_path / "processed.xml" )
        with patch( 'geos.xml_tools.pyvista_viewer.process', return_value=mock_processed_path ) as mock_process:

            # FIX: Restore the original, correct mocking for the lxml parsing functions.
            # This is necessary because the lxml module itself is mocked globally.
            mock_root = MagicMock()
            mock_field_spec1 = MagicMock()
            mock_field_spec1.get.return_value = "{Surface1, Surface2, all}"
            mock_field_spec2 = MagicMock()
            mock_field_spec2.get.return_value = "{Surface3}"
            mock_root.findall.return_value = [ mock_field_spec1, mock_field_spec2 ]

            mock_tree = MagicMock()
            mock_tree.getroot.return_value = mock_root

            # Patch the call to ElementTree.parse to return our mocked tree structure
            with patch( 'geos.xml_tools.pyvista_viewer.ElementTree.parse', return_value=mock_tree ):

                # --- Run the function ---
                surfaces = pyvista_viewer.find_surfaces( str( xml_file ) )

                # --- Assert the results ---
                mock_process.assert_called_once_with( inputFiles=[ str( xml_file ) ],
                                                      keep_parameters=True,
                                                      keep_includes=True )
                assert sorted( surfaces ) == sorted( [ "Surface1", "Surface2", "Surface3" ] )
