import pytest
import sys
from geos.xml_tools import xml_formatter


class TestFormatAttribute:
    """Tests the format_attribute helper function."""

    @pytest.mark.parametrize(
        "input_str, expected_str",
        [
            ( "a,b, c", "a, b, c" ),
            ( "{ a, b }", "{ a, b }" ),  # check consistency
            ( "  a   b  ", " a b " ),
            ( "{{1,2,3}}", "{ { 1, 2, 3 } }" )
        ] )
    def test_basic_formatting( self, input_str, expected_str ):
        """Tests basic whitespace and comma/bracket handling."""
        # Dummy indent and key name, as they don't affect these tests
        formatted = xml_formatter.format_attribute( "  ", "key", input_str )
        assert formatted == expected_str

    def test_multiline_attribute_formatting( self ):
        """Tests the specific logic for splitting attributes onto multiple lines."""
        input_str = "{{1,2,3}, {4,5,6}}"
        # The indent length and key name length (4 + 5 + 4) determine the newline indent
        attribute_indent = "    "
        key_name = "value"
        expected_gap = len( attribute_indent ) + len( key_name ) + 4
        expected_str = ( "{ { 1, 2, 3 },\n" + " " * expected_gap + "{ 4, 5, 6 } }" )

        formatted = xml_formatter.format_attribute( attribute_indent, key_name, input_str )
        assert formatted == expected_str


class TestFormatFile:
    """Tests the main file formatting logic."""

    @pytest.fixture
    def unformatted_xml_path( self, tmp_path ):
        """Creates a temporary, messy XML file and returns its path."""
        content = '<?xml version="1.0" ?><Root z="3" a="1"><Child b="2" a="1"/><Empty/></Root>'
        xml_file = tmp_path / "test.xml"
        xml_file.write_text( content )
        return str( xml_file )

    def test_format_file_defaults( self, unformatted_xml_path ):
        """Tests the formatter with its default settings."""
        xml_formatter.format_file( unformatted_xml_path )

        with open( unformatted_xml_path, 'r' ) as f:
            content = f.read()

        expected_content = ( '<?xml version="1.0" ?>\n\n'
                             '<Root\n'
                             '  z="3"\n'
                             '  a="1">\n'
                             '  <Child\n'
                             '    b="2"\n'
                             '    a="1"/>\n\n'
                             '  <Empty/>\n'
                             '</Root>\n' )
        assert content == expected_content

    def test_format_file_sorted_and_hanging_indent( self, unformatted_xml_path ):
        """Tests with attribute sorting and hanging indents enabled."""
        xml_formatter.format_file(
            unformatted_xml_path,
            alphebitize_attributes=True,
            indent_style=True  # Enables hanging indent
        )

        with open( unformatted_xml_path, 'r' ) as f:
            content = f.read()

        expected_content = ( '<?xml version="1.0" ?>\n\n'
                             '<Root a="1"\n'
                             '      z="3">\n'
                             '  <Child a="1"\n'
                             '         b="2"/>\n\n'
                             '  <Empty/>\n'
                             '</Root>\n' )
        assert content == expected_content


class TestMainFunction:
    """Tests the main() function which handles command-line execution."""

    def test_main_calls_format_file_correctly( self, monkeypatch ):
        """
        Verifies that main() parses arguments and calls format_file with them.
        """
        # Create a spy to record the arguments passed to format_file
        call_args = {}

        def spy_format_file( *args, **kwargs ):
            call_args[ 'args' ] = args
            call_args[ 'kwargs' ] = kwargs

        # 1. Mock sys.argv to simulate command-line input
        test_argv = [ 'xml_formatter.py', 'my_file.xml', '--indent', '4', '--alphebitize', '1' ]
        monkeypatch.setattr( sys, 'argv', test_argv )

        # 2. Replace the real format_file with our spy
        monkeypatch.setattr( xml_formatter, 'format_file', spy_format_file )

        # 3. Run the main function
        xml_formatter.main()

        # 4. Assert that our spy was called with the correct arguments
        assert call_args[ 'kwargs' ][ 'indent_size' ] == 4
        assert call_args[ 'kwargs' ][ 'alphebitize_attributes' ] == 1
        assert call_args[ 'args' ][ 0 ] == 'my_file.xml'
