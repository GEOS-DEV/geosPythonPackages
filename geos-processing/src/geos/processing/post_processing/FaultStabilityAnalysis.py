# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
from pathlib import Path
import numpy as np
import pyvista as pv
import matplotlib.pyplot as plt
import pyfiglet
from scipy.spatial import cKDTree
from scipy.interpolate import splprep, splev, LinearNDInterpolator, Rbf
import os
import math


# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    """Configuration parameters for fault analysis"""

    # Mechanical parameters
    FRICTION_ANGLE = 12    # [degrees]
    COHESION = 0           # [bar]

    # Normal orientation
    ROTATE_NORMALS = False  # Rotate normals and tangents from 180°

    # Sensitivity analysis
    RUN_SENSITIVITY = True  # Enable sensitivity analysis
    SENSITIVITY_FRICTION_ANGLES = [12,15,18,20,22,25]  # degrees
    SENSITIVITY_COHESIONS = [0,1,2,5,10]  # bar

    # Visualization
    Z_SCALE = 1.0
    SHOW_NORMAL_PLOTS = True       # Show the mesh grid and normals at fault planes
    SHOW_CONTRIBUTION_VIZ = True  # Show volume contribution visualization (first timestep only)
    SHOW_DEPTH_PROFILES = True     # Active les profils verticaux
    N_DEPTH_PROFILES = 1           # Nombre de lignes verticales

    MIN_DEPTH_PROFILES = None
    MAX_DEPTH_PROFILES = None
    SHOW_PLOTS = True              # Set to False to skip interactive plots
    SAVE_PLOTS = True              # Set to False to skip saving plots
    SAVE_CONTRIBUTION_CELLS = True # Save vtu contributive cells
    WEIGHTING_SCHEME = "arithmetic"

    COMPUTE_PRINCIPAL_STRESS = False
    SHOW_PROFILE_EXTRACTOR = True

    PROFILE_START_POINTS = [
    (2282.61, 1040, 0)]   # Profile Fault 1

    PROFILE_SEARCH_RADIUS = None

    # Time series - List of time indices to process (None = all)
    TIME_INDEX = [0,-1]

    # File paths
    PATH = ""
    GRID_FILE = "mesh_faulted_reservoir_60_mod.vtu"
    PVD_FILE = "faultModel.pvd"

    # Variable names
    STRESS_NAME = "averageStress"
    BIOT_NAME = "rockPorosity_biotCoefficient"

    # Faults attributes
    FAULT_ATTRIBUTE = "Fault"
    FAULT_VALUES = [1]

    # Output
    OUTPUT_DIR = "Processed_Fault_Analysis"
    SENSITIVITY_OUTPUT_DIR = "Processed_Fault_Analysis/Sensitivity_Analysis"


# ============================================================================
# MOHR COULOMB
# ============================================================================
class MohrCoulomb:
    """Mohr-Coulomb failure criterion analysis"""

    @staticmethod
    def analyze(surface, cohesion, frictionAngleDeg, time=0, verbose=True):
        """
        Perform Mohr-Coulomb stability analysis

        Parameters:
            surface: fault surface with stress data
            cohesion: cohesion in bar
            frictionAngleDeg: friction angle in degrees
            time: simulation time
            verbose: print statistics
        """
        mu = np.tan(np.radians(frictionAngleDeg))

        # Extract stress components
        sigmaN = surface.cell_data["sigmaNEffective"]
        tau = surface.cell_data["tauEffective"]
        deltaSigmaN = surface.cell_data['deltaSigmaNEffective']
        deltaTau = surface.cell_data['deltaTauEffective']

        # Mohr-Coulomb failure envelope
        tauCritical = cohesion - sigmaN * mu

        # Coulomb Failure Stress
        CFS = tau - mu * sigmaN
        # deltaCFS = deltaTau - mu * deltaSigmaN

        # Shear Capacity Utilization: SCU = τ / τ_crit
        SCU = np.divide(tau, tauCritical, out=np.zeros_like(tau), where=tauCritical != 0)

        if "SCUInitial" not in surface.cell_data:
            # First timestep: store as initial reference
            SCUInitial = SCU.copy()
            CFSInitial = CFS.copy()
            deltaSCU = np.zeros_like(SCU)
            deltaCFS = np.zeros_like(CFS)

            surface.cell_data["SCUInitial"] = SCUInitial
            surface.cell_data["CFSInitial"] = CFSInitial

            isInitial = True
        else:
            # Subsequent timesteps: calculate change from initial
            SCUInitial = surface.cell_data["SCUInitial"]
            CFSInitial = surface.cell_data['CFSInitial']
            deltaSCU = SCU - SCUInitial
            deltaCFS = CFS - CFSInitial
            isInitial = False

        # Stability classification
        stability = np.zeros_like(tau, dtype=int)
        stability[SCU >= 0.8] = 1  # Critical
        stability[SCU >= 1.0] = 2  # Unstable

        # Failure probability (sigmoid)
        k = 10.0
        failureProba = 1.0 / (1.0 + np.exp(-k * (SCU - 1.0)))

        # Safety margin
        safety = tauCritical - tau

        # Store results
        surface.cell_data.update({
            "mohrCohesion": np.full(surface.n_cells, cohesion),
            "mohrFrictionAngle": np.full(surface.n_cells, frictionAngleDeg),
            "mohrFrictionCoefficient": np.full(surface.n_cells, mu),
            "mohr_critical_shear_stress": tauCritical,
            "SCU": SCU,
            "deltaSCU": deltaSCU,
            "CFS" : CFS,
            "deltaCFS": deltaCFS,
            "safetyMargin": safety,
            "stabilityState": stability,
            "failureProbability": failureProba
        })

        if verbose:
            nStable = np.sum(stability == 0)
            nCritical = np.sum(stability == 1)
            nUnstable = np.sum(stability == 2)

            # Additional info on deltaSCU
            if not isInitial:
                meanDelta = np.mean(np.abs(deltaSCU))
                maxIncrease = np.max(deltaSCU)
                maxDecrease = np.min(deltaSCU)
                print(f"  ✅ Mohr-Coulomb: {nUnstable} unstable, {nCritical} critical, "
                      f"{nStable} stable cells")
                print(f"     ΔSCU: mean={meanDelta:.3f}, maxIncrease={maxIncrease:.3f}, "
                      f"maxDecrease={maxDecrease:.3f}")
            else:
                print(f"  ✅ Mohr-Coulomb (initial): {nUnstable} unstable, {nCritical} critical, "
                      f"{nStable} stable cells")

        return surface


