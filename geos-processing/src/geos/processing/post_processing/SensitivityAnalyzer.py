# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================
import pandas as pd
from pathlib import Path
import numpy as np
from matplotlib.colors import Normalize
from matplotlib.cm import ScalarMappable
import matplotlib.pyplot as plt
from typing_extensions import Any, Self


from vtkmodules.vtkCommonDataModel import vtkCellData, vtkDataSet, vtkPolyData, vtkUnstructuredGrid

from geos.utils.pieceEnum import Piece
from geos.mesh.utils.arrayHelpers import ( getArrayInObject )
from geos.processing.post_processing.MohrCoulomb import (  MohrCoulomb )

from geos.processing.post_processing.ProfileExtractor import ( ProfileExtractor )


class SensitivityAnalyzer:
    """Performs sensitivity analysis on Mohr-Coulomb parameters."""

    # -------------------------------------------------------------------
    def __init__( self: Self, outputDir: str = ".", showPlots: bool = True ) -> None:
        """Init."""
        self.outputDir = Path( outputDir )
        self.outputDir.mkdir( exist_ok=True )
        self.results: list[ dict[ str, Any ] ] = []
        self.showPlots = showPlots

    # -------------------------------------------------------------------
    def runAnalysis( self: Self, surfaceWithStress, time: float, sensitivityFrictionAngles: list[float], sensitivityCohesions: list[float], profileStartPoints: list[tuple[float]], profileSearchRadius: list[tuple[float]] ) -> list[ dict[ str, Any ] ]:
        """Run sensitivity analysis for multiple friction angles and cohesions."""
        frictionAngles = sensitivityFrictionAngles
        cohesions = sensitivityCohesions

        print( "\n" + "=" * 60 )
        print( "SENSITIVITY ANALYSIS" )
        print( "=" * 60 )
        print( f"Friction angles: {frictionAngles}" )
        print( f"Cohesions: {cohesions}" )
        print( f"Total combinations: {len(frictionAngles) * len(cohesions)}" )

        results = []
        for frictionAngle in frictionAngles:
            for cohesion in cohesions:
                print( f"\n→ Testing φ={frictionAngle}°, C={cohesion} bar" )

                surfaceCopy = type(surfaceWithStress)()
                surfaceCopy.DeepCopy( surfaceWithStress )

                surfaceAnalyzed = MohrCoulomb.analyze(
                    surfaceCopy,
                    cohesion,
                    frictionAngle,
                    verbose=False )

                stats = self._extractStatistics( surfaceAnalyzed, frictionAngle, cohesion )
                results.append( stats )

                print( f"   Unstable: {stats['nUnstable']}, "
                       f"Critical: {stats['nCritical']}, "
                       f"Stable: {stats['nStable']}" )

        self.results = results

        # Generate plots
        self._plotSensitivityResults( results, time )

        # Plot SCU vs depth
        self._plotSCUDepthProfiles( results, time, surfaceWithStress, profileStartPoints, profileSearchRadius )

        return results

    # -------------------------------------------------------------------
    def _extractStatistics( self: Self, surface: vtkPolyData, frictionAngle: float,
                            cohesion: float ) -> dict[ str, Any ]:
        """Extract statistical metrics from analyzed surface."""
        stability = getArrayInObject( surface, "stabilityState", Piece.CELLS )
        SCU = getArrayInObject( surface, "SCU", Piece.CELLS )
        failureProba = getArrayInObject( surface, "failureProbability", Piece.CELLS )
        safetyMargin = getArrayInObject( surface, "safetyMargin", Piece.CELLS )

        nCells = surface.GetNumberOfCells()


        stats = {
            'frictionAngle': frictionAngle,
            'cohesion': cohesion,
            'nCells': nCells,
            'nStable': np.sum( stability == 0 ),
            'nCritical': np.sum( stability == 1 ),
            'nUnstable': np.sum( stability == 2 ),
            'pctUnstable': np.sum( stability == 2 ) / nCells * 100,
            'pctCritical': np.sum( stability == 1 ) / nCells * 100,
            'pctStable': np.sum( stability == 0 ) / nCells * 100,
            'meanSCU': np.mean( SCU ),
            'maxSCU': np.max( SCU ),
            'meanFailureProb': np.mean( failureProba ),
            'meanSafetyMargin': np.mean( safetyMargin ),
            'minSafetyMargin': np.min( safetyMargin )
        }

        return stats

    # -------------------------------------------------------------------
    def _plotSensitivityResults( self: Self, results: list[ dict[ str, Any ] ], time: float ) -> None:
        """Create comprehensive sensitivity analysis plots."""
        df = pd.DataFrame( results )

        fig, axes = plt.subplots( 2, 2, figsize=( 16, 12 ) )

        # Plot heatmaps
        self._plotHeatMap( df, 'pctUnstable', 'Unstable Cells [%]', axes[ 0, 0 ] )
        self._plotHeatMap( df, 'pctCritical', 'Critical Cells [%]', axes[ 0, 1 ] )
        self._plotHeatMap( df, 'meanSCU', 'Mean SCU [-]', axes[ 1, 0 ] )
        self._plotHeatMap( df, 'meanSafetyMargin', 'Mean Safety Margin [bar]', axes[ 1, 1 ] )

        fig.tight_layout()

        years = time / ( 365.25 * 24 * 3600 )
        filename = f'sensitivity_analysis_{years:.0f}y.png'
        fig.savefig( self.outputDir / filename, dpi=300, bbox_inches='tight' )
        print( f"\n📊 Sensitivity plot saved: {filename}" )

        if self.showPlots:
            fig.show()

    # -------------------------------------------------------------------
    def _plotHeatMap( self: Self, df: pd.DataFrame, column: str, title: str, ax: plt.Axes ) -> None:
        """Create a single heatmap for sensitivity analysis."""
        pivot = df.pivot( index='cohesion', columns='frictionAngle', values=column )

        im = ax.imshow( pivot.values, cmap='RdYlGn_r', aspect='auto', origin='lower' )

        ax.set_xticks( np.arange( len( pivot.columns ) ) )
        ax.set_yticks( np.arange( len( pivot.index ) ) )
        ax.set_xticklabels( pivot.columns )
        ax.set_yticklabels( pivot.index )

        ax.set_xlabel( 'Friction Angle [°]' )
        ax.set_ylabel( 'Cohesion [bar]' )
        ax.set_title( title )

        # Add values in cells
        for i in range( len( pivot.index ) ):
            for j in range( len( pivot.columns ) ):
                value = pivot.values[ i, j ]
                textColor = 'white' if value > pivot.values.max() * 0.5 else 'black'
                ax.text( j, i, f'{value:.1f}', ha='center', va='center', color=textColor, fontsize=9 )

        plt.colorbar( im, ax=ax )

    # -------------------------------------------------------------------
    def _plotSCUDepthProfiles( self: Self, results: list[ dict[ str, Any ] ], time: float,
                               surfaceWithStress: vtkDataSet, profileStartPoints=None, profileSearchRadius=None,
                               maxDepthProfiles=None ) -> None:
        """Plot SCU depth profiles for all parameter combinations.

        Each (cohesion, friction) pair gets a unique color
        """
        print( "\n  📊 Creating SCU sensitivity depth profiles..." )

        # Extract depth data
        centers = getArrayInObject( surfaceWithStress, 'elementCenter', Piece.CELLS )
        centers[ :, 2 ]

        # Get profile points from config

        # Auto-generate if not provided
        if profileStartPoints is None:
            print( "  ⚠️  No PROFILE_START_POINTS in config, auto-generating..." )
            xMin, xMax = np.min( centers[ :, 0 ] ), np.max( centers[ :, 0 ] )
            yMin, yMax = np.min( centers[ :, 1 ] ), np.max( centers[ :, 1 ] )

            xRange = xMax - xMin
            yRange = yMax - yMin

            if xRange > yRange:
                # Fault oriented in X, sample at mid-Y
                xPos = ( xMin + xMax ) / 2
                yPos = ( yMin + yMax ) / 2
            else:
                # Fault oriented in Y, sample at mid-X
                xPos = ( xMin + xMax ) / 2
                yPos = ( yMin + yMax ) / 2

            profileStartPoints = [ ( xPos, yPos ) ]

        # Get search radius from config or auto-compute
        if profileSearchRadius is None:
            xMin, xMax = np.min( centers[ :, 0 ] ), np.max( centers[ :, 0 ] )
            yMin, yMax = np.min( centers[ :, 1 ] ), np.max( centers[ :, 1 ] )
            xRange = xMax - xMin
            yRange = yMax - yMin
            searchRadius = min( xRange, yRange ) * 0.15
        else:
            searchRadius = profileSearchRadius

        print( f"  📍 Using {len(profileStartPoints)} profile point(s) from config" )
        print( f"     Search radius: {searchRadius:.1f}m" )

        # Create colormap for parameter combinations
        nCombinations = len( results )
        cmap = plt.cm.viridis  # type: ignore [attr-defined]
        norm = Normalize( vmin=0, vmax=nCombinations - 1 )
        ScalarMappable( norm=norm, cmap=cmap )

        # Create figure with subplots for each profile point
        nProfiles = len( profileStartPoints )
        fig, axes = plt.subplots( 1, nProfiles, figsize=( 8 * nProfiles, 10 ) )

        # Handle single subplot case
        if nProfiles == 1:
            axes = [ axes ]

        # Plot each profile point
        for profileIdx, ( xPos, yPos, zPos ) in enumerate( profileStartPoints ):
            ax = axes[ profileIdx ]

            print( f"\n  → Profile {profileIdx+1} at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f}):" )

            # Plot each parameter combination
            for idx, params in enumerate( results ):
                frictionAngle = params[ 'frictionAngle' ]
                cohesion = params[ 'cohesion' ]

                # Re-analyze surface with these parameters
                surfaceCopy = type(surfaceWithStress)()
                surfaceCopy.DeepCopy( surfaceWithStress )
                surfaceAnalyzed = MohrCoulomb.analyze(
                    surfaceCopy,
                    cohesion,
                    frictionAngle,
                    verbose=False )

                # Extract SCU
                SCU = np.abs( getArrayInObject( surfaceAnalyzed, "SCU", Piece.CELLS ) )

                # Extract profile using adaptive method
                # depthsSCU, profileSCU, _, _ = ProfileExtractor.extractVerticalProfileTopologyBased(
                #         surfaceAnalyzed, 'SCU', xPos, yPos, zPos, verbose=False)
                depthsSCU, profileSCU, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centers, SCU, xPos, yPos, searchRadius )

                if len( depthsSCU ) >= 3:
                    color = cmap( norm( idx ) )
                    label = f'φ={frictionAngle}°, C={cohesion} bar'
                    ax.plot( profileSCU, depthsSCU, color=color, label=label, linewidth=2, alpha=0.8 )

                    if idx == 0:  # Print info only once per profile
                        print( f"     ✅ {len(depthsSCU)} points extracted" )
                else:
                    if idx == 0:
                        print( f"     ⚠️  Insufficient points ({len(depthsSCU)})" )

            # Add critical lines
            ax.axvline( x=0.8,
                        color='forestgreen',
                        linestyle='--',
                        linewidth=2,
                        label='Critical (SCU=0.8)',
                        zorder=100 )
            ax.axvline( x=1.0, color='red', linestyle='--', linewidth=2, label='Failure (SCU=1.0)', zorder=100 )

            # Configure plot
            ax.set_xlabel( 'Shear Capacity Utilization (SCU) [-]', fontsize=14, weight='bold' )
            ax.set_ylabel( 'Depth [m]', fontsize=14, weight='bold' )
            ax.set_title( f'Profile {profileIdx+1} @ ({xPos:.0f}, {yPos:.0f})', fontsize=14, weight='bold' )
            ax.grid( True, alpha=0.3, linestyle='--' )
            ax.set_xlim( left=0 )

            # Change verticale scale
            if maxDepthProfiles is not None:
                ax.set_ylim( bottom=maxDepthProfiles )

            # Légende en dehors à droite
            ax.legend( loc='center left', bbox_to_anchor=( 1, 0.5 ), fontsize=9, ncol=1 )

            ax.tick_params( labelsize=12 )

        # Overall title
        years = time / ( 365.25 * 24 * 3600 )
        fig.suptitle( 'SCU Depth Profiles - Sensitivity Analysis', fontsize=16, weight='bold', y=0.98 )

        fig.tight_layout( rect=( 0, 0, 1, 0.96 ) )

        # Save
        filename = f'sensitivity_scu_profiles_{years:.0f}y.png'
        fig.savefig( self.outputDir / filename, dpi=300, bbox_inches='tight' )
        print( f"\n  💾 SCU sensitivity profiles saved: {filename}" )

        if self.showPlots:
            fig.show()
