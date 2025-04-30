# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
import pandas as pd
from enum import Enum
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import (
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON
)
from geos.mesh.processing.meshQualityMetricHelpers import (
        getAllCellTypesExtended,
        QualityMetricEnum,
        qualityMetricsFromCellType
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

class QualityMetricSummary():

    _LEVELS: tuple[str] = ("MetricIndex", "CellType")
    _STATS_NUMBER: tuple[str] = ("Count", "Mean", "StdDev", "Min", "Max")

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
        nb_rows: int = len(self._STATS_NUMBER)
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

    def getCellTypeCounts(self: Self)-> float:
        """Get cell type counts.

        Returns:
            int: number of cell
        """
        return self._counts

    def getCellTypeCountsOfCellType(self: Self, cellType: int)-> float:
        """Get cell type counts.

        Returns:
            int: number of cell
        """
        return self._counts.getTypeCount(cellType)

    def isStatsValidForMetricAndCellType(self: Self,
                                         metricIndex: int,
                                         cellType: int,
                                        ) ->bool:
        print(np.any(np.isfinite(self.getStatsFromMetricAndCellType(metricIndex, cellType))))
        return np.any(np.isfinite(self.getStatsFromMetricAndCellType(metricIndex, cellType)))

    def getAllStats(self: Self)-> pd.DataFrame:
        """Get all mesh stats.

        Returns:
            pd.DataFrame: stats
        """
        return self._stats

    def getStatValueToMetricAndCellType(self: Self,
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

    def setStatValueToMetricAndCellType(self: Self,
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


