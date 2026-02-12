# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay, Paloma Martinez
import numpy as np
import numpy.typing as npt
import pandas as pd
from enum import Enum
from typing import Any, Union
from typing_extensions import Self, Iterable

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from vtkmodules.vtkCommonDataModel import ( vtkCellTypeUtilities, VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID,
                                            VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON )
from geos.mesh.stats.meshQualityMetricHelpers import ( QUALITY_METRIC_OTHER_START_INDEX, getAllCellTypesExtended,
                                                       getQualityMeasureNameFromIndex, getQualityMetricFromIndex,
                                                       MeshQualityMetricEnum, CellQualityMetricEnum,
                                                       VtkCellQualityMetricEnum, CellQualityMetricAdditionalEnum,
                                                       QualityMetricOtherEnum, QualityRange )
from geos.mesh.model.CellTypeCounts import CellTypeCounts

from packaging.version import Version
if Version( mpl.__version__ ) < Version( "3.3" ):
    from geos.mesh.model._bar_label import _bar_label

__doc__ = """
QualityMetricSummary stores the statistics of mesh quality metrics.

To use QualityMetricSummary:

.. code-block:: python

    from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes

    qualityMetricSummary: QualityMetricSummary = QualityMetricSummary()
    # Set data
    qualityMetricSummary.setCellTypeCounts(counts)
    qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(cellMetricIndex, cellType, statType, value))
    qualityMetricSummary.setOtherStatValueFromMetric(metricIndex, statType, value)

    # Get stats
    count: int = qualityMetricSummary.getCellTypeCountsOfCellType(cellType)
    value: float = qualityMetricSummary.getCellStatValueFromStatMetricAndCellType(cellMetricIndex, cellType, statType)
    subSetStats: pd.DataFrame = stats.getStatsFromMetric(cellMetricIndex)
    stats: pd.DataFrame = stats.getAllCellStats()

    # Output figure
    fig: Figure = stats.plotSummaryFigure()
"""


class StatTypes( Enum ):
    MEAN = ( 0, "Mean", float, np.nanmean )
    STD_DEV = ( 1, "StdDev", float, np.nanstd )
    MIN = ( 2, "Min", float, np.nanmin )
    MAX = ( 3, "Max", float, np.nanmax )
    COUNT = ( 4, "Count", int, lambda v: np.count_nonzero( np.isfinite( v ) ) )

    def getIndex( self: Self ) -> int:
        """Get stat index.

        Returns:
            int: Index
        """
        return self.value[ 0 ]

    def getString( self: Self ) -> str:
        """Get stat name.

        Returns:
            str: Name
        """
        return self.value[ 1 ]

    def getType( self: Self ) -> object:
        """Get stat type.

        Returns:
            object: Type
        """
        return self.value[ 2 ]

    def compute( self: Self, array: Iterable[ float ] ) -> Union[ int, float ]:
        """Compute statistics using function.

        Args:
            array (Iterable[float]): Input array

        Returns:
            int | float: Output stat
        """
        return self.value[ 3 ]( array )

    @staticmethod
    def getNameFromIndex( index: int ) -> str:
        """Get stat name from index.

        Args:
            index (int): Index

        Returns:
            str: Name
        """
        return list( StatTypes )[ index ].getString()

    @staticmethod
    def getIndexFromName( name: str ) -> int:
        """Get stat index from name.

        Args:
            name (str): Name

        Returns:
            int: Index
        """
        for stat in list( StatTypes ):
            if stat.getString() == name:
                return stat.getIndex()
        return -1

    @staticmethod
    def getTypeFromIndex( index: int ) -> object:
        """Get stat type from index.

        Args:
            index (int): Index

        Returns:
            object: Type
        """
        return list( StatTypes )[ index ].getType()


_RANGE_COLORS: tuple[ str, str, str ] = (
    'lightcoral',
    'sandybrown',
    'palegreen',
)


