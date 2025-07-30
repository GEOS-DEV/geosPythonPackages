import pytest
import numpy as np
import os
from geos.xml_tools import table_generator


class TestGEOS_Table:
    """A test suite for the GEOS table read/write functions."""

    @pytest.fixture
    def sample_data( self ):
        """Provides a reusable set of sample axes and properties for tests."""
        # Define table axes (e.g., 2x3 grid)
        a = np.array( [ 10.0, 20.0 ] )
        b = np.array( [ 1.0, 2.0, 3.0 ] )
        axes_values = [ a, b ]

        # Generate a corresponding property value for each point on the grid
        A, B = np.meshgrid( a, b, indexing='ij' )
        properties = { 'porosity': A * 0.1 + B }  # e.g., porosity = [[2, 3, 4], [3, 4, 5]]

        return {
            "axes_values": axes_values,
            "properties": properties,
            "axes_names": [ 'a', 'b' ],
            "property_names": [ 'porosity' ]
        }

    def test_write_read_round_trip( self, tmp_path, sample_data ):
        """
        Tests that writing a table and reading it back results in the original data.
        """
        # Change to the temporary directory to work with files
        os.chdir( tmp_path )

        # Write the GEOS table files
        table_generator.write_GEOS_table( axes_values=sample_data[ "axes_values" ],
                                          properties=sample_data[ "properties" ],
                                          axes_names=sample_data[ "axes_names" ] )

        # Check that the files were actually created
        assert os.path.exists( "a.geos" )
        assert os.path.exists( "b.geos" )
        assert os.path.exists( "porosity.geos" )

        # Read the GEOS table files back
        read_axes, read_properties = table_generator.read_GEOS_table( axes_files=sample_data[ "axes_names" ],
                                                                      property_files=sample_data[ "property_names" ] )

        # Compare axes
        original_axes = sample_data[ "axes_values" ]
        assert len( read_axes ) == len( original_axes )
        for i in range( len( read_axes ) ):
            np.testing.assert_allclose( read_axes[ i ], original_axes[ i ] )

        # Compare properties
        original_properties = sample_data[ "properties" ]
        assert len( read_properties ) == len( original_properties )
        for key in original_properties:
            np.testing.assert_allclose( read_properties[ key ], original_properties[ key ] )

    def test_write_fails_on_shape_mismatch( self, sample_data ):
        """
        Tests that write_GEOS_table raises an exception if property and axis shapes
        are incompatible.
        """
        # Create a property with a deliberately incorrect shape (2x2 instead of 2x3)
        bad_properties = { 'porosity': np.array( [ [ 1, 2 ], [ 3, 4 ] ] ) }

        with pytest.raises( Exception, match="Shape of parameter porosity is incompatible with given axes" ):
            table_generator.write_GEOS_table( axes_values=sample_data[ "axes_values" ], properties=bad_properties )
