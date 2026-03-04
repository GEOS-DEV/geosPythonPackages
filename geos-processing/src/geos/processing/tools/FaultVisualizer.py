# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import os
import pandas as pd
import numpy as np
import numpy.typing as npt
from pathlib import Path
from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import pyvista as pv
from typing_extensions import Self, Union

from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkUnstructuredGrid

from geos.processing.tools.ProfileExtractor import ProfileExtractor
from geos.mesh.utils.arrayHelpers import ( isAttributeInObject, getArrayInObject )
from geos.utils.pieceEnum import Piece
from geos.utils.Logger import ( Logger, getLogger )

loggerTitle = "Fault Visualizer"

class Visualizer:
    """Visualization utilities."""


    def __init__( self, profileSearchRadius: float| None = None,
                        minDepthProfiles: float | None = None,
                        maxDepthProfiles: float | None = None,
                        savePlots:bool = True,
                        logger: Union[ Logger, None] = None ) -> None:
        """Visualization utilities.

        Args:
            profileSearchRadius (float | None): Searching radius for determination of profile.
            minDepthProfiles (float | None): Minimum depth profile.
            maxDepthProfiles: (float | None): Maximum depth profile.
            savePlots (bool): Flag to save the figures.
                    Defaults is True,
            logger (Union[Logger, None], optional): A logger to manage the output messages.
                    Defaults to None, an internal logger is used.
        """
        self.profileSearchRadius = profileSearchRadius
        self.minDepthProfiles = minDepthProfiles
        self.maxDepthProfiles = maxDepthProfiles
        self.savePlots = savePlots

        # Logger
        self.logger: Logger
        if logger is None:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( f"{logger.name}" )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False


    def plotMohrCoulombDiagram( self: Self,
                                surface: vtkUnstructuredGrid,
                                time: float,
                                path: Path = Path( "." ),
                                save: bool = True ) -> None:
        """Create Mohr-Coulomb diagram with depth coloring.

        Args:
            surface (vtkUnstructuredGrid): Fault mesh containing mohr attributes.
            time (float): Time.
            path (Path): Saving path.
            save (bool): Flag to save figures. Defaults is True.
        """
        sigmaN = - getArrayInObject( surface, "sigmaNEffective", Piece.CELLS )
        tau = np.abs( getArrayInObject( surface, "tauEffective", Piece.CELLS ) )
        SCU = np.abs( getArrayInObject( surface, "SCU", Piece.CELLS ) )
        depth =  getArrayInObject( surface, 'elementCenter', Piece.CELLS )[ :, 2 ]

        cohesion = getArrayInObject( surface, "mohrCohesion", Piece.CELLS )[ 0 ]
        mu = getArrayInObject( surface, "mohrFrictionCoefficient" , Piece.CELLS )[ 0 ]
        phi = getArrayInObject( surface, 'mohrFrictionAngle' , Piece.CELLS )[ 0 ]

        fig, axes = plt.subplots( 1, 2, figsize=( 16, 8 ) )

        # Plot 1: τ vs σ_n
        ax1 = axes[ 0 ]
        ax1.scatter( sigmaN, tau, c=depth, cmap='turbo_r', s=20, alpha=0.8 )
        sigmaRange = np.linspace( 0, np.max( sigmaN ), 100 )
        tauCritical = cohesion + mu * sigmaRange
        ax1.plot( sigmaRange, tauCritical, 'k--', linewidth=2, label=f'M-C (C={cohesion} bar, φ={phi}°)' )
        ax1.set_xlabel( 'Normal Stress [bar]' )
        ax1.set_ylabel( 'Shear Stress [bar]' )
        ax1.legend()
        ax1.grid( True, alpha=0.3 )
        ax1.set_title( 'Mohr-Coulomb Diagram' )

        # Plot 2: SCU vs σ_n
        ax2 = axes[ 1 ]
        sc2 = ax2.scatter( sigmaN, SCU, c=depth, cmap='turbo_r', s=20, alpha=0.8 )
        ax2.axhline( y=1.0, color='r', linestyle='--', label='Failure (SCU=1)' )
        ax2.set_xlabel( 'Normal Stress [bar]' )
        ax2.set_ylabel( 'SCU [-]' )
        ax2.legend()
        ax2.grid( True, alpha=0.3 )
        ax2.set_title( 'Shear Capacity Utilization' )
        ax2.set_ylim( bottom=0 )

        plt.colorbar( sc2, ax=ax2, label='Depth [m]' )
        plt.tight_layout()

        if save:
            years = time / ( 365.25 * 24 * 3600 )
            filename = f'mohr_coulomb_phi{phi}_c{cohesion}_{years:.0f}y.png'
            plt.savefig( os.path.join( path, filename), dpi=300, bbox_inches='tight' )
            self.logger.info( f"  📊 Plot saved: {filename}" )


    def plotDepthProfiles( self: Self,
                           surface: vtkUnstructuredGrid,
                           time: float,
                           path: Path = Path( "." ),
                           save: bool = True,
                           profileStartPoints: list[ tuple[ float, float ] ] | None = None,
                           maxProfilePoints: int = 1000,
                           referenceProfileId: int = 1,
                         ) -> None:
        """Plot vertical profiles along the fault showing stress and SCU vs depth.

        Args:
            surface (vtkUnstructuredGrid): Fault mesh.
            time (float): Time.
            path (Path): Saving path. Defaults is current directory.
            save (bool): Flag to save plots. Defaults is True.
            profileStartPoints (list[ tuple[ float, float ] ] | None): List of start points for profile analysis
            maxProfilePoints (int): Max profile points displayed. Defaults is 1000.
            referenceProfileId (int): Id of profile to plot. Defaults is 1.
        """
        self.logger.info( "  📊 Creating depth profiles " )

        # Extract data
        centers = surface.cell_data[ 'elementCenter' ]
        depth = centers[ :, 2 ]
        sigmaN = surface.cell_data[ 'sigmaNEffective' ]
        tau = surface.cell_data[ 'tauEffective' ]
        SCU = surface.cell_data[ 'SCU' ]
        SCU = np.sqrt( SCU**2 )
        surface.cell_data[ 'deltaSCU' ]

        # Extraire les IDs de faille
        faultIds = None
        if 'FaultMask' in surface.cell_data:
            faultIds = surface.cell_data[ 'FaultMask' ]
            self.logger.info( f"  📋 Detected {len(np.unique(faultIds[faultIds > 0]))} distinct faults" )
        elif 'attribute' in surface.cell_data:
            faultIds = surface.cell_data[ 'attribute' ]
            self.logger.info( "  📋 Using 'attribute' field for fault identification" )
        else:
            self.logger.warning( "  ⚠️ No fault IDs found - profiles may jump between faults" )

        # ===================================================================
        # LOAD REFERENCE DATA (GEOS + Analytical)
        # ===================================================================
        scriptDir = os.path.dirname( os.path.abspath( __file__ ) )
        referenceData = Visualizer.loadReferenceData( time, scriptDir, profileId=referenceProfileId )

        geosData = referenceData[ 'geos' ]
        analyticalData = referenceData[ 'analytical' ]

        # ===================================================================
        # PROFILE EXTRACTION SETUP
        # ===================================================================

        # Get fault bounds
        xMin, xMax = np.min( centers[ :, 0 ] ), np.max( centers[ :, 0 ] )
        yMin, yMax = np.min( centers[ :, 1 ] ), np.max( centers[ :, 1 ] )
        zMin, zMax = np.min( depth ), np.max( depth )

        # Auto-compute search radius if not provided
        xRange = xMax - xMin
        yRange = yMax - yMin
        zMax - zMin

        if self.profileSearchRadius is not None:
            searchRadius = self.profileSearchRadius
        else:
            searchRadius = min( xRange, yRange ) * 0.15

        # Auto-generate profile points if not provided
        if profileStartPoints is None:
            self.logger.warning( "  ⚠️  No profileStartPoints provided, auto-generating 5 profiles..." )
            nProfiles = 5

            # Determine dominant fault direction
            if xRange > yRange:
                coordName = 'X'
                fixedValue = ( yMin + yMax ) / 2
                samplePositions = np.linspace( xMin, xMax, nProfiles )
                profileStartPoints = [ ( x, fixedValue ) for x in samplePositions ]
            else:
                coordName = 'Y'
                fixedValue = ( xMin + xMax ) / 2
                samplePositions = np.linspace( yMin, yMax, nProfiles )
                profileStartPoints = [ ( fixedValue, y ) for y in samplePositions ]

            self.logger.info( f"     Auto-generated {nProfiles} profiles along {coordName} direction" )

        nProfiles = len( profileStartPoints )

        # ===================================================================
        # CREATE FIGURE
        # ===================================================================

        fig, axes = plt.subplots( 1, 4, figsize=( 24, 12 ) )
        colors = plt.cm.RdYlGn( np.linspace( 0, 1, nProfiles ) )  # type: ignore [attr-defined]

        self.logger.info( f"  📍 Processing {nProfiles} profiles:" )
        self.logger.info( f"     Depth range: [{zMin:.1f}, {zMax:.1f}]m" )

        successfulProfiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES
        # ===================================================================

        for i, ( xPos, yPos, zPos ) in enumerate( profileStartPoints ):
            self.logger.info( f"     → Profile {i+1}: starting at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f})" )

            depthsSigma, profileSigmaN, PathXSigma, PathYSigma = ProfileExtractor.extractAdaptiveProfile(
                centers, sigmaN, xPos, yPos, searchRadius )

            depthsTau, profileTau, _, _ = ProfileExtractor.extractAdaptiveProfile( centers, tau, xPos, yPos,
                                                                                   searchRadius )

            depthsSCU, profileSCU, _, _ = ProfileExtractor.extractAdaptiveProfile( centers, SCU, xPos, yPos,
                                                                                   searchRadius )

            depthsDeltaSCU, profileDeltaSCU, _, _ = ProfileExtractor.extractAdaptiveProfile(
                centers, SCU, xPos, yPos, searchRadius )

            # Calculate path length
            if len( PathXSigma ) > 1:
                pathLength = np.sum(
                    np.sqrt( np.diff( PathXSigma )**2 + np.diff( PathYSigma )**2 + np.diff( depthsSigma )**2 ) )
                self.logger.info(
                    f"        Path length: {pathLength:.1f}m (horizontal displacement: {np.abs(PathXSigma[-1] - PathXSigma[0]):.1f}m)"
                )

            # Check if we have enough points
            minPoints = 3
            nPoints = len( depthsSigma )

            if nPoints >= minPoints:
                label = f'Profile {i+1} → ({xPos:.0f}, {yPos:.0f})'

                # Plot 1: Normal stress vs depth
                axes[ 0 ].plot( profileSigmaN,
                                depthsSigma,
                                color=colors[ i ],
                                label=label,
                                linewidth=2.5,
                                alpha=0.8,
                                marker='o',
                                markersize=3,
                                markevery=2 )

                # Plot 2: Shear stress vs depth
                axes[ 1 ].plot( profileTau,
                                depthsTau,
                                color=colors[ i ],
                                label=label,
                                linewidth=2.5,
                                alpha=0.8,
                                marker='o',
                                markersize=3,
                                markevery=2 )

                # Plot 3: SCU vs depth
                axes[ 2 ].plot( profileSCU,
                                depthsSCU,
                                color=colors[ i ],
                                label=label,
                                linewidth=2.5,
                                alpha=0.8,
                                marker='o',
                                markersize=3,
                                markevery=2 )

                # Plot 4: Detla SCU vs depth
                axes[ 3 ].plot( profileDeltaSCU,
                                depthsDeltaSCU,
                                color=colors[ i ],
                                label=label,
                                linewidth=2.5,
                                alpha=0.8,
                                marker='o',
                                markersize=3,
                                markevery=2 )

                successfulProfiles += 1
                self.logger.info( f"        ✅ {nPoints} points found" )
            else:
                self.logger.warning( f"        ⚠️  Insufficient points ({nPoints}), skipping" )

        if successfulProfiles == 0:
            self.logger.error( "  ❌ No valid profiles found!" )
            plt.close()
            return

        # ===================================================================
        # ADD REFERENCE DATA (GEOS + Analytical) - Only once
        # ===================================================================

        if geosData is not None:
            # Colonnes: [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU]
            # Index:    [0,       1,                 2,                 3]

            axes[ 0 ].plot( geosData[ :, 1 ] * 10,
                            geosData[ :, 0 ],
                            'o',
                            color='blue',
                            markersize=6,
                            label='GEOS Contact Solver',
                            alpha=0.7,
                            mec='k',
                            mew=1,
                            fillstyle='none' )

            axes[ 1 ].plot( geosData[ :, 2 ] * 10,
                            geosData[ :, 0 ],
                            'o',
                            color='blue',
                            markersize=6,
                            label='GEOS Contact Solver',
                            alpha=0.7,
                            mec='k',
                            mew=1,
                            fillstyle='none' )

            if geosData.shape[ 1 ] > 3:  # SCU column exists
                axes[ 2 ].plot( geosData[ :, 3 ],
                                geosData[ :, 0 ],
                                'o',
                                color='blue',
                                markersize=6,
                                label='GEOS Contact Solver',
                                alpha=0.7,
                                mec='k',
                                mew=1,
                                fillstyle='none' )

        if analyticalData is not None:
            # Format analytique (peut varier)
            axes[ 0 ].plot( analyticalData[ :, 1 ] * 10,
                            analyticalData[ :, 0 ],
                            '--',
                            color='darkorange',
                            linewidth=2,
                            label='Analytical',
                            alpha=0.8 )
            if analyticalData.shape[ 1 ] > 2:
                axes[ 1 ].plot( analyticalData[ :, 2 ] * 10,
                                analyticalData[ :, 0 ],
                                '--',
                                color='darkorange',
                                linewidth=2,
                                label='Analytical',
                                alpha=0.8 )

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 1: Normal Stress
        axes[ 0 ].set_xlabel( 'Normal Stress σₙ [bar]', fontsize=fsize, weight="bold" )
        axes[ 0 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 0 ].set_title( 'Normal Stress Profile', fontsize=fsize + 2, weight="bold" )
        axes[ 0 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 0 ].legend( loc='upper left', fontsize=fsize - 2 )
        axes[ 0 ].tick_params( labelsize=fsize - 2 )

        # Plot 2: Shear Stress
        axes[ 1 ].set_xlabel( 'Shear Stress τ [bar]', fontsize=fsize, weight="bold" )
        axes[ 1 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 1 ].set_title( 'Shear Stress Profile', fontsize=fsize + 2, weight="bold" )
        axes[ 1 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 1 ].legend( loc='upper left', fontsize=fsize - 2 )
        axes[ 1 ].tick_params( labelsize=fsize - 2 )

        # Plot 3: SCU
        axes[ 2 ].set_xlabel( 'SCU [-]', fontsize=fsize, weight="bold" )
        axes[ 2 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 2 ].set_title( 'Shear Capacity Utilization', fontsize=fsize + 2, weight="bold" )
        axes[ 2 ].axvline( x=0.8, color='forestgreen', linestyle='--', linewidth=2, label='Critical (0.8)' )
        axes[ 2 ].axvline( x=1.0, color='red', linestyle='--', linewidth=2, label='Failure (1.0)' )
        axes[ 2 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 2 ].legend( loc='upper right', fontsize=fsize - 2 )
        axes[ 2 ].tick_params( labelsize=fsize - 2 )
        axes[ 2 ].set_xlim( left=0 )

        # Plot 4: Delta SCU
        axes[ 3 ].set_xlabel( 'Δ SCU [-]', fontsize=fsize, weight="bold" )
        axes[ 3 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 3 ].set_title( 'Delta SCU', fontsize=fsize + 2, weight="bold" )
        axes[ 3 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 3 ].legend( loc='upper right', fontsize=fsize - 2 )
        axes[ 3 ].tick_params( labelsize=fsize - 2 )
        axes[ 3 ].set_xlim( left=0, right=2 )

        # Change vertical scale
        if self.maxDepthProfiles is not None:
            for i in range( len( axes ) ):
                axes[ i ].set_ylim( bottom=self.maxDepthProfiles )

        if self.minDepthProfiles is not None:
            for i in range( len( axes ) ):
                axes[ i ].set_ylim( top=self.minDepthProfiles )

        # Overall title
        years = time / ( 365.25 * 24 * 3600 )
        fig.suptitle( f'Fault Depth Profiles - t={years:.1f} years', fontsize=fsize + 2, fontweight='bold', y=0.98 )

        plt.tight_layout( rect=( 0, 0, 1, 0.96 ) )

        # Save
        if save:
            filename = f'depth_profiles_{years:.0f}y.png'
            plt.savefig( os.path.join( path, filename ), dpi=300, bbox_inches='tight' )
            self.logger.info( f"  💾 Depth profiles saved: {filename}" )


    def plotVolumeStressProfiles( self: Self,
                                  volumeMesh: vtkUnstructuredGrid,
                                  faultSurface: vtkUnstructuredGrid,
                                  time: float,
                                  path: Path = Path( "." ),
                                  save: bool = True,
                                  profileStartPoints: list[ tuple[ float, float, float ] ] | None = None,
                                  maxProfilePoints: int = 1000,
                                ) -> None:
        """Plot stress profiles in volume cells adjacent to the fault.

        Extracts profiles through contributing cells on BOTH sides of the fault
        Shows plus side and minus side on the same plots for comparison.

        Args:
            volumeMesh (vtkUnstructuredGrid): Volumic mesh.
            faultSurface (vtkUnstucturedGrid): Fault mesh.
            time (float): Time.
            path (Path): Saving path. Defaults is current directory.
            save (bool): Flag to save plots. Defaults is True.
            profileStartPoints (list[ tuple[ float, float ] ] | None): List of start points for profile analysis
            maxProfilePoints (int): Max profile points displayed. Defaults is 1000.
        """
        self.logger.info( "  📊 Creating volume stress profiles (both sides)" )

        # ===================================================================
        # CHECK IF REQUIRED DATA EXISTS
        # ===================================================================
        requiredFields = [ 'sigma1', 'sigma2', 'sigma3', 'side', 'elementCenter' ]

        for field in requiredFields:
            if isAttributeInObject( volumeMesh, field, Piece.CELLS ):
                self.logger.warning( f"  ⚠️  Missing required field: {field}" )
                return

        # Check for pressure
        if isAttributeInObject( volumeMesh, 'pressure_bar', Piece.CELLS):
            pressureField = 'pressure_bar'
            pressure = getArrayInObject( volumeMesh, pressureField, Piece.CELLS )
        elif isAttributeInObject( volumeMesh, 'pressure', Piece.CELLS ):
            pressureField = 'pressure'
            pressure = getArrayInObject( volumeMesh, pressureField, Piece.CELLS ) / 1e5
            self.logger.info( "  ℹ️  Converting pressure from Pa to bar" )
        else:
            self.logger.warning( "  ⚠️  No pressure field found" )
            pressure = None

        # Extract volume data
        centers = getArrayInObject( volumeMesh, 'elementCenter', Piece.CELLS )
        sigma1 = getArrayInObject( volumeMesh, 'sigma1', Piece.CELLS )
        sigma2 = getArrayInObject( volumeMesh, 'sigma2', Piece.CELLS )
        sigma3 = getArrayInObject( volumeMesh, 'sigma3', Piece.CELLS )
        sideData = getArrayInObject( volumeMesh, 'side', Piece.CELLS )

        # ===================================================================
        # FILTER CELLS BY SIDE (BOTH PLUS AND MINUS)
        # ===================================================================

        # Plus side (side = 1 or 3)
        maskPlus = ( sideData == 1 ) | ( sideData == 3 )
        centersPlus = centers[ maskPlus ]
        sigma1Plus = sigma1[ maskPlus ]
        sigma2Plus = sigma2[ maskPlus ]
        sigma3Plus = sigma3[ maskPlus ]
        if pressure is not None:
            pressurePlus = pressure[ maskPlus ]

        # Minus side (side = 2 or 3)
        maskMinus = ( sideData == 2 ) | ( sideData == 3 )
        centersMinus = centers[ maskMinus ]
        sigma1Minus = sigma1[ maskMinus ]
        sigma2Minus = sigma2[ maskMinus ]
        sigma3Minus = sigma3[ maskMinus ]
        if pressure is not None:
            pressureMinus = pressure[ maskMinus ]

        # Créer subset de cellData pour le côté plus
        cellDataPlus = {}
        cellDataMinus = {}
        for key in volumeMesh.GetCellData().items():
            cellDataPlus[ key ] = getArrayInObject( volumeMesh, key )[ maskPlus ]
            cellDataMinus[ key ] = getArrayInObject( volumeMesh, key )[ maskMinus ]


        self.logger.info( f"  📍 Plus side: {len(centersPlus):,} cells" )
        self.logger.info( f"  📍 Minus side: {len(centersMinus):,} cells" )

        if len( centersPlus ) == 0 and len( centersMinus ) == 0:
            self.logger.error( "  ⚠️  No contributing cells found!" )
            return

        # ===================================================================
        # GET FAULT BOUNDS
        # ===================================================================

        faultCenters = faultSurface.cell_data[ 'elementCenter' ]

        xMin, xMax = np.min( faultCenters[ :, 0 ] ), np.max( faultCenters[ :, 0 ] )
        yMin, yMax = np.min( faultCenters[ :, 1 ] ), np.max( faultCenters[ :, 1 ] )
        zMin, zMax = np.min( faultCenters[ :, 2 ] ), np.max( faultCenters[ :, 2 ] )

        xRange = xMax - xMin
        yRange = yMax - yMin
        zMax - zMin

        # Search radius (pour extractAdaptiveProfile sur volumes)
        if self.profileSearchRadius is not None:
            searchRadius = self.profileSearchRadius
        else:
            searchRadius = min( xRange, yRange ) * 0.2

        # ===================================================================
        # AUTO-GENERATE PROFILE POINTS IF NOT PROVIDED
        # ===================================================================

        if profileStartPoints is None:
            self.logger.warning( "  ⚠️  No profileStartPoints provided, auto-generating..." )
            nProfiles = 3

            if xRange > yRange:
                coordName = 'X'
                fixedValue = ( yMin + yMax ) / 2
                samplePositions = np.linspace( xMin, xMax, nProfiles )
                profileStartPoints = [ ( x, fixedValue, zMax ) for x in samplePositions ]
            else:
                coordName = 'Y'
                fixedValue = ( xMin + xMax ) / 2
                samplePositions = np.linspace( yMin, yMax, nProfiles )
                profileStartPoints = [ ( fixedValue, y, zMax ) for y in samplePositions ]

            self.logger.info( f"     Auto-generated {nProfiles} profiles along {coordName}" )

        nProfiles = len( profileStartPoints )

        # ===================================================================
        # CREATE FIGURE WITH 5 SUBPLOTS
        # ===================================================================

        fig, axes = plt.subplots( 1, 5, figsize=( 22, 10 ) )

        # Colors: different for plus and minus sides
        colorsPlus = plt.cm.Reds( np.linspace( 0.4, 0.9, nProfiles ) )  # type: ignore [attr-defined]
        colorsMinus = plt.cm.Blues( np.linspace( 0.4, 0.9, nProfiles ) )  # type: ignore [attr-defined]

        self.logger.info( f"  📍 Processing {nProfiles} volume profiles:" )
        self.logger.info( f"     Depth range: [{zMin:.1f}, {zMax:.1f}]m" )

        successfulProfiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES FOR BOTH SIDES
        # ===================================================================

        for i, ( xPos, yPos, zPos ) in enumerate( profileStartPoints ):
            self.logger.info( f"     → Profile {i+1}: starting at ({xPos:.1f}, {yPos:.1f}, {zPos:.1f})" )

            # ================================================================
            # PLUS SIDE
            # ================================================================
            if len( centersPlus ) > 0:
                self.logger.info( "        Processing PLUS side..." )

                # Pour VOLUMES, utiliser extractAdaptiveProfile avec cellData
                depthsSigma1Plus, profileSigma1Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma1Plus, xPos, yPos, zPos, searchRadius, cellData=cellDataPlus )

                depthsSigma2Plus, profileSigma2Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma2Plus, xPos, yPos, zPos, searchRadius, cellData=cellDataPlus )

                depthsSigma3Plus, profileSigma3Plus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersPlus, sigma3Plus, xPos, yPos, zPos, searchRadius, cellData=cellDataPlus )

                if pressure is not None:
                    depthsPressurePlus, profilePressurePlus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersPlus,
                        pressurePlus,
                        xPos,
                        yPos,
                        zPos,
                        searchRadius,
                        cellData=cellDataPlus )

                if len( depthsSigma1Plus ) >= 3:
                    labelPlus = 'Plus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[ 0 ].plot( profilePressurePlus,
                                        depthsPressurePlus,
                                        color=colorsPlus[ i ],
                                        label=labelPlus if i == 0 else '',
                                        linewidth=2.5,
                                        alpha=0.8,
                                        marker='o',
                                        markersize=3,
                                        markevery=2 )

                    # Plot σ1
                    axes[ 1 ].plot( profileSigma1Plus,
                                    depthsSigma1Plus,
                                    color=colorsPlus[ i ],
                                    label=labelPlus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='o',
                                    markersize=3,
                                    markevery=2 )

                    # Plot σ2
                    axes[ 2 ].plot( profileSigma2Plus,
                                    depthsSigma2Plus,
                                    color=colorsPlus[ i ],
                                    label=labelPlus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='o',
                                    markersize=3,
                                    markevery=2 )

                    # Plot σ3
                    axes[ 3 ].plot( profileSigma3Plus,
                                    depthsSigma3Plus,
                                    color=colorsPlus[ i ],
                                    label=labelPlus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='o',
                                    markersize=3,
                                    markevery=2 )

                    # Plot All stresses
                    axes[ 4 ].plot( profileSigma1Plus,
                                    depthsSigma1Plus,
                                    color=colorsPlus[ i ],
                                    linewidth=2.5,
                                    alpha=0.8,
                                    linestyle='-',
                                    marker="o",
                                    markersize=2,
                                    markevery=2 )
                    axes[ 4 ].plot( profileSigma2Plus,
                                    depthsSigma2Plus,
                                    color=colorsPlus[ i ],
                                    linewidth=2.0,
                                    alpha=0.6,
                                    linestyle='-',
                                    marker="s",
                                    markersize=2,
                                    markevery=2 )
                    axes[ 4 ].plot( profileSigma3Plus,
                                    depthsSigma3Plus,
                                    color=colorsPlus[ i ],
                                    linewidth=2.5,
                                    alpha=0.8,
                                    linestyle='-',
                                    marker="v",
                                    markersize=2,
                                    markevery=2 )

                    self.logger.info( f"        ✅ PLUS: {len(depthsSigma1Plus)} points" )
                    successfulProfiles += 1

            # ================================================================
            # MINUS SIDE
            # ================================================================
            if len( centersMinus ) > 0:
                self.logger.info( "        Processing MINUS side..." )

                # Pour VOLUMES, utiliser extractAdaptiveProfile avec cellData
                depthsSigma1Minus, profileSigma1Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma1Minus, xPos, yPos, zPos, searchRadius, cellData=cellDataMinus )

                depthsSigma2Minus, profileSigma2Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma2Minus, xPos, yPos, zPos, searchRadius, cellData=cellDataMinus )

                depthsSigma3Minus, profileSigma3Minus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                    centersMinus, sigma3Minus, xPos, yPos, zPos, searchRadius, cellData=cellDataMinus )

                if pressure is not None:
                    depthsPressureMinus, profilePressureMinus, _, _ = ProfileExtractor.extractAdaptiveProfile(
                        centersMinus,
                        pressureMinus,
                        xPos,
                        yPos,
                        zPos,
                        searchRadius,
                        cellData=cellDataMinus )

                if len( depthsSigma1Minus ) >= 3:
                    labelMinus = 'Minus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[ 0 ].plot( profilePressureMinus,
                                        depthsPressureMinus,
                                        color=colorsMinus[ i ],
                                        label=labelMinus if i == 0 else '',
                                        linewidth=2.5,
                                        alpha=0.8,
                                        marker='s',
                                        markersize=3,
                                        markevery=2 )

                    # Plot σ1
                    axes[ 1 ].plot( profileSigma1Minus,
                                    depthsSigma1Minus,
                                    color=colorsMinus[ i ],
                                    label=labelMinus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='s',
                                    markersize=3,
                                    markevery=2 )

                    # Plot σ2
                    axes[ 2 ].plot( profileSigma2Minus,
                                    depthsSigma2Minus,
                                    color=colorsMinus[ i ],
                                    label=labelMinus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='s',
                                    markersize=3,
                                    markevery=2 )

                    # Plot σ3
                    axes[ 3 ].plot( profileSigma3Minus,
                                    depthsSigma3Minus,
                                    color=colorsMinus[ i ],
                                    label=labelMinus if i == 0 else '',
                                    linewidth=2.5,
                                    alpha=0.8,
                                    marker='s',
                                    markersize=3,
                                    markevery=2 )

                    # Plot All stresses
                    axes[ 4 ].plot( profileSigma1Minus,
                                    depthsSigma1Minus,
                                    color=colorsMinus[ i ],
                                    linewidth=2.5,
                                    alpha=0.8,
                                    linestyle='-',
                                    marker="o",
                                    markersize=2,
                                    markevery=2 )
                    axes[ 4 ].plot( profileSigma2Minus,
                                    depthsSigma2Minus,
                                    color=colorsMinus[ i ],
                                    linewidth=2.0,
                                    alpha=0.6,
                                    linestyle='-',
                                    marker="s",
                                    markersize=2,
                                    markevery=2 )
                    axes[ 4 ].plot( profileSigma3Minus,
                                    depthsSigma3Minus,
                                    color=colorsMinus[ i ],
                                    linewidth=2.5,
                                    alpha=0.8,
                                    linestyle='-',
                                    marker='v',
                                    markersize=2,
                                    markevery=2 )

                    self.logger.info( f"        ✅ MINUS: {len(depthsSigma1Minus)} points" )
                    successfulProfiles += 1

        if successfulProfiles == 0:
            self.logger.error( "  ❌ No valid profiles found!" )
            plt.close()
            return

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 0: Pressure
        axes[ 0 ].set_xlabel( 'Pressure [bar]', fontsize=fsize, weight="bold" )
        axes[ 0 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 0 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 0 ].legend( loc='best', fontsize=fsize - 2 )
        axes[ 0 ].tick_params( labelsize=fsize - 2 )

        if pressure is None:
            axes[ 0 ].text( 0.5,
                            0.5,
                            'No pressure data available',
                            ha='center',
                            va='center',
                            transform=axes[ 0 ].transAxes,
                            fontsize=fsize,
                            style='italic',
                            color='gray' )

        # Plot 1: σ1 (Maximum principal stress)
        axes[ 1 ].set_xlabel( 'σ₁ (Max Principal) [bar]', fontsize=fsize, weight="bold" )
        axes[ 1 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 1 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 1 ].legend( loc='best', fontsize=fsize - 2 )
        axes[ 1 ].tick_params( labelsize=fsize - 2 )

        # Plot 2: σ2 (Intermediate principal stress)
        axes[ 2 ].set_xlabel( 'σ₂ (Inter Principal) [bar]', fontsize=fsize, weight="bold" )
        axes[ 2 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 2 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 2 ].legend( loc='best', fontsize=fsize - 2 )
        axes[ 2 ].tick_params( labelsize=fsize - 2 )

        # Plot 3: σ3 (Min principal stress)
        axes[ 3 ].set_xlabel( 'σ₃ (Min Principal) [bar]', fontsize=fsize, weight="bold" )
        axes[ 3 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 3 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 3 ].legend( loc='best', fontsize=fsize - 2 )
        axes[ 3 ].tick_params( labelsize=fsize - 2 )

        # Plot 4: All stresses together
        axes[ 4 ].set_xlabel( 'Principal Stresses [bar]', fontsize=fsize, weight="bold" )
        axes[ 4 ].set_ylabel( 'Depth [m]', fontsize=fsize, weight="bold" )
        axes[ 4 ].grid( True, alpha=0.3, linestyle='--' )
        axes[ 4 ].tick_params( labelsize=fsize - 2 )

        # Add legend for line styles
        customLines = [
            Line2D( [ 0 ], [ 0 ], color='red', linewidth=2.5, marker=None, label='Plus side', alpha=0.5 ),
            Line2D( [ 0 ], [ 0 ], color='blue', linewidth=2.5, marker=None, label='Minus side', alpha=0.5 ),
            Line2D( [ 0 ], [ 0 ], color='gray', linewidth=2.5, linestyle='-', marker='o', label='σ₁ (max)' ),
            Line2D( [ 0 ], [ 0 ], color='gray', linewidth=2.0, linestyle='-', marker='s', label='σ₂ (inter)' ),
            Line2D( [ 0 ], [ 0 ], color='gray', linewidth=2.5, linestyle='-', marker='v', label='σ₃ (min)' )
        ]
        axes[ 4 ].legend( handles=customLines, loc='best', fontsize=fsize - 3, ncol=1 )

        # Change vertical scale
        if self.maxDepthProfile is not None:
            for i in range( len( axes ) ):
                axes[ i ].set_ylim( bottom=self.maxDepthProfiles )

        if self.minDepthProfiles is not None:
            for i in range( len( axes ) ):
                axes[ i ].set_ylim( top=self.minDepthProfiles )

        # Overall title
        years = time / ( 365.25 * 24 * 3600 )
        fig.suptitle( f'Volume Stress Profiles - Both Sides Comparison - t={years:.1f} years',
                      fontsize=fsize + 2,
                      fontweight='bold',
                      y=0.98 )

        plt.tight_layout( rect=( 0, 0, 1, 0.96 ) )

        # Save
        if save:
            filename = f'volume_stress_profiles_both_sides_{years:.0f}y.png'
            plt.savefig( os.path.join( path, filename ), dpi=300, bbox_inches='tight' )
            self.logger.info( f"  💾 Volume profiles saved: {filename}" )

