# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
from pathlib import Path
import numpy as np
from typing_extensions import Self

from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.io.vtkIO import PVDReader
from geos.mesh.utils.arrayHelpers import (isAttributeInObject, getAttributeSet)

from geos.processing.post_processing.FaultGeometry import FaultGeometry
from geos.processing.tools.FaultVisualizer import Visualizer
from geos.processing.post_processing.SensitivityAnalyzer import SensitivityAnalyzer
from geos.processing.post_processing.StressProjector import StressProjector
from geos.processing.post_processing.MohrCoulomb import MohrCoulomb

from geos.utils.pieceEnum import Piece
# ============================================================================
# TIME SERIES PROCESSING
# ============================================================================
class TimeSeriesProcessor:
    """Process multiple time steps from PVD file."""

    # -------------------------------------------------------------------
    def __init__( self: Self, outputDir: str = ".", showPlots: bool = True, savePlots: bool = True ) -> None:
        """Init."""
        self.outputDir = Path( outputDir )
        self.outputDir.mkdir( exist_ok=True )

        self.showPlots: bool = showPlots
        self.savePlots: bool = savePlots

    # -------------------------------------------------------------------
    def process( self: Self,
        path: Path,
        faultGeometry: FaultGeometry,
        pvdFile: str,
        timeIndexes: list[ int ] = [],
        weightingScheme: str = "arithmetic",
        cohesion: float = 0,
        frictionAngle: float = 10,
        runSensitivity: bool = True,
        profileStartPoints: list[tuple[ float, ...]] = [],
        computePrincipalStress: bool = False,
        showDepthProfiles: bool = True,
        stressName: str = "averageStress",
        biotCoefficient: str = "rockPorosity_biotCoefficient",
        profileSearchRadius=None,
        minDepthProfiles=None,
        maxDepthProfiles=None,
        sensitivityFrictionAngles=None,
        sensitivityCohesions=None ):
        """Process all time steps using pre-computed fault geometry.

        Parameters:
            path: base path for input files
            faultGeometry: FaultGeometry object with initialized topology
            pvdFile: PVD file name
        """
        reader = PVDReader( path / pvdFile )
        timeValues = reader.getAllTimestepsValues()

        if timeIndexes:
            timeValues = timeValues[ timeIndexes ]

        outputFiles = []
        dataInitial = None

        # Get pre-computed data from faultGeometry
        surface = faultGeometry.faultSurface
        adjacencyMapping = faultGeometry.adjacencyMapping
        geometricProperties = faultGeometry.getGeometricProperties()

        # Initialize projector with pre-computed topology
        projector = StressProjector( adjacencyMapping, geometricProperties, self.outputDir )

        print( '\n' )
        print( "=" * 60 )
        print( "TIME SERIES PROCESSING" )
        print( "=" * 60 )

        for i, time in enumerate( timeValues ):
            print( f"\n→ Step {i+1}/{len(timeValues)}: {time/(365.25*24*3600):.2f} years" )

            # Read time step
            idx = timeIndexes[ i ] if timeIndexes else i
            dataset = reader.getDataSetAtTimeIndex( idx )

            # Merge blocks
            volumeData = mergeBlocks( dataset, keepPartialAttributes=True )

            if dataInitial is None:
                dataInitial = volumeData


            # -----------------------------------
            # Projection using pre-computed topology
            # -----------------------------------
            # Projection
            surfaceResult, volumeMarked, contributingCells = projector.projectStressToFault(
                volumeData,
                dataInitial,
                surface,
                time=timeValues[ i ],  # Simulation time
                timestep=i,  # Timestep index
                stressName=stressName,
                biotName=biotCoefficient,
                weightingScheme=weightingScheme )

            # -----------------------------------
            # Mohr-Coulomb analysis
            # -----------------------------------
            cohesion = cohesion
            frictionAngle = frictionAngle
            surfaceResult = MohrCoulomb.analyze( surfaceResult, cohesion, frictionAngle )  #, time )

            # -----------------------------------
            # Visualize
            # -----------------------------------
            self._plotResults( surfaceResult, contributingCells, time, self.outputDir, profileStartPoints, computePrincipalStress, showDepthProfiles,
            profileSearchRadius, minDepthProfiles, maxDepthProfiles )

            # -----------------------------------
            # Sensitivity analysis
            # -----------------------------------
            if runSensitivity:
                analyzer = SensitivityAnalyzer( self.outputDir, self.showPlots )
                if sensitivityFrictionAngles is None or sensitivityCohesions is None:
                    raise ValueError( "sensitivity friction angles and cohesions required if runSensitivity is set to True" )
                analyzer.runAnalysis( surfaceResult, time, sensitivityFrictionAngles, sensitivityCohesions, profileStartPoints, profileSearchRadius )

            # Save
            filename = f'fault_analysis_{i:04d}.vtu'
            # surfaceResult.save( self.outputDir / filename )
            outputFiles.append( ( time, filename ) )
            print( f"  💾 Saved: {filename}" )

        # Create master PVD
        self._createPVD( outputFiles )

        return surfaceResult
    # -------------------------------------------------------------------
    def _plotResults( self, surface, contributingCells, time: list[ int ],
                      path: str, profileStartPoints: list[tuple[float, ...]], computePrincipalStress: bool = False, showDepthProfiles:bool = True,
                      profileSearchRadius: float|None=None, minDepthProfiles: float | None = None,
                                             maxDepthProfiles: float | None = None,  ) -> None:  # TODO check type surface
        Visualizer.plotMohrCoulombDiagram( surface,
                                           time,
                                           path,
                                           show=self.showPlots,
                                           save=self.savePlots, )


        # Profils verticaux automatiques
        if showDepthProfiles:
            Visualizer( profileSearchRadius).plotDepthProfiles( surface=surface,
                                          time=time,
                                          path=path,
                                          show=self.showPlots,
                                          save=self.savePlots,
                                          profileStartPoints=profileStartPoints)


        visualizer = Visualizer( profileSearchRadius,
                                minDepthProfiles,
                                maxDepthProfiles,
                                showPlots = self.showPlots, savePlots = self.savePlots )

        if computePrincipalStress:
            # Plot principal stress from volume cells
            visualizer.plotVolumeStressProfiles( volumeMesh=contributingCells,
                                                 faultSurface=surface,
                                                 time=time,
                                                 path=path,
                                                 profileStartPoints=profileStartPoints )

            # Visualize comparison analytical/numerical
            visualizer.plotAnalyticalVsNumericalComparison( volumeMesh=contributingCells,
                                                            faultSurface=surface,
                                                            time=time,
                                                            path=path,
                                                            show=self.showPlots,
                                                            save=self.savePlots,
                                                            profileStartPoints=profileStartPoints )

    # -------------------------------------------------------------------
    def _createPVD( self, outputFiles: list[ tuple[ int, str ] ] ) -> None:
        """Create PVD collection file."""
        pvdPath = self.outputDir / 'fault_analysis.pvd'
        with open( pvdPath, 'w' ) as f:
            f.write( '<VTKFile type="Collection" version="0.1">\n' )
            f.write( '  <Collection>\n' )
            for t, fname in outputFiles:
                f.write( f'    <DataSet timestep="{t}" file="{fname}"/>\n' )
            f.write( '  </Collection>\n' )
            f.write( '</VTKFile>\n' )
        print( f"\n✅ PVD created: {pvdPath}" )

