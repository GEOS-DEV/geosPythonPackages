# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
import math
from typing import Any

import matplotlib.pyplot as plt  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
from matplotlib import axes, figure, lines  # type: ignore[import-untyped]
from matplotlib.font_manager import (  # type: ignore[import-untyped]
    FontProperties,  # type: ignore[import-untyped]
)

import geos_posp.processing.geosLogReaderFunctions as fcts
"""
Plotting tools for 2D figure and axes generation.
"""


def oneSubplot(
        df: pd.DataFrame,
        userChoices: dict[ str, Any ] ) -> tuple[ figure.Figure, list[ axes.Axes ], list[ lines.Line2D ], list[ str ] ]:
    """Created a single subplot.

    From a dataframe, knowing which curves to plot along which variable,
    generates a fig and its list of axes with the data plotted.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName"
        userChoices (dict[str, Any]): Choices made by widget selection
            in PythonViewConfigurator filter.

    Returns:
        tuple[figure.Figure, list[axes.Axes],
        list[lines.Line2D] , list[str]]: the fig and its list of axes.
    """
    curveNames: list[ str ] = userChoices[ "curveNames" ]
    variableName: str = userChoices[ "variableName" ]
    curvesAspect: dict[ str, tuple[ tuple[ float, float, float ], str, float, str,
                                    float ] ] = userChoices[ "curvesAspect" ]
    associatedProperties: dict[ str, list[ str ] ] = associatePropertyToAxeType( curveNames )
    fig, ax = plt.subplots( constrained_layout=True )
    all_ax: list[ axes.Axes ] = setupAllAxes( ax, variableName, associatedProperties, True )
    lineList: list[ lines.Line2D ] = []
    labels: list[ str ] = []
    cpt_cmap: int = 0
    x: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
    for cpt_ax, ( ax_name, propertyNames ) in enumerate( associatedProperties.items() ):
        ax_to_use: axes.Axes = setupAxeToUse( all_ax, cpt_ax, ax_name, False )
        for propName in propertyNames:
            y: npt.NDArray[ np.float64 ] = df[ propName ].to_numpy()
            plotAxe( ax_to_use, x, y, propName, cpt_cmap, curvesAspect )
            cpt_cmap += 1
        new_lines, new_labels = ax_to_use.get_legend_handles_labels()
        lineList += new_lines  # type: ignore[arg-type]
        labels += new_labels
    labels, lineList = smartLabelsSorted( labels, lineList, userChoices )
    if userChoices[ "displayLegend" ]:
        ax.legend(
            lineList,
            labels,
            loc=userChoices[ "legendPosition" ],
            fontsize=userChoices[ "legendSize" ],
        )
    ax.grid()
    return ( fig, all_ax, lineList, labels )


def oneSubplotInverted(
        df: pd.DataFrame,
        userChoices: dict[ str, Any ] ) -> tuple[ figure.Figure, list[ axes.Axes ], list[ lines.Line2D ], list[ str ] ]:
    """Created a single subplot with inverted X Y axes.

    From a dataframe, knowing which curves to plot along which variable,
    generates a fig and its list of axes with the data plotted.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName"
        userChoices (dict[str, Any]): Choices made by widget selection
            in PythonViewConfigurator filter.

    Returns:
        tuple[figure.Figure, list[axes.Axes],
        list[lines.Line2D] , list[str]]: the fig and its list of axes.
    """
    curveNames: list[ str ] = userChoices[ "curveNames" ]
    variableName: str = userChoices[ "variableName" ]
    curvesAspect: dict[ str, tuple[ tuple[ float, float, float ], str, float, str,
                                    float ] ] = userChoices[ "curvesAspect" ]
    associatedProperties: dict[ str, list[ str ] ] = associatePropertyToAxeType( curveNames )
    fig, ax = plt.subplots( constrained_layout=True )
    all_ax: list[ axes.Axes ] = setupAllAxes( ax, variableName, associatedProperties, False )
    linesList: list[ lines.Line2D ] = []
    labels: list[ str ] = []
    cpt_cmap: int = 0
    y: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
    for cpt_ax, ( ax_name, propertyNames ) in enumerate( associatedProperties.items() ):
        ax_to_use: axes.Axes = setupAxeToUse( all_ax, cpt_ax, ax_name, True )
        for propName in propertyNames:
            x: npt.NDArray[ np.float64 ] = df[ propName ].to_numpy()
            plotAxe( ax_to_use, x, y, propName, cpt_cmap, curvesAspect )
            cpt_cmap += 1
        new_lines, new_labels = ax_to_use.get_legend_handles_labels()
        linesList += new_lines  # type: ignore[arg-type]
        labels += new_labels
    labels, linesList = smartLabelsSorted( labels, linesList, userChoices )
    if userChoices[ "displayLegend" ]:
        ax.legend(
            linesList,
            labels,
            loc=userChoices[ "legendPosition" ],
            fontsize=userChoices[ "legendSize" ],
        )
    ax.grid()
    return ( fig, all_ax, linesList, labels )


def multipleSubplots(
        df: pd.DataFrame,
        userChoices: dict[ str, Any ] ) -> tuple[ figure.Figure, list[ axes.Axes ], list[ lines.Line2D ], list[ str ] ]:
    """Created multiple subplots.

    From a dataframe, knowing which curves to plot along which variable,
    generates a fig and its list of axes with the data plotted.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName".
        userChoices (dict[str, Any]): Choices made by widget selection
            in PythonViewConfigurator filter.

    Returns:
        tuple[figure.Figure, list[axes.Axes],
        list[lines.Line2D] , list[str]]: the fig and its list of axes.
    """
    curveNames: list[ str ] = userChoices[ "curveNames" ]
    variableName: str = userChoices[ "variableName" ]
    curvesAspect: dict[ str, tuple[ tuple[ float, float, float ], str, float, str,
                                    float ] ] = userChoices[ "curvesAspect" ]
    ratio: float = userChoices[ "ratio" ]
    assosIdentifiers: dict[ str, dict[ str, list[ str ] ] ] = associationIdentifiers( curveNames )
    nbr_suplots: int = len( assosIdentifiers.keys() )
    # if only one subplots needs to be created
    if nbr_suplots == 1:
        return oneSubplot( df, userChoices )

    layout: tuple[ int, int, int ] = smartLayout( nbr_suplots, ratio )
    fig, axs0 = plt.subplots( layout[ 0 ], layout[ 1 ], constrained_layout=True )
    axs: list[ axes.Axes ] = axs0.flatten().tolist()  # type: ignore[union-attr]
    for i in range( layout[ 2 ] ):
        fig.delaxes( axs[ -( i + 1 ) ] )
    all_lines: list[ lines.Line2D ] = []
    all_labels: list[ str ] = []
    # first loop for subplots
    propertiesExtremas: dict[ str, tuple[ float, float ] ] = ( findExtremasPropertiesForAssociatedIdentifiers(
        df, assosIdentifiers, True ) )
    for j, identifier in enumerate( assosIdentifiers.keys() ):
        first_ax: axes.Axes = axs[ j ]
        associatedProperties: dict[ str, list[ str ] ] = assosIdentifiers[ identifier ]
        all_ax: list[ axes.Axes ] = setupAllAxes( first_ax, variableName, associatedProperties, True )
        axs += all_ax[ 1: ]
        linesList: list[ lines.Line2D ] = []
        labels: list[ str ] = []
        cpt_cmap: int = 0
        x: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
        # second loop for axes per subplot
        for cpt_ax, ( ax_name, propertyNames ) in enumerate( associatedProperties.items() ):
            ax_to_use: axes.Axes = setupAxeToUse( all_ax, cpt_ax, ax_name, False )
            for propName in propertyNames:
                y: npt.NDArray[ np.float64 ] = df[ propName ].to_numpy()
                plotAxe( ax_to_use, x, y, propName, cpt_cmap, curvesAspect )
                ax_to_use.set_ylim( *propertiesExtremas[ ax_name ] )
                cpt_cmap += 1
            new_lines, new_labels = ax_to_use.get_legend_handles_labels()
            linesList += new_lines  # type: ignore[arg-type]
            all_lines += new_lines  # type: ignore[arg-type]
            labels += new_labels
            all_labels += new_labels
        labels, linesList = smartLabelsSorted( labels, linesList, userChoices )
        if userChoices[ "displayLegend" ]:
            first_ax.legend(
                linesList,
                labels,
                loc=userChoices[ "legendPosition" ],
                fontsize=userChoices[ "legendSize" ],
            )
        if userChoices[ "displayTitle" ]:
            first_ax.set_title( identifier, fontsize=10 )
        first_ax.grid()
    return ( fig, axs, all_lines, all_labels )


