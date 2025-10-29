# ------------------------------------------------------------------------------------------------------------
# SPDX-License-Identifier: LGPL-2.1-only
#
# Copyright (c) 2016-2024 Lawrence Livermore National Security LLC
# Copyright (c) 2018-2024 TotalEnergies
# Copyright (c) 2018-2024 The Board of Trustees of the Leland Stanford Junior University
# Copyright (c) 2023-2024 Chevron
# Copyright (c) 2019-     GEOS/GEOSX Contributors
# All rights reserved
#
# See top level LICENSE, COPYRIGHT, CONTRIBUTORS, NOTICE, and ACKNOWLEDGEMENTS files for details.
# ------------------------------------------------------------------------------------------------------------
import numpy as np
from typing import Iterable

__doc__ = """
Multi-dimensional Table I/O for GEOS.

This module provides tools to save and load multi-dimensional data tables to and from .geos file extensions.
Features:
* Write GEOS-compatible ASCII tables for axes and properties.
* Read tables back into numpy arrays for analysis or simulation.

Typical usage:
    from geos.xml_tools.table_generator import write_GEOS_table, read_GEOS_table

Intended for use in workflows that require tabular data exchange with GEOS.
"""


def write_GEOS_table( axes_values: Iterable[ np.ndarray ],
                      properties: dict[ str, np.ndarray ],
                      axes_names: Iterable[ str ] = [ 'x', 'y', 'z', 't' ],
                      string_format: str = '%1.5e' ) -> None:
    """Write a GEOS-compatible ascii table.

    Args:
        axes_values (list): List of arrays containing the coordinates for each axis of the table.
        properties (dict): dict of arrays with dimensionality/size defined by the axes_values
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
                     property_files: Iterable[ str ] ) -> tuple[ Iterable[ np.ndarray ], dict[ str, np.ndarray ] ]:
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
