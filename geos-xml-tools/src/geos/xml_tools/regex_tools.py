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
import re

__doc__ = """
Regular Expression Utilities for geos-xml-tools.

This module defines and manages regex patterns used throughout the package for:
* Parameter substitution
* Unit recognition and conversion
* Symbolic math evaluation
* String sanitization and formatting

Pattern         |  Example targets             | Notes
------------------------------------------------------------------------------------
parameters      | $Parameter, $Parameter$      | Matches entire parameter string
units           | 9.81[m**2/s],  1.0 [bbl/day] | Matches entire unit string
units_b         | m, bbl, day                  | Matches unit names
symbolic        | `1 + 2.34e5*2`               | Matches the entire symbolic string
sanitize        |                              | Removes any residual characters before evaluating symbolic expressions
strip_trailing  | 3.0000, 5.150050             | Removes unnecessary float strings
strip_trailing_b| 3.0000e0, 1.23e0             | Removes unnecessary float strings

Intended for internal use by XML processing and unit management tools.
"""

patterns: dict[ str, str ] = {
    'parameters': r"\$:?([a-zA-Z_0-9]*)\$?",
    'units': r"([0-9]*?\.?[0-9]+(?:[eE][-+]?[0-9]*?)?)\ *?\[([-+.*/()a-zA-Z0-9]*)\]",
    'units_b': r"([a-zA-Z]*)",
    'symbolic': r"\`([-+.*/() 0-9eE]*)\`",
    'sanitize': r"[a-z-[e]A-Z-[E]]",
    'strip_trailing': r"\.?0+(?=e)",
    'strip_trailing_b': r"e\+00|\+0?|(?<=-)0"
}

# String formatting for symbolic expressions
symbolic_format = '%1.6e'


def SymbolicMathRegexHandler( match: re.Match ) -> str:
    """Evaluate symbolic expressions that are identified using the regex_tools.patterns['symbolic'].

    Args:
        match (re.match): A matching string identified by the regex.
    """
    k = match.group( 1 )
    if k:
        # Sanitize the input
        sanitized = re.sub( patterns[ 'sanitize' ], '', k ).strip()
        value = eval( sanitized, { '__builtins__': None } )

        # Format the string, removing any trailing zeros, decimals, etc.
        str_value = re.sub( patterns[ 'strip_trailing' ], '', symbolic_format % ( value ) )
        str_value = re.sub( patterns[ 'strip_trailing_b' ], '', str_value )
        return str_value
    else:
        return ''


class DictRegexHandler():
    """This class is used to substitute matched values with those stored in a dict."""

    def __init__( self ) -> None:
        """Initialize the handler with an empty target list.

        The key/value pairs of self.target indicate which values
        to look for and the values they will replace with.
        """
        self.target: dict[ str, str ] = {}

    def __call__( self, match: re.Match ) -> str:
        """Replace the matching strings with their target.

        Args:
            match (re.match): A matching string identified by the regex.
        """
        k = match.group( 1 )
        if k:
            if ( k not in self.target ):
                raise Exception( 'Error: Target (%s) is not defined in the regex handler' % k )
            value = self.target[ k ]
            return str( value )
        else:
            return ''