# ============================================================================
# TIME SERIES PROCESSING
# ============================================================================
class TimeSeriesProcessor:
    """Process multiple time steps from PVD file"""

    # -------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.outputDir = Path(config.OUTPUT_DIR)
        self.outputDir.mkdir(exist_ok=True)

    # -------------------------------------------------------------------
    def process(self, path, faultGeometry, pvdFile):
        """
        Process all time steps using pre-computed fault geometry

        Parameters:
            path: base path for input files
            faultGeometry: FaultGeometry object with initialized topology
            pvdFile: PVD file name
        """
        pvdReader = pv.PVDReader(path / pvdFile)
        timeValues = np.array(pvdReader.timeValues)

        if self.config.TIME_INDEX:
            timeValues = timeValues[self.config.TIME_INDEX]

        outputFiles = []
        dataInitial = None
        SCUInitialReference = None

        # Get pre-computed data from faultGeometry
        surface = faultGeometry.faultSurface
        adjacencyMapping = faultGeometry.adjacencyMapping
        geometricProperties = faultGeometry.getGeometricProperties()

        # Initialize projector with pre-computed topology
        projector = StressProjector(self.config, adjacencyMapping, geometricProperties)


        print('\n')
        print("=" * 60)
        print("TIME SERIES PROCESSING")
        print("=" * 60)

        for i, time in enumerate(timeValues):
            print(f"\n→ Step {i+1}/{len(timeValues)}: {time/(365.25*24*3600):.2f} years")

            # Read time step
            idx = self.config.TIME_INDEX[i] if self.config.TIME_INDEX else i
            pvdReader.set_active_time_point(idx)
            dataset = pvdReader.read()

            # Merge blocks
            volumeData = self._mergeBlocks(dataset)

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
                time=timeValues[i],                            # Simulation time
                timestep=i,                                     # Timestep index
                weightingScheme=self.config.WEIGHTING_SCHEME
            )

            # -----------------------------------
            # Mohr-Coulomb analysis
            # -----------------------------------
            cohesion = self.config.COHESION
            frictionAngle = self.config.FRICTION_ANGLE
            surfaceResult = MohrCoulomb.analyze(surfaceResult, cohesion, frictionAngle, time)

            # -----------------------------------
            # Visualize
            # -----------------------------------
            self._plotResults(surfaceResult, contributingCells, time, self.outputDir)

            # -----------------------------------
            # Sensitivity analysis
            # -----------------------------------
            if self.config.RUN_SENSITIVITY:
                analyzer = SensitivityAnalyzer(self.config)
                sensitivityResults = analyzer.runAnalysis(surfaceResult, time)

            # Save
            filename = f'fault_analysis_{i:04d}.vtu'
            surfaceResult.save(self.outputDir / filename)
            outputFiles.append((time, filename))
            print(f"  💾 Saved: {filename}")

        # Create master PVD
        self._createPVD(outputFiles)

        return surfaceResult

    # -------------------------------------------------------------------
    def _mergeBlocks(self, dataset):
        """Merge multi-block dataset - descente automatique jusqu'aux données"""

        # -----------------------------------------------
        def extractLeafBlocks(block, path="", depth=0):
            """
            Descend récursivement dans la structure MultiBlock jusqu'aux feuilles avec données

            Returns:
                list of (block, path, bounds) tuples
            """
            leaves = []

            # Cas 1: C'est un MultiBlock avec des sous-blocs
            if hasattr(block, 'n_blocks') and block.n_blocks > 0:
                for i in range(block.n_blocks):
                    subBlock = block.GetBlock(i)
                    blockName = block.get_block_name(i) if hasattr(block, 'get_block_name') else f"Block{i}"
                    newPath = f"{path}/{blockName}" if path else blockName

                    if subBlock is not None:
                        # Récursion
                        leaves.extend(extractLeafBlocks(subBlock, newPath, depth + 1))

            # Cas 2: C'est un dataset final (feuille)
            elif hasattr(block, 'n_cells') and block.n_cells > 0:
                bounds = block.bounds
                leaves.append((block, path, bounds))

            return leaves

        print(f"  📦 Extracting volume blocks")

        # Extraire toutes les feuilles
        allBlocks = extractLeafBlocks(dataset)

        # Filtrer et afficher
        merged = []
        blocksWithPressure = 0
        blocksWithoutPressure = 0

        for block, path, bounds in allBlocks:
            hasPressure = 'pressure' in block.cell_data

            if hasPressure:
                blocksWithPressure += 1
                merged.append(block)
            else:
                blocksWithoutPressure += 1

        # Combiner
        combined = pv.MultiBlock(merged).combine()

        return combined

    # -------------------------------------------------------------------
    def _plotResults(self, surface, contributingCells, time, path):

        Visualizer.plotMohrCoulombDiagram( surface, time, path,
                                              show=self.config.SHOW_PLOTS,
                                              save=self.config.SAVE_PLOTS )

        # Profils verticaux automatiques
        if self.config.SHOW_DEPTH_PROFILES:
            Visualizer.plotDepthProfiles(
                self,
                surface, time, path,
                show=self.config.SHOW_PLOTS,
                save=self.config.SAVE_PLOTS,
                profileStartPoints=self.config.PROFILE_START_POINTS )

        visualizer = Visualizer(self.config)

        if self.config.COMPUTE_PRINCIPAL_STRESS:

            # Plot principal stress from volume cells
            visualizer.plotVolumeStressProfiles(
                volumeMesh=contributingCells,
                faultSurface=surface,
                time=time,
                path=path,
                profileStartPoints=self.config.PROFILE_START_POINTS )

            # Visualize comparison analytical/numerical
            visualizer.plotAnalyticalVsNumericalComparison(
                volumeMesh=contributingCells,
                faultSurface=surface,
                time=time,
                path=path,
                show=self.config.SHOW_PLOTS,
                save=self.config.SAVE_PLOTS,
                profileStartPoints=self.config.PROFILE_START_POINTS)

    # -------------------------------------------------------------------
    def _createPVD(self, outputFiles):
        """Create PVD collection file"""
        pvdPath = self.outputDir / 'fault_analysis.pvd'
        with open(pvdPath, 'w') as f:
            f.write('<VTKFile type="Collection" version="0.1">\n')
            f.write('  <Collection>\n')
            for t, fname in outputFiles:
                f.write(f'    <DataSet timestep="{t}" file="{fname}"/>\n')
            f.write('  </Collection>\n')
            f.write('</VTKFile>\n')
        print(f"\n✅ PVD created: {pvdPath}")