def multipleSubplotsInverted(
        df: pd.DataFrame,
        userChoices: dict[ str, Any ] ) -> tuple[ figure.Figure, list[ axes.Axes ], list[ lines.Line2D ], list[ str ] ]:
    """Created multiple subplots with inverted X Y axes.

    From a dataframe, knowing which curves to plot along which variable,
    generates a fig and its list of axes with the data plotted.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName".
        userChoices (dict[str, Any]): Choices made by widget selection
            in PythonViewConfigurator filter.

    Returns:
        tuple[figure.Figure, list[axes.Axes],
        list[lines.Line2D] , list[str]]: the fig and its list of axes.
    """
    curveNames: list[ str ] = userChoices[ "curveNames" ]
    variableName: str = userChoices[ "variableName" ]
    curvesAspect: dict[ str, tuple[ tuple[ float, float, float ], str, float, str,
                                    float ] ] = userChoices[ "curvesAspect" ]
    ratio: float = userChoices[ "ratio" ]
    assosIdentifiers: dict[ str, dict[ str, list[ str ] ] ] = associationIdentifiers( curveNames )
    nbr_suplots: int = len( assosIdentifiers.keys() )
    # if only one subplots needs to be created
    if nbr_suplots == 1:
        return oneSubplotInverted( df, userChoices )

    layout: tuple[ int, int, int ] = smartLayout( nbr_suplots, ratio )
    fig, axs0 = plt.subplots( layout[ 0 ], layout[ 1 ], constrained_layout=True )
    axs: list[ axes.Axes ] = axs0.flatten().tolist()  # type: ignore[union-attr]
    for i in range( layout[ 2 ] ):
        fig.delaxes( axs[ -( i + 1 ) ] )
    all_lines: list[ lines.Line2D ] = []
    all_labels: list[ str ] = []
    # first loop for subplots
    propertiesExtremas: dict[ str, tuple[ float, float ] ] = ( findExtremasPropertiesForAssociatedIdentifiers(
        df, assosIdentifiers, True ) )
    for j, identifier in enumerate( assosIdentifiers.keys() ):
        first_ax: axes.Axes = axs[ j ]
        associatedProperties: dict[ str, list[ str ] ] = assosIdentifiers[ identifier ]
        all_ax: list[ axes.Axes ] = setupAllAxes( first_ax, variableName, associatedProperties, False )
        axs += all_ax[ 1: ]
        linesList: list[ lines.Line2D ] = []
        labels: list[ str ] = []
        cpt_cmap: int = 0
        y: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
        # second loop for axes per subplot
        for cpt_ax, ( ax_name, propertyNames ) in enumerate( associatedProperties.items() ):
            ax_to_use: axes.Axes = setupAxeToUse( all_ax, cpt_ax, ax_name, True )
            for propName in propertyNames:
                x: npt.NDArray[ np.float64 ] = df[ propName ].to_numpy()
                plotAxe( ax_to_use, x, y, propName, cpt_cmap, curvesAspect )
                ax_to_use.set_xlim( propertiesExtremas[ ax_name ] )
                cpt_cmap += 1
            new_lines, new_labels = ax_to_use.get_legend_handles_labels()
            linesList += new_lines  # type: ignore[arg-type]
            all_lines += new_lines  # type: ignore[arg-type]
            labels += new_labels
            all_labels += new_labels
        labels, linesList = smartLabelsSorted( labels, linesList, userChoices )
        if userChoices[ "displayLegend" ]:
            first_ax.legend(
                linesList,
                labels,
                loc=userChoices[ "legendPosition" ],
                fontsize=userChoices[ "legendSize" ],
            )
        if userChoices[ "displayTitle" ]:
            first_ax.set_title( identifier, fontsize=10 )
        first_ax.grid()
    return ( fig, axs, all_lines, all_labels )


def setupAllAxes(
    first_ax: axes.Axes,
    variableName: str,
    associatedProperties: dict[ str, list[ str ] ],
    axisX: bool,
) -> list[ axes.Axes ]:
    """Modify axis name and ticks avec X or Y axis of all subplots.

    Args:
        first_ax (axes.Axes): subplot id.
        variableName (str): name of the axis.
        associatedProperties (dict[str, list[str]]): Name of the properties
        axisX (bool): X (True) or Y (False) axis to modify.

    Returns:
        list[axes.Axes]: modified subplots
    """
    all_ax: list[ axes.Axes ] = [ first_ax ]
    if axisX:
        first_ax.set_xlabel( variableName )
        first_ax.ticklabel_format( style="sci", axis="x", scilimits=( 0, 0 ), useMathText=True )
        for i in range( 1, len( associatedProperties.keys() ) ):
            second_ax = first_ax.twinx()
            assert isinstance( second_ax, axes.Axes )
            all_ax.append( second_ax )
            all_ax[ i ].spines[ "right" ].set_position( ( "axes", 1 + 0.07 * ( i - 1 ) ) )
            all_ax[ i ].tick_params( axis="y", which="both", left=False, right=True )
            all_ax[ i ].yaxis.set_ticks_position( "right" )
            all_ax[ i ].yaxis.offsetText.set_position( ( 1.04 + 0.07 * ( i - 1 ), 0 ) )
        first_ax.yaxis.offsetText.set_position( ( -0.04, 0 ) )
    else:
        first_ax.set_ylabel( variableName )
        first_ax.ticklabel_format( style="sci", axis="y", scilimits=( 0, 0 ), useMathText=True )
        for i in range( 1, len( associatedProperties.keys() ) ):
            second_ax = first_ax.twiny()
            assert isinstance( second_ax, axes.Axes )
            all_ax.append( second_ax )
            all_ax[ i ].spines[ "bottom" ].set_position( ( "axes", -0.08 * i ) )
            all_ax[ i ].xaxis.set_label_position( "bottom" )
            all_ax[ i ].tick_params( axis="x", which="both", bottom=True, top=False )
            all_ax[ i ].xaxis.set_ticks_position( "bottom" )
    return all_ax


