# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Bertrand Denel, Paloma Martinez
import logging
import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Any
from geos.utils.Logger import ( Logger, getLogger )

from vtkmodules.vtkCommonDataModel import vtkDataSet
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle

from geos.mesh.stats.tetrahedraAnalysisHelpers import ( getCoordinatesDoublePrecision, extractTetConnectivity,
                                                        analyzeAllTets, computeQualityScore )

__doc__ = """
TetQualityAnalysis module is a filter that performs an analysis of tetrahedras quality of one or several meshes and generates a plot as summary.

Filter input should be vtkUnstructuredGrid.


To use the filter:

.. code-block:: python
    from geos.processing.pre_processing.TetQualityAnalysis import TetQualityAnalysis

    # Filter inputs
    inputMesh: dict[str, vtkUnstructuredGrid]
    speHandler: bool # optional

    # Instantiate the filter
    tetQualityAnalysisFilter: TetQualityAnalysis = TetQualityAnalysis( inputMesh, speHandler )

    # Use your own handler (if speHandler is True)
    yourHandler: logging.Handler
    tetQualityAnalysisFilter.setLoggerHandler( yourHandler )

    # Change output filename [optional]
    tetQualityAnalysisFilter.SetFilename( filename )


    # Do calculations
    try:
        tetQualityAnalysisFilter.applyFilter()
    except ( ValueError, IndexError, TypeError, AttributeError ) as e:
        tetQualityAnalysisFilter.logger.error( f"The filter { tetQualityAnalysisFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { meshQualityEnhancedFilter.logger.name } failed due to: { e }"
        tetQualityAnalysisFilter.logger.critical( mess, exc_info=True )
"""

loggerName: str = "Tetrahedra Quality Analysis"


