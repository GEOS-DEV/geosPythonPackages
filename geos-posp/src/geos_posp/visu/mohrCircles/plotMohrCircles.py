# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
from typing import Any

import matplotlib.pyplot as plt  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt
from matplotlib import ticker
from matplotlib.axes import Axes  # type: ignore[import-untyped]
from matplotlib.figure import Figure  # type: ignore[import-untyped]
from matplotlib.lines import Line2D  # type: ignore[import-untyped]

import geos_posp.visu.mohrCircles.functionsMohrCircle as mcf
from geos_posp.processing.MohrCircle import MohrCircle
from geos_posp.processing.MohrCoulomb import MohrCoulomb
from geos_posp.utils.enumUnits import Pressure, Unit, convert
from geos_posp.utils.GeosOutputsConstants import FAILURE_ENVELOPE
from geos_posp.visu.PVUtils.matplotlibOptions import (
    FontStyleEnum,
    FontWeightEnum,
    LegendLocationEnum,
    LineStyleEnum,
    MarkerStyleEnum,
)

__doc__ = """
plotMohrCircles module provides a set of functions to plot multiple Mohr's
circles and a failure envelope from a list of MohrCircle and MohrCoulomb
objects respectively.
"""


def createMohrCirclesFigure(
    mohrCircles: list[MohrCircle], mohrCoulomb: MohrCoulomb, userChoices: dict[str, Any]
) -> Figure:
    """Create Mohr's circle figure.

    Args:
        mohrCircles (list[MohrCircle]): list of MohrCircle objects.

        mohrCoulomb (MohrCoulomb): MohrCoulomb object defining the failure
        envelope.

        userChoices (dict[str, Any]): dictionnary to define figure properties.

    Returns:
        Figure: Figure object
    """
    plt.close()

    # create figure
    fig, ax = plt.subplots(constrained_layout=True)

    # plot Mohr's Circles
    curvesAspect: dict[str, Any] = userChoices.get("curvesAspect", {})
    annotate: bool = userChoices.get("annotateCircles", False)
    _plotMohrCircles(ax, mohrCircles, curvesAspect, annotate)

    # plot Mohr Coulomb failure envelop
    failureEnvelopeAspect: dict[str, Any] = curvesAspect.get(FAILURE_ENVELOPE, {})
    _plotMohrCoulomb(ax, mohrCoulomb, failureEnvelopeAspect)

    # set user preferences
    _setUserChoices(ax, userChoices)

    return fig


def _plotMohrCircles(
    ax: Axes,
    mohrCircles: list[MohrCircle],
    circlesAspect: dict[str, dict[str, Any]],
    annotate: bool,
) -> None:
    """Plot multiple Mohr's circles on input Axes.

    Args:
        ax (Axes): Axes where to plot Mohr's circles

        mohrCircles (list[MohrCircle]): list of MohrCircle objects to plot.

        circlesAspect (dict[str, dict[str, Any]]): dictionnary defining Mohr's
        circle line properties.

        annotate (bool): if True, display min and max normal stress.
    """
    nbPts: int = 361
    ang: npt.NDArray[np.float64] = np.linspace(0.0, np.pi, nbPts)
    for mohrCircle in mohrCircles:
        radius: float = mohrCircle.getCircleRadius()
        xCoords = mohrCircle.getCircleCenter() + radius * np.cos(ang)
        yCoords = radius * (np.sin(ang))
        label: str = mohrCircle.getCircleId()

        p: list[Line2D]  # plotted lines to get the color later
        if label in circlesAspect.keys():
            circleAspect: dict[str, Any] = circlesAspect[label]
            color: tuple[float, float, float] = circleAspect.get("color", "k")
            linestyle: str = circleAspect.get(
                "linestyle", LineStyleEnum.SOLID.optionValue
            )
            linewidth: float = circleAspect.get("linewidth", 1)
            marker: str = circleAspect.get("marker", MarkerStyleEnum.NONE.optionValue)
            markersize: float = circleAspect.get("markersize", 1)
            p = ax.plot(
                xCoords,
                yCoords,
                label=label,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                marker=marker,
                markersize=markersize,
            )
        else:
            p = ax.plot(xCoords, yCoords, label=label, linestyle="-", marker="")

        if annotate:
            fontColor = p[0].get_color()
            annot: tuple[str, str, tuple[float, float], tuple[float, float]] = (
                mcf.findAnnotateTuples(mohrCircle)
            )
            ax.annotate(annot[0], xy=annot[2], ha="left", rotation=30, color=fontColor)
            ax.annotate(annot[1], xy=annot[3], ha="right", rotation=30, color=fontColor)


