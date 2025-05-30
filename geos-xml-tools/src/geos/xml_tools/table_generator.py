import numpy as np
from typing import Tuple, Iterable, Dict

__doc__ = """Tools for reading/writing GEOSX ascii tables."""


def write_GEOS_table( axes_values: Iterable[ np.ndarray ],
                      properties: Dict[ str, np.ndarray ],
                      axes_names: Iterable[ str ] = [ 'x', 'y', 'z', 't' ],
                      string_format: str = '%1.5e' ) -> None:
    """Write an GEOS-compatible ascii table.

    Args:
        axes_values (list): List of arrays containing the coordinates for each axis of the table.
        properties (dict): Dict of arrays with dimensionality/size defined by the axes_values
        axes_names (list): Names for each axis (default = ['x', 'y', 'z', 't'])
        string_format (str): Format for output values (default = %1.5e)
    """
    # Check to make sure the axes/property files have the correct shape
    axes_shape = tuple( [ len( x ) for x in axes_values ] )
    for k in properties:
        if ( np.shape( properties[ k ] ) != axes_shape ):
            raise Exception( "Shape of parameter %s is incompatible with given axes" % ( k ) )

    # Write axes files
    for ka, x in zip( axes_names, axes_values, strict=False ):
        np.savetxt( '%s.geos' % ( ka ), x, fmt=string_format, delimiter=',' )

    # Write property files
    for k in properties:
        tmp = np.reshape( properties[ k ], ( -1 ), order='F' )
        np.savetxt( '%s.geos' % ( k ), tmp, fmt=string_format, delimiter=',' )


def read_GEOS_table( axes_files: Iterable[ str ],
                     property_files: Iterable[ str ] ) -> Tuple[ Iterable[ np.ndarray ], Dict[ str, np.ndarray ] ]:
    """Read an GEOS-compatible ascii table.

    Args:
        axes_files (list): List of the axes file names in order.
        property_files (list): List of property file names

    Returns:
        tuple: List of axis definitions, dict of property values
    """
    axes_values = []
    for f in axes_files:
        axes_values.append( np.loadtxt( '%s.geos' % ( f ), unpack=True, delimiter=',' ) )
    axes_shape = tuple( [ len( x ) for x in axes_values ] )

    # Open property files
    properties = {}
    for f in property_files:
        tmp = np.loadtxt( '%s.geos' % ( f ), unpack=True, delimiter=',' )
        properties[ f ] = np.reshape( tmp, axes_shape, order='F' )

    return axes_values, properties


def write_read_GEOS_table_example() -> None:
    """Table read / write example."""
    # Define table axes
    a = np.array( [ 0.0, 1.0 ] )
    b = np.array( [ 0.0, 0.5, 1.0 ] )
    axes_values = [ a, b ]

    # Generate table values (note: the indexing argument is important)
    A, B = np.meshgrid( a, b, indexing='ij' )
    properties = { 'c': A + 2.0 * B }

    # Write, then read tables
    write_GEOS_table( axes_values, properties, axes_names=[ 'a', 'b' ] )
    axes_b, properties_b = read_GEOS_table( [ 'a', 'b' ], [ 'c' ] )
