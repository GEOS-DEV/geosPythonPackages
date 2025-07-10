import pytest
import os
import time
from lxml import etree as ElementTree
from geos.xml_tools import xml_processor
from geos.xml_tools import regex_tools
from geos.xml_tools import unit_manager

# Fixtures for creating XML content and files

@pytest.fixture
def base_xml_content():
    """Provides a basic XML structure as a string."""
    return """
    <Problem name="BaseProblem">
        <A name="a1" val="1"/>
    </Problem>
    """

@pytest.fixture
def include_xml_content():
    """Provides an XML structure to be included."""
    return """
    <Problem name="IncludeProblem">
        <B name="b1" val="override"/>
        <C name="c1" val="3"/>
    </Problem>
    """

@pytest.fixture
def complex_xml_content_with_params():
    """Provides an XML with parameters, units, and symbolic math."""
    return """
    <Problem>
        <Parameters>
            <Parameter name="pressure" value="100.0"/>
            <Parameter name="length" value="10.0"/>
        </Parameters>
        <MyBlock
            pressure_val="$:pressure$[psi]"
            length_val="$:length$[ft]"
            area_calc="`$:length$**2`"
        />
        <Included>
            <File name="include.xml"/>
        </Included>
    </Problem>
    """


# --- Test Suite ---

class TestNodeMerging:
    """Tests for the merge_xml_nodes function."""

    def test_merge_attributes(self):
        existing = ElementTree.fromstring('<Node a="1" b="2"/>')
        target = ElementTree.fromstring('<Node a="3" c="4"/>')
        xml_processor.merge_xml_nodes(existing, target, level=1)
        assert existing.get("a") == "3"  # a from "existing" is overwritten by a from 
        assert existing.get("b") == "2"
        assert existing.get("c") == "4"

    def test_merge_new_children(self):
        existing = ElementTree.fromstring('<Root><A/></Root>')
        target = ElementTree.fromstring('<Root><B/><C/></Root>')
        xml_processor.merge_xml_nodes(existing, target, level=1)
        assert len(existing) == 3
        # FIX: Correctly check the tags of all children in order.
        assert existing[0].tag == 'B'  # because of insert(-1, ..), target nodes are added before the existing ones
        assert existing[1].tag == 'C'  # same here
        assert existing[2].tag == 'A'

    def test_merge_named_children_recursively(self):
        existing = ElementTree.fromstring('<Root><Child name="child1" val="a"/></Root>')
        target = ElementTree.fromstring('<Root><Child name="child1" val="b" new_attr="c"/></Root>')
        xml_processor.merge_xml_nodes(existing, target, level=1)
        assert len(existing) == 1
        merged_child = existing.find('Child')
        assert merged_child.get('name') == 'child1'
        assert merged_child.get('val') == 'b'
        assert merged_child.get('new_attr') == 'c'

    def test_merge_root_problem_node(self):
        existing = ElementTree.fromstring('<Problem name="base"><A/></Problem>')
        target = ElementTree.fromstring('<Problem name="included" attr="new"><B/></Problem>')
        xml_processor.merge_xml_nodes(existing, target, level=0)
        # FIX: The root node's original name should be preserved.
        assert existing.get('name') == 'included'
        assert existing.get('attr') == 'new'
        assert len(existing) == 2
        assert existing[0].tag == 'B'
        assert existing[1].tag == 'A'


class TestFileInclusion:
    """Tests for merge_included_xml_files."""

    def test_simple_include(self, tmp_path, base_xml_content, include_xml_content):
        base_file = tmp_path / "base.xml"
        include_file = tmp_path / "include.xml"
        base_file.write_text(base_xml_content)
        include_file.write_text(include_xml_content)
        
        root = ElementTree.fromstring(base_xml_content)
        
        os.chdir(tmp_path)
        xml_processor.merge_included_xml_files(root, "include.xml", 0)

        b_node = root.find(".//B")
        c_node = root.find(".//C")
        assert b_node is not None and b_node.get("val") == "override"
        assert c_node is not None and c_node.get("val") == "3"

    def test_include_nonexistent_file(self, tmp_path):
        root = ElementTree.Element("Problem")
        # FIX: Adjust the regex to correctly match the exception message.
        with pytest.raises(Exception, match="Check included file path!"):
            xml_processor.merge_included_xml_files(root, str(tmp_path / "nonexistent.xml"), 0)

    def test_include_loop_fails(self, tmp_path):
        file_a_content = '<Problem><Included><File name="b.xml"/></Included></Problem>'
        file_b_content = '<Problem><Included><File name="a.xml"/></Included></Problem>'
        
        (tmp_path / "a.xml").write_text(file_a_content)
        (tmp_path / "b.xml").write_text(file_b_content)

        root = ElementTree.Element("Problem")
        os.chdir(tmp_path)
        with pytest.raises(Exception, match="Reached maximum recursive includes"):
            xml_processor.merge_included_xml_files(root, "a.xml", 0, maxInclude=5)

    def test_malformed_include_file(self, tmp_path):
        (tmp_path / "malformed.xml").write_text("<Problem><UnclosedTag></Problem>")
        root = ElementTree.Element("Problem")
        with pytest.raises(Exception, match="Check included file!"):
            xml_processor.merge_included_xml_files(root, str(tmp_path / "malformed.xml"), 0)


