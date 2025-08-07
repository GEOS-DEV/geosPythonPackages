import pytest
import re
from geos.xml_tools import regex_tools


class TestSymbolicMathRegexHandler:
    """Tests for the SymbolicMathRegexHandler function."""

    @pytest.mark.parametrize(
        "input_str, expected_output",
        [
            ( "1 + 2", "3" ),
            ( "10 / 4.0", "2.5" ),
            ( "2 * (3 + 5)", "1.6e1" ),
            ( "1.5e2", "1.5e2" ),
            # Test stripping of trailing zeros and exponents
            ( "1.23000e+00", "1.23" ),
            ( "5.000e-01", "5e-1" )
        ] )
    def test_symbolic_math_evaluation( self, input_str, expected_output ):
        """Verify correct evaluation of various math expressions."""
        # Create a real match object using the pattern from the module
        pattern = regex_tools.patterns[ 'symbolic' ]
        match = re.match( pattern, f"`{input_str}`" )

        assert match is not None, "Regex pattern did not match the input string"

        result = regex_tools.SymbolicMathRegexHandler( match )
        assert result == expected_output

    def test_empty_match_returns_empty_string( self ):
        """Verify that an empty match group returns an empty string."""
        pattern = regex_tools.patterns[ 'symbolic' ]
        match = re.match( pattern, "``" )

        result = regex_tools.SymbolicMathRegexHandler( match )
        assert result == ""


class TestDictRegexHandler:
    """Tests for the DictRegexHandler class."""

    @pytest.fixture
    def populated_handler( self ):
        """Provides a handler instance with a prepopulated target dictionary."""
        handler = regex_tools.DictRegexHandler()
        handler.target = { "var1": "100", "var2": "some_string", "pressure": "1.0e5" }
        return handler

    def test_successful_lookup( self, populated_handler ):
        """Verify that a known key is replaced with its target value."""
        # We can use a simple regex for testing the handler logic
        pattern = r"\$([a-zA-Z0-9_]*)"
        match = re.match( pattern, "$var1" )

        result = populated_handler( match )
        assert result == "100"

    def test_string_value_lookup( self, populated_handler ):
        """Verify that non-numeric string values are returned correctly."""
        pattern = r"\$([a-zA-Z0-9_]*)"
        match = re.match( pattern, "$var2" )

        result = populated_handler( match )
        assert result == "some_string"

    def test_fails_on_undefined_target( self, populated_handler ):
        """Verify that an exception is raised for an unknown key."""
        pattern = r"\$([a-zA-Z0-9_]*)"
        match = re.match( pattern, "$unknown_var" )

        with pytest.raises( Exception, match="Error: Target \\(unknown_var\\) is not defined" ):
            populated_handler( match )

    def test_empty_match_group_returns_empty_string( self, populated_handler ):
        """Verify that an empty match group returns an empty string."""
        pattern = r"\$()"  # Match a '$' followed by an empty group
        match = re.match( pattern, "$" )

        result = populated_handler( match )
        assert result == ""