def setupAxeToUse( all_ax: list[ axes.Axes ], axeId: int, ax_name: str, axisX: bool ) -> axes.Axes:
    """Modify axis name and ticks avec X or Y axis of subplot axeId in all_ax.

    Args:
        all_ax (list[axes.Axes]): list of all subplots
        axeId (int): id of the subplot
        ax_name (str): name of the X or Y axis
        axisX (bool): X (True) or Y (False) axis to modify.

    Returns:
        axes.Axes: modified subplot
    """
    ax_to_use: axes.Axes = all_ax[ axeId ]
    if axisX:
        ax_to_use.set_xlabel( ax_name )
        ax_to_use.ticklabel_format( style="sci", axis="x", scilimits=( 0, 0 ), useMathText=True )
    else:
        ax_to_use.set_ylabel( ax_name )
        ax_to_use.ticklabel_format( style="sci", axis="y", scilimits=( 0, 0 ), useMathText=True )
    return ax_to_use


def plotAxe(
    ax_to_use: axes.Axes,
    x: npt.NDArray[ np.float64 ],
    y: npt.NDArray[ np.float64 ],
    propertyName: str,
    cpt_cmap: int,
    curvesAspect: dict[ str, tuple[ tuple[ float, float, float ], str, float, str, float ] ],
) -> None:
    """Plot x, y data using input ax_to_use according to curvesAspect.

    Args:
        ax_to_use (axes.Axes): subplot to use
        x (npt.NDArray[np.float64]): abscissa data
        y (npt.NDArray[np.float64]): ordinate data
        propertyName (str): name of the property
        cpt_cmap (int): colormap to use
        curvesAspect (dict[str, tuple[tuple[float, float, float],str, float, str, float]]):
            user choices on curve aspect
    """
    cmap = plt.rcParams[ "axes.prop_cycle" ].by_key()[ "color" ][ cpt_cmap % 10 ]
    mask = np.logical_and( np.isnan( x ), np.isnan( y ) )
    not_mask = ~mask
    # Plot only when x and y values are not nan values
    if propertyName in curvesAspect:
        asp: tuple[ tuple[ float, float, float ], str, float, str, float ] = curvesAspect[ propertyName ]
        ax_to_use.plot(
            x[ not_mask ],
            y[ not_mask ],
            label=propertyName,
            color=asp[ 0 ],
            linestyle=asp[ 1 ],
            linewidth=asp[ 2 ],
            marker=asp[ 3 ],
            markersize=asp[ 4 ],
        )
    else:
        ax_to_use.plot( x[ not_mask ], y[ not_mask ], label=propertyName, color=cmap )


def getExtremaAllAxes( axes: list[ axes.Axes ], ) -> tuple[ tuple[ float, float ], tuple[ float, float ] ]:
    """Gets the limits of both X and Y axis as a 2x2 element tuple.

    Args:
        axes (list[axes.Axes]): list of subplots to get limits.

    Returns:
        tuple[tuple[float, float], tuple[float, float]]:: ((xMin, xMax), (yMin, yMax))
    """
    assert len( axes ) > 0
    xMin, xMax, yMin, yMax = getAxeLimits( axes[ 0 ] )
    if len( axes ) > 1:
        for i in range( 1, len( axes ) ):
            x1, x2, y1, y2 = getAxeLimits( axes[ i ] )
            if x1 < xMin:
                xMin = x1
            if x2 > xMax:
                xMax = x2
            if y1 < yMin:
                yMin = y1
            if y2 > yMax:
                yMax = y2
    return ( ( xMin, xMax ), ( yMin, yMax ) )


def getAxeLimits( ax: axes.Axes ) -> tuple[ float, float, float, float ]:
    """Gets the limits of both X and Y axis as a 4 element tuple.

    Args:
        ax (axes.Axes): subplot to get limits.

    Returns:
        tuple[float, float, float, float]: (xMin, xMax, yMin, yMax)
    """
    xMin, xMax = ax.get_xlim()
    yMin, yMax = ax.get_ylim()
    return ( xMin, xMax, yMin, yMax )


def findExtremasPropertiesForAssociatedIdentifiers(
    df: pd.DataFrame,
    associatedIdentifiers: dict[ str, dict[ str, list[ str ] ] ],
    offsetPlotting: bool = False,
    offsetPercentage: int = 5,
) -> dict[ str, tuple[ float, float ] ]:
    """Find min and max of all properties linked to a same identifier.

    Using an associatedIdentifiers dict containing associatedProperties dict,
    we can find the extremas for each property of each identifier. Once we have them all,
    we compare for each identifier what are the most extreme values and only the biggest and
    lowest are kept in the end.


    Args:
        df (pd.DataFrame): Pandas dataframe
        associatedIdentifiers (dict[str, dict[str, list[str]]]): property identifiers.
        offsetPlotting (bool, optional): When using the values being returned,
            we might want to add an offset to these values. If set to True,
            the offsetPercentage is taken into account. Defaults to False.
        offsetPercentage (int, optional): Value by which we will offset
            the min and max values of each tuple of floats. Defaults to 5.

    Returns:
        dict[str, tuple[float, float]]: {
        "BHP (Pa)": (minAllWells, maxAllWells),
        "TotalMassRate (kg)": (minAllWells, maxAllWells),
        "TotalSurfaceVolumetricRate (m3/s)": (minAllWells, maxAllWells),
        "SurfaceVolumetricRateCO2 (m3/s)": (minAllWells, maxAllWells),
        "SurfaceVolumetricRateWater (m3/s)": (minAllWells, maxAllWells)
        }
    """
    extremasProperties: dict[ str, tuple[ float, float ] ] = {}
    # first we need to find the extrema for each property type per region
    propertyTypesExtremas: dict[ str, list[ tuple[ float, float ] ] ] = {}
    for associatedProperties in associatedIdentifiers.values():
        extremasPerProperty: dict[ str,
                                   tuple[ float,
                                          float ] ] = ( findExtremasAssociatedProperties( df, associatedProperties ) )
        for propertyType, extremaFound in extremasPerProperty.items():
            if propertyType not in propertyTypesExtremas:
                propertyTypesExtremas[ propertyType ] = [ extremaFound ]
            else:
                propertyTypesExtremas[ propertyType ].append( extremaFound )
    # then, once all extrema have been found for all regions, we need to figure out
    # which extrema per property type is the most extreme one
    for propertyType in propertyTypesExtremas:
        values: list[ tuple[ float, float ] ] = propertyTypesExtremas[ propertyType ]
        minValues: list[ float ] = [ values[ i ][ 0 ] for i in range( len( values ) ) ]
        maxValues: list[ float ] = [ values[ i ][ 1 ] for i in range( len( values ) ) ]
        lowest, highest = ( min( minValues ), max( maxValues ) )
        if offsetPlotting:
            offset: float = ( highest - lowest ) / 100 * offsetPercentage
            lowest, highest = ( lowest - offset, highest + offset )
        extremasProperties[ propertyType ] = ( lowest, highest )
    return extremasProperties


