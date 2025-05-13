# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
import pandas as pd
from enum import Enum
from typing import Any
from typing_extensions import Self
from packaging.version import Version
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from vtkmodules.vtkCommonDataModel import (
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)
from geos.mesh.processing.meshQualityMetricHelpers import (
        getAllCellTypesExtended,
        getQualityMeasureNameFromIndex,
        QualityMetricEnum,
        QualityRange
)
from geos.mesh.model.CellTypeCounts import CellTypeCounts

__doc__ = """
QualityMetricSummary stores the statistics of mesh quality metrics.
"""

class StatTypes(Enum):
    MEAN    = (0, "Mean", float)
    STD_DEV = (1, "StdDev", float)
    MIN     = (2, "Min", float)
    MAX     = (3, "Max", float)
    COUNT   = (4, "Count", int)

    def getIndex(self: Self) ->int:
        """Get stat index.

        Returns:
            int: index
        """
        return self.value[0]

    def getString(self: Self) ->str:
        """Get stat name.

        Returns:
            str: name
        """
        return self.value[1]

    def getType(self: Self) ->object:
        """Get stat type.

        Returns:
            object: type
        """
        return self.value[2]

    @staticmethod
    def getNameFromIndex(index: int) ->str:
        """Get stat name from index.

        Args:
            index (int): index

        Returns:
            str: name
        """
        return list(StatTypes)[index].getString()

    @staticmethod
    def getIndexFromName(name: str) ->int:
        """Get stat index from name.

        Args:
            name (str): name

        Returns:
            int: index
        """
        for stat in list(StatTypes):
            if stat.getString() == name:
                return stat.getIndex()
        return -1

    @staticmethod
    def getTypeFromIndex(index: int) ->object:
        """Get stat type from index.

        Args:
            index (int): index

        Returns:
            object: type
        """
        return list(StatTypes)[index].getType()

_RANGE_COLORS: tuple[str, str, str] = ('lightcoral', 'sandybrown', 'palegreen', )