# ============================================================================
# MAIN
# ============================================================================
def main():

    """Main execution function"""
    config = Config()

    print("=" * 62)
    ascii_banner = pyfiglet.figlet_format("Fault Analysis")
    print(ascii_banner)
    print("=" * 62)

    path = Path(config.PATH)

    # Load fault geometry
    mesh = pv.read(path / config.GRID_FILE)
    print(f"✅ Mesh loaded: {config.GRID_FILE} | {mesh.n_cells} cells")

    # Read first volume dataset
    pvdReader = pv.PVDReader(path / config.PVD_FILE)
    pvdReader.set_active_time_point(0)
    dataset = pvdReader.read()

    # IMPORTANT : Utiliser le même merge que dans la boucle
    processor = TimeSeriesProcessor(config)
    volumeMesh = processor._mergeBlocks(dataset)
    print(f"✅ Volume mesh extracted: {volumeMesh.n_cells} cells")


    # Initialize fault geometry with topology pre-computation
    print("\n📐 Initialize fault geometry")
    faultGeometry = FaultGeometry(
        config = config,
        mesh=mesh,
        faultValues=config.FAULT_VALUES,
        faultAttribute=config.FAULT_ATTRIBUTE,
        volumeMesh=volumeMesh)


    # Compute normals and adjacency topology (done once!)
    print("🔧 Computing normals and adjacency topology")
    faultSurface, adjacencyMapping = faultGeometry.initialize( scaleFactor=50.0 )


    # Process time series
    processor = TimeSeriesProcessor(config)
    processor.process(path, faultGeometry, config.PVD_FILE)

    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