class TestRegexSubstitution:
    """Tests for apply_regex_to_node."""

    @pytest.fixture(autouse=True)
    def setup_handlers(self):
        xml_processor.parameterHandler.target = {"varA": "10", "varB": "2.5"}
        xml_processor.unitManager = unit_manager.UnitManager()

    def test_unit_substitution(self):
        node = ElementTree.fromstring('<Node val="10[ft]"/>')
        xml_processor.apply_regex_to_node(node)
        assert pytest.approx(float(node.get("val"))) == 3.047851

    def test_symbolic_math_substitution(self):
        node = ElementTree.fromstring('<Node val="`2 * (3 + 5)`"/>')
        xml_processor.apply_regex_to_node(node)
        assert pytest.approx(float(node.get("val"))) == 1.6e1

    def test_combined_substitution(self):
        node = ElementTree.fromstring('<Node val="`$:varA$ * $:varB$`"/>')
        xml_processor.apply_regex_to_node(node)
        # When using apply_regex_to_node
        # 1st step will make val="'10 * 2.5'"
        # 2nd step will substitute val by the result which is 2.5e1
        assert node.get("val") == "2.5e1"


# A fixture to create a temporary, self-contained testing environment
@pytest.fixture
def setup_test_files(tmp_path):
    """
    Creates a set of test files with absolute paths to avoid issues with chdir.
    Returns a dictionary of absolute paths to the created files.
    """
    # --- Define XML content with placeholders for absolute paths ---
    main_xml_content = """
    <Problem>
        <Parameters>
            <Parameter name="pressure" value="100.0"/>
            <Parameter name="length" value="10.0"/>
        </Parameters>
        <MyBlock
            pressure_val="$:pressure$[psi]"
            length_val="$:length$[ft]"
            area_calc="`$:length$**2`"
        />
        <Included>
            <File name="{include_path}"/>
        </Included>
    </Problem>
    """
    include_xml_content = '<Problem><IncludedBlock val="included_ok"/></Problem>'

    # --- Create file paths ---
    main_file_path = tmp_path / "main.xml"
    include_file_path = tmp_path / "include.xml"

    # --- Write content to files, injecting absolute paths ---
    include_file_path.write_text(include_xml_content)
    main_file_path.write_text(main_xml_content.format(include_path=include_file_path.resolve()))

    return {"main": str(main_file_path), "include": str(include_file_path)}


# A fixture to create a temporary, self-contained testing environment
@pytest.fixture
def setup_test_files(tmp_path):
    """
    Creates a set of test files with absolute paths to avoid issues with chdir.
    Returns a dictionary of absolute paths to the created files.
    """
    # --- Define XML content with placeholders for absolute paths ---
    main_xml_content = """
    <Problem>
        <Parameters>
            <Parameter name="pressure" value="100.0"/>
            <Parameter name="length" value="10.0"/>
        </Parameters>
        <MyBlock
            pressure_val="$:pressure$[psi]"
            length_val="$:length$[ft]"
            area_calc="`$:length$**2`"
        />
        <Included>
            <File name="{include_path}"/>
        </Included>
    </Problem>
    """
    include_xml_content = '<Problem><IncludedBlock val="included_ok"/></Problem>'

    # --- Create file paths ---
    main_file_path = tmp_path / "main.xml"
    include_file_path = tmp_path / "include.xml"

    # --- Write content to files, injecting absolute paths ---
    include_file_path.write_text(include_xml_content)
    # Use .resolve() to get a clean, absolute path for the include tag
    main_file_path.write_text(main_xml_content.format(include_path=include_file_path.resolve()))

    return {"main": str(main_file_path), "include": str(include_file_path)}