def _plotMohrCoulomb(
    ax: Axes, mohrCoulomb: MohrCoulomb, curvesAspect: dict[str, Any]
) -> None:
    """Plot Mohr-Coulomb failure envelope in input Axes object.

    Args:
        ax (Axes): Axes where to plot the failure envelope.

        mohrCoulomb (MohrCoulomb): MohrCoulomb object to define failure envelope
        parameters.

        curvesAspect (dict[str, Any]): dictionnary defining line properties of
        the failure envelope.
    """
    xmin, xmax = ax.get_xlim()
    principalStresses, shearStress = mohrCoulomb.computeFailureEnvelop(xmax)
    color: tuple[float, float, float] = curvesAspect.get("color", "k")
    linestyle: str = curvesAspect.get("linestyle", LineStyleEnum.SOLID.optionValue)
    linewidth: float = curvesAspect.get("linewidth", 1)
    marker: str = curvesAspect.get("marker", MarkerStyleEnum.NONE.optionValue)
    markersize: float = curvesAspect.get("markersize", 1)
    ax.plot(
        principalStresses,
        shearStress,
        label="Failure Envelope",
        color=color,
        linestyle=linestyle,
        linewidth=linewidth,
        marker=marker,
        markersize=markersize,
    )


def _setUserChoices(ax: Axes, userChoices: dict[str, Any]) -> None:
    """Set user preferences on input Axes.

    Args:
        ax (Axes): Axes object to modify.

        userChoices (dict[str, Any]): dictionnary of user-defined properties.
    """
    _updateAxis(ax, userChoices)

    # set title properties
    if userChoices.get("displayTitle", False):
        updateTitle(ax, userChoices)

    # set legend
    if userChoices.get("displayLegend", False):
        _updateLegend(ax, userChoices)

    if userChoices.get("customAxisLim", False):
        _updateAxisLimits(ax, userChoices)


def _updateAxis(ax: Axes, userChoices: dict[str, Any]) -> None:
    """Update axis ticks and labels.

    Args:
        ax (Axes): axes object.

        userChoices (dict[str, Any]): user parameters.
    """
    # update axis labels
    xlabel: str = userChoices.get("xAxis", "Normal stress")
    ylabel: str = userChoices.get("xAyAxisxis", "Shear stress")

    # get unit
    unitChoice: int = userChoices.get("stressUnit", 0)
    unitObj: Unit = list(Pressure)[unitChoice].value
    unitLabel: str = unitObj.unitLabel

    # change displayed units
    xlabel += f" ({unitLabel})"
    ylabel += f" ({unitLabel})"
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    # function to do conversion and set format
    def _tickFormatterFunc(x: float, pos: str) -> str:
        return f"{convert(x, unitObj):.2E}"

    # apply formatting to xticks and yticks
    ax.xaxis.set_major_formatter(ticker.FuncFormatter(_tickFormatterFunc))
    ax.yaxis.set_major_formatter(ticker.FuncFormatter(_tickFormatterFunc))

    # set axis properties
    ax.set_aspect("equal", anchor="C")
    xmin, xmax = ax.get_xlim()
    ax.set_xlim(0.0)
    ax.set_ylim(0.0, xmax)
    ax.grid()
    ax.minorticks_off()
    if "minorticks" in userChoices.keys() and userChoices["minorticks"]:
        ax.minorticks_on()


def updateTitle(ax: Axes, userChoices: dict[str, Any]) -> None:
    """Update title.

    Args:
        ax (Axes): axes object.

        userChoices (dict[str, Any]): user parameters.
    """
    title = userChoices.get("title", "Mohr's Circles")
    style = userChoices.get("titleStyle", FontStyleEnum.NORMAL.optionValue)
    weight = userChoices.get("titleWeight", FontWeightEnum.BOLD.optionValue)
    size = userChoices.get("titleSize", 12)
    ax.set_title(title, fontstyle=style, weight=weight, fontsize=size)


def _updateLegend(ax: Axes, userChoices: dict[str, Any]) -> None:
    """Update legend.

    Args:
        ax (Axes): axes object.

        userChoices (dict[str, Any]): user parameters.
    """
    loc = userChoices.get("legendPosition", LegendLocationEnum.BEST.optionValue)
    size = userChoices.get("legendSize", 10)
    ax.legend(loc=loc, fontsize=size)


def _updateAxisLimits(ax: Axes, userChoices: dict[str, Any]) -> None:
    """Update axis limits.

    Args:
        ax (Axes): axes object.

        userChoices (dict[str, Any]): user parameters.
    """
    xmin, xmax = ax.get_xlim()
    if userChoices.get("limMinX", None) is not None:
        xmin = userChoices["limMinX"]
    if userChoices.get("limMaxX", None) is not None:
        xmax = userChoices["limMaxX"]
    ax.set_xlim(xmin, xmax)

    ymin, ymax = ax.get_xlim()
    if userChoices.get("limMinY", None) is not None:
        ymin = userChoices["limMinY"]
    if userChoices.get("limMaxY", None) is not None:
        ymax = userChoices["limMaxY"]
    ax.set_ylim(ymin, ymax)