def findExtremasAssociatedProperties(
        df: pd.DataFrame, associatedProperties: dict[ str, list[ str ] ] ) -> dict[ str, tuple[ float, float ] ]:
    """Find the min and max of properties.

    Using an associatedProperties dict containing property types
    as keys and a list of property names as values,
    and a pandas dataframe whose column names are composed of those same
    property names, you can find the min and max values of each property
    type and return it as a tuple.

    Args:
        df (pd.DataFrame): Pandas dataframe
        associatedProperties (dict[str, list[str]]): {
            "Pressure (Pa)": ["Reservoir__Pressure__Pa__Source1"],
            "Mass (kg)": ["CO2__Mass__kg__Source1",
            "Water__Mass__kg__Source1"]
            }

    Returns:
        dict[str, tuple[float, float]]: {
        "Pressure (Pa)": (minPressure, maxPressure),
        "Mass (kg)": (minMass, maxMass)
        }
    """
    extremasProperties: dict[ str, tuple[ float, float ] ] = {}
    for propertyType, propertyNames in associatedProperties.items():
        minValues = np.empty( len( propertyNames ) )
        maxValues = np.empty( len( propertyNames ) )
        for i, propertyName in enumerate( propertyNames ):
            values: npt.NDArray[ np.float64 ] = df[ propertyName ].to_numpy()
            minValues[ i ] = np.nanmin( values )
            maxValues[ i ] = np.nanmax( values )
        extrema: tuple[ float, float ] = (
            float( np.min( minValues ) ),
            float( np.max( maxValues ) ),
        )
        extremasProperties[ propertyType ] = extrema
    return extremasProperties


"""
Utils for treatment of the data
"""


def associatePropertyToAxeType( propertyNames: list[ str ] ) -> dict[ str, list[ str ] ]:
    """Identify property types.

    From a list of property names, identify if each of this property
    corresponds to a certain property type like "Pressure", "Mass",
    "Temperature" etc ... and returns a dict where the keys are the property
    type and the value the list of property names associated to it.

    Args:
        propertyNames (list[str]): ["Reservoir__Pressure__Pa__Source1",
            "CO2__Mass__kg__Source1", "Water__Mass__kg__Source1"]

    Returns:
        dict[str, list[str]]: { "Pressure (Pa)": ["Reservoir__Pressure__Pa__Source1"],
            "Mass (kg)": ["CO2__Mass__kg__Source1",
            "Water__Mass__kg__Source1"] }
    """
    propertyIds: list[ str ] = fcts.identifyProperties( propertyNames )
    associationTable: dict[ str, str ] = {
        "0": "Pressure",
        "1": "Pressure",
        "2": "Temperature",
        "3": "PoreVolume",
        "4": "PoreVolume",
        "5": "Mass",
        "6": "Mass",
        "7": "Mass",
        "8": "Mass",
        "9": "Mass",
        "10": "Mass",
        "11": "BHP",
        "12": "MassRate",
        "13": "VolumetricRate",
        "14": "VolumetricRate",
        "15": "BHP",
        "16": "MassRate",
        "17": "VolumetricRate",
        "18": "VolumetricRate",
        "19": "VolumetricRate",
        "20": "Volume",
        "21": "VolumetricRate",
        "22": "Volume",
        "23": "Iterations",
        "24": "Iterations",
        "25": "Stress",
        "26": "Displacement",
        "27": "Permeability",
        "28": "Porosity",
        "29": "Ratio",
        "30": "Fraction",
        "31": "BulkModulus",
        "32": "ShearModulus",
        "33": "OedometricModulus",
        "34": "Points",
        "35": "Density",
        "36": "Mass",
        "37": "Mass",
        "38": "Time",
        "39": "Time",
    }
    associatedPropertyToAxeType: dict[ str, list[ str ] ] = {}
    noUnitProperties: list[ str ] = [
        "Iterations",
        "Porosity",
        "Ratio",
        "Fraction",
        "OedometricModulus",
    ]
    for i, propId in enumerate( propertyIds ):
        idProp: str = propId.split( ":" )[ 0 ]
        propNoId: str = propId.split( ":" )[ 1 ]
        associatedType: str = associationTable[ idProp ]
        if associatedType in noUnitProperties:
            axeName: str = associatedType
        else:
            propIdElts: list[ str ] = propNoId.split( "__" )
            # no unit was found
            if len( propIdElts ) <= 2:
                axeName = associatedType
            # there is a unit
            else:
                unit: str = propIdElts[ -2 ]
                axeName = associatedType + " (" + unit + ")"
        if axeName not in associatedPropertyToAxeType:
            associatedPropertyToAxeType[ axeName ] = []
        associatedPropertyToAxeType[ axeName ].append( propertyNames[ i ] )
    return associatedPropertyToAxeType


def propertiesPerIdentifier( propertyNames: list[ str ] ) -> dict[ str, list[ str ] ]:
    """Extract identifiers with associatied properties.

    From a list of property names, extracts the identifier (name of the
    region for flow property or name of a well for well property) and creates
    a dictionnary with identifiers as keys and the properties containing them
    for value in a list.

    Args:
        propertyNames (list[str]): property names
            Example

            .. code-block:: python

                [
                "WellControls1__BHP__Pa__Source1",
                "WellControls1__TotalMassRate__kg/s__Source1",
                "WellControls2__BHP__Pa__Source1",
                "WellControls2__TotalMassRate__kg/s__Source1"
                ]

    Returns:
        dict[str, list[str]]: property identifiers
            Example

            .. code-block:: python

                {
                    "WellControls1": [
                    "WellControls1__BHP__Pa__Source1",
                    "WellControls1__TotalMassRate__kg/s__Source1"
                    ],
                    "WellControls2": [
                    "WellControls2__BHP__Pa__Source1",
                    "WellControls2__TotalMassRate__kg/s__Source1"
                    ]
                }
    """
    propsPerIdentfier: dict[ str, list[ str ] ] = {}
    for propertyName in propertyNames:
        elements: list[ str ] = propertyName.split( "__" )
        identifier: str = elements[ 0 ]
        if identifier not in propsPerIdentfier:
            propsPerIdentfier[ identifier ] = []
        propsPerIdentfier[ identifier ].append( propertyName )
    return propsPerIdentfier


