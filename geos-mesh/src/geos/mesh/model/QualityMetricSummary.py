# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
import pandas as pd
from enum import Enum
from typing import Any
from typing_extensions import Self, Iterable
from packaging.version import Version
import matplotlib as mpl
import matplotlib.cm as cm
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.figure import Figure
from matplotlib.axes import Axes
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID,
                                            VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON )
from geos.mesh.processing.meshQualityMetricHelpers import ( QUALITY_METRIC_OTHER_START_INDEX, getAllCellTypesExtended,
                                                            getQualityMeasureNameFromIndex, getQualityMetricFromIndex,
                                                            MeshQualityMetricEnum, CellQualityMetricEnum,
                                                            VtkCellQualityMetricEnum, CellQualityMetricAdditionalEnum,
                                                            QualityMetricOtherEnum, QualityRange )
from geos.mesh.model.CellTypeCounts import CellTypeCounts

__doc__ = """
QualityMetricSummary stores the statistics of mesh quality metrics.

To use QualityMetricSummary:

.. code-block:: python

    from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes

    qualityMetricSummary: QualityMetricSummary = QualityMetricSummary()
    # set data
    qualityMetricSummary.setCellTypeCounts(counts)
    qualityMetricSummary.setCellStatValueFromStatMetricAndCellType(cellMetricIndex, cellType, statType, value))
    qualityMetricSummary.setOtherStatValueFromMetric(metricIndex, statType, value)

    # get stats
    count: int = qualityMetricSummary.getCellTypeCountsOfCellType(cellType)
    value: float = qualityMetricSummary.getCellStatValueFromStatMetricAndCellType(cellMetricIndex, cellType, statType)
    subSetStats: pd.DataFrame = stats.getStatsFromMetric(cellMetricIndex)
    stats: pd.DataFrame = stats.getAllCellStats()

    # output figure
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

    def compute( self: Self, array: Iterable[ float ] ) -> int | float:
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
    _CELL_TYPES_PLOT: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_POLYGON, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE,
                                           VTK_HEXAHEDRON, VTK_POLYHEDRON )
    _CELL_TYPES_NAME: list[ str ] = [
        vtkCellTypes.GetClassNameFromTypeId( cellType ).removeprefix( "vtk" ) for cellType in _CELL_TYPES_PLOT
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
        print( self._meshOtherStats.head() )
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

    def setOtherStatValueFromMetric( self: Self, metricIndex: int, statType: StatTypes, value: int | float ) -> None:
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
                                                   value: int | float ) -> None:
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

    def getComputedCellMetricIndexes( self: Self ) -> list[ Any ]:
        """Get the list of index of computed cell quality metrics.

        Returns:
            tuple[int]: List of metrics index
        """
        validCellStats: pd.DataFrame = self.getAllValidCellStats()
        columns: list[ int ] = validCellStats.columns.get_level_values( 0 ).to_list()
        return np.unique( columns ).tolist()

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
        # compute layout
        nbAxes: int = len( computedCellMetrics ) + len( computedOtherMetrics ) + 1
        ncols: int = 3
        nrows: int = 1
        # 3 columns for these number of axes, else 4 columns
        if nbAxes not in ( 1, 2, 3, 5, 6, 9 ):
            ncols = 4
        nrows = nbAxes // ncols
        if nbAxes % ncols > 0:
            nrows += 1
        figSize = ( ncols * 3, nrows * 4 )
        fig, axes = plt.subplots( nrows, ncols, figsize=figSize, tight_layout=True )
        axesFlat = axes.flatten()
        # index of current axes
        currentAxIndex: int = 0

        # plot cell type counts
        self._plotCellTypeCounts( axesFlat[ 0 ] )
        currentAxIndex += 1

        # plot other mesh quality stats
        ax: Axes
        if len( computedOtherMetrics ) > 0:
            ax = axesFlat[ currentAxIndex ]
            self._plotOtherMetricStats( ax )
            currentAxIndex += 1
        # plot cell quality metrics
        for metricIndex in computedCellMetrics:
            ax = axesFlat[ currentAxIndex ]
            self._plotCellMetricStats( ax, metricIndex )
            currentAxIndex += 1

        # remove unused axes
        for ax in axesFlat[ currentAxIndex: ]:
            ax.remove()
        return fig

    def _plotCellTypeCounts( self: Self, ax: Axes ) -> None:
        """Plot cell type counts.

        Args:
            ax (Axes): Axes object
        """
        xticks: npt.NDArray[ np.int64 ] = np.arange( len( self._CELL_TYPES_PLOT ), dtype=int )
        toplot: list[ int ] = [ self._counts.getTypeCount( cellType ) for cellType in self._CELL_TYPES_PLOT ]
        p = ax.bar( self._CELL_TYPES_NAME, toplot )
        # bar_label only available for matplotlib version >= 3.3
        if Version( mpl.__version__ ) >= Version( "3.3" ):
            plt.bar_label( p, label_type='center', rotation=90, padding=5 )
        ax.set_xticks( xticks )
        ax.set_xticklabels( self._CELL_TYPES_NAME, rotation=30, ha="right" )
        ax.set_xlabel( "Cell types" )
        ax.set_title( "Cell Type Counts" )

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
        cmap: mpl.colors.Colormap = cm.get_cmap( 'plasma' )
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
        # get data to plot
        maxs: pd.Series = self._cellStats.loc[ StatTypes.MAX.getIndex(), metricIndex ]
        mins: pd.Series = self._cellStats.loc[ StatTypes.MIN.getIndex(), metricIndex ]
        means: pd.Series = self._cellStats.loc[ StatTypes.MEAN.getIndex(), metricIndex ]
        xticks: npt.NDArray[ np.int64 ] = np.arange( means.index.size, dtype=int )
        stdDev: pd.Series = self._cellStats.loc[ StatTypes.STD_DEV.getIndex(), metricIndex ]

        # order of cell types in each axes
        xtickslabels: list[ str ] = []
        # min max rectangle width
        recWidth: float = 0.5
        # range rectangle width
        rangeRecWidth: float = 1.8 * recWidth
        ylim0: float = mins.max()
        ylim1: float = maxs.min()
        xtick: float = 0.0
        for k, cellType in enumerate( self._CELL_TYPES_PLOT ):
            if cellType in means.index:
                xtickslabels += [ self._CELL_TYPES_NAME[ k ] ]
                # add quality metric range
                ( ylim0, ylim1 ) = self._plotRangePatch( ax, metricIndex, cellType, ylim0, ylim1, xtick, rangeRecWidth )
                # add rectangle from min to max
                x: float = xtick - recWidth / 2.0
                y: float = mins[ cellType ]
                recHeight: float = maxs[ cellType ] - mins[ cellType ]
                ax.add_patch( Rectangle( ( x, y ), recWidth, recHeight, edgecolor='black', fill=False, lw=1 ) )
                # plot mean and error bars for std dev
                ax.errorbar( xtick, means[ cellType ], yerr=stdDev[ cellType ], fmt='-o', color='k' )
                xtick += 1.0

        # set y axis limits
        ax.set_ylim( 0.1 * ylim0, 1.1 * ylim1 )
        # set x tick names
        ax.set_xticks( xticks )  #, xtickslabels, rotation=30, ha="right")
        ax.set_xticklabels( xtickslabels, rotation=30, ha="right" )
        ax.set_xlabel( "Cell types" )
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
            # add quality range patches if relevant
            qualityRange: QualityRange | None = metric.getQualityRange( cellType )
            if qualityRange is not None:
                ( ylim0, ylim1 ) = self._plotQualityRange( ax, qualityRange, xtick - rangeRecWidth / 2.0,
                                                           ( ylim0, ylim1 ), rangeRecWidth )
            else:
                # add white patch for tick alignment
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
