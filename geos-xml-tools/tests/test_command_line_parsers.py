import sys
from geos.xml_tools import command_line_parsers


class TestPreprocessorParser:
    """Tests for the XML preprocessor command line parser."""

    def test_preprocessor_defaults( self ):
        """Verify the parser's default values when no arguments are given."""
        parser = command_line_parsers.build_preprocessor_input_parser()
        args = parser.parse_args( [] )
        assert args.input is None
        assert args.compiled_name == ''
        assert args.schema == ''
        assert args.verbose == 0
        assert args.parameters == []

    def test_preprocessor_all_args( self ):
        """Test the parser with all arguments provided."""
        parser = command_line_parsers.build_preprocessor_input_parser()
        cmd_args = [
            '--input', 'file1.xml', '-i', 'file2.xml', '--compiled-name', 'output.xml', '--schema', 'schema.xsd',
            '--verbose', '1', '--parameters', 'p1', 'v1', '-p', 'p2', 'v2'
        ]
        args = parser.parse_args( cmd_args )
        assert args.input == [ 'file1.xml', 'file2.xml' ]
        assert args.compiled_name == 'output.xml'
        assert args.schema == 'schema.xsd'
        assert args.verbose == 1
        assert args.parameters == [ [ 'p1', 'v1' ], [ 'p2', 'v2' ] ]

    def test_parse_known_args( self, monkeypatch ):
        """Test that unknown arguments are separated correctly."""
        test_args = [
            'script_name.py',  # The first element is always the script name
            '-i',
            'file.xml',
            '--unknown-flag',
            'value',
            '-z'  # another unknown
        ]

        # 1. Use monkeypatch to temporarily set sys.argv for this test
        monkeypatch.setattr( sys, 'argv', test_args )

        # 2. Now call the function, which will use the patched sys.argv
        args, unknown = command_line_parsers.parse_xml_preprocessor_arguments()

        # 3. Assert the results
        assert args.input == [ 'file.xml' ]
        assert unknown == [ '--unknown-flag', 'value', '-z' ]


class TestFormatterParser:
    """Tests for the XML formatter command line parser."""

    def test_formatter_defaults( self ):
        """Verify the formatter parser's defaults."""
        parser = command_line_parsers.build_xml_formatter_input_parser()
        args = parser.parse_args( [ 'my_file.xml' ] )
        assert args.input == 'my_file.xml'
        assert args.indent == 2
        assert args.style == 0
        assert args.depth == 2
        assert args.alphebitize == 0
        assert args.close == 0
        assert args.namespace == 0

    def test_formatter_custom_args( self ):
        """Test providing custom arguments to the formatter parser."""
        parser = command_line_parsers.build_xml_formatter_input_parser()
        cmd_args = [
            'input.xml', '--indent', '4', '--style', '1', '--depth', '3', '--alphebitize', '1', '--close', '1',
            '--namespace', '1'
        ]
        args = parser.parse_args( cmd_args )
        assert args.input == 'input.xml'
        assert args.indent == 4
        assert args.style == 1
        assert args.depth == 3
        assert args.alphebitize == 1
        assert args.close == 1
        assert args.namespace == 1


class TestAttributeCoverageParser:
    """Tests for the attribute coverage command line parser."""

    def test_coverage_defaults( self ):
        """Verify the coverage parser's defaults."""
        parser = command_line_parsers.build_attribute_coverage_input_parser()
        args = parser.parse_args( [] )
        assert args.root == ''
        assert args.output == 'attribute_test.xml'

    def test_coverage_custom_args( self ):
        """Test providing custom arguments to the coverage parser."""
        parser = command_line_parsers.build_attribute_coverage_input_parser()
        args = parser.parse_args( [ '-r', '/my/root', '-o', 'report.xml' ] )
        assert args.root == '/my/root'
        assert args.output == 'report.xml'


class TestXmlRedundancyParser:
    """Tests for the XML redundancy command line parser."""

    def test_redundancy_defaults( self ):
        """Verify the redundancy parser's defaults."""
        parser = command_line_parsers.build_xml_redundancy_input_parser()
        args = parser.parse_args( [] )
        assert args.root == ''

    def test_redundancy_custom_args( self ):
        """Test providing a custom root to the redundancy parser."""
        parser = command_line_parsers.build_xml_redundancy_input_parser()
        args = parser.parse_args( [ '--root', '/some/path' ] )
        assert args.root == '/some/path'