def associationIdentifiers( propertyNames: list[ str ] ) -> dict[ str, dict[ str, list[ str ] ] ]:
    """Extract identifiers with associatied curves.

    From a list of property names, extracts the identifier (name of the
    region for flow property or name of a well for well property) and creates
    a dictionnary with identifiers as keys and the properties containing them
    for value in a list.

    Args:
        propertyNames (list[str]): property names
        Example

        .. code-block:: python

            [
            "WellControls1__BHP__Pa__Source1",
            "WellControls1__TotalMassRate__kg/s__Source1",
            "WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls1__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls2__BHP__Pa__Source1",
            "WellControls2__TotalMassRate__kg/s__Source1",
            "WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1",
            "WellControls2__SurfaceVolumetricRateWater__m3/s__Source1",
            "WellControls3__BHP__Pa__Source1",
            "WellControls3__TotalMassRate__tons/day__Source1",
            "WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1",
            "Mean__BHP__Pa__Source1",
            "Mean__TotalMassRate__tons/day__Source1",
            "Mean__TotalSurfaceVolumetricRate__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateCO2__bbl/day__Source1",
            "Mean__SurfaceVolumetricRateWater__bbl/day__Source1"
            ]

    Returns:
        dict[str, dict[str, list[str]]]: property identifiers
            Example

            .. code-block:: python

                {
                    "WellControls1": {
                        'BHP (Pa)': [
                            'WellControls1__BHP__Pa__Source1'
                        ],
                        'MassRate (kg/s)': [
                            'WellControls1__TotalMassRate__kg/s__Source1'
                        ],
                        'VolumetricRate (m3/s)': [
                            'WellControls1__TotalSurfaceVolumetricRate__m3/s__Source1',
                            'WellControls1__SurfaceVolumetricRateCO2__m3/s__Source1',
                            'WellControls1__SurfaceVolumetricRateWater__m3/s__Source1'
                        ]
                    },
                    "WellControls2": {
                        'BHP (Pa)': [
                            'WellControls2__BHP__Pa__Source1'
                        ],
                        'MassRate (kg/s)': [
                            'WellControls2__TotalMassRate__kg/s__Source1'
                        ],
                        'VolumetricRate (m3/s)': [
                            'WellControls2__TotalSurfaceVolumetricRate__m3/s__Source1',
                            'WellControls2__SurfaceVolumetricRateCO2__m3/s__Source1',
                            'WellControls2__SurfaceVolumetricRateWater__m3/s__Source1'
                        ]
                    },
                    "WellControls3": {
                        'BHP (Pa)': [
                            'WellControls3__BHP__Pa__Source1'
                        ],
                        'MassRate (tons/day)': [
                            'WellControls3__TotalMassRate__tons/day__Source1'
                        ],
                        'VolumetricRate (bbl/day)': [
                            'WellControls3__TotalSurfaceVolumetricRate__bbl/day__Source1',
                            'WellControls3__SurfaceVolumetricRateCO2__bbl/day__Source1',
                            'WellControls3__SurfaceVolumetricRateWater__bbl/day__Source1'
                        ]
                    },
                    "Mean": {
                        'BHP (Pa)': [
                            'Mean__BHP__Pa__Source1'
                        ],
                        'MassRate (tons/day)': [
                            'Mean__TotalMassRate__tons/day__Source1'
                        ],
                        'VolumetricRate (bbl/day)': [
                            'Mean__TotalSurfaceVolumetricRate__bbl/day__Source1',
                            'Mean__SurfaceVolumetricRateCO2__bbl/day__Source1',
                            'Mean__SurfaceVolumetricRateWater__bbl/day__Source1'
                        ]
                    }
                }
    """
    propsPerIdentfier: dict[ str, list[ str ] ] = propertiesPerIdentifier( propertyNames )
    assosIdentifier: dict[ str, dict[ str, list[ str ] ] ] = {}
    for ident, propNames in propsPerIdentfier.items():
        assosPropsToAxeType: dict[ str, list[ str ] ] = associatePropertyToAxeType( propNames )
        assosIdentifier[ ident ] = assosPropsToAxeType
    return assosIdentifier


def buildFontTitle( userChoices: dict[ str, Any ] ) -> FontProperties:
    """Builds a Fontproperties object according to user choices on title.

    Args:
        userChoices (dict[str, Any]): customization parameters.

    Returns:
        FontProperties: FontProperties object for the title.
    """
    fontTitle: FontProperties = FontProperties()
    if "titleStyle" in userChoices:
        fontTitle.set_style( userChoices[ "titleStyle" ] )
    if "titleWeight" in userChoices:
        fontTitle.set_weight( userChoices[ "titleWeight" ] )
    if "titleSize" in userChoices:
        fontTitle.set_size( userChoices[ "titleSize" ] )
    return fontTitle


def buildFontVariable( userChoices: dict[ str, Any ] ) -> FontProperties:
    """Builds a Fontproperties object according to user choices on variables.

    Args:
        userChoices (dict[str, Any]): customization parameters.

    Returns:
        FontProperties: FontProperties object for the variable axes.
    """
    fontVariable: FontProperties = FontProperties()
    if "variableStyle" in userChoices:
        fontVariable.set_style( userChoices[ "variableStyle" ] )
    if "variableWeight" in userChoices:
        fontVariable.set_weight( userChoices[ "variableWeight" ] )
    if "variableSize" in userChoices:
        fontVariable.set_size( userChoices[ "variableSize" ] )
    return fontVariable


def buildFontCurves( userChoices: dict[ str, Any ] ) -> FontProperties:
    """Builds a Fontproperties object according to user choices on curves.

    Args:
        userChoices (dict[str, str]): customization parameters.

    Returns:
        FontProperties: FontProperties object for the curves axes.
    """
    fontCurves: FontProperties = FontProperties()
    if "curvesStyle" in userChoices:
        fontCurves.set_style( userChoices[ "curvesStyle" ] )
    if "curvesWeight" in userChoices:
        fontCurves.set_weight( userChoices[ "curvesWeight" ] )
    if "curvesSize" in userChoices:
        fontCurves.set_size( userChoices[ "curvesSize" ] )
    return fontCurves


