# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file

from enum import Enum

from typing_extensions import Self


class OptionSelectionEnum( Enum ):

    def __init__( self: Self, displayName: str, optionValue: str ) -> None:
        """Define the enumeration to options for Paraview selectors.

        Args:
            displayName (str): name displayed in the selector
            optionValue (str): value used by matplotlib.

                Defaults to None (same optionName as displayName)
        """
        self.displayName: str = displayName
        self.optionValue: str = optionValue


class LegendLocationEnum( OptionSelectionEnum ):
    BEST = ( "best", "best" )
    UPPER_LEFT = ( "upper left", "upper left" )
    UPPER_CENTER = ( "upper center", "upper center" )
    UPPER_RIGHT = ( "upper right", "upper right" )
    CENTER_LEFT = ( "center left", "center left" )
    CENTER = ( "center", "center" )
    CENTER_RIGHT = ( "center right", "center right" )
    LOWER_LEFT = ( "lower left", "lower left" )
    LOWER_CENTER = ( "lower center", "lower center" )
    LOWER_RIGHT = ( "lower right", "lower right" )


class FontStyleEnum( OptionSelectionEnum ):
    NORMAL = ( "normal", "normal" )
    ITALIC = ( "italic", "italic" )
    OBLIQUE = ( "oblique", "oblique" )


class FontWeightEnum( OptionSelectionEnum ):
    NORMAL = ( "normal", "normal" )
    BOLD = ( "bold", "bold" )
    HEAVY = ( "heavy", "heavy" )
    LIGHT = ( "light", "light" )


class LineStyleEnum( OptionSelectionEnum ):
    NONE = ( "None", "None" )
    SOLID = ( "solid", "-" )
    DASHED = ( "dashed", "--" )
    DASHDOT = ( "dashdot", "-." )
    DOTTED = ( "dotted", ":" )


class MarkerStyleEnum( OptionSelectionEnum ):
    NONE = ( "None", "" )
    POINT = ( "point", "." )
    CIRCLE = ( "circle", "o" )
    TRIANGLE = ( "triangle", "^" )
    SQUARE = ( "square", "s" )
    STAR = ( "star", "*" )
    DIAMOND = ( "diamond", "D" )
    PLUS = ( "plus", "+" )
    X = ( "x", "x" )


def optionEnumToXml( enumObj: OptionSelectionEnum ) -> str:
    """Creates an enumeration domain from an OptionSelectionEnum object.

    Dedicated to the dropdown widgets of paraview plugin.

    Args:
        enumObj (OptionSelectionEnum): Enumeration values to put in the dropdown
            widget.

    Returns:
        str: the XML string.
    """
    xml: str = """<EnumerationDomain name='enum'>"""
    for i, unitObj in enumerate( list( enumObj ) ):  # type: ignore[call-overload]
        xml += f"""<Entry text='{unitObj.displayName}' value='{i}'/>"""
    xml += """</EnumerationDomain>"""
    return xml
