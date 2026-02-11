# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
from pathlib import Path
import numpy as np
import pyvista as pv
from typing_extensions import Self

from geos.processing.post_processing.FaultGeometry import FaultGeometry
from geos.processing.tools.FaultVisualizer import Visualizer
from geos.processing.post_processing.SensitivityAnalyzer import SensitivityAnalyzer
from geos.processing.post_processing.StressProjector import StressProjector
from geos.processing.post_processing.MohrCoulomb import MohrCoulomb

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
    def process( self: Self, path: Path, faultGeometry: FaultGeometry, pvdFile: str, timeIndexes: list[ int ] = [], weightingScheme: str = "arithmetic", cohesion: float = 0, frictionAngle: float = 10, runSensitivity: bool = True, profileStartPoints: list[tuple[ float, ...]] = [], computePrincipalStress: bool = True, showDepthProfiles: bool = True, stressName: str = "averageStress", biotCoefficient: str = "rockPorosity_biotCoefficient", profileSearchRadius=None, minDepthProfiles=None, maxDepthProfiles=None ) -> pv.DataSet:
        """Process all time steps using pre-computed fault geometry.

        Parameters:
            path: base path for input files
            faultGeometry: FaultGeometry object with initialized topology
            pvdFile: PVD file name
        """
        pvdReader = pv.PVDReader( path / pvdFile )
        timeValues = np.array( pvdReader.time_values )

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
            pvdReader.set_active_time_point( idx )
            dataset = pvdReader.read()

            # Merge blocks
            volumeData = self._mergeBlocks( dataset )

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
                analyzer.runAnalysis( surfaceResult, time )

            # Save
            filename = f'fault_analysis_{i:04d}.vtu'
            surfaceResult.save( self.outputDir / filename )
            outputFiles.append( ( time, filename ) )
            print( f"  💾 Saved: {filename}" )

        # Create master PVD
        self._createPVD( outputFiles )

        return surfaceResult

    # -------------------------------------------------------------------
    @staticmethod
    def _mergeBlocks( dataset: pv.DataSet ) -> pv.UnstructuredGrid:
        """Merge multi-block dataset - descente automatique jusqu'aux données."""

        # -----------------------------------------------
        def extractLeafBlocks(
                block: pv.DataSet,
                path: str = "",
                depth: float = 0
        ) -> list[ tuple[ pv.DataSet, str, tuple[ float, float, float, float, float, float ] ] ]:
            """Descend récursivement dans la structure MultiBlock jusqu'aux feuilles avec données.

            Returns:
                list of (block, path, bounds) tuples
            """
            leaves = []

            # Cas 1: C'est un MultiBlock avec des sous-blocs
            if hasattr( block, 'n_blocks' ) and block.n_blocks > 0:
                for i in range( block.n_blocks ):
                    subBlock = block.GetBlock( i )
                    blockName = block.get_block_name( i ) if hasattr( block, 'get_block_name' ) else f"Block{i}"
                    newPath = f"{path}/{blockName}" if path else blockName

                    if subBlock is not None:
                        # Récursion
                        leaves.extend( extractLeafBlocks( subBlock, newPath, depth + 1 ) )

            # Cas 2: C'est un dataset final (feuille)
            elif hasattr( block, 'n_cells' ) and block.n_cells > 0:
                bounds = block.bounds
                leaves.append( ( block, path, bounds ) )

            return leaves

        print( "  📦 Extracting volume blocks" )

        # Extraire toutes les feuilles
        allBlocks = extractLeafBlocks( dataset )

        # Filtrer et afficher
        merged = []
        blocksWithPressure = 0
        blocksWithoutPressure = 0

        for block, _path, _bounds in allBlocks:
            hasPressure = 'pressure' in block.cell_data

            if hasPressure:
                blocksWithPressure += 1
                merged.append( block )
            else:
                blocksWithoutPressure += 1

        # Combiner
        combined = pv.MultiBlock( merged ).combine()

        return combined

    # -------------------------------------------------------------------
    def _plotResults( self, surface: pv.PolyData, contributingCells: pv.DataSet, time: list[ int ],
                      path: str, profileStartPoints: list[tuple[float, ...]], computePrincipalStress: bool = True, showDepthProfiles:bool = True,
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