def customizeLines( userChoices: dict[ str, Any ], labels: list[ str ],
                    linesList: list[ lines.Line2D ] ) -> list[ lines.Line2D ]:
    """Customize lines according to user choices.

    By applying the user choices, we modify or not the list of lines
    and return it with the same number of lines in the same order.

    Args:
        userChoices (dict[str, Any]): customization parameters.
        labels (list[str]): labels of lines.
        linesList (list[lines.Line2D]): list of lines object.

    Returns:
        list[lines.Line2D]: list of lines object modified.
    """
    if "linesModified" in userChoices:
        linesModifs: dict[ str, dict[ str, Any ] ] = userChoices[ "linesModified" ]
        linesChanged: list[ lines.Line2D ] = []
        for i, label in enumerate( labels ):
            if label in linesModifs:
                lineChanged: lines.Line2D = applyCustomizationOnLine( linesList[ i ], linesModifs[ label ] )
                linesChanged.append( lineChanged )
            else:
                linesChanged.append( linesList[ i ] )
        return linesChanged
    else:
        return linesList


def applyCustomizationOnLine( line: lines.Line2D, parameters: dict[ str, Any ] ) -> lines.Line2D:
    """Apply modification methods on a line from parameters.

    Args:
        line (lines.Line2D): Matplotlib Line2D
        parameters (dict[str, Any]): dictionary of {
            "linestyle": one of ["-","--","-.",":"]
            "linewidth": positive int
            "color": color code
            "marker": one of ["",".","o","^","s","*","D","+","x"]
            "markersize":positive int
            }

    Returns:
        lines.Line2D: Line2D object modified.
    """
    if "linestyle" in parameters:
        line.set_linestyle( parameters[ "linestyle" ] )
    if "linewidth" in parameters:
        line.set_linewidth( parameters[ "linewidth" ] )
    if "color" in parameters:
        line.set_color( parameters[ "color" ] )
    if "marker" in parameters:
        line.set_marker( parameters[ "marker" ] )
    if "markersize" in parameters:
        line.set_markersize( parameters[ "markersize" ] )
    return line


"""
Layout tools for layering subplots in a figure
"""


def isprime( x: int ) -> bool:
    """Checks if a number is primer or not.

    Args:
        x (int): Positive number to test.

    Returns:
        bool: True if prime, False if not.
    """
    if x < 0:
        print( "Invalid number entry, needs to be positive int" )
        return False

    return all( x % n != 0 for n in range( 2, int( x**0.5 ) + 1 ) )


def findClosestPairIntegers( x: int ) -> tuple[ int, int ]:
    """Get the pair of integers that multiply the closest to input value.

    Finds the closest pair of integers that when multiplied together,
    gives a number the closest to the input number (always above or equal).

    Args:
        x (int): Positive number.

    Returns:
        tuple[int, int]: (highest int, lowest int)
    """
    if x < 4:
        return ( x, 1 )
    while isprime( x ):
        x += 1
    N: int = round( math.sqrt( x ) )
    while x > N:
        if x % N == 0:
            M = x // N
            highest = max( M, N )
            lowest = min( M, N )
            return ( highest, lowest )
        else:
            N += 1
    return ( x, 1 )


def smartLayout( x: int, ratio: float ) -> tuple[ int, int, int ]:
    """Return the best layout according to the number of subplots.

    For multiple subplots, we need to have a layout that can adapt to
    the number of subplots automatically. This function figures out the
    best layout possible knowing the number of suplots and the figure ratio.

    Args:
        x (int): Positive number.
        ratio (float): width to height ratio of a figure.

    Returns:
        tuple[int]: (nbr_rows, nbr_columns, number of axes to remove)
    """
    pair: tuple[ int, int ] = findClosestPairIntegers( x )
    nbrAxesToRemove: int = pair[ 0 ] * pair[ 1 ] - x
    if ratio < 1:
        return ( pair[ 0 ], pair[ 1 ], nbrAxesToRemove )
    else:
        return ( pair[ 1 ], pair[ 0 ], nbrAxesToRemove )


"""
Legend tools
"""

commonAssociations: dict[ str, str ] = {
    "pressuremin": "Pmin",
    "pressureMax": "Pmax",
    "pressureaverage": "Pavg",
    "deltapressuremin": "DPmin",
    "deltapressuremax": "DPmax",
    "temperaturemin": "Tmin",
    "temperaturemax": "Tmax",
    "temperatureaverage": "Tavg",
    "effectivestressxx": "ESxx",
    "effectivestresszz": "ESzz",
    "effectivestressratio": "ESratio",
    "totaldisplacementx": "TDx",
    "totaldisplacementy": "TDy",
    "totaldisplacementz": "TDz",
    "totalstressXX": "TSxx",
    "totalstressZZ": "TSzz",
    "stressxx": "Sxx",
    "stressyy": "Syy",
    "stresszz": "Szz",
    "stressxy": "Sxy",
    "stressxz": "Sxz",
    "stressyz": "Syz",
    "poissonratio": "PR",
    "porosity": "PORO",
    "specificgravity": "SG",
    "theoreticalverticalstress": "TVS",
    "density": "DNST",
    "pressure": "P",
    "permeabilityx": "PERMX",
    "permeabilityy": "PERMY",
    "permeabilityz": "PERMZ",
    "oedometric": "OEDO",
    "young": "YOUNG",
    "shear": "SHEAR",
    "bulk": "BULK",
    "totaldynamicporevolume": "TDPORV",
    "time": "TIME",
    "dt": "DT",
    "meanbhp": "MBHP",
    "meantotalmassrate": "MTMR",
    "meantotalvolumetricrate": "MTSVR",
    "bhp": "BHP",
    "totalmassrate": "TMR",
    "cumulatedlineariter": "CLI",
    "cumulatednewtoniter": "CNI",
    "lineariter": "LI",
    "newtoniter": "NI",
}

phasesAssociations: dict[ str, str ] = {
    "dissolvedmass": " IN ",
    "immobile": "IMOB ",
    "mobile": "MOB ",
    "nontrapped": "NTRP ",
    "dynamicporevolume": "DPORV ",
    "meansurfacevolumetricrate": "MSVR ",
    "surfacevolumetricrate": "SVR ",
}


def smartLabelsSorted( labels: list[ str ], lines: list[ lines.Line2D ],
                       userChoices: dict[ str, Any ] ) -> tuple[ list[ str ], list[ lines.Line2D ] ]:
    """Shorten all legend labels and sort them.

    To improve readability of the legend for an axe in ParaView, we can apply the
    smartLegendLabel functionnality to reduce the size of each label. Plus we sort them
    alphabetically and therefore, we also sort the lines the same way.

    Args:
        labels (list[str]): Labels to use ax.legend() like
            ["Region1__TemperatureAvg__K__job_123456", "Region1__PressureMin__Pa__job_123456"]
        lines (list[lines.Line2D]): Lines plotted on axes of matplotlib figure like [line1, line2]
        userChoices (dict[str, Any]): Choices made by widget selection
            in PythonViewConfigurator filter.

    Returns:
        tuple[list[str], list[lines.Line2D]]: Improved labels and sorted labels / lines like
        (["Region1 Pmin", "Region1 Tavg"], [line2, line1])
    """
    smartLabels: list[ str ] = [ smartLabel( label, userChoices ) for label in labels ]
    # I need the labels to be ordered alphabetically for better readability of the legend
    # Therefore, if I sort smartLabels, I need to also sort lines with the same order.
    # But this can only be done if there are no duplicates of labels in smartLabels.
    # If a duplicate is found, "sorted" will try to sort with line which has no comparison built in
    # which will throw an error.
    if len( set( smartLabels ) ) == len( smartLabels ):
        sortedBothLists = sorted( zip( smartLabels, lines ) )
        sortedLabels, sortedLines = zip( *sortedBothLists )
        return ( list( sortedLabels ), list( sortedLines ) )
    else:
        return ( smartLabels, lines )