class TetQualityAnalysis:

    def __init__( self: Self, meshes: dict[ str, vtkDataSet ], speHandler: bool = False ) -> None:
        """Tetrahedra Quality Analysis.

        Args:
            meshes (dict[str,vtkUnstructuredGrid]): Meshes to analyze.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.meshes: dict[ str, vtkDataSet ] = meshes
        self.analyzedMesh: dict[ int, dict[ str, Any ] ] = {}
        self.issues: dict[ int, Any ] = {}
        self.qualityScore: dict[ int, Any ] = {}
        self.validMetrics: dict[ int, dict[ str, Any ] ] = {}
        self.medians: dict[ int, dict[ str, Any ] ] = {}
        self.sample: dict[ int, npt.NDArray[ Any ] ] = {}
        self.tets: dict[ int, int ] = {}
        self.filename = 'mesh_comparison.png'

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerName, True )
        else:
            self.logger = logging.getLogger( loggerName )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        self.handler = handler
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler'"
                                 " to True during the filter initialization." )

    def applyFilter( self: Self ) -> None:
        """Apply Tetrahedra Analysis."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        self.__loggerSection( "MESH COMPARISON DASHBOARD" )

        for n, ( nfilename, mesh ) in enumerate( self.meshes.items(), 1 ):
            coords = getCoordinatesDoublePrecision( mesh )
            tetrahedraIds, tetrahedraConnectivity = extractTetConnectivity( mesh )
            ntets = len( tetrahedraIds )

            self.logger.info( f" Mesh {n} info: \n" + f"  Name: {nfilename}\n" +
                              f"  Total cells: {mesh.GetNumberOfCells()}\n" + f"  Tetrahedra: {ntets}\n" +
                              f"  Points: {mesh.GetNumberOfPoints()}" + "\n" + "-" * 80 + "\n" )

            # Analyze both meshes
            self.analyzedMesh[ n ] = analyzeAllTets( n, coords, tetrahedraConnectivity )
            metrics = self.analyzedMesh[ n ]
            self.tets[ n ] = ntets

            # Extract data with consistent filtering
            validAspectRatio = np.isfinite( metrics[ 'aspectRatio' ] )
            validRadiusRatio = np.isfinite( metrics[ 'radiusRatio' ] )

            # Combined valid mask
            validMask = validAspectRatio & validRadiusRatio

            aspectRatio = metrics[ 'aspectRatio' ][ validMask ]
            radiusRatio = metrics[ 'radiusRatio' ][ validMask ]
            flatnessRatio = metrics[ 'flatnessRatio' ][ validMask ]
            volume = metrics[ 'volumes' ][ validMask ]
            shapeQuality = metrics[ 'shapeQuality' ][ validMask ]

            # Edge length data
            minEdge = metrics[ 'minEdge' ][ validMask ]
            maxEdge = metrics[ 'maxEdge' ][ validMask ]

            # Edge length ratio
            edgeRatio = maxEdge / np.maximum( minEdge, 1e-15 )

            # Dihedral angles
            minDihedral = metrics[ 'minDihedral' ][ validMask ]
            maxDihedral = metrics[ 'maxDihedral' ][ validMask ]
            dihedralRange = metrics[ 'dihedralRange' ][ validMask ]

            qualityScore = computeQualityScore( aspectRatio, shapeQuality, edgeRatio, minDihedral )

            # Store all values
            self.validMetrics[ n ] = {
                'aspectRatio': aspectRatio,
                'radiusRatio': radiusRatio,
                'flatnessRatio': flatnessRatio,
                'volume': volume,
                'shapeQuality': shapeQuality,
                'minEdge': minEdge,
                'maxEdge': maxEdge,
                'edgeRatio': edgeRatio,
                'minDihedral': minDihedral,
                'maxDihedral': maxDihedral,
                'dihedralRange': dihedralRange,
                'qualityScore': qualityScore
            }

            # # ==================== Print Distribution Statistics ====================

            # Problem element counts
            highAspectRatio = np.sum( aspectRatio > 100 )
            lowShapeQuality = np.sum( shapeQuality < 0.3 )
            lowFlatness = np.sum( flatnessRatio < 0.01 )
            highEdgeRatio = np.sum( edgeRatio > 10 )
            criticalMinDihedral = np.sum( minDihedral < 5 )
            criticalMaxDihedral = np.sum( maxDihedral > 175 )
            combined = np.sum( ( aspectRatio > 100 ) & ( shapeQuality < 0.3 ) )
            criticalCombo = np.sum( ( aspectRatio > 100 ) & ( shapeQuality < 0.3 ) & ( minDihedral < 5 ) )

            self.issues[ n ] = {
                "highAspectRatio": highAspectRatio,
                "lowShapeQuality": lowShapeQuality,
                "lowFlatness": lowFlatness,
                "highEdgeRatio": highEdgeRatio,
                "criticalMinDihedral": criticalMinDihedral,
                "criticalMaxDihedral": criticalMaxDihedral,
                "combined": combined,
                "criticalCombo": criticalCombo
            }

            # Overall quality scores
            excellent = np.sum( qualityScore > 80 ) / len( qualityScore ) * 100
            good = np.sum( ( qualityScore > 60 ) & ( qualityScore <= 80 ) ) / len( qualityScore ) * 100
            fair = np.sum( ( qualityScore > 30 ) & ( qualityScore <= 60 ) ) / len( qualityScore ) * 100
            poor = np.sum( qualityScore <= 30 ) / len( qualityScore ) * 100

            self.qualityScore[ n ] = { 'excellent': excellent, 'good': good, 'fair': fair, 'poor': poor }

            extremeAspectRatio = aspectRatio > 1e4
            self.issues[ n ][ "extremeAspectRatio" ] = extremeAspectRatio

            # Nearly degenerate elements
            degenerateElements = ( minDihedral < 0.1 ) | ( maxDihedral > 179.9 )
            self.issues[ n ][ "degenerate" ] = degenerateElements

            self.medians[ n ] = {
                "aspectRatio": np.median( self.validMetrics[ n ][ "aspectRatio" ] ),
                "shapeQuality": np.median( self.validMetrics[ n ][ "shapeQuality" ] ),
                "volume": np.median( self.validMetrics[ n ][ "volume" ] ),
                "minEdge": np.median( self.validMetrics[ n ][ "minEdge" ] ),
                "maxEdge": np.median( self.validMetrics[ n ][ "maxEdge" ] ),
                "edgeRatio": np.median( self.validMetrics[ n ][ "edgeRatio" ] ),
                "minDihedral": np.median( self.validMetrics[ n ][ "minDihedral" ] ),
                "maxDihedral": np.median( self.validMetrics[ n ][ "maxDihedral" ] ),
                "qualityScore": np.median( self.validMetrics[ n ][ "qualityScore" ] ),
            }

        # ==================== Report ====================

        self.printDistributionStatistics()

        self.__orderMeshes()

        self.printPercentileAnalysis()

        self.printQualityIssueSummary()

        self.printExtremeOutlierAnalysis()

        self.printSummary()

        self.computeDeltasFromBest()
        self.createComparisonDashboard()

        self.logger.info( f"The filter { self.logger.name } succeeded." )

    def printDistributionStatistics( self: Self ) -> None:
        """Print the distribution statistics for various metrics."""
        self.__loggerSection( "DISTRIBUTION STATISTICS (MIN / MEDIAN / MAX)" )

        def printMetricStats( metricName: str, name: str, fmt: str = '.2e' ) -> None:
            """Helper function to print min/median/max for a metric.

            Args:
                metricName (str): The metric name to display.
                name (str): Metric name in dict of values.
                fmt (str): Display format.
            """
            msg = f"{metricName}:\n"

            for n, _ in enumerate( self.meshes.items(), 1 ):
                data = self.validMetrics[ n ][ name ]
                msg += f"  Mesh{n:2}:  Min={data.min():<10{fmt}}Median={np.median(data):<10{fmt}}Max={data.max():<10{fmt}}\n"

            self.logger.info( msg )

        printMetricStats( "Aspect Ratio", 'aspectRatio' )
        printMetricStats( "Radius Ratio", 'radiusRatio' )
        printMetricStats( "Flatness Ratio", 'flatnessRatio' )
        printMetricStats( "Shape Quality", 'shapeQuality', fmt='.4f' )
        printMetricStats( "Volume", 'volume' )
        printMetricStats( "Min Edge Length", 'minEdge' )
        printMetricStats( "Max Edge Length", 'maxEdge' )
        printMetricStats( "Edge Length Ratio", 'edgeRatio', fmt='.2f' )
        printMetricStats( "Min Dihedral Angle (degrees)", 'minDihedral', fmt='.2f' )
        printMetricStats( "Max Dihedral Angle (degrees)", 'maxDihedral', fmt='.2f' )
        printMetricStats( "Dihedral Range (degrees)", 'dihedralRange', fmt='.2f' )
        printMetricStats( "Overall Quality Score (0-100)", 'qualityScore', fmt='.2f' )

    def printPercentileAnalysis( self: Self, fmt: str = '.2f' ) -> None:
        """Print percentile analysis.

        Args:
            fmt (str): Display formatting.
        """
        self.__loggerSection( "PERCENTILE ANALYSIS (25th / 75th / 90th / 99th)" )

        for metricName, name in zip( *[ (
                "Aspect Ratio", "Shape Quality", "Edge Length Ratio", "Min Dihedral Angle (degrees)",
                "Overall Quality Score" ), ( 'aspectRatio', 'shapeQuality', 'edgeRatio', 'minDihedral',
                                             'qualityScore' ) ] ):
            msg = f"{metricName}:\n"

            for n, _ in enumerate( self.meshes.items(), 1 ):
                data = self.validMetrics[ n ][ name ]
                p1 = np.percentile( data, [ 25, 75, 90, 99 ] )
                msg += f"  Mesh {n}: 25th = {p1[0]:<7,{fmt}}75th = {p1[1]:<7,{fmt}}90th = {p1[2]:<7,{fmt}}99th = {p1[3]:<7,{fmt}}\n"

            self.logger.info( msg )

    def printQualityIssueSummary( self: Self ) -> None:
        """Print the quality issues."""
        self.__loggerSection( "QUALITY ISSUE SUMMARY" )

        fmt = '.2f'
        for n, _ in enumerate( self.meshes.items(), 1 ):
            msg = f"Mesh {n} Issues:\n"

            w = False
            for issueType, name, reference in zip( *[ ( "Aspect Ratio > 100", "Shape Quality < 0.3", "Flatness < 0.01",
                                                        "Edge Ratio > 10", "Min Dihedral < 5°", "Max Dihedral > 175°",
                                                        "Combined (AR>100 & Q<0.3)",
                                                        "CRITICAL (AR>100 & Q<0.3 & MinDih<5°" ),
                                                      ( "highAspectRatio", "lowShapeQuality", "lowFlatness",
                                                        "highEdgeRatio", "criticalMinDihedral", "criticalMaxDihedral",
                                                        "combined", "criticalCombo" ),
                                                      ( 'aspectRatio', 'shapeQuality', "flatnessRatio", "edgeRatio",
                                                        "minDihedral", 'maxDihedral', 'aspectRatio',
                                                        'aspectRatio' ) ] ):
                pb = self.issues[ n ][ name ]
                m = len( self.validMetrics[ n ][ reference ] )
                pb / m * 100
                msg += f"  {f'{issueType}:':37}{pb:>8,} ({(pb/m*100):{fmt}}%)\n"
                if pb != 0:
                    w = True
            self.logger.warning( msg ) if w else self.logger.info( msg )

        self.compareIssuesFromBest()

        self.printOverallQualityScore()

    def printOverallQualityScore( self: Self ) -> None:
        """Print the quality score distribution from excellent to poor."""
        msg = "Overall Quality Score Distribution:\n"
        msg += f"   {'Mesh n':10}{'Excellent (>80)':20}{'Good (60-80)':17}{'Fair (30-60)':15}{'Poor (≤30)':15}\n"

        for n, _ in enumerate( self.meshes.items(), 1 ):
            qualityScore = self.qualityScore[ n ]
            msg += f"   {f'Mesh {n}':10}{qualityScore[ 'excellent' ]:10,.1f}%{qualityScore[ 'good' ]:15,.1f}%  {qualityScore[ 'fair' ]:15,.1f}%{qualityScore[ 'poor' ]:15,.1f}%\n"
        self.logger.info( msg )

    def printExtremeOutlierAnalysis( self: Self ) -> None:
        """Print the extreme outlier analysis results."""
        self.__loggerSection( "EXTREME OUTLIER ANALYSIS" )

        msg = "Elements with Aspect Ratio > 10,000:\n"
        msg2 = ""

        # Change log type to warning if problematic elements
        w = False
        w2 = False
        for n, _ in enumerate( self.meshes, 1 ):
            extremeAspectRatio = self.issues[ n ][ 'extremeAspectRatio' ]
            data = self.analyzedMesh[ n ]
            aspectRatio = data[ 'aspectRatio' ]

            if np.sum( extremeAspectRatio ) > 0:
                msg += f"  Mesh {n}: {np.sum(extremeAspectRatio):,} elements ({np.sum(extremeAspectRatio)/len(aspectRatio)*100:.3f}%)"
                w = True
                volume = data[ "volume" ]
                minDihedral = data[ "minDihedral" ]
                shapeQuality = data[ "shapeQuality" ]

                msg += f"    Worst AR:        {aspectRatio[extremeAspectRatio].max():.2e}\n"
                msg += f"    Avg volume:      {volume[extremeAspectRatio].mean():.2e}\n"
                msg += f"    Min dihedral:    {minDihedral[extremeAspectRatio].min():.2f}° - {minDihedral[extremeAspectRatio].mean():.2f}° (avg)\n"
                msg += f"    Shape quality:   {shapeQuality[extremeAspectRatio].min():.4f} - {shapeQuality[extremeAspectRatio].mean():.4f} (avg)\n"

                if np.sum( extremeAspectRatio ) > 10:
                    w2 = True
                    msg2 += f" Recommendation: Investigate/remove {np.sum(extremeAspectRatio):,} extreme elements in Mesh {n}\n   These are likely artifacts from mesh generation or geometry issues.\n"

        self.logger.warning( msg ) if w else self.logger.info( msg + "   N/A\n" )
        if w2:
            self.logger.warning( msg2 )

        # Nearly degenerate elements
        degMsg = "Nearly Degenerate Elements (dihedral < 0.1° or > 179.9°):\n"
        ww = False
        for n, _ in enumerate( self.meshes, 1 ):
            degenerate = self.issues[ n ][ "degenerate" ]
            data = self.validMetrics[ n ][ "minDihedral" ]
            if np.sum( degenerate ) > 0:
                ww = True
                degMsg += f"  Mesh {n}: {np.sum(degenerate):,} elements ({np.sum(degenerate)/len(data)*100:.3f}%)\n"

        self.logger.warning( degMsg ) if ww else self.logger.info( degMsg + "   N/A\n" )

    def printSummary( self: Self ) -> None:
        """Print the summary."""
        self.__loggerSection( "COMPARISON SUMMARY" )

        for n, _ in enumerate( self.meshes, 1 ):
            name = f"Mesh {n}"
            if n == self.best:
                name += " [BEST]"
            elif n == self.worst:
                name += " [LEAST GOOD]"

            msg = f"{name}\n"
            msg += f"  Tetrahedra: {self.tets[n]:,}\n"
            msg += f"  Median Aspect Ratio: {self.medians[n]['aspectRatio']:.2f}\n"
            msg += f"  Median Shape Quality: {self.medians[n]['shapeQuality']:.4f}\n"
            msg += f"  Median Volume: {self.medians[n]['volume']:.2e}\n"
            msg += f"  Median Min Edge: {self.medians[n]['minEdge']:.2e}\n"
            msg += f"  Median Max Edge: {self.medians[n]['maxEdge']:.2e}\n"
            msg += f"  Median Edge Ratio: {self.medians[n]['edgeRatio']:.2f}\n"
            msg += f"  Median Min Dihedral: {self.medians[n]['minDihedral']:.1f}°\n"
            msg += f"  Median Max Dihedral: {self.medians[n]['maxDihedral']:.1f}°\n"
            msg += f"  Median Quality Score: {self.medians[n]['qualityScore']:.1f}/100\n"

            self.logger.info( msg )

    def computeDeltasFromBest( self: Self ) -> None:
        """Compute and print the."""
        self.logger.info( f"Best mesh: Mesh {self.best}" )
        self.deltas: dict[ int, Any ] = {}

        for n, _ in enumerate( self.meshes, 1 ):
            self.deltas[ n ] = {}

            self.deltas[ n ][ "tetrahedra" ] = ( ( self.tets[ n ] - self.tets[ self.best ] ) / self.tets[ self.best ] *
                                                 100 ) if self.tets[ self.best ] > 0 else 0
            for metric in ( "aspectRatio", "shapeQuality", "volume", "minEdge", "maxEdge", "edgeRatio" ):
                value = self.medians[ n ][ metric ]
                valueBest = self.medians[ self.best ][ metric ]
                self.deltas[ n ][ metric ] = ( ( value - valueBest ) / valueBest * 100 ) if valueBest > 0 else 0

        deltaTets = [
            f"{self.deltas[ n ][ 'tetrahedra' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaAspectRatio = [
            f"{self.deltas[ n ][ 'aspectRatio' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaShapeQuality = [
            f"{self.deltas[ n ][ 'shapeQuality' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaVolume = [
            f"{self.deltas[ n ][ 'volume' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaMinEdge = [
            f"{self.deltas[ n ][ 'minEdge' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaMaxEdge = [
            f"{self.deltas[ n ][ 'maxEdge' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        deltaEdgeRatio = [
            f"{self.deltas[ n ][ 'edgeRatio' ]:>+12,.1f}%" if n != self.best else ""
            for n, _ in enumerate( self.meshes, 1 )
        ]
        names = [ f"{f'Mesh {n}':>13}" if n != self.best else "" for n, _ in enumerate( self.meshes, 1 ) ]

        self.logger.info( f"Changes vs BEST [Mesh {self.best}]:\n" + f"{'  Mesh:':<20}{('').join(names)}\n" +
                          f"{'  Tetrahedra:':<20}{('').join(deltaTets)}\n" +
                          f"{'  Aspect Ratio:':<20}{('').join(deltaAspectRatio)}\n" +
                          f"{'  Shape Quality:':<20}{('').join(deltaShapeQuality)}\n" +
                          f"{'  Volume:':<20}{('').join(deltaVolume)}\n" +
                          f"{'  Min Edge Length:':<20}{('').join(deltaMinEdge)}\n" +
                          f"{'  Max Edge Length:':<20}{('').join(deltaMaxEdge)}\n" +
                          f"{'  Edge Length Ratio:':<20}{('').join(deltaEdgeRatio)}\n" )

    def createComparisonDashboard( self: Self ) -> None:
        """Create the comparison dashboard."""
        lbl = [ f'Mesh {n}' for n, _ in enumerate( self.meshes, 1 ) ]
        # Determine smart plot limits

        ar99 = []
        for n, _ in enumerate( self.meshes, 1 ):
            ar99.append( np.percentile( self.validMetrics[ n ][ "aspectRatio" ], 99 ) )

        ar99Max = np.max( np.array( ar99 ) )

        if ar99Max < 10:
            arPlotLimit = 100
        elif ar99Max < 100:
            arPlotLimit = 1000
        else:
            arPlotLimit = 10000

        # Set style
        plt.rcParams[ 'figure.facecolor' ] = 'white'
        plt.rcParams.update( {
            'font.size': 9,
            'axes.titlesize': 10,
            'axes.labelsize': 9,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 8
        } )

        # Create figure with flexible layout
        fig = plt.figure( figsize=( 25, 20 ) )

        # Row 1: Executive Summary (3 columns - wider)
        gs_row1 = gridspec.GridSpec( 1, 3, figure=fig, left=0.05, right=0.95, top=0.94, bottom=0.84, wspace=0.20 )

        # Rows 2-5: Main dashboard (5 columns each)
        gs_main = gridspec.GridSpec( 4,
                                     5,
                                     figure=fig,
                                     left=0.05,
                                     right=0.95,
                                     top=0.80,
                                     bottom=0.05,
                                     hspace=0.35,
                                     wspace=0.30 )

        # Title
        suptitle = 'Mesh Quality Comparison Dashboard (Progressive Detail Layout)\n'
        suptitle += ( ' - ' ).join( [ f'Mesh {n}: {self.tets[n]} tets ' for n, _ in enumerate( self.meshes, 1 ) ] )
        # for n, _ in enumerate( self.meshes, 1 ):
        #     suptitle += f'Mesh {n}: {self.tets[n]:<15} tets '
        fig.suptitle( suptitle, fontsize=16, fontweight='bold', y=0.99 )

        # Color scheme
        color = plt.cm.tab10( np.arange( 20 ) )  # type: ignore[attr-defined]

        # ==================== ROW 1: EXECUTIVE SUMMARY ====================

        # 1. Overall Quality Score Distribution
        ax1 = fig.add_subplot( gs_row1[ 0, 0 ] )
        bins = np.linspace( 0, 100, 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            qualityScore = self.validMetrics[ n ][ 'qualityScore' ]
            ax1.hist( qualityScore,
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
            ax1.axvline( np.median( qualityScore ), color=color[ n - 1 ], linestyle='--', linewidth=2.5, alpha=0.9 )

        # Add quality zones
        ax1.axvspan( 0, 30, alpha=0.15, color='red', zorder=0 )
        ax1.axvspan( 30, 60, alpha=0.15, color='yellow', zorder=0 )
        ax1.axvspan( 60, 80, alpha=0.15, color='lightgreen', zorder=0 )
        ax1.axvspan( 80, 100, alpha=0.15, color='darkgreen', zorder=0 )

        # Add summary text   #### ONLY BEST AND WORST MESH?
        ax1.text(
            0.98,
            0.92,
            f'Median Score:\n{f"M{self.best}[+]:":<5}{np.median(self.validMetrics[self.best][ "qualityScore" ]):.1f}\n'
            + f'{f"M{self.worst}[-]:":<5}{np.median(self.validMetrics[self.worst][ "qualityScore" ]):.1f}\n\n' +
            f'Excellent (>80):\n{f"M{self.best}[+]:":<5}{self.qualityScore[self.best]["excellent"]:.1f}%\n' +
            f'{f"M{self.worst}[-]:":<5}{self.qualityScore[self.worst]["excellent"]:.1f}%',
            transform=ax1.transAxes,
            va='top',
            ha='right',
            bbox={
                "boxstyle": 'round',
                "facecolor": 'wheat',
                "alpha": 0.9
            },
            fontsize=9,
            fontweight='bold' )

        ax1.set_xlabel( 'Combined Quality Score', fontweight='bold' )
        ax1.set_ylabel( 'Count', fontweight='bold' )
        ax1.set_title( 'OVERALL MESH QUALITY VERDICT', fontsize=12, fontweight='bold', color='darkblue', pad=10 )
        ax1.legend( loc='upper left', fontsize=9 )
        ax1.grid( True, alpha=0.3 )

        # Add zone labels
        ax1.text( 15, ax1.get_ylim()[ 1 ] * 0.95, 'Poor', ha='center', fontsize=8, color='darkred' )
        ax1.text( 45, ax1.get_ylim()[ 1 ] * 0.95, 'Fair', ha='center', fontsize=8, color='orange' )
        ax1.text( 70, ax1.get_ylim()[ 1 ] * 0.95, 'Good', ha='center', fontsize=8, color='green' )
        ax1.text( 90, ax1.get_ylim()[ 1 ] * 0.95, 'Excellent', ha='center', fontsize=8, color='darkgreen' )

        # 2. Shape Quality vs Aspect Ratio
        ax2 = fig.add_subplot( gs_row1[ 0, 1 ] )

        # Create sample for plotting
        for n, _ in enumerate( self.meshes, 1 ):
            aspectRatio = self.validMetrics[ n ][ "aspectRatio" ]
            shapeQuality = self.validMetrics[ n ][ "shapeQuality" ]
            self.setSampleForPlot( aspectRatio, n )

            idx = self.sample[ n ]

            mask1Plot = aspectRatio[ idx ] < arPlotLimit

            ax2.scatter( aspectRatio[ idx ][ mask1Plot ],
                         shapeQuality[ idx ][ mask1Plot ],
                         alpha=0.4,
                         s=5,
                         color=color[ n - 1 ],
                         label=f'Mesh {n}',
                         edgecolors='none' )

        # Add quality threshold lines
        ax2.axhline( y=0.3, color='red', linestyle='--', linewidth=2, alpha=0.8, label='Poor (Q < 0.3)', zorder=5 )
        ax2.axhline( y=0.7, color='green', linestyle='--', linewidth=2, alpha=0.8, label='Good (Q > 0.7)', zorder=5 )
        ax2.axvline( x=100, color='orange', linestyle='--', linewidth=2, alpha=0.8, label='High AR (> 100)', zorder=5 )

        # Highlight problem zone
        problemZone = Rectangle( ( 100, 0 ),
                                 arPlotLimit - 100,
                                 0.3,
                                 alpha=0.2,
                                 facecolor='red',
                                 edgecolor='none',
                                 zorder=0 )
        ax2.add_patch( problemZone )

        # Count ALL elements
        np.sum( ( aspectRatio > 100 ) & ( shapeQuality < 0.3 ) )
        np.sum( aspectRatio > arPlotLimit )

        # Problem annotation
        annotateIssues = ( '\n' ).join(
            [ f"{f'M{n}':4}{np.sum(self.issues[n]['combined']):,}" for n, _ in enumerate( self.meshes, 1 ) ] )

        ax2.text( 0.98,
                  0.02,
                  'PROBLEM ELEMENTS\n(AR>100 & Q<0.3):\n\n' + annotateIssues,
                  transform=ax2.transAxes,
                  va='bottom',
                  ha='right',
                  bbox={
                      "boxstyle": 'round',
                      "facecolor": '#ffcccc',
                      "alpha": 0.95,
                      "edgecolor": 'darkred',
                      "linewidth": 2
                  },
                  fontsize=8,
                  fontweight='bold' )

        ax2.set_xscale( 'log' )
        ax2.set_xlabel( 'Aspect Ratio', fontweight='bold' )
        ax2.set_ylabel( 'Shape Quality', fontweight='bold' )
        ax2.set_title( 'KEY QUALITY INDICATOR: Shape Quality vs Aspect Ratio',
                       fontsize=12,
                       fontweight='bold',
                       color='darkred',
                       pad=10 )
        ax2.set_xlim( ( 1, arPlotLimit ) )
        ax2.set_ylim( ( 0, 1.05 ) )
        ax2.legend( loc='upper right', fontsize=7, framealpha=0.95 )
        ax2.grid( True, alpha=0.3 )

        # 3. Critical Issues Summary Table
        ax3 = fig.add_subplot( gs_row1[ 0, 2 ] )
        ax3.axis( 'off' )

        summaryStats = []
        summaryStats.append( [ 'CRITICAL ISSUE', f'BEST [M{self.best}]', f'WORST [M{self.worst}]', 'CHANGE' ] )
        summaryStats.append( [ '─' * 18, '─' * 10, '─' * 10, '─' * 10 ] )

        criticalCombo = self.issues[ self.best ][ "criticalCombo" ]
        criticalCombo2 = self.issues[ self.worst ][ "criticalCombo" ]

        aspectRatio = self.validMetrics[ self.best ][ "aspectRatio" ]
        aspectRatio2 = self.validMetrics[ self.worst ][ "aspectRatio" ]

        highAspectRatio = self.issues[ self.best ][ "highAspectRatio" ]
        highAspectRatio2 = self.issues[ self.worst ][ "highAspectRatio" ]

        lowShapeQuality = self.issues[ self.best ][ "lowShapeQuality" ]
        lowShapeQuality2 = self.issues[ self.worst ][ "lowShapeQuality" ]

        criticalMinDihedral = self.issues[ self.best ][ "criticalMinDihedral" ]
        criticalMinDihedral2 = self.issues[ self.worst ][ "criticalMinDihedral" ]

        criticalMaxDihedral = self.issues[ self.best ][ "criticalMaxDihedral" ]
        criticalMaxDihedral2 = self.issues[ self.worst ][ "criticalMaxDihedral" ]

        highEdgeRatio = self.issues[ self.best ][ "highEdgeRatio" ]
        highEdgeRatio2 = self.issues[ self.worst ][ "highEdgeRatio" ]

        summaryStats.append( [
            'CRITICAL Combo', f'{criticalCombo:,}', f'{criticalCombo2:,}',
            f'{((criticalCombo2-criticalCombo)/max(criticalCombo,1)*100):+.1f}%' if criticalCombo > 0 else 'N/A'
        ] )
        summaryStats.append( [
            '(AR>100 & Q<0.3', f'({criticalCombo/len(aspectRatio)*100:.2f}%)',
            f'({criticalCombo2/len(aspectRatio2)*100:.2f}%)', ''
        ] )
        summaryStats.append( [ ' & MinDih<5°)', '', '', '' ] )

        summaryStats.append( [ '', '', '', '' ] )
        summaryStats.append( [
            'AR > 100', f'{highAspectRatio:,}', f'{highAspectRatio2:,}',
            f'{((highAspectRatio2-highAspectRatio)/max(highAspectRatio,1)*100):+.1f}%'
        ] )

        summaryStats.append( [
            'Quality < 0.3', f'{lowShapeQuality:,}', f'{lowShapeQuality2:,}',
            f'{((lowShapeQuality2-lowShapeQuality)/max(lowShapeQuality,1)*100):+.1f}%'
        ] )

        summaryStats.append( [
            'MinDih < 5°', f'{criticalMinDihedral:,}', f'{criticalMinDihedral2:,}',
            f'{((criticalMinDihedral2-criticalMinDihedral)/max(criticalMinDihedral,1)*100):+.1f}%'
            if criticalMinDihedral > 0 else 'N/A'
        ] )

        summaryStats.append( [
            'MaxDih > 175°', f'{criticalMaxDihedral:,}', f'{criticalMaxDihedral2:,}',
            f'{((criticalMaxDihedral2-criticalMaxDihedral)/max(criticalMaxDihedral,1)*100):+.1f}%'
            if criticalMaxDihedral > 0 else 'N/A'
        ] )

        summaryStats.append( [
            'Edge Ratio > 10', f'{highEdgeRatio:,}', f'{highEdgeRatio2:,}',
            f'{((highEdgeRatio2-highEdgeRatio)/max(highEdgeRatio,1)*100):+.1f}%'
        ] )

        summaryStats.append( [ '─' * 18, '─' * 10, '─' * 10, '─' * 10 ] )
        summaryStats.append( [ 'Quality Grade', '', '', '' ] )
        excellent = self.qualityScore[ self.best ][ "excellent" ]
        excellent2 = self.qualityScore[ self.worst ][ "excellent" ]
        good = self.qualityScore[ self.best ][ "good" ]
        good2 = self.qualityScore[ self.worst ][ "good" ]
        poor = self.qualityScore[ self.best ][ "poor" ]
        poor2 = self.qualityScore[ self.worst ][ "poor" ]

        summaryStats.append(
            [ '  Excellent (>80)', f'{excellent:.1f}%', f'{excellent2:.1f}%', f'{excellent2-excellent:+.1f}%' ] )
        summaryStats.append( [ '  Good (60-80)', f'{good:.1f}%', f'{good2:.1f}%', f'{good2-good:+.1f}%' ] )
        summaryStats.append( [ '  Poor (≤30)', f'{poor:.1f}%', f'{poor2:.1f}%', f'{poor2-poor:+.1f}%' ] )

        table = ax3.table(
            cellText=summaryStats,
            cellLoc='left',
            bbox=[ 0, 0, 1, 1 ],  # type: ignore[arg-type]
            edges='open' )
        table.auto_set_font_size( False )
        table.set_fontsize( 8 )

        # Style header
        for i in range( 4 ):
            table[ ( 0, i ) ].set_facecolor( '#34495e' )
            table[ ( 0, i ) ].set_text_props( weight='bold', color='black', fontsize=9 )

        # Highlight CRITICAL row
        for col in range( 4 ):
            table[ ( 2, col ) ].set_facecolor( '#fadbd8' )
            table[ ( 2, col ) ].set_text_props( weight='bold', fontsize=9 )

        # Color code changes
        for row in [ 2, 6, 7, 8, 9, 10, 13, 14, 15 ]:
            if row < len( summaryStats ):
                changeText = summaryStats[ row ][ 3 ]
                if '%' in changeText and changeText != 'N/A':
                    val = float( changeText.replace( '%', '' ).replace( '+', '' ) )
                    if row in [ 2, 6, 7, 8, 9, 10, 15 ]:  # Lower is better
                        if val < -10:
                            table[ ( row, 3 ) ].set_facecolor( '#d5f4e6' )  # Green
                        elif val > 10:
                            table[ ( row, 3 ) ].set_facecolor( '#fadbd8' )  # Red
                    else:  # Higher is better (excellent, good)
                        if val > 10:
                            table[ ( row, 3 ) ].set_facecolor( '#d5f4e6' )
                        elif val < -10:
                            table[ ( row, 3 ) ].set_facecolor( '#fadbd8' )

        ax3.set_title( 'CRITICAL ISSUES SUMMARY', fontsize=12, fontweight='bold', color='darkgreen', pad=10 )

        # ==================== ROW 2: QUALITY DISTRIBUTIONS ====================

        # 4. Shape Quality Histogram
        ax4 = fig.add_subplot( gs_main[ 0, 0 ] )
        bins = np.linspace( 0, 1, 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            shapeQuality = self.validMetrics[ n ][ "shapeQuality" ]
            ax4.hist( shapeQuality,
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
        ax4.set_xlabel( 'Shape Quality', fontweight='bold' )
        ax4.set_ylabel( 'Count', fontweight='bold' )
        ax4.set_title( 'Shape Quality Distribution', fontweight='bold' )
        ax4.legend()
        ax4.grid( True, alpha=0.3 )

        # 5. Aspect Ratio Histogram
        ax5 = fig.add_subplot( gs_main[ 0, 1 ] )
        arMax = np.array( [ self.validMetrics[ n ][ "aspectRatio" ].max() for n, _ in enumerate( self.meshes, 1 ) ] )

        bins = np.logspace( 0, np.log10( min( arPlotLimit, arMax.max() ) ), 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            aspectRatio = self.validMetrics[ n ][ 'aspectRatio' ]
            ax5.hist( aspectRatio[ aspectRatio < arPlotLimit ],
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
        ax5.set_xscale( 'log' )
        ax5.set_xlabel( 'Aspect Ratio', fontweight='bold' )
        ax5.set_ylabel( 'Count', fontweight='bold' )
        ax5.set_title( 'Aspect Ratio Distribution', fontweight='bold' )
        ax5.legend()
        ax5.grid( True, alpha=0.3 )

        # 6. Min Dihedral Histogram
        ax6 = fig.add_subplot( gs_main[ 0, 2 ] )
        bins = np.linspace( 0, 90, 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            minDihedral = self.validMetrics[ n ][ "minDihedral" ]
            ax6.hist( minDihedral,
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
        ax6.axvline( 5, color='red', linestyle='--', linewidth=1.5, alpha=0.7 )
        ax6.set_xlabel( 'Min Dihedral Angle (degrees)', fontweight='bold' )
        ax6.set_ylabel( 'Count', fontweight='bold' )
        ax6.set_title( 'Min Dihedral Angle Distribution', fontweight='bold' )
        ax6.legend()
        ax6.grid( True, alpha=0.3 )

        # 7. Edge Ratio Histogram
        ax7 = fig.add_subplot( gs_main[ 0, 3 ] )
        bins = np.logspace( 0, 3, 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            edgeRatio = self.validMetrics[ n ][ "edgeRatio" ]
            ax7.hist( edgeRatio[ edgeRatio < 1000 ],
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
        ax7.set_xscale( 'log' )
        ax7.axvline( 1, color='green', linestyle='--', linewidth=1.5, alpha=0.7 )
        ax7.set_xlabel( 'Edge Length Ratio', fontweight='bold' )
        ax7.set_ylabel( 'Count', fontweight='bold' )
        ax7.set_title( 'Edge Length Ratio Distribution', fontweight='bold' )
        ax7.legend()
        ax7.grid( True, alpha=0.3 )

        # 8. Volume Histogram
        ax8 = fig.add_subplot( gs_main[ 0, 4 ] )
        volMin = np.array( [ self.validMetrics[ n ][ "volume" ].min() for n, _ in enumerate( self.meshes, 1 ) ] ).min()
        volMax = np.array( [ self.validMetrics[ n ][ "volume" ].max() for n, _ in enumerate( self.meshes, 1 ) ] ).max()

        bins = np.logspace( np.log10( volMin ), np.log10( volMax ), 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            volume = self.validMetrics[ n ][ "volume" ]
            ax8.hist( volume,
                      bins=bins,
                      alpha=0.6,
                      label=f'Mesh {n}',
                      color=color[ n - 1 ],
                      edgecolor='black',
                      linewidth=0.5 )
        ax8.set_xscale( 'log' )
        ax8.set_xlabel( 'Volume', fontweight='bold' )
        ax8.set_ylabel( 'Count', fontweight='bold' )
        ax8.set_title( 'Volume Distribution', fontweight='bold' )
        ax8.legend()
        ax8.grid( True, alpha=0.3 )

        # ==================== ROW 3: STATISTICAL COMPARISON (BOX PLOTS) ====================

        # 9. Shape Quality Box Plot
        ax9 = fig.add_subplot( gs_main[ 1, 0 ] )
        sq = [ self.validMetrics[ n ][ "shapeQuality" ] for n, _ in enumerate( self.meshes, 1 ) ]
        bp1 = ax9.boxplot( sq, labels=lbl, patch_artist=True, showfliers=False )  # type: ignore[call-arg]
        ax9.set_ylabel( 'Shape Quality', fontweight='bold' )
        ax9.set_title( 'Shape Quality Comparison', fontweight='bold' )
        ax9.grid( True, alpha=0.3, axis='y' )

        # 10. Aspect Ratio Box Plot
        ax10 = fig.add_subplot( gs_main[ 1, 1 ] )
        ar = [ self.validMetrics[ n ][ "aspectRatio" ] for n, _ in enumerate( self.meshes, 1 ) ]
        bp2 = ax10.boxplot( ar, labels=lbl, patch_artist=True, showfliers=False )  # type: ignore[call-arg]
        ax10.set_yscale( 'log' )
        ax10.set_ylabel( 'Aspect Ratio (log)', fontweight='bold' )
        ax10.set_title( 'Aspect Ratio Comparison', fontweight='bold' )
        ax10.grid( True, alpha=0.3, axis='y' )

        # 11. Min Dihedral Box Plot
        ax11 = fig.add_subplot( gs_main[ 1, 2 ] )
        minDihedral = [ self.validMetrics[ n ][ "minDihedral" ] for n, _ in enumerate( self.meshes, 1 ) ]
        bp3 = ax11.boxplot( minDihedral, labels=lbl, patch_artist=True, showfliers=False )  # type: ignore[call-arg]
        ax11.set_ylabel( 'Min Dihedral Angle (degrees)', fontweight='bold' )
        ax11.set_title( 'Min Dihedral Comparison', fontweight='bold' )
        ax11.grid( True, alpha=0.3, axis='y' )

        # 12. Edge Ratio Box Plot
        ax12 = fig.add_subplot( gs_main[ 1, 3 ] )
        edgeRatio = [ self.validMetrics[ n ][ "edgeRatio" ] for n, _ in enumerate( self.meshes, 1 ) ]
        bp4 = ax12.boxplot( edgeRatio, labels=lbl, patch_artist=True, showfliers=False )  # type: ignore[call-arg]
        ax12.set_yscale( 'log' )
        ax12.set_ylabel( 'Edge Length Ratio (log)', fontweight='bold' )
        ax12.set_title( 'Edge Ratio Comparison', fontweight='bold' )
        ax12.grid( True, alpha=0.3, axis='y' )

        # 13. Volume Box Plot
        ax13 = fig.add_subplot( gs_main[ 1, 4 ] )
        vol = [ self.validMetrics[ n ][ "volume" ] for n, _ in enumerate( self.meshes, 1 ) ]
        bp5 = ax13.boxplot( vol, labels=lbl, patch_artist=True, showfliers=False )  # type: ignore[call-arg]
        ax13.set_yscale( 'log' )
        ax13.set_ylabel( 'Volume (log)', fontweight='bold' )
        ax13.set_title( 'Volume Comparison', fontweight='bold' )
        ax13.grid( True, alpha=0.3, axis='y' )

        for n, _ in enumerate( self.meshes, 1 ):
            bp1[ 'boxes' ][ n - 1 ].set_facecolor( color[ n - 1 ] )
            bp1[ 'medians' ][ n - 1 ].set_color( "black" )
            bp2[ 'boxes' ][ n - 1 ].set_facecolor( color[ n - 1 ] )
            bp2[ 'medians' ][ n - 1 ].set_color( "black" )
            bp3[ 'boxes' ][ n - 1 ].set_facecolor( color[ n - 1 ] )
            bp3[ 'medians' ][ n - 1 ].set_color( "black" )
            bp4[ 'boxes' ][ n - 1 ].set_facecolor( color[ n - 1 ] )
            bp4[ 'medians' ][ n - 1 ].set_color( "black" )
            bp5[ 'boxes' ][ n - 1 ].set_facecolor( color[ n - 1 ] )
            bp5[ 'medians' ][ n - 1 ].set_color( "black" )

        # ==================== ROW 4: CORRELATION ANALYSIS (SCATTER PLOTS) ====================
        # 14. Shape Quality vs Aspect Ratio (duplicate for detail)
        ax14 = fig.add_subplot( gs_main[ 2, 0 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            idx = self.sample[ n ]
            aspectRatio = self.validMetrics[ n ][ 'aspectRatio' ]
            shapeQuality = self.validMetrics[ n ][ 'shapeQuality' ]
            mask1 = aspectRatio[ idx ] < arPlotLimit
            ax14.scatter( aspectRatio[ idx ][ mask1 ],
                          shapeQuality[ idx ][ mask1 ],
                          alpha=0.4,
                          s=5,
                          color=color[ n - 1 ],
                          label=f'Mesh {n}',
                          edgecolors='none' )
        ax14.set_xscale( 'log' )
        ax14.set_xlabel( 'Aspect Ratio', fontweight='bold' )
        ax14.set_ylabel( 'Shape Quality', fontweight='bold' )
        ax14.set_title( 'Shape Quality vs Aspect Ratio', fontweight='bold' )
        ax14.set_xlim( ( 1, arPlotLimit ) )
        ax14.set_ylim( ( 0, 1.05 ) )
        ax14.legend( loc='upper right', fontsize=7 )
        ax14.grid( True, alpha=0.3 )

        # 15. Aspect Ratio vs Flatness
        ax15 = fig.add_subplot( gs_main[ 2, 1 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            idx = self.sample[ n ]
            aspectRatio = self.validMetrics[ n ][ "aspectRatio" ]
            flatnessRatio = self.validMetrics[ n ][ 'flatnessRatio' ]
            mask1 = aspectRatio[ idx ] < arPlotLimit
            ax15.scatter( aspectRatio[ idx ][ mask1 ],
                          flatnessRatio[ idx ][ mask1 ],
                          alpha=0.4,
                          s=5,
                          color=color[ n - 1 ],
                          label=f'Mesh {n}',
                          edgecolors='none' )
        ax15.set_xscale( 'log' )
        ax15.set_yscale( 'log' )
        ax15.set_xlabel( 'Aspect Ratio', fontweight='bold' )
        ax15.set_ylabel( 'Flatness Ratio', fontweight='bold' )
        ax15.set_title( 'Aspect Ratio vs Flatness', fontweight='bold' )
        ax15.set_xlim( ( 1, arPlotLimit ) )
        ax15.legend( loc='upper right', fontsize=7 )
        ax15.grid( True, alpha=0.3 )

        # 16. Volume vs Aspect Ratio
        ax16 = fig.add_subplot( gs_main[ 2, 2 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            idx = self.sample[ n ]
            aspectRatio = self.validMetrics[ n ][ "aspectRatio" ]
            volume = self.validMetrics[ n ][ 'volume' ]
            mask1 = aspectRatio[ idx ] < arPlotLimit
            ax16.scatter( volume[ idx ][ mask1 ],
                          aspectRatio[ idx ][ mask1 ],
                          alpha=0.4,
                          s=5,
                          color=color[ n - 1 ],
                          label=f'Mesh {n}',
                          edgecolors='none' )
        ax16.set_xscale( 'log' )
        ax16.set_yscale( 'log' )
        ax16.set_xlabel( 'Volume', fontweight='bold' )
        ax16.set_ylabel( 'Aspect Ratio', fontweight='bold' )
        ax16.set_title( 'Volume vs Aspect Ratio', fontweight='bold' )
        ax16.set_ylim( ( 1, arPlotLimit ) )
        ax16.legend( loc='upper right', fontsize=7 )
        ax16.grid( True, alpha=0.3 )

        # 17. Volume vs Shape Quality
        ax17 = fig.add_subplot( gs_main[ 2, 3 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            idx = self.sample[ n ]
            volume = self.validMetrics[ n ][ 'volume' ]
            shapeQuality = self.validMetrics[ n ][ 'shapeQuality' ]
            ax17.scatter( volume[ idx ],
                          shapeQuality[ idx ],
                          alpha=0.4,
                          s=5,
                          color=color[ n - 1 ],
                          label=f'Mesh {n}',
                          edgecolors='none' )
        ax17.set_xscale( 'log' )
        ax17.set_xlabel( 'Volume', fontweight='bold' )
        ax17.set_ylabel( 'Shape Quality', fontweight='bold' )
        ax17.set_title( 'Volume vs Shape Quality', fontweight='bold' )
        ax17.legend( loc='upper right', fontsize=7 )
        ax17.grid( True, alpha=0.3 )

        # 18. Edge Ratio vs Volume
        ax18 = fig.add_subplot( gs_main[ 2, 4 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            idx = self.sample[ n ]
            volume = self.validMetrics[ n ][ 'volume' ]
            edgeRatio = self.validMetrics[ n ][ 'edgeRatio' ]
            ax18.scatter( volume[ idx ],
                          edgeRatio[ idx ],
                          alpha=0.4,
                          s=5,
                          color=color[ n - 1 ],
                          label=f'Mesh {n}',
                          edgecolors='none' )
        ax18.axhline( y=1, color='green', linestyle='--', linewidth=1.5, alpha=0.7 )
        ax18.set_xscale( 'log' )
        ax18.set_yscale( 'log' )
        ax18.set_xlabel( 'Volume', fontweight='bold' )
        ax18.set_ylabel( 'Edge Length Ratio', fontweight='bold' )
        ax18.set_title( 'Edge Ratio vs Volume', fontweight='bold' )
        ax18.legend( loc='upper right', fontsize=7 )
        ax18.grid( True, alpha=0.3 )

        # ==================== ROW 5: DETAILED DIAGNOSTICS ====================

        # 19. Min Edge Length Histogram
        ax19 = fig.add_subplot( gs_main[ 3, 0 ] )
        edgeMinMin = np.array( [ self.validMetrics[ n ][ "minEdge" ].min()
                                 for n, _ in enumerate( self.meshes, 1 ) ] ).min()
        edgeMaxMin = np.array( [ self.validMetrics[ n ][ "minEdge" ].max()
                                 for n, _ in enumerate( self.meshes, 1 ) ] ).min()

        bins = np.logspace( np.log10( edgeMinMin ), np.log10( edgeMaxMin ), 40 ).tolist()

        for n, _ in enumerate( self.meshes, 1 ):
            minEdge = self.validMetrics[ n ][ 'minEdge' ]
            ax19.hist( minEdge,
                       bins=bins,
                       alpha=0.6,
                       label=f'Mesh {n}',
                       color=color[ n - 1 ],
                       edgecolor='black',
                       linewidth=0.5 )
            ax19.axvline( np.median( minEdge ), color=color[ n - 1 ], linestyle=':', linewidth=2, alpha=0.8 )
        ax19.set_xscale( 'log' )

        ax19.set_xlabel( 'Minimum Edge Length', fontweight='bold' )
        ax19.set_ylabel( 'Count', fontweight='bold' )
        ax19.set_title( 'Min Edge Length Distribution', fontweight='bold' )
        ax19.legend()
        ax19.grid( True, alpha=0.3 )

        # 20. Max Edge Length Histogram
        ax20 = fig.add_subplot( gs_main[ 3, 1 ] )
        edgeMaxMax = np.array( [ self.validMetrics[ n ][ "maxEdge" ].max()
                                 for n, _ in enumerate( self.meshes, 1 ) ] ).max()
        edgeMinMax = np.array( [ self.validMetrics[ n ][ "maxEdge" ].min()
                                 for n, _ in enumerate( self.meshes, 1 ) ] ).min()

        bins = np.logspace( np.log10( edgeMinMax ), np.log10( edgeMaxMax ), 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            maxEdge = self.validMetrics[ n ][ "maxEdge" ]
            ax20.hist( maxEdge,
                       bins=bins,
                       alpha=0.6,
                       label=f'Mesh {n}',
                       color=color[ n - 1 ],
                       edgecolor='black',
                       linewidth=0.5 )
            ax20.axvline( np.median( maxEdge ), color=color[ n - 1 ], linestyle=':', linewidth=2, alpha=0.8 )
        ax20.set_xscale( 'log' )
        ax20.set_xlabel( 'Maximum Edge Length', fontweight='bold' )
        ax20.set_ylabel( 'Count', fontweight='bold' )
        ax20.set_title( 'Max Edge Length Distribution', fontweight='bold' )
        ax20.legend()
        ax20.grid( True, alpha=0.3 )

        # 21. Max Dihedral Histogram
        ax21 = fig.add_subplot( gs_main[ 3, 2 ] )
        bins = np.linspace( 90, 180, 40 ).tolist()
        for n, _ in enumerate( self.meshes, 1 ):
            maxDihedral = self.validMetrics[ n ][ "maxDihedral" ]
            ax21.hist( maxDihedral,
                       bins=bins,
                       alpha=0.6,
                       label=f'Mesh {n}',
                       color=color[ n - 1 ],
                       edgecolor='black',
                       linewidth=0.5 )
        ax21.axvline( 175, color='red', linestyle='--', linewidth=1.5, alpha=0.7 )
        ax21.set_xlabel( 'Max Dihedral Angle (degrees)', fontweight='bold' )
        ax21.set_ylabel( 'Count', fontweight='bold' )
        ax21.set_title( 'Max Dihedral Angle Distribution', fontweight='bold' )
        ax21.legend()
        ax21.grid( True, alpha=0.3 )

        # 22. Dihedral Range Box Plot
        ax22 = fig.add_subplot( gs_main[ 3, 3 ] )
        nmesh = len( self.meshes )
        positions = np.delete( np.arange( 1, nmesh * 2 + 2 ), nmesh )
        dih = [ self.validMetrics[ n ][ "minDihedral" ] for n, _ in enumerate( self.meshes, 1 )
               ] + [ self.validMetrics[ n ][ "maxDihedral" ] for n, _ in enumerate( self.meshes, 1 ) ]
        lbl_boxplot = [ f'M{n}Min' for n, _ in enumerate( self.meshes, 1 )
                       ] + [ f'M{n}Max' for n, _ in enumerate( self.meshes, 1 ) ]
        boxplot_color = [ n for n, _ in enumerate( self.meshes, ) ] * 2
        bp_dih = ax22.boxplot(
            dih,
            positions=positions,
            labels=lbl_boxplot,  # type: ignore[call-arg]
            patch_artist=True,
            showfliers=False,
            widths=0.6 )
        for m in range( len( self.meshes ) * 2 ):
            bp_dih[ 'boxes' ][ m ].set_facecolor( color[ boxplot_color[ m ] ] )
            bp_dih[ 'medians' ][ m ].set_color( "black" )

        ax22.axhline( 5, color='red', linestyle='--', linewidth=1, alpha=0.5, zorder=0 )
        ax22.axhline( 175, color='red', linestyle='--', linewidth=1, alpha=0.5, zorder=0 )
        ax22.axhline( 70.5, color='green', linestyle=':', linewidth=1, alpha=0.5, zorder=0 )
        ax22.set_ylabel( 'Dihedral Angle (degrees)', fontweight='bold' )
        ax22.set_title( 'Dihedral Angle Comparison', fontweight='bold' )
        ax22.grid( True, alpha=0.3, axis='y' )

        # 23. Shape Quality CDF
        ax23 = fig.add_subplot( gs_main[ 3, 4 ] )
        for n, _ in enumerate( self.meshes, 1 ):
            shapeQuality = self.validMetrics[ n ][ "shapeQuality" ]
            sorted_sq1 = np.sort( shapeQuality )
            cdf_sq1 = np.arange( 1, len( sorted_sq1 ) + 1 ) / len( sorted_sq1 ) * 100
            ax23.plot( sorted_sq1, cdf_sq1, color=color[ n - 1 ], linewidth=2, label=f'Mesh {n}' )

        ax23.axvline( 0.3, color='red', linestyle='--', linewidth=1, alpha=0.5 )
        ax23.axvline( 0.7, color='green', linestyle='--', linewidth=1, alpha=0.5 )
        ax23.axhline( 50, color='gray', linestyle='--', linewidth=1, alpha=0.5 )
        ax23.set_xlabel( 'Shape Quality', fontweight='bold' )
        ax23.set_ylabel( 'Cumulative %', fontweight='bold' )
        ax23.set_title( 'Cumulative Distribution - Shape Quality', fontweight='bold' )
        ax23.legend( loc='lower right' )
        ax23.grid( True, alpha=0.3 )

        # Save figure

        plt.savefig( self.filename, dpi=300, bbox_inches='tight', facecolor='white' )
        self.logger.info( f"Dashboard saved successfully: {self.filename}" )

    def setDashboardFilename( self: Self, filename: str ) -> None:
        """Set comparison dashboard output filename.

        Args:
            filename (str): Output filename.
        """
        self.filename = filename

    def __loggerSection( self: Self, sectionName: str ) -> None:
        self.logger.info( "=" * 80 )
        self.logger.info( sectionName )
        self.logger.info( "=" * 80 )

    def __orderMeshes( self: Self ) -> None:
        """Proposition of ordering as fonction of median quality score."""
        self.__loggerSection( "ORDERING MESHES (from median quality score)" )
        medianScore = {
            n: np.median( self.validMetrics[ n ][ "qualityScore" ] )
            for n, _ in enumerate( self.meshes, 1 )
        }

        sortedMeshes = sorted( medianScore.items(), key=lambda x: x[ 1 ], reverse=True )
        self.sorted = sortedMeshes
        self.best = sortedMeshes[ 0 ][ 0 ]
        self.worst = sortedMeshes[ -1 ][ 0 ]

        self.logger.info( "Mesh order from median quality score:" )
        top = [ f"Mesh {m[0]} ({m[1]:.2f})" for m in sortedMeshes ]
        toprint: str = ( " > " ).join( top )
        self.logger.info( " [+] " + toprint + " [-]\n" )

    def compareIssuesFromBest( self: Self ) -> None:
        """Compare issues values vs [BEST] mesh."""
        highAspectRatioBest = self.issues[ self.best ][ "highAspectRatio" ]
        criticalMinDihedralBest = self.issues[ self.best ][ "criticalMinDihedral" ]
        lowShapeQualityBest = self.issues[ self.best ][ "lowShapeQuality" ]
        criticalComboBest = self.issues[ self.best ][ "criticalCombo" ]

        def getPercentChange( data: np.float64, ref: np.float64 ) -> np.float64:
            """Compute and return the percent change.

            Args:
                data (np.float64): Data to compare.
                ref (np.float64): Reference.

            Returns:
                np.float64: The percent change from reference.
            """
            return ( data - ref ) / max( ref, 1 ) * 100

        msg: str = f"Change from BEST [Mesh {self.best}]\n"
        msg += f"  {'Mesh':20}" + ( "" ).join( [ f"{f'Mesh {n}':>16}" for n, _ in enumerate( self.meshes, 1 ) ] ) + "\n"
        highAspectRatio: list[ str ] = [
            f"{getPercentChange( self.issues[ n ][ 'highAspectRatio' ], highAspectRatioBest ):>+15,.1f}%"
            if n != self.best else f"{'N/A':>16}" for n, _ in enumerate( self.meshes, 1 )
        ]
        lowShapeQuality: list[ str ] = [
            f"{getPercentChange( self.issues[ n ][ 'lowShapeQuality' ], lowShapeQualityBest ):>+15,.1f}%"
            if n != self.best else f"{'N/A':>16}" for n, _ in enumerate( self.meshes, 1 )
        ]
        criticalMinDihedral: list[ str ] = [
            f"{getPercentChange( self.issues[ n ][ 'criticalMinDihedral' ], criticalMinDihedralBest ):>+15,.1f}%"
            if criticalMinDihedralBest > 0 and n != self.best else f"{'N/A':>16}"
            for n, _ in enumerate( self.meshes, 1 )
        ]
        criticalCombo: list[ str ] = [
            f"{getPercentChange( self.issues[ n ][ 'criticalCombo' ], criticalComboBest ):>+15,.1f}%"
            if criticalComboBest > 0 and n != self.best else f"{'N/A':>16}" for n, _ in enumerate( self.meshes, 1 )
        ]

        msg += f"{'  AR > 100:':20}{('').join( highAspectRatio )}\n"
        msg += f"{'  Quality < 0.3:':20}{('').join( lowShapeQuality )}\n"
        msg += f"{'  MinDih < 5°:':20}{('').join( criticalMinDihedral )}\n"
        msg += f"{'  CRITICAL combo:':20}{('').join( criticalCombo )}\n"

        self.logger.info( msg )

    def setSampleForPlot( self: Self, data: npt.NDArray[ Any ], n: int ) -> None:
        """Set sampling for a given metric of mesh n.

        Args:
            data (npt.NDArray[Any]): Metric array to sample.
            n (int): Mesh id.
        """
        sampleSize = min( 10000, len( data ) )
        self.sample[ n ] = np.random.choice( len( data ), sampleSize, replace=False )
