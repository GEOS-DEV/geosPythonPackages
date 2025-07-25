# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from logging import Logger
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from matplotlib import axes, figure, lines  # type: ignore[import-untyped]
from matplotlib.font_manager import (  # type: ignore[import-untyped]
    FontProperties,  # type: ignore[import-untyped]
)
from typing_extensions import Self

import geos.pv.pythonViewUtils.functionsFigure2DGenerator as fcts


class Figure2DGenerator:

    def __init__( self: Self, dataframe: pd.DataFrame, userChoices: dict[ str, list[ str ] ], logger: Logger ) -> None:
        """Utility to create cross plots using Python View.

        We want to plot f(X) = Y where in this class,
        "X" will be called "variable", "Y" will be called "curves".

        Args:
            dataframe (pd.DataFrame): data to plot
            userChoices (dict[str, list[str]]): user choices.
            logger (Logger): Logger to use.
        """
        self.m_dataframe: pd.DataFrame = dataframe
        self.m_userChoices: dict[ str, Any ] = userChoices
        self.m_fig: figure.Figure
        self.m_axes: list[ axes._axes.Axes ] = []
        self.m_lines: list[ lines.Line2D ] = []
        self.m_labels: list[ str ] = []
        self.m_logger: Logger = logger

        try:
            # apply minus 1 multiplication on certain columns
            self.initMinus1Multiplication()
            # defines m_fig, m_axes, m_lines and m_lables
            self.plotInitialFigure()
            # then to edit and customize the figure
            self.enhanceFigure()
            self.m_logger.info( "Data were successfully plotted." )

        except Exception as e:
            mess: str = "Plot creation failed due to:"
            self.m_logger.critical( mess )
            self.m_logger.critical( e, exc_info=True )

    def initMinus1Multiplication( self: Self ) -> None:
        """Multiply by -1 certain columns of the input dataframe."""
        df: pd.DataFrame = self.m_dataframe.copy( deep=True )
        minus1CurveNames: list[ str ] = self.m_userChoices[ "curveConvention" ]
        for name in minus1CurveNames:
            df[ name ] = df[ name ] * ( -1 )
        self.m_dataframe = df

    def enhanceFigure( self: Self ) -> None:
        """Apply all the enhancement features to the initial figure."""
        self.changeTitle()
        self.changeMinorticks()
        self.changeAxisScale()
        self.changeAxisLimits()

    def plotInitialFigure( self: Self ) -> None:
        """Generates a figure and axes objects from matplotlib.

        The figure plots all the curves along the X or Y axis, with legend and
        label for X and Y.
        """
        if self.m_userChoices[ "plotRegions" ]:
            if not self.m_userChoices[ "reverseXY" ]:
                ( fig, ax_all, lines, labels ) = fcts.multipleSubplots( self.m_dataframe, self.m_userChoices )
            else:
                ( fig, ax_all, lines, labels ) = fcts.multipleSubplotsInverted( self.m_dataframe, self.m_userChoices )
        else:
            if not self.m_userChoices[ "reverseXY" ]:
                ( fig, ax_all, lines, labels ) = fcts.oneSubplot( self.m_dataframe, self.m_userChoices )
            else:
                ( fig, ax_all, lines, labels ) = fcts.oneSubplotInverted( self.m_dataframe, self.m_userChoices )
        self.m_fig = fig
        self.m_axes = ax_all
        self.m_lines = lines
        self.m_labels = labels

    def changeTitle( self: Self ) -> None:
        """Update title of the first axis of the figure based on user choices."""
        if self.m_userChoices[ "displayTitle" ]:
            title: str = self.m_userChoices[ "title" ]
            fontTitle: FontProperties = fcts.buildFontTitle( self.m_userChoices )
            self.m_fig.suptitle( title, fontproperties=fontTitle )

    def changeMinorticks( self: Self ) -> None:
        """Set the minorticks on or off for every axes."""
        choice: bool = self.m_userChoices[ "minorticks" ]
        if choice:
            for ax in self.m_axes:
                ax.minorticks_on()
        else:
            for ax in self.m_axes:
                ax.minorticks_off()

    def changeAxisScale( self: Self ) -> None:
        """Set the minorticks on or off for every axes."""
        for ax in self.m_axes:
            if self.m_userChoices[ "logScaleX" ]:
                ax.set_xscale( "log" )
            if self.m_userChoices[ "logScaleY" ]:
                ax.set_yscale( "log" )

    def changeAxisLimits( self: Self ) -> None:
        """Update axis limits."""
        if self.m_userChoices[ "customAxisLim" ]:
            for ax in self.m_axes:
                xmin, xmax = ax.get_xlim()
                if self.m_userChoices[ "limMinX" ] is not None:
                    xmin = self.m_userChoices[ "limMinX" ]
                if self.m_userChoices[ "limMaxX" ] is not None:
                    xmax = self.m_userChoices[ "limMaxX" ]
                ax.set_xlim( xmin, xmax )

                ymin, ymax = ax.get_ylim()
                if self.m_userChoices[ "limMinY" ] is not None:
                    ymin = self.m_userChoices[ "limMinY" ]
                if self.m_userChoices[ "limMaxY" ] is not None:
                    ymax = self.m_userChoices[ "limMaxY" ]
                ax.set_ylim( ymin, ymax )

    def getFigure( self: Self ) -> figure.Figure:
        """Acces the m_fig attribute.

        Returns:
            figure.Figure: Figure containing all the plots.
        """
        return self.m_fig