def smartLabel( label: str, userChoices: dict[ str, Any ] ) -> str:
    """Shorten label according to user choices.

    Labels name can tend to be too long. Therefore, we need to reduce the size of the label.
    Depending on the choices made by the user, the identifier and the job name can disappear.

    Args:
        label (str): A label to be plotted.
            Example- Reservoir__DissolvedMassphaseName0InphaseName1__kg__job123456.out
        userChoices (dict[str, Any]): user choices.

    Returns:
        str: "phaseName0 in phaseName1" or "Reservoir phaseName0 in phaseName1"
        or "phaseName0 in phaseName1 job123456.out" or
        "Reservoir phaseName0 in phaseName1 job123456.out"
    """
    # first step is to abbreviate the label to reduce its size
    smartLabel: str = abbreviateLabel( label )
    # When only one source is used as input, there is no need to precise which one is used
    # in the label so the job name is useless. Same when removeJobName option is selected by user.
    inputNames: list[ str ] = userChoices[ "inputNames" ]
    removeJobName: bool = userChoices[ "removeJobName" ]
    if len( inputNames ) > 1 and not removeJobName:
        jobName: str = findJobName( label )
        smartLabel += " " + jobName
    # When the user chooses to split the plot into subplots to plot by region or well,
    # this identifier name will appear as a title of the subplot so no need to use it.
    # Same applies when user decides to remove regions.
    plotRegions: bool = userChoices[ "plotRegions" ]
    removeRegions: bool = userChoices[ "removeRegions" ]
    if not plotRegions and not removeRegions:
        smartLabel = findIdentifier( label ) + " " + smartLabel
    return smartLabel


def abbreviateLabel( label: str ) -> str:
    """Get the abbreviation of the label according to reservoir nomenclature.

    When using labels to plot, the name can tend to be too long. Therefore, to respect
    the logic of reservoir engineering vocabulary, abbreviations for common property names
    can be used to shorten the name. The goal is therefore to generate the right abbreviation
    for the label input.

    Args:
        label (str): A label to be plotted.
            Example- Reservoir__DissolvedMassphaseName0InphaseName1__kg__job123456.out

    Returns:
        str: "phaseName0 in phaseName1"
    """
    for commonAsso in commonAssociations:
        if commonAsso in label.lower():
            return commonAssociations[ commonAsso ]
    for phaseAsso in phasesAssociations:
        if phaseAsso in label.lower():
            phases: list[ str ] = findPhasesLabel( label )
            phase0: str = "" if len( phases ) < 1 else phases[ 0 ]
            phase1: str = "" if len( phases ) < 2 else phases[ 1 ]
            if phaseAsso == "dissolvedmass":
                return phase0 + phasesAssociations[ phaseAsso ] + phase1
            else:
                return phasesAssociations[ phaseAsso ] + phase0
    return label


def findIdentifier( label: str ) -> str:
    """Find identifier inside the label.

    When looking at a label, it may contain or not an identifier at the beginning of it.
    An identifier is either a regionName or a wellName.
    The goal is to find it and extract it if present.

    Args:
        label (str): A label to be plotted.
            Example- Reservoir__DissolvedMassphaseName0InphaseName1__kg__job123456.out

    Returns:
        str: "Reservoir"
    """
    identifier: str = ""
    if "__" not in label:
        print( "Invalid label, cannot search identifier when no '__' in label." )
        return identifier
    subParts: list[ str ] = label.split( "__" )
    if len( subParts ) == 4:
        identifier = subParts[ 0 ]
    return identifier


def findJobName( label: str ) -> str:
    """Find the Geos job name at the end of the label.

    When looking at a label, it may contain or not a job name at the end of it.
    The goal is to find it and extract it if present.

    Args:
        label (str): A label to be plotted.
            Example- Reservoir__DissolvedMassphaseName0InphaseName1__kg__job123456.out

    Returns:
        str: "job123456.out"
    """
    jobName: str = ""
    if "__" not in label:
        print( "Invalid label, cannot search jobName when no '__' in label." )
        return jobName
    subParts: list[ str ] = label.split( "__" )
    if len( subParts ) == 4:
        jobName = subParts[ 3 ]
    return jobName


def findPhasesLabel( label: str ) -> list[ str ]:
    """Find phase name inside label.

    When looking at a label, it may contain or not patterns that indicates
    the presence of a phase name within it. Therefore, if one of these patterns
    is present, one or multiple phase names can be found and be extracted.

    Args:
        label (str): A label to be plotted.
            Example- Reservoir__DissolvedMassphaseName0InphaseName1__kg__job123456.out

    Returns:
        list[str]: [phaseName0, phaseName1]
    """
    phases: list[ str ] = []
    lowLabel: str = label.lower()
    indexStart: int = 0
    indexEnd: int = 0
    if "__" not in label:
        print( "Invalid label, cannot search phases when no '__' in label." )
        return phases
    if "dissolvedmass" in lowLabel:
        indexStart = lowLabel.index( "dissolvedmass" ) + len( "dissolvedmass" )
        indexEnd = lowLabel.rfind( "__" )
        phasesSubstring: str = lowLabel[ indexStart:indexEnd ]
        phases = phasesSubstring.split( "in" )
        phases = [ phase.capitalize() for phase in phases ]
    else:
        if "dynamicporevolume" in lowLabel:
            indexStart = lowLabel.index( "__" ) + 2
            indexEnd = lowLabel.index( "dynamicporevolume" )
        else:
            for pattern in [ "nontrapped", "trapped", "immobile", "mobile", "rate" ]:
                if pattern in lowLabel:
                    indexStart = lowLabel.index( pattern ) + len( pattern )
                    indexEnd = lowLabel.rfind( "mass" )
                    if indexEnd < 0:
                        indexEnd = indexStart + lowLabel[ indexStart: ].find( "__" )
                    break
        if indexStart < indexEnd:
            phases = [ lowLabel[ indexStart:indexEnd ].capitalize() ]
    return phases


"""
Under this is the first version of smartLabels without abbreviations.
"""

