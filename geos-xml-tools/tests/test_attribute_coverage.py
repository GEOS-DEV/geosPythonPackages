import pytest
from lxml import etree as ElementTree
from geos.xml_tools import attribute_coverage


@pytest.fixture
def mock_project_files(tmp_path):
    """Creates a mock file system with a schema and some XML files for testing."""
    # 1. Define a simple schema
    schema_content = """<?xml version="1.0" encoding="UTF-8" ?>
    <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
      <xs:element name="Problem" type="ProblemType"/>
      <xs:complexType name="ProblemType">
        <xs:choice>
          <xs:element name="ChildNode" type="ChildType"/>
        </xs:choice>
        <xs:attribute name="name" type="xs:string"/>
        <xs:attribute name="version" type="xs:string" default="1.0"/>
      </xs:complexType>
      <xs:complexType name="ChildType">
        <xs:attribute name="id" type="xs:string"/>
      </xs:complexType>
    </xs:schema>
    """
    schema_path = tmp_path / "schema.xsd"
    schema_path.write_text(schema_content)

    # 2. Define a couple of XML files that use this schema
    xml_content_src = """<Problem name="Test1" version="1.1">
      <ChildNode id="c1"/>
    </Problem>"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    (src_dir / "test1.xml").write_text(xml_content_src)

    xml_content_examples = """<Problem name="Test2">
      <ChildNode id="c2"/>
    </Problem>"""
    examples_dir = tmp_path / "examples"
    examples_dir.mkdir()
    (examples_dir / "test2.xml").write_text(xml_content_examples)

    return {"schema": str(schema_path), "src_xml": str(src_dir / "test1.xml"), "examples_xml": str(examples_dir / "test2.xml")}


class TestAttributeCoverageWorkflow:
    """Tests the individual functions of the attribute_coverage module."""

    def test_parse_schema(self, mock_project_files):
        """Verify that the schema is parsed into the correct dictionary structure."""
        schema_file = mock_project_files["schema"]
        
        xml_types = attribute_coverage.parse_schema(schema_file)

        # Check top-level structure
        assert "Problem" in xml_types
        problem_attrs = xml_types["Problem"]["attributes"]
        problem_children = xml_types["Problem"]["children"]

        # Check attributes and defaults
        assert "name" in problem_attrs
        assert "version" in problem_attrs
        assert problem_attrs["version"]["default"] == "1.0"
        assert "default" not in problem_attrs["name"]

        # Check children
        assert "ChildNode" in problem_children
        child_attrs = problem_children["ChildNode"]["attributes"]
        assert "id" in child_attrs
        
    def test_collect_xml_attributes(self, mock_project_files):
        """Verify that attributes from an XML file are collected into the structure."""
        schema_file = mock_project_files["schema"]
        src_xml_file = mock_project_files["src_xml"]

        # 1. Get the initial empty structure from the schema
        xml_types = attribute_coverage.parse_schema(schema_file)

        # 2. Collect attributes from the source XML file
        attribute_coverage.collect_xml_attributes(xml_types, src_xml_file, folder="src")

        # 3. Assert that the structure is now populated
        problem_attrs = xml_types["Problem"]["attributes"]
        child_attrs = xml_types["Problem"]["children"]["ChildNode"]["attributes"]

        assert problem_attrs["name"]["src"] == ["Test1"]
        assert problem_attrs["version"]["src"] == ["1.1"]
        assert child_attrs["id"]["src"] == ["c1"]
        
        # Ensure other folders are still empty
        assert problem_attrs["name"]["examples"] == []

    def test_write_attribute_usage_xml(self, mock_project_files, tmp_path):
        """Verify that the final XML report is written correctly."""
        schema_file = mock_project_files["schema"]
        src_xml_file = mock_project_files["src_xml"]
        examples_xml_file = mock_project_files["examples_xml"]
        output_file = tmp_path / "report.xml"

        # 1. Create a fully populated data structure
        xml_types = attribute_coverage.parse_schema(schema_file)
        attribute_coverage.collect_xml_attributes(xml_types, src_xml_file, folder="src")
        attribute_coverage.collect_xml_attributes(xml_types, examples_xml_file, folder="examples")

        # 2. Write the XML report
        attribute_coverage.write_attribute_usage_xml(xml_types, str(output_file))

        # 3. Parse the report and verify its content
        assert output_file.exists()
        tree = ElementTree.parse(str(output_file))
        root = tree.getroot()

        assert root.tag == "Problem"
        
        # Check an attribute with values from both folders
        name_node = root.find("name")
        assert name_node.get("src") == "Test1"
        assert name_node.get("examples") == "Test2"
        assert name_node.get("unique_values") == "2"

        # Check an attribute with a default value
        version_node = root.find("version")
        assert version_node.get("default") == "1.0"
        assert version_node.get("src") == "1.1" # Value from src
        assert version_node.get("examples") == "" # No value from examples
        assert version_node.get("unique_values") == "1"

        # Check a child node's attribute
        child_node = root.find("ChildNode")
        assert child_node is not None
        id_node = child_node.find("id")
        assert id_node.get("src") == "c1"
        assert id_node.get("examples") == "c2"
