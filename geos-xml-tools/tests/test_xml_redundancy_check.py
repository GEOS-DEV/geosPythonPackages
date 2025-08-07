import pytest
from lxml import etree as ElementTree
from copy import deepcopy
from geos.xml_tools import xml_redundancy_check


@pytest.fixture
def mock_schema():
    """Provides a mock schema dictionary for testing."""
    return {
        "Problem": {
            "attributes": {
                "name": {},  # Attribute with no default
                "version": {
                    "default": "1.0"
                },
                "mode": {
                    "default": "normal"
                }
            },
            "children": {
                "RequiredChild": {
                    "attributes": {
                        "id": {}  # Required attribute
                    },
                    "children": {}
                },
                "RedundantChild": {
                    "attributes": {
                        "value": {
                            "default": "abc"
                        }
                    },
                    "children": {}
                }
            }
        }
    }


@pytest.fixture
def sample_xml_tree():
    """Provides a sample XML tree with redundant and required data."""
    xml_string = """
    <Problem name="Test1" version="1.1" mode="normal" component="Solver">
        <RequiredChild id="c1"/>
        <RedundantChild value="abc"/>
        </Problem>
    """
    return ElementTree.fromstring( xml_string )


class TestXmlRedundancyCheck:
    """Tests for the XML redundancy check script."""

    def test_check_redundancy_level( self, mock_schema, sample_xml_tree ):
        """
        Tests the core recursive function to ensure it correctly identifies
        and removes redundant attributes and nodes wrt a schema.
        """
        # We work on a copy to not modify the original fixture object
        node_to_modify = deepcopy( sample_xml_tree )
        schema_level = mock_schema[ "Problem" ]
        required_count = xml_redundancy_check.check_redundancy_level( schema_level, node_to_modify )

        # The required attributes are: name, version, component, and the child's 'id'. Total = 4.
        assert required_count == 4

        # Check attributes on the root node
        assert node_to_modify.get( "name" ) == "Test1"  # Kept (no default in schema)
        assert node_to_modify.get( "version" ) == "1.1"  # Kept (value != default)
        assert node_to_modify.get( "component" ) is not None  # Kept (in whitelist)
        assert node_to_modify.get( "mode" ) is None  # Removed (value == default)

        # Check children
        assert node_to_modify.find( "RequiredChild" ) is not None  # Kept (has a required attribute)
        assert node_to_modify.find( "RedundantChild" ) is None  # Removed (child became empty and was pruned)

    def test_check_xml_redundancy_file_io( self, mock_schema, sample_xml_tree, tmp_path, monkeypatch ):
        """
        Tests the wrapper function to ensure it reads, processes, and writes
        the file correctly.
        """
        # Create a temporary file with the sample XML content
        xml_file = tmp_path / "test.xml"
        tree = ElementTree.ElementTree( sample_xml_tree )
        tree.write( str( xml_file ) )

        # Mock the external formatter to isolate the test
        monkeypatch.setattr( xml_redundancy_check, 'format_file', lambda *args, **kwargs: None )
        xml_redundancy_check.check_xml_redundancy( mock_schema, str( xml_file ) )
        processed_tree = ElementTree.parse( str( xml_file ) ).getroot()

        # Check for the same conditions as the direct test
        assert processed_tree.get( "mode" ) is None
        assert processed_tree.find( "RedundantChild" ) is None
        assert processed_tree.get( "name" ) == "Test1"