# def smartLegendLabelsAndLines(
#     labelNames: list[str], lines: list[Any], userChoices: dict[str, Any], regionName=""
# ) -> tuple[list[str], list[Any]]:
#     """To improve readability of the legend for an axe in ParaView, we can apply the
#     smartLegendLabel functionnality to reduce the size of each label. Plus we sort them
#     alphabetically and therefore, we also sort the lines the same way.

#     Args:
#         labelNames (list[str]): Labels to use ax.legend() like
#         ["Region1__PressureMin__Pa__job_123456", "Region1__Temperature__K__job_123456"]
#         lines (list[Any]): Lines plotted on axes of matplotlib figure like [line1, line2]
#         userChoices (dict[str, Any]): Choices made by widget selection
#         in PythonViewConfigurator filter.
#         regionName (str, optional): name of the region. Defaults to "".

#     Returns:
#         tuple[list[str], list[Any]]: Improved labels and sorted labels / lines like
#         (["Temperature K", "PressureMin Pa"], [line2, line1])
#     """
#     smartLabels: list[str] = [
#         smartLegendLabel(labelName, userChoices, regionName) for labelName in labelNames
#     ]
#     # I need the labels to be ordered alphabetically for better readability of the legend
#     # Therefore, if I sort smartLabels, I need to also sort lines with the same order
#     sortedBothLists = sorted(zip(smartLabels, lines)
#     sortedLabels, sortedLines = zip(*sortedBothLists)
#     return (sortedLabels, sortedLines)

# def smartLegendLabel(labelName: str, userChoices: dict[str, Any], regionName="") -> str:
#     """When plotting legend label, the label format can be improved by removing some
#     overwhelming / repetitive prefixe / suffixe and have a shorter label.

#     Args:
#         labelName (str): Label to use ax.legend() like
#         Region1__PressureMin__Pa__job_123456
#         userChoices (dict[str, Any]): Choices made by widget selection
#         in PythonViewConfigurator filter.
#         regionName (str, optional): name of the region. Defaults to "".

#     Returns:
#         str: Improved label name like PressureMin Pa.
#     """
#     smartLabel: str = ""
#     # When only one source is used as input, there is no need to precise which one
#     # is used in the label. Same when removeJobName option is selected by user.
#     inputNames: list[str] = userChoices["inputNames"]
#     removeJobName: bool = userChoices["removeJobName"]
#     if len(inputNames) <= 1 or removeJobName:
#         smartLabel = removeJobNameInLegendLabel(labelName, inputNames)
#     # When the user chooses to split the plot into subplots to plot by region,
#     # the region name will appear as a title of the subplot so no need to use it.
#     # Same applies when user decides to remove regions.
#     plotRegions: bool = userChoices["plotRegions"]
#     removeRegions: bool = userChoices["removeRegions"]
#     if plotRegions or removeRegions:
#         smartLabel = removeIdentifierInLegendLabel(smartLabel, regionName)
#     smartLabel = smartLabel.replace("__", " ")
#     return smartLabel

# def removeJobNameInLegendLabel(legendLabel: str, inputNames: list[str]) -> str:
#     """When plotting legends, the name of the job is by default at the end of
#     the label. Therefore, it can increase tremendously the size of the legend
#     and we can avoid that by removing the job name from it.

#     Args:
#         legendLabel (str): Label to use ax.legend() like
#         Region1__PressureMin__Pa__job_123456
#         inputNames (list[str]): names of the sources use to plot.

#     Returns:
#         str: Label without the job name like Region1__PressureMin__Pa.
#     """
#     for inputName in inputNames:
#         pattern: str = "__" + inputName
#         if legendLabel.endswith(pattern):
#             jobIndex: int = legendLabel.index(pattern)
#             return legendLabel[:jobIndex]
#     return legendLabel

# def removeIdentifierInLegendLabel(legendLabel: str, regionName="") -> str:
#     """When plotting legends, the name of the region is by default at the
#     beginning of the label. Here we remove the region name from the legend label.

#     Args:
#         legendLabel (str): Label to use ax.legend() like
#         Region1__PressureMin__Pa__job_123456
#         regionName (str): name of the region. Defaults to "".

#     Returns:
#         str: Label without the job name like PressureMin__Pa__job_123456
#     """
#     if "__" not in legendLabel:
#         return legendLabel
#     if regionName == "":
#         firstRegionIndex: int = legendLabel.index("__")
#         return legendLabel[firstRegionIndex + 2:]
#     pattern: str = regionName + "__"
#     if legendLabel.startswith(pattern):
#         return legendLabel[len(pattern):]
#     return legendLabel
"""
Other 2D tools for simplest figures
"""


def basicFigure( df: pd.DataFrame, variableName: str, curveName: str ) -> tuple[ figure.Figure, axes.Axes ]:
    """Creates a plot.

    Generates a figure and axes objects from matplotlib that plots
    one curve along the X axis, with legend and label for X and Y.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName"
        variableName (str): Name of the variable column
        curveName (str): Name of the column to display along that variable.

    Returns:
        tuple[figure.Figure, axes.Axes]: the fig and the ax.
    """
    fig, ax = plt.subplots()
    x: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
    y: npt.NDArray[ np.float64 ] = df[ curveName ].to_numpy()
    ax.plot( x, y, label=curveName )
    ax.set_xlabel( variableName )
    ax.set_ylabel( curveName )
    ax.legend( loc="best" )
    return ( fig, ax )


def invertedBasicFigure( df: pd.DataFrame, variableName: str, curveName: str ) -> tuple[ figure.Figure, axes.Axes ]:
    """Creates a plot with inverted XY axis.

    Generates a figure and axes objects from matplotlib that plots
    one curve along the Y axis, with legend and label for X and Y.

    Args:
        df (pd.DataFrame): dataframe containing at least two columns,
            one named "variableName" and the other "curveName"
        variableName (str): Name of the variable column
        curveName (str): Name of the column to display along that variable.

    Returns:
        tuple[figure.Figure, axes.Axes]: the fig and the ax.
    """
    fig, ax = plt.subplots()
    x: npt.NDArray[ np.float64 ] = df[ curveName ].to_numpy()
    y: npt.NDArray[ np.float64 ] = df[ variableName ].to_numpy()
    ax.plot( x, y, label=variableName )
    ax.set_xlabel( curveName )
    ax.set_ylabel( variableName )
    ax.legend( loc="best" )
    return ( fig, ax )


def adjust_subplots( fig: figure.Figure, invertXY: bool ) -> figure.Figure:
    """Adjust the size of the subplot in the fig.

    Args:
        fig (figure.Figure): Matplotlib figure
        invertXY (bool): Choice to either intervert or not the X and Y axes

    Returns:
        figure.Figure: Matplotlib figure with adjustements
    """
    if invertXY:
        fig.subplots_adjust( left=0.05, right=0.98, top=0.9, bottom=0.2 )
    else:
        fig.subplots_adjust( left=0.06, right=0.94, top=0.95, bottom=0.08 )
    return fig