class TestProcessFunction:
    """A test suite for the xml_processor.process function."""

    @pytest.mark.parametrize(
        "keep_includes, keep_parameters, expect_comments",
        [
            (True, True, True),   # Keep both as comments
            (False, False, False), # Remove both entirely
            (True, False, True),  # Keep includes as comments, remove parameters
        ]
    )
    def test_process_success_and_cleanup(self, setup_test_files, monkeypatch, keep_includes, keep_parameters, expect_comments):
        """
        Tests the main success path of the process function, including includes,
        parameters, overrides, and cleanup flags.
        """
        # Mock the external formatter to isolate the test
        monkeypatch.setattr(xml_processor.xml_formatter, 'format_file', lambda *args, **kwargs: None)

        main_file = setup_test_files["main"]
        output_file = os.path.join(os.path.dirname(main_file), "processed.xml")

        # --- Execute the function with a parameter override ---
        final_path = xml_processor.process(
            inputFiles=[main_file],
            outputFile=output_file,
            parameter_override=[("pressure", "200.0")], # Override pressure from 100 to 200
            keep_includes=keep_includes,
            keep_parameters=keep_parameters
        )

        assert final_path == output_file
        
        # --- Verify the output file content ---
        processed_tree = ElementTree.parse(final_path).getroot()

        # Check that the included file was merged successfully
        assert processed_tree.find("IncludedBlock") is not None
        assert processed_tree.find("IncludedBlock").get("val") == "included_ok"

        # Check that substitutions happened correctly with the override
        block = processed_tree.find("MyBlock")
        assert block is not None
        # 200[psi] -> 200 * 6894.76 Pa -> 1378952.0
        assert pytest.approx(float(block.get("pressure_val"))) == 1378952.0
        assert pytest.approx(float(block.get("length_val"))) == 10 / 3.281
        assert pytest.approx(float(block.get("area_calc"))) == 100.0

        # Check if Included/Parameters blocks were removed or commented out
        comments = [c.text for c in processed_tree.iter(ElementTree.Comment)]
        if expect_comments:
            assert any('<Included>' in c for c in comments)
            # This logic branch only checks for included comments, as per the parameters
            if keep_parameters:
                assert any('<Parameters>' in c for c in comments)
        else:
            assert processed_tree.find("Parameters") is None
            assert processed_tree.find("Included") is None
            assert not any('<Included>' in c for c in comments)
            assert not any('<Parameters>' in c for c in comments)

    def test_process_fails_on_unmatched_character(self, tmp_path, monkeypatch):
        """
        Tests that the function fails if a special character makes it to the final output.
        """
        monkeypatch.setattr(xml_processor.xml_formatter, 'format_file', lambda *args, **kwargs: None)

        bad_file = tmp_path / "bad.xml"
        # A lone backtick is not a valid pattern and will not be substituted
        bad_file.write_text('<Problem val="This is an error `"/>')

        with pytest.raises(Exception, match="Reached maximum symbolic expands"):
            xml_processor.process(inputFiles=[str(bad_file)])

    def test_process_fails_on_undefined_parameter(self, tmp_path, monkeypatch):
        """
        Tests that the function fails if a parameter is used but not defined.
        """
        monkeypatch.setattr(xml_processor.xml_formatter, 'format_file', lambda *args, **kwargs: None)

        bad_file = tmp_path / "bad.xml"
        bad_file.write_text('<Problem val="$undefinedVar"/>')

        with pytest.raises(Exception, match="Error: Target \\(undefinedVar\\) is not defined"):
            xml_processor.process(inputFiles=[str(bad_file)])


class TestHelpers:
    """Tests for miscellaneous helper functions."""

    def test_generate_random_name(self):
        name1 = xml_processor.generate_random_name(prefix="test_", suffix=".tmp")
        # Small delay to prevent a race condition with time.time()
        time.sleep(0.001)
        name2 = xml_processor.generate_random_name(prefix="test_", suffix=".tmp")
        assert name1.startswith("test_")
        assert name1.endswith(".tmp")
        assert name1 != name2

    def test_validate_xml(self, tmp_path, capsys):
        schema_content = """
        <xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
            <xs:element name="Problem">
                <xs:complexType>
                    <xs:attribute name="name" type="xs:string" use="required"/>
                </xs:complexType>
            </xs:element>
        </xs:schema>
        """
        invalid_xml_content = '<Problem/>'

        schema_file = tmp_path / "schema.xsd"
        invalid_file = tmp_path / "invalid.xml"
        schema_file.write_text(schema_content)
        invalid_file.write_text(invalid_xml_content)

        xml_processor.validate_xml(str(invalid_file), str(schema_file), verbose=0)
        captured = capsys.readouterr()
        assert "Warning: input XML contains potentially invalid input parameters" in captured.out