class QualityMetricSummary():

    _LEVELS: tuple[ str, str ] = ( "MetricIndex", "CellType" )
    _CELL_TYPES_PLOT: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON,
                                           VTK_POLYGON, VTK_POLYHEDRON )
    _CELL_TYPES_NAME: list[ str ] = [
        vtkCellTypeUtilities.GetClassNameFromTypeId( cellType ).removeprefix( "vtk" ) for cellType in _CELL_TYPES_PLOT
    ]

    def __init__( self: Self ) -> None:
        """CellTypeCounts stores the number of cells of each type."""
        #: stores for each cell type, and metric type, the stats
        self._counts: CellTypeCounts = CellTypeCounts()
        self._cellStats: pd.DataFrame
        self._meshOtherStats: pd.DataFrame
        self._initStats()

    def _initStats( self: Self ) -> None:
        """Initialize self._cellStats dataframe."""
        rows: list[ int ] = [ statType.getIndex() for statType in list( StatTypes ) ]
        nb_rows: int = len( rows )
        cellTypes: list[ int ] = getAllCellTypesExtended()
        indexes = [ ( metric.getMetricIndex(), cellType )
                    for metric in ( list( VtkCellQualityMetricEnum ) + list( CellQualityMetricAdditionalEnum ) )
                    for cellType in cellTypes if metric.isApplicableToCellType( cellType ) ]
        df_indexes: pd.MultiIndex = pd.MultiIndex.from_tuples( ( indexes ), names=self._LEVELS )
        nb_col: int = df_indexes.size
        self._cellStats = pd.DataFrame( np.full( ( nb_rows, nb_col ), np.nan ), columns=df_indexes, index=rows )

        columns = [ metric.getMetricIndex() for metric in list( QualityMetricOtherEnum ) ]
        self._meshOtherStats = pd.DataFrame( np.full( ( nb_rows, len( columns ) ), np.nan ),
                                             columns=columns,
                                             index=rows )

    def setCellTypeCounts( self: Self, counts: CellTypeCounts ) -> None:
        """Set cell type counts.

        Args:
            counts (CellTypeCounts): CellTypeCounts instance
        """
        self._counts = counts

    def getCellTypeCountsObject( self: Self ) -> int:
        """Get cell type counts.

        Returns:
            int: Number of cell
        """
        return self._counts

    def getCellTypeCountsOfCellType( self: Self, cellType: int ) -> int:
        """Get cell type counts.

        Returns:
            int: Number of cell
        """
        return self._counts.getTypeCount( cellType )

    def isCellStatsValidForMetricAndCellType(
        self: Self,
        metricIndex: int,
        cellType: int,
    ) -> bool:
        """Returns True if input quality metric applies to input cell type.

        Args:
            metricIndex (int): Metric index
            cellType (int): Cell type index

        Returns:
            bool: True if input quality metric applies
        """
        return bool( np.any( np.isfinite( self.getStatsFromMetricAndCellType( metricIndex, cellType ) ) ) )

    def getAllCellStats( self: Self ) -> pd.DataFrame:
        """Get all cell stats including nan values.

        Returns:
            pd.DataFrame: Stats
        """
        return self._cellStats

    def getAllValidCellStats( self: Self ) -> pd.DataFrame:
        """Get all valid cell stats.

        Returns:
            pd.DataFrame: Stats
        """
        return self._cellStats.dropna( axis=1 )

    def getAllValidOtherMetricStats( self: Self ) -> pd.DataFrame:
        """Get all valid other metric stats.

        Returns:
            pd.DataFrame: Stats
        """
        return self._meshOtherStats.dropna( axis=1 )

    def getCellStatValueFromStatMetricAndCellType(
        self: Self,
        metricIndex: int,
        cellType: int,
        statType: StatTypes,
    ) -> float:
        """Get cell stat value for the given metric and cell types.

        Args:
            metricIndex (int): Metric index
            cellType (int): Cell type index
            statType (StatTypes): Stat number

        Returns:
            float: Stats value
        """
        if ( metricIndex, cellType ) not in self._cellStats.columns:
            raise IndexError( f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats" )
        return self._cellStats[ ( metricIndex, cellType ) ][ statType.getIndex() ]

    def getStatsFromMetricAndCellType( self: Self, metricIndex: int, cellType: int ) -> pd.Series:
        """Get stats for the given metric and cell types.

        Args:
            metricIndex (int): Metric index
            cellType (int): Cell type index

        Returns:
            pd.Series: Stats
        """
        if ( metricIndex, cellType ) not in self._cellStats.columns:
            raise IndexError( f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats" )
        return self._cellStats[ ( metricIndex, cellType ) ]

    def getStatsFromMetric(
        self: Self,
        metricIndex: int,
    ) -> pd.DataFrame:
        """Get stats for the given metric index.

        Args:
            metricIndex (int): Metric index

        Returns:
            pd.DataFrame: Stats
        """
        if metricIndex < QUALITY_METRIC_OTHER_START_INDEX:
            return self._cellStats.xs( metricIndex, level=self._LEVELS[ 0 ], axis=1 )
        else:
            return self._meshOtherStats[ metricIndex ]

    def setOtherStatValueFromMetric( self: Self, metricIndex: int, statType: StatTypes, value: Union[ int,
                                                                                                      float ] ) -> None:
        """Set other stat value for the given metric.

        Args:
            metricIndex (int): Metric index
            statType (StatTypes): Stat number
            value (int | float): Value
        """
        if metricIndex not in self._meshOtherStats.columns:
            raise IndexError( f"Index {metricIndex} not in QualityMetricSummary meshOtherStats" )
        self._meshOtherStats.loc[ statType.getIndex(), metricIndex ] = value

    def getCellStatsFromCellType(
        self: Self,
        cellType: int,
    ) -> pd.DataFrame:
        """Get cell stats for the given cell type.

        Args:
            cellType (int): Cell type index

        Returns:
            pd.DataFrame: Stats
        """
        return self._cellStats.xs( cellType, level=self._LEVELS[ 1 ], axis=1 )

    def setCellStatValueFromStatMetricAndCellType( self: Self, metricIndex: int, cellType: int, statType: StatTypes,
                                                   value: Union[ int, float ] ) -> None:
        """Set cell stats for the given metric and cell types.

        Args:
            metricIndex (int): Metric index
            cellType (int): Cell type index
            statType (StatTypes): Stat number
            value (int | float): Value
        """
        if ( metricIndex, cellType ) not in self._cellStats.columns:
            raise IndexError( f"Index ({metricIndex}, {cellType}) not in QualityMetricSummary stats" )
        self._cellStats.loc[ statType.getIndex(), ( metricIndex, cellType ) ] = value

    def getComputedCellMetricIndexes( self: Self ) -> list[ int ]:
        """Get the list of index of computed cell quality metrics.

        Returns:
            List[int]: List of metrics index
        """
        validCellStats: pd.DataFrame = self.getAllValidCellStats()
        return validCellStats.columns.get_level_values( 0 ).unique().tolist()

    def getComputedOtherMetricIndexes( self: Self ) -> list[ Any ]:
        """Get the list of index of computed other quality metrics.

        Returns:
            tuple[int]: List of metrics index
        """
        validOtherStats: pd.DataFrame = self.getAllValidOtherMetricStats()
        columns: list[ int ] = [ validOtherStats.columns.to_list() ]
        return np.unique( columns ).tolist()

    def getAllComputedMetricIndexes( self: Self ) -> list[ Any ]:
        """Get the list of index of all computed metrics.

        Returns:
            tuple[int]: List of metrics index
        """
        return self.getComputedCellMetricIndexes() + self.getComputedOtherMetricIndexes()

    def plotSummaryFigure( self: Self ) -> Figure:
        """Plot quality metric summary figure.

        Returns:
            plt.figure: Output Figure
        """
        computedCellMetrics: list[ int ] = self.getComputedCellMetricIndexes()
        computedOtherMetrics: list[ int ] = self.getComputedOtherMetricIndexes()
        # Compute layout
        nbAxes: int = len( computedCellMetrics ) + len( computedOtherMetrics ) + 3
        ncols: int = 3
        nrows: int = 1
        # 3 columns for these number of axes, else 4 columns
        if nbAxes not in ( 1, 2, 3, 5, 6, 9 ):
            ncols = 6
        nrows = nbAxes // ncols
        if nbAxes % ncols > 0:
            nrows += 1
        figSize = ( ncols * 3, nrows * 4 )
        fig, axes = plt.subplots( nrows, ncols, figsize=figSize, tight_layout=True )
        axesFlat = axes.flatten()
        # Index of current axes
        currentAxIndex: int = 1

        # Plot cell types counts
        self._plotGlobalCellCount( axesFlat[ currentAxIndex ] )
        currentAxIndex += 1

        # Plot specific cell type counts
        self._plotCellTypeCounts( axesFlat[ currentAxIndex ] )
        currentAxIndex += 1

        ax: Axes
        # Plot cell quality metrics
        for metricIndex in computedCellMetrics:
            ax = axesFlat[ currentAxIndex ]
            self._plotCellMetricStats( ax, metricIndex )
            currentAxIndex += 1

        # Plot other mesh quality stats
        if len( computedOtherMetrics ) > 0:
            ax = axesFlat[ currentAxIndex ]
            self._plotOtherMetricStats( ax )
            currentAxIndex += 1

        # Plot legend
        self._plotLegend( axesFlat[ 0 ] )

        # Remove unused axes
        for ax in axesFlat[ currentAxIndex: ]:
            ax.remove()

        print(
            "Please refer to the Verdict Manual for metrics and range definitions.\n https://visit-sphinx-github-user-manual.readthedocs.io/en/v3.4.0/_downloads/9d944264b44b411aeb4a867a1c9b1ed5/VerdictManual-revA.pdf"
        )
        return fig

    def _plotLegend( self: Self, ax: Axes ) -> None:
        """Add a legend to the figure.

        Args:
            ax (Axes): Axes object
        """
        ax.axis( 'off' )
        handles = [
            Patch( facecolor=_RANGE_COLORS[ 0 ], label="full range" ),
            Patch( facecolor=_RANGE_COLORS[ 1 ], label="normal range" ),
            Patch( facecolor=_RANGE_COLORS[ 2 ], label="acceptable range" ),
            Patch( facecolor="None", edgecolor="black", label="range min-max" ),
            Line2D( [ 0 ], [ 0 ], color="black", marker="o", lw=2, label="standard deviation" ),
        ]

        ax.legend( handles=handles, frameon=False, loc="upper left" )

    def _plotCellTypeCounts( self: Self, ax: Axes ) -> None:
        """Plot cell type counts.

        Args:
            ax (Axes): Axes object
        """
        xticks: npt.NDArray[ np.int64 ] = np.arange( len( self._CELL_TYPES_PLOT[ :-2 ] ), dtype=int )
        toplot: list[ int ] = [ self._counts.getTypeCount( cellType ) for cellType in self._CELL_TYPES_PLOT[ :-2 ] ]
        p = ax.bar( self._CELL_TYPES_NAME[ :-2 ], toplot, alpha=0.6 )

        # bar_label only available for matplotlib version >= 3.3
        if Version( mpl.__version__ ) >= Version( "3.3" ):
            ax.bar_label( p, label_type='center', rotation=90, padding=20 )
        else:
            _bar_label( ax, p, toplot, label_type='center', rotation=90, padding=20 )

        ax.set_xticks( xticks )
        ax.set_xticklabels( self._CELL_TYPES_NAME[ :-2 ], rotation=30, ha="right" )
        ax.set_title( "Cell Type Counts" )

    def _plotGlobalCellCount( self: Self, ax: Axes ) -> None:
        """Plot polygon and polyhedra cell type counts along with the total number of cells.

        Args:
            ax (Axes): Subplot axes object
        """
        xticks: npt.NDArray[ np.int64 ] = np.arange( len( self._CELL_TYPES_PLOT[ -2: ] ) + 1, dtype=int )
        toplot: list[ int ] = [ self._counts.getTypeCount( VTK_POLYGON ),
                                self._counts.getTypeCount( VTK_POLYHEDRON ) ] + [ self._counts.getTotalCount() ]

        colors = [ "tab:blue" ] * len( toplot[ :-1 ] ) + [ "mediumblue" ]

        names = self._CELL_TYPES_NAME[ -2: ] + [ "Total count" ]
        p = ax.bar( names, toplot, alpha=0.6, color=colors )
        # bar_label only available for matplotlib version >= 3.3
        if Version( mpl.__version__ ) >= Version( "3.3" ):
            ax.bar_label( p, label_type='center', padding=10 )
        else:
            _bar_label( ax, p, toplot, label_type='center', padding=10 )
        ax.set_xticks( xticks )
        ax.set_xticklabels( names, rotation=30, ha="right" )
        ax.set_title( "Global Cell Type Counts" )

    def _plotOtherMetricStats( self: Self, ax0: Axes ) -> None:
        """Plot other metric stats.

        Args:
            ax0 (Axes): Axes object
            metricIndex (int): Metric index
        """
        # order of cell types in each axes
        computedMetrics: list[ int ] = self.getComputedOtherMetricIndexes()
        # get data to plot
        maxs: pd.Series = self._meshOtherStats.loc[ StatTypes.MAX.getIndex(), computedMetrics ]
        mins: pd.Series = self._meshOtherStats.loc[ StatTypes.MIN.getIndex(), computedMetrics ]
        means: pd.Series = self._meshOtherStats.loc[ StatTypes.MEAN.getIndex(), computedMetrics ]
        stdDev: pd.Series = self._meshOtherStats.loc[ StatTypes.STD_DEV.getIndex(), computedMetrics ]
        xticks: npt.NDArray[ np.int64 ] = np.arange( means.index.size, dtype=int )
        xtickslabels = [ getQualityMeasureNameFromIndex( metricIndex ) for metricIndex in computedMetrics ]
        # define colors
        cmap: mpl.colors.Colormap = plt.get_cmap( 'plasma' )
        colors = cmap( np.linspace( 0, 1, len( computedMetrics ) ) )

        # min max rectangle width
        recWidth: float = 0.5
        xtick: float = 0.0
        ax: Axes
        for k, metricIndex in enumerate( computedMetrics ):
            ax = ax0 if k == 0 else ax0.twinx()
            color = colors[ k ]
            # add rectangle from min to max
            x: float = xtick - recWidth / 2.0
            y: float = mins[ metricIndex ]
            recHeight: float = maxs[ metricIndex ] - mins[ metricIndex ]
            ax.add_patch( Rectangle( ( x, y ), recWidth, recHeight, edgecolor=color, fill=False, lw=1 ) )

            # plot mean and error bars for std dev
            ax.errorbar( k, means[ metricIndex ], yerr=stdDev[ metricIndex ], fmt='-o', color=color )
            xtick += 1.0

            # set y axis color
            ax.yaxis.label.set_color( color )
            ax.tick_params( axis='y', colors=color )

        # set x tick names
        ax0.set_xticks( xticks )
        ax0.set_xticklabels( xtickslabels, rotation=30, ha="right" )
        ax0.set_xlabel( "Mesh Quality Metric" )
        ax0.set_title( "Other Mesh Quality Metric" )

    def _plotCellMetricStats( self: Self, ax: Axes, metricIndex: int ) -> None:
        """Plot cell metric stats.

        Args:
            ax (Axes): Axes object
            metricIndex (int): Metric index
        """
        # Get data to plot
        maxs: pd.Series = self._cellStats.loc[ StatTypes.MAX.getIndex(), metricIndex ]
        mins: pd.Series = self._cellStats.loc[ StatTypes.MIN.getIndex(), metricIndex ]
        means: pd.Series = self._cellStats.loc[ StatTypes.MEAN.getIndex(), metricIndex ]
        stdDev: pd.Series = self._cellStats.loc[ StatTypes.STD_DEV.getIndex(), metricIndex ]

        # Order of cell types in each axes
        xtickslabels: list[ str ] = []
        # Min max rectangle width
        recWidth: float = 0.5
        # Range rectangle width
        rangeRecWidth: float = 1.8 * recWidth

        # Height
        ylim0: float = mins.min()
        ylim1: float = maxs.max()
        xtick: float = 0.0
        for k, cellType in enumerate( self._CELL_TYPES_PLOT ):
            if cellType in means.index and self.getCellTypeCountsOfCellType( cellType ) > 0 and not np.isnan(
                    means[ cellType ] ):
                xtickslabels += [ self._CELL_TYPES_NAME[ k ] ]
                # Add quality metric range
                self._plotRangePatch( ax, metricIndex, cellType, ylim0, ylim1, xtick, rangeRecWidth )

                # Add rectangle from min to max
                x: float = xtick - recWidth / 2.0
                y: float = mins[ cellType ]
                recHeight: float = maxs[ cellType ] - mins[ cellType ]
                ax.add_patch( Rectangle( ( x, y ), recWidth, recHeight, edgecolor='black', fill=False, lw=1 ) )

                # Plot mean and error bars for std dev
                ax.errorbar( xtick, means[ cellType ], yerr=stdDev[ cellType ], fmt='-o', color='k' )
                xtick += 1.0

        # Set y axis limits
        ax.set_ylim( ylim0 - abs( ylim0 ) * 0.1, 1.1 * ylim1 )

        # Set x ticks
        xticks: npt.NDArray[ np.int64 ] = np.arange( len( xtickslabels ), dtype=int )
        ax.set_xticks( xticks )
        ax.set_xticklabels( xtickslabels, rotation=30, ha="right" )
        ax.set_title( f"{getQualityMeasureNameFromIndex(metricIndex)}" )

    def _plotRangePatch( self: Self, ax: Axes, metricIndex: int, cellType: int, ylim0: float, ylim1: float,
                         xtick: float, rangeRecWidth: float ) -> tuple[ float, float ]:
        """Plot quality metric ranges.

        Args:
            ax (Axes): Axes object
            metricIndex (int): Metric index
            cellType (int): Cell type index
            ylim0 (float): Min y
            ylim1 (float): Max y
            xtick (float): Abscissa
            rangeRecWidth (float): Patch width

        Returns:
            tuple[float, float]: Tuple containing min y and max y
        """
        try:
            metric: MeshQualityMetricEnum = getQualityMetricFromIndex( metricIndex )
            assert isinstance( metric, CellQualityMetricEnum ), "Mesh quality metric is of wrong type."
            # Add quality range patches if relevant
            qualityRange: QualityRange | None = metric.getQualityRange( cellType )
            if qualityRange is not None:
                ( ylim0, ylim1 ) = self._plotQualityRange( ax, qualityRange, xtick - rangeRecWidth / 2.0,
                                                           ( ylim0, ylim1 ), rangeRecWidth )
            else:
                # Add white patch for tick alignment
                ax.add_patch(
                    Rectangle(
                        ( xtick - rangeRecWidth / 2.0, 0. ),
                        rangeRecWidth,
                        1.0,
                        facecolor='w',
                        fill=True,
                    ) )
        except AssertionError as e:
            print( "Cell quality metric range cannot be displayed due to: ", e )
        return ( ylim0, ylim1 )

    def _plotQualityRange( self: Self, ax: Axes, qualityRange: QualityRange, x: float, ylim: tuple[ float, float ],
                           rangeRecWidth: float ) -> tuple[ float, float ]:
        """Plot quality range patches.

        Args:
            ax (Axes): Axes object
            qualityRange (QualityRange): Quality ranges to plot
            x (float): Origin abscissa of the patches
            ylim (tuple[float, float]): Y limits for updates
            rangeRecWidth (float): Patch width

        Returns:
            tuple[float, float]: Y limits for updates
        """
        ylim0: float = ylim[ 0 ]
        ylim1: float = ylim[ 1 ]
        for k, ( vmin, vmax ) in enumerate(
            ( qualityRange.fullRange, qualityRange.normalRange, qualityRange.acceptableRange ) ):
            if not np.isfinite( vmin ):
                vmin = -1e12
            else:
                ylim0 = min( ylim0, vmin )
            if not np.isfinite( vmax ):
                vmax = 1e12
            else:
                ylim1 = max( ylim1, vmax )
            y: float = vmin
            recHeight = vmax - vmin
            ax.add_patch( Rectangle(
                ( x, y ),
                rangeRecWidth,
                recHeight,
                facecolor=_RANGE_COLORS[ k ],
                fill=True,
            ) )
        return ( ylim0, ylim1 )