class QualityMetricSummary():

    _LEVELS: tuple[str] = ("MetricIndex", "CellType")
    _CELL_TYPES_PLOT: tuple[int] = (VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON, VTK_POLYHEDRON)

    def __init__(self: Self ) ->None:
        """CellTypeCounts stores the number of cells of each type."""
        #: stores for each cell type, and metric type, the stats
        self._counts: CellTypeCounts = CellTypeCounts()
        self._stats: pd.DataFrame
        self._initStats()

    def _initStats(self: Self) ->None:
        """Initialize self._stats dataframe."""
        rows: tuple[str] = (statType.getIndex() for statType in list(StatTypes))
        cellTypes: list[int] = getAllCellTypesExtended()
        indexes = [(metric.metricIndex, cellType) for metric in list(QualityMetricEnum) for cellType in cellTypes if metric.isApplicableToCellType(cellType)]
        df_indexes: pd.MultiIndex = pd.MultiIndex.from_tuples((indexes), names=self._LEVELS)
        nb_rows: int = len(list(StatTypes))
        nb_col: int = df_indexes.size
        self._stats = pd.DataFrame(np.full((nb_rows, nb_col), np.nan), columns=df_indexes, index=rows)

    def __str__(self: Self) ->str:
        """Overload __str__ method.

        Returns:
            str: counts as string.
        """
        return self.print()

    def print(self: Self) ->str:
        """Print quality metric summary as string.

        Returns:
            str: quality metric summary.
        """
        out: str = ""
        return out

    def setCellTypeCounts(self: Self, counts: CellTypeCounts) ->None:
        """Set cell type counts.

        Args:
            counts (CellTypeCounts): CellTypeCounts instance
        """
        self._counts = counts

    def getCellTypeCountsObject(self: Self)-> int:
        """Get cell type counts.

        Returns:
            int: number of cell
        """
        return self._counts

    def getCellTypeCountsOfCellType(self: Self, cellType: int)-> int:
        """Get cell type counts.

        Returns:
            int: number of cell
        """
        return self._counts.getTypeCount(cellType)

    def isStatsValidForMetricAndCellType(self: Self,
                                         metricIndex: int,
                                         cellType: int,
                                        ) ->bool:
        """Returns True if input quality metric applies to input cell type.

        Args:
            metricIndex (int): metric index
            cellType (int): cell type index

        Returns:
            bool: True if input quality metric applies
        """
        return np.any(np.isfinite(self.getStatsFromMetricAndCellType(metricIndex, cellType)))

    def getAllStats(self: Self)-> pd.DataFrame:
        """Get all mesh stats including nan values.

        Returns:
            pd.DataFrame: stats
        """
        return self._stats

    def getAllValidStats(self: Self)-> pd.DataFrame:
        """Get all valid mesh stats.

        Returns:
            pd.DataFrame: stats
        """
        return self._stats.dropna(axis=1)

    def getStatValueFromStatMetricAndCellType(self: Self,
                                              metricIndex: int,
                                              cellType: int,
                                              statType: StatTypes,
                                             ) -> float:
        """Get stat value for the given metric and cell types.

        Args:
            metricIndex (int): metric index
            cellType (int): cell type index
            statType (StatTypes): stat number

        Returns:
            float: stats value
        """
        if (metricIndex, cellType) not in self._stats.columns:
            raise IndexError(f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats")
        return self._stats[(metricIndex, cellType)][statType.getIndex()]

    def getStatsFromMetricAndCellType(self: Self,
                                      metricIndex: int,
                                      cellType: int
                                     ) -> pd.Series:
        """Get stats for the given metric and cell types.

        Args:
            metricIndex (int): metric index
            cellType (int): cell type index

        Returns:
            pd.Series: stats
        """
        if (metricIndex, cellType) not in self._stats.columns:
            raise IndexError(f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats")
        return self._stats[(metricIndex, cellType)]

    def getStatsFromMetric(self: Self,
                           metricIndex: int,
                          ) -> pd.DataFrame:
        """Get stats for the given metric.

        Args:
            metricIndex (int): metric index

        Returns:
            pd.DataFrame: stats
        """
        return self._stats.xs(metricIndex, level=self._LEVELS[0], axis=1)

    def getStatsFromCellType(self: Self,
                             cellType: int,
                            ) -> pd.DataFrame:
        """Get stats for the given cell type.

        Args:
            cellType (int): cell type index

        Returns:
            pd.DataFrame: stats
        """
        return self._stats.xs(cellType, level=self._LEVELS[1], axis=1)

    def setStatValueFromStatMetricAndCellType(self: Self,
                                              metricIndex: int,
                                              cellType: int,
                                              statType: StatTypes,
                                              value: int | float
                                             ) -> None:
        """Set stats for the given metric and cell types.

        Args:
            metricIndex (int): metric index
            cellType (int): cell type index
            statType (StatTypes): stat number
            value (int | float): value
        """
        if (metricIndex, cellType) not in self._stats.columns:
            raise IndexError(f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats")
        self._stats.loc[statType.getIndex(), (metricIndex, cellType)] = value

    def getComputedMetricIndexes(self: Self) ->list[Any]:
        """Get the list of index of computed metrics.

        Returns:
            tuple[int]: list of metrics index
        """
        validStats: pd.DataFrame = self.getAllValidStats()
        columns: pd.MultiIndex = validStats.columns
        return np.unique(columns.get_level_values(0)).tolist()

    def plotSummaryFigure(self: Self) -> Figure:
        """Plot quality metric summary figure.

        Returns:
            plt.figure: output Figure
        """
        computedMetrics: list[int] = self.getComputedMetricIndexes()
        # compute layout
        nbAxes: int = len(computedMetrics) + 1
        ncols: int = 3
        nrows: int = 1
        if nbAxes not in (1, 2, 3, 5, 6, 9):
            ncols = 4
        nrows: int = nbAxes // ncols
        if nbAxes % ncols > 0:
            nrows += 1
        figSize = (ncols * 3, nrows * 4)
        fig, axes = plt.subplots(nrows, ncols, figsize=figSize, tight_layout=True)
        axesFlat = axes.flatten()

        # plot cell type counts
        self._plotCellTypeCounts(axesFlat[0])

        # plot quality metrics
        for i in range(1, nbAxes, 1):
            ax: Axes = axesFlat[i]
            self._plotAx(ax, computedMetrics[i-1])
        for ax in axesFlat[nbAxes:]:
            ax.remove()
        return fig

    def _plotCellTypeCounts(self: Self, ax: Axes)  ->None:
        """Plot cell type counts.

        Args:
            ax (Axes): Axes object
        """
        xticks: npt.NDArray[np.int64] = np.arange(len(self._CELL_TYPES_PLOT), dtype=int)
        xtickslabels = [vtkCellTypes.GetClassNameFromTypeId(cellType).removeprefix("vtk") for cellType in self._CELL_TYPES_PLOT]
        toplot: list[int] = [self._counts.getTypeCount(cellType) for cellType in self._CELL_TYPES_PLOT]
        p = ax.bar(xtickslabels, toplot)
        # bar_label only for matplotlib version >= 3.3
        if Version(mpl.__version__) >= Version("3.3"):
            plt.bar_label(p, label_type='center', rotation=90, padding=5)
        ax.set_xticks(xticks)
        ax.set_xticklabels(xtickslabels, rotation=30, ha="right")
        ax.set_xlabel("Cell types")
        ax.set_title("Cell Type Counts")

    def _plotAx(self: Self, ax: Axes, metricIndex: int) ->None:
        """Plot a single Axes.

        Args:
            ax (Axes): Axes object
            metricIndex (int): metric index
        """
        # get data to plot
        maxs: pd.Series = self._stats.loc[StatTypes.MAX.getIndex(), metricIndex]
        mins: pd.Series = self._stats.loc[StatTypes.MIN.getIndex(), metricIndex]
        means: pd.Series = self._stats.loc[StatTypes.MEAN.getIndex(), metricIndex]
        xticks: npt.NDArray[np.int64] = np.arange(means.index.size, dtype=int)
        stdDev: pd.Series = self._stats.loc[StatTypes.STD_DEV.getIndex(), metricIndex]

        # order of cell types in each axes
        xtickslabels: list[str] = []
        # min max rectangle width
        recWidth: float = 0.5
        # range rectangle width
        rangeRecWidth: float = 1.8 * recWidth
        ylim0: float = mins.max()
        ylim1: float = maxs.min()
        xtick: float = 0.0
        for k, cellType in enumerate(self._CELL_TYPES_PLOT):
            if cellType in means.index:
                xtickslabels += [vtkCellTypes.GetClassNameFromTypeId(cellType).removeprefix("vtk")]
                # add quality range patches if relevant
                qualityRange: QualityRange | None = list(QualityMetricEnum)[metricIndex].getQualityRange(cellType)
                if qualityRange is not None:
                    (ylim0, ylim1) = self._plotQualityRange(ax, qualityRange, xtick - rangeRecWidth / 2.0, (ylim0, ylim1), rangeRecWidth)
                else:
                    # add white patch for tick alignment
                    ax.add_patch(Rectangle((xtick - rangeRecWidth / 2.0, 0.), rangeRecWidth, 1.0,
                                 facecolor = 'w', fill=True,))
                # add rectangle from min to max
                x: float = xtick - recWidth / 2.0
                y: float = mins[cellType]
                recHeight: float = maxs[cellType] - mins[cellType]
                ax.add_patch(Rectangle((x, y), recWidth, recHeight,
                                        edgecolor = 'black',
                                        fill=False,
                                        lw=1))

                # plot mean and error bars for std dev
                ax.errorbar(k, means[cellType], yerr=stdDev[cellType], fmt='-o', color='k')
                xtick += 1.0

        # set y axis limits
        ax.set_ylim(0.1*ylim0, 1.1*ylim1)
        # set x tick names
        ax.set_xticks(xticks)#, xtickslabels, rotation=30, ha="right")
        ax.set_xticklabels(xtickslabels, rotation=30, ha="right")
        ax.set_xlabel("Cell types")
        ax.set_title(f"{getQualityMeasureNameFromIndex(metricIndex)}")

    def _plotQualityRange(self: Self,
                          ax: Axes,
                          qualityRange: QualityRange,
                          x: float,
                          ylim: tuple[float, float],
                          rangeRecWidth: float
                         ) ->tuple[float, float]:
        """Plot quality range patches.

        Args:
            ax (Axes): axes object
            qualityRange (QualityRange): quality ranges to plot
            x (float): origin abscissa of the patches
            ylim (tuple[float, float]): y limits for updates
            rangeRecWidth (float): patch width

        Returns:
            tuple[float, float]: y limits for updates
        """
        ylim0: float = ylim[0]
        ylim1: float = ylim[1]
        for k, (vmin, vmax) in enumerate((qualityRange.fullRange, qualityRange.normalRange, qualityRange.acceptableRange)):
            if not np.isfinite(vmin):
                vmin = -1e12
            else:
                ylim0 = min(ylim0, vmin)
            if not np.isfinite(vmax):
                vmax = 1e12
            else:
                ylim1 = max(ylim1, vmax)
            y: float = vmin
            recHeight = vmax - vmin
            ax.add_patch(Rectangle((x, y), rangeRecWidth, recHeight,
                                facecolor = _RANGE_COLORS[k],
                                fill=True,))
        return (ylim0, ylim1)
