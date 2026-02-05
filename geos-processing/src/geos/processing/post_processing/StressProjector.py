# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import numpy as np
from geos.geomechanics.model.StressTensor import StressTensor
from scipy.spatial import cKDTree

# ============================================================================
# STRESS PROJECTION
# ============================================================================
class StressProjector:
    """Projects volume stress onto fault surfaces and tracks principal stresses in VTU"""

    # -------------------------------------------------------------------
    def __init__(self, config, adjacencyMapping, geometricProperties):
        """
        Initialize with pre-computed adjacency mapping and geometric properties

        Parameters
        ----------
        config : Configuration object
        adjacencyMapping : dict
            Pre-computed dict mapping fault cells to volume cells
        geometricProperties : dict
            Pre-computed geometric properties from FaultGeometry:
            - 'volumes': cell volumes
            - 'centers': cell centers
            - 'distances': distances to fault
            - 'faultTree': KDTree for fault
        """
        self.config = config
        self.adjacencyMapping = adjacencyMapping

        # Store pre-computed geometric properties
        self.volumeCellVolumes = geometricProperties['volumes']
        self.volumeCenters = geometricProperties['centers']
        self.distanceToFault = geometricProperties['distances']
        self.faultTree = geometricProperties['faultTree']

        # Storage for time series metadata
        self.timestepInfo = []

        # Track which cells to monitor (optional)
        self.monitoredCells = None

        # Output directory for VTU files
        self.vtuOutputDir = None

    # -------------------------------------------------------------------
    def setMonitoredCells(self, cellIndices):
        """
        Set specific cells to monitor (optional)

        Parameters:
            cellIndices: list of volume cell indices to track
                         If None, all contributing cells are tracked
        """
        self.monitoredCells = set(cellIndices) if cellIndices is not None else None

    # -------------------------------------------------------------------
    def projectStressToFault(self, volumeData, volumeInitial, faultSurface,
                                time=None, timestep=None, weightingScheme="arithmetic"):
        """
        Project stress and save principal stresses to VTU

        Now uses pre-computed geometric properties for efficiency
        """
        stressName = self.config.STRESS_NAME
        biotName = self.config.BIOT_NAME

        if stressName not in volumeData.array_names:
            raise ValueError(f"No stress data '{stressName}' in dataset")

        # =====================================================================
        # 1. EXTRACT STRESS DATA
        # =====================================================================
        pressure = volumeData["pressure"] / 1e5
        pressureFault = volumeInitial["pressure"] / 1e5
        pressureInitial = volumeInitial["pressure"] / 1e5
        biot = volumeData[biotName]

        stressEffective = StressTensor.buildFromArray(volumeData[stressName] / 1e5)
        stressEffectiveInitial = StressTensor.buildFromArray(volumeInitial[stressName] / 1e5)

        # Convert effective stress to total stress
        I = np.eye(3)[None, :, :]
        stressTotal = stressEffective - biot[:, None, None] * pressure[:, None, None] * I
        stressTotalInitial = stressEffectiveInitial - biot[:, None, None] * pressureInitial[:, None, None] * I

        # =====================================================================
        # 2. USE PRE-COMPUTED ADJACENCY
        # =====================================================================
        mapping = self.adjacencyMapping

        # =====================================================================
        # 3. PREPARE FAULT GEOMETRY
        # =====================================================================
        normals = faultSurface.cell_data["Normals"]
        tangent1 = faultSurface.cell_data["tangent1"]
        tangent2 = faultSurface.cell_data["tangent2"]

        faultCenters = faultSurface.cell_centers().points
        faultSurface.cell_data['elementCenter'] = faultCenters

        nFault = faultSurface.n_cells
        nVolume = volumeData.n_cells

        # =====================================================================
        # 4. COMPUTE PRINCIPAL STRESSES FOR CONTRIBUTING CELLS
        # =====================================================================
        if self.config.COMPUTE_PRINCIPAL_STRESS and timestep is not None:

            # Collect all unique contributing cells
            allContributingCells = set()
            for faultIdx, neighbors in mapping.items():
                allContributingCells.update(neighbors['plus'])
                allContributingCells.update(neighbors['minus'])

            # Filter by monitored cells if specified
            if self.monitoredCells is not None:
                cellsToTrack = allContributingCells.intersection(self.monitoredCells)
            else:
                cellsToTrack = allContributingCells

            print(f"  📊 Computing principal stresses for {len(cellsToTrack)} contributing cells...")

            # Create mesh with only contributing cells
            contributingMesh = self._createVolumicContribMesh(
                volumeData, faultSurface, cellsToTrack, mapping
            )

            # Save to VTU
            if self.vtuOutputDir is None:
                self.vtuOutputDir = Path(self.config.OUTPUT_DIR) / "principal_stresses"

            self._savePrincipalStressVTU(contributingMesh, time, timestep)

        else:
            contributingMesh = None

        # =====================================================================
        # 6. PROJECT STRESS FOR EACH FAULT CELL
        # =====================================================================
        sigmaNArr = np.zeros(nFault)
        tauArr = np.zeros(nFault)
        tauDipArr = np.zeros(nFault)
        tauStrikeArr = np.zeros(nFault)
        deltaSigmaNArr = np.zeros(nFault)
        deltaTauArr = np.zeros(nFault)
        nContributors = np.zeros(nFault, dtype=int)

        print(f"  🔄 Projecting stress to {nFault} fault cells...")
        print(f"     Weighting scheme: {weightingScheme}")

        for faultIdx in range(nFault):
            if faultIdx not in mapping:
                continue

            volPlus = mapping[faultIdx]['plus']
            volMinus = mapping[faultIdx]['minus']
            allVol = volPlus + volMinus

            if len(allVol) == 0:
                continue

            # ===================================================================
            # CALCULATE WEIGHTS (using pre-computed properties)
            # ===================================================================

            if weightingScheme == 'arithmetic':
                weights = np.ones(len(allVol)) / len(allVol)

            elif weightingScheme == 'harmonic':
                weights = np.ones(len(allVol)) / len(allVol)

            elif weightingScheme == 'distance':
                # Use pre-computed distances
                dists = np.array([self.distanceToFault[v] for v in allVol])
                dists = np.maximum(dists, 1e-6)
                invDists = 1.0 / dists
                weights = invDists / np.sum(invDists)

            elif weightingScheme == 'volume':
                # Use pre-computed volumes
                vols = np.array([self.volumeCellVolumes[v] for v in allVol])
                weights = vols / np.sum(vols)

            elif weightingScheme == 'distanceVolume':
                # Use pre-computed volumes and distances
                vols = np.array([self.volumeCellVolumes[v] for v in allVol])
                dists = np.array([self.distanceToFault[v] for v in allVol])
                dists = np.maximum(dists, 1e-6)

                weights = vols / dists
                weights = weights / np.sum(weights)

            elif weightingScheme == 'inverseSquareDistance':
                # Use pre-computed distances
                dists = np.array([self.distanceToFault[v] for v in allVol])
                dists = np.maximum(dists, 1e-6)
                invSquareDistance = 1.0 / (dists ** 2)
                weights = invSquareDistance / np.sum(invSquareDistance)

            else:
                raise ValueError(f"Unknown weighting scheme: {weightingScheme}")

            # ===================================================================
            # ACCUMULATE WEIGHTED CONTRIBUTIONS
            # ===================================================================

            sigmaN = 0.0
            tau = 0.0
            tauDip = 0.0
            tauStrike = 0.0
            deltaSigmaN = 0.0
            deltaTau = 0.0

            for volIdx, w in zip(allVol, weights):

                # Total stress (with pressure)
                sigmaFinal = stressTotal[volIdx] + pressureFault[volIdx] * np.eye(3)
                sigmaInit = stressTotalInitial[volIdx] + pressureInitial[volIdx] * np.eye(3)

                # Rotate to fault frame
                resFinal = StressTensor.rotateToFaultFrame(
                    sigmaFinal, normals[faultIdx], tangent1[faultIdx], tangent2[faultIdx]
                )

                resInitial = StressTensor.rotateToFaultFrame(
                    sigmaInit, normals[faultIdx], tangent1[faultIdx], tangent2[faultIdx]
                )

                # Accumulate weighted contributions
                sigmaN += w * resFinal['normalStress']
                tau += w * resFinal['shearStress']
                tauDip += w * resFinal['shearDip']
                tauStrike += w * resFinal['shearStrike']
                deltaSigmaN += w * (resFinal['normalStress'] - resInitial['normalStress'])
                deltaTau += w * (resFinal['shearStress'] - resInitial['shearStress'])

            sigmaNArr[faultIdx] = sigmaN
            tauArr[faultIdx] = tau
            tauDipArr[faultIdx] = tauDip
            tauStrikeArr[faultIdx] = tauStrike
            deltaSigmaNArr[faultIdx] = deltaSigmaN
            deltaTauArr[faultIdx] = deltaTau
            nContributors[faultIdx] = len(allVol)

        # =====================================================================
        # 7. STORE RESULTS ON FAULT SURFACE
        # =====================================================================
        faultSurface.cell_data["sigmaNEffective"] = sigmaNArr
        faultSurface.cell_data["tauEffective"] = tauDipArr
        faultSurface.cell_data["tauStrike"] = tauStrikeArr
        faultSurface.cell_data["tauDip"] = tauDipArr
        faultSurface.cell_data["deltaSigmaNEffective"] = deltaSigmaNArr
        faultSurface.cell_data["deltaTauEffective"] = deltaTauArr

        # =====================================================================
        # 8. STATISTICS
        # =====================================================================
        valid = nContributors > 0
        nValid = np.sum(valid)

        print(f"  ✅ Stress projected: {nValid}/{nFault} fault cells ({nValid/nFault*100:.1f}%)")

        if np.sum(valid) > 0:
            print(f"     Contributors per fault cell: min={np.min(nContributors[valid])}, "
                  f"max={np.max(nContributors[valid])}, "
                  f"mean={np.mean(nContributors[valid]):.1f}")

        return faultSurface, volumeData, contributingMesh

    # -------------------------------------------------------------------
    @staticmethod
    def computePrincipalStresses(stressTensor):
        """
        Compute principal stresses and directions

        Convention: Compression is NEGATIVE
        - σ1 = most compressive (most negative)
        - σ3 = least compressive (least negative, or most tensile)

        Returns:
            dict with eigenvalues, eigenvectors, meanStress, deviatoricStress
        """
        eigenvalues, eigenvectors = np.linalg.eigh(stressTensor)

        # Sort from MOST NEGATIVE to LEAST NEGATIVE (most compressive to least)
        # Example: -600 < -450 < -200, so -600 is σ1 (most compressive)
        idx = np.argsort(eigenvalues)  # Ascending order (most negative first)
        eigenvaluesSorted = eigenvalues[idx]
        eigenVectorsSorted = eigenvectors[:, idx]

        return {
            'sigma1': eigenvaluesSorted[0],  # Most compressive (most negative)
            'sigma2': eigenvaluesSorted[1],  # Intermediate
            'sigma3': eigenvaluesSorted[2],  # Least compressive (least negative)
            'meanStress': np.mean(eigenvaluesSorted),
            'deviatoricStress': eigenvaluesSorted[0] - eigenvaluesSorted[2],  # σ1 - σ3 (negative - more negative = positive or less negative)
            'direction1': eigenVectorsSorted[:, 0],  # Direction of σ1
            'direction2': eigenVectorsSorted[:, 1],  # Direction of σ2
            'direction3': eigenVectorsSorted[:, 2]   # Direction of σ3
        }

    # -------------------------------------------------------------------
    def _createVolumicContribMesh(self, volumeData, faultSurface, cellsToTrack, mapping):
        """
        Create a mesh containing only contributing cells with principal stress data
        and compute analytical normal/shear stresses based on fault dip angle

        Parameters
        ----------
        volumeData : pyvista.UnstructuredGrid
            Volume mesh with stress data (rock_stress or averageStress)
        faultSurface : pyvista.PolyData
            Fault surface with dipAngle and strikeAngle per cell
        cellsToTrack : set
            Set of volume cell indices to include
        mapping : dict
            Adjacency mapping {faultIdx: {'plus': [...], 'minus': [...]}}
        """

        # ===================================================================
        # EXTRACT STRESS DATA FROM VOLUME
        # ===================================================================
        stressName = self.config.STRESS_NAME
        biotName = self.config.BIOT_NAME

        if stressName not in volumeData.array_names:
            raise ValueError(f"No stress data '{stressName}' in volume dataset")

        print(f"  📊 Extracting stress from field: '{stressName}'")

        # Extract effective stress and pressure
        pressure = volumeData["pressure"] / 1e5  # Convert to bar
        biot = volumeData[biotName]

        stressEffective = StressTensor.buildFromArray(volumeData[stressName] / 1e5)

        # Convert effective stress to total stress
        I = np.eye(3)[None, :, :]
        stressTotal = stressEffective - biot[:, None, None] * pressure[:, None, None] * I

        # ===================================================================
        # EXTRACT SUBSET OF CELLS
        # ===================================================================
        cellIndices = sorted(list(cellsToTrack))
        cellMask = np.zeros(volumeData.n_cells, dtype=bool)
        cellMask[cellIndices] = True

        subsetMesh = volumeData.extract_cells(cellMask)

        # ===================================================================
        # REBUILD MAPPING: subsetIdx -> originalIdx
        # ===================================================================
        originalCenters = volumeData.cell_centers().points[cellIndices]
        subsetCenters = subsetMesh.cell_centers().points

        tree = cKDTree(originalCenters)

        subsetToOriginal = np.zeros(subsetMesh.n_cells, dtype=int)
        for subsetIdx in range(subsetMesh.n_cells):
            dist, idx = tree.query(subsetCenters[subsetIdx])
            if dist > 1e-6:
                print(f"        WARNING: Cell {subsetIdx} not matched (dist={dist})")
            subsetToOriginal[subsetIdx] = cellIndices[idx]

        # ===================================================================
        # MAP VOLUME CELLS TO FAULT DIP/STRIKE ANGLES
        # ===================================================================
        print(f"     📐 Mapping volume cells to fault dip/strike angles...")

        # Check if fault surface has required data
        if 'dipAngle' not in faultSurface.cell_data:
            print(f"        ⚠️ WARNING: 'dipAngle' not found in faultSurface")
            print(f"        Available fields: {list(faultSurface.cell_data.keys())}")
            return None

        if 'strikeAngle' not in faultSurface.cell_data:
            print(f"        ⚠️ WARNING: 'strikeAngle' not found in faultSurface")

        # Create mapping: volume_cell_id -> [dip_angles, strike_angles]
        volumeToDip = {}
        volumeToStrike = {}

        for faultIdx, neighbors in mapping.items():
            # Get dip and strike angle from fault cell
            faultDip = faultSurface.cell_data['dipAngle'][faultIdx]

            # Strike is optional
            if 'strikeAngle' in faultSurface.cell_data:
                faultStrike = faultSurface.cell_data['strikeAngle'][faultIdx]
            else:
                faultStrike = np.nan

            # Assign to all contributing volume cells (plus and minus)
            for volIdx in neighbors['plus'] + neighbors['minus']:
                if volIdx not in volumeToDip:
                    volumeToDip[volIdx] = []
                    volumeToStrike[volIdx] = []
                volumeToDip[volIdx].append(faultDip)
                volumeToStrike[volIdx].append(faultStrike)

        # Average if a volume cell contributes to multiple fault cells
        volumeToDipAvg = {volIdx: np.mean(dips)
                             for volIdx, dips in volumeToDip.items()}
        volumeToStrikeAvg = {volIdx: np.mean(strikes)
                                for volIdx, strikes in volumeToStrike.items()}

        print(f"        ✅ Mapped {len(volumeToDipAvg)} volume cells to fault angles")

        # Statistics
        allDips = [np.mean(dips) for dips in volumeToDip.values()]
        if len(allDips) > 0:
            print(f"        Dip angle range: [{np.min(allDips):.1f}, {np.max(allDips):.1f}]°")

        # ===================================================================
        # COMPUTE PRINCIPAL STRESSES AND ANALYTICAL FAULT STRESSES
        # ===================================================================
        n_cells = subsetMesh.n_cells

        sigma1Arr = np.zeros(nCells)
        sigma2Arr = np.zeros(nCells)
        sigma3Arr = np.zeros(nCells)
        meanStressArr = np.zeros(nCells)
        deviatoricStressArr = np.zeros(nCells)
        pressureArr = np.zeros(nCells)

        direction1Arr = np.zeros((nCells, 3))
        direction2Arr = np.zeros((nCells, 3))
        direction3Arr = np.zeros((nCells, 3))

        # NEW: Analytical fault stresses
        sigmaNAnalyticalArr = np.zeros(nCells)
        tauAnalyticalArr = np.zeros(nCells)
        dipAngleArr = np.zeros(nCells)
        strikeAngleArr = np.zeros(nCells)
        deltaArr = np.zeros(nCells)

        sideArr = np.zeros(nCells, dtype=int)
        nFaultCellsArr = np.zeros(nCells, dtype=int)

        print(f"     🔢 Computing principal stresses and analytical projections...")

        for subsetIdx in range(nCells):
            origIdx = subsetToOriginal[subsetIdx]

            # ===============================================================
            # COMPUTE PRINCIPAL STRESSES
            # ===============================================================
            # Total stress = effective stress + pore pressure
            sigmaTotalCell = stressTotal[origIdx] + pressure[origIdx] * np.eye(3)
            principal = self.computePrincipalStresses(sigmaTotalCell)

            sigma1Arr[subsetIdx] = principal['sigma1']
            sigma2Arr[subsetIdx] = principal['sigma2']
            sigma3Arr[subsetIdx] = principal['sigma3']
            meanStressArr[subsetIdx] = principal['meanStress']
            deviatoricStressArr[subsetIdx] = principal['deviatoricStress']
            pressureArr[subsetIdx] = pressure[origIdx]

            direction1Arr[subsetIdx] = principal['direction1']
            direction2Arr[subsetIdx] = principal['direction2']
            direction3Arr[subsetIdx] = principal['direction3']

            # ===============================================================
            # COMPUTE ANALYTICAL FAULT STRESSES (Anderson formulas)
            # ===============================================================
            if origIdx in volumeToDipAvg:
                dipDeg = volumeToDipAvg[origIdx]
                dipAngleArr[subsetIdx] = dipDeg

                strikeDeg = volumeToStrikeAvg.get(origIdx, np.nan)
                strikeAngleArr[subsetIdx] = strikeDeg

                # δ = 90° - dip (angle from horizontal)
                deltaDeg = 90.0 - dipDeg
                deltaRad = np.radians(deltaDeg)
                deltaArr[subsetIdx] = deltaDeg

                # Extract principal stresses (compression negative)
                sigma1 = principal['sigma1']  # Most compressive (most negative)
                sigma3 = principal['sigma3']  # Least compressive (least negative)

                # Anderson formulas (1951)
                # σ_n = (σ1 + σ3)/2 - (σ1 - σ3)/2 * cos(2δ)
                # τ = |(σ1 - σ3)/2 * sin(2δ)|

                sigmaMean = (sigma1 + sigma3) / 2.0
                sigmaDiff = (sigma1 - sigma3) / 2.0

                sigmaNAnalytical = sigmaMean - sigmaDiff * np.cos(2 * deltaRad)
                tauAnalytical = sigmaDiff * np.sin(2 * deltaRad)

                sigmaNAnalyticalArr[subsetIdx] = sigmaNAnalytical
                tauAnalyticalArr[subsetIdx] = np.abs(tauAnalytical)
            else:
                # No fault association - set to NaN
                dipAngleArr[subsetIdx] = np.nan
                strikeAngleArr[subsetIdx] = np.nan
                deltaArr[subsetIdx] = np.nan
                sigmaNAnalyticalArr[subsetIdx] = np.nan
                tauAnalyticalArr[subsetIdx] = np.nan

            # ===============================================================
            # DETERMINE SIDE (plus/minus/both)
            # ===============================================================
            isPlus = False
            isMinus = False
            faultCellCount = 0

            for faultIdx, neighbors in mapping.items():
                if origIdx in neighbors['plus']:
                    isPlus = True
                    faultCellCount += 1
                if origIdx in neighbors['minus']:
                    isMinus = True
                    faultCellCount += 1

            if isPlus and isMinus:
                sideArr[subsetIdx] = 3  # both
            elif isPlus:
                sideArr[subsetIdx] = 1  # plus
            elif isMinus:
                sideArr[subsetIdx] = 2  # minus
            else:
                sideArr[subsetIdx] = 0  # none (should not happen)

            nFaultCellsArr[subsetIdx] = faultCellCount

        # ===================================================================
        # ADD DATA TO MESH
        # ===================================================================
        subsetMesh.cell_data['sigma1'] = sigma1Arr
        subsetMesh.cell_data['sigma2'] = sigma2Arr
        subsetMesh.cell_data['sigma3'] = sigma3Arr
        subsetMesh.cell_data['meanStress'] = meanStressArr
        subsetMesh.cell_data['deviatoricStress'] = deviatoricStressArr
        subsetMesh.cell_data['pressure_bar'] = pressureArr

        subsetMesh.cell_data['sigma1Direction'] = direction1Arr
        subsetMesh.cell_data['sigma2Direction'] = direction2Arr
        subsetMesh.cell_data['sigma3Direction'] = direction3Arr

        # Analytical fault stresses
        subsetMesh.cell_data['sigmaNAnalytical'] = sigmaNAnalyticalArr
        subsetMesh.cell_data['tauAnalytical'] = tauAnalyticalArr
        subsetMesh.cell_data['dipAngle'] = dipAngleArr
        subsetMesh.cell_data['strikeAngle'] = strikeAngleArr
        subsetMesh.cell_data['deltaAngle'] = deltaArr

        # ===================================================================
        # COMPUTE SCU ANALYTICALLY (Mohr-Coulomb)
        # ===================================================================
        if hasattr(self.config, 'FRICTION_ANGLE') and hasattr(self.config, 'COHESION'):
            mu = np.tan(np.radians(self.config.FRICTION_ANGLE))
            cohesion = self.config.COHESION

            # τ_crit = C - σ_n * μ
            # Note: σ_n is negative (compression), so -σ_n * μ is positive
            tauCriticalArr = cohesion - sigmaNAnalyticalArr * mu

            # SCU = τ / τ_crit
            SCUAnalyticalArr = np.divide(
                tauAnalyticalArr,
                tauCriticalArr,
                out=np.zeros_like(tauAnalyticalArr),
                where=tauCriticalArr != 0
            )

            subsetMesh.cell_data['tauCriticalAnalytical'] = tauCriticalArr
            subsetMesh.cell_data['SCUAnalytical'] = SCUAnalyticalArr

            # CFS (Coulomb Failure Stress)
            CFSAnalyticalArr = tauAnalyticalArr - mu * (-sigmaNAnalyticalArr)
            subsetMesh.cell_data['CFSAnalytical'] = CFSAnalyticalArr

        subsetMesh.cell_data['side'] = sideArr
        subsetMesh.cell_data['nFaultCells'] = nFaultCellsArr
        subsetMesh.cell_data['originalCellId'] = subsetToOriginal

        # ===================================================================
        # STATISTICS
        # ===================================================================
        validAnalytical = ~np.isnan(sigmaNAnalyticalArr)
        nValid = np.sum(validAnalytical)

        if nValid > 0:
            print(f"     📊 Analytical fault stresses computed for {nValid}/{nCells} cells")
            print(f"        σ_n range: [{np.nanmin(sigmaNAnalyticalArr):.1f}, {np.nanmax(sigmaNAnalyticalArr):.1f}] bar")
            print(f"        τ range: [{np.nanmin(tauAnalyticalArr):.1f}, {np.nanmax(tauAnalyticalArr):.1f}] bar")
            print(f"        Dip angle range: [{np.nanmin(dipAngleArr):.1f}, {np.nanmax(dipAngleArr):.1f}]°")

            if hasattr(self.config, 'FRICTION_ANGLE') and hasattr(self.config, 'COHESION'):
                print(f"        SCU range: [{np.nanmin(SCUAnalyticalArr[validAnalytical]):.2f}, {np.nanmax(SCUAnalyticalArr[validAnalytical]):.2f}]")
                nCritical = np.sum((SCUAnalyticalArr >= 0.8) & (SCUAnalyticalArr < 1.0))
                nUnstable = np.sum(SCUAnalyticalArr >= 1.0)
                print(f"        Critical cells (SCU≥0.8): {nCritical} ({nCritical/nValid*100:.1f}%)")
                print(f"        Unstable cells (SCU≥1.0): {nUnstable} ({nUnstable/nValid*100:.1f}%)")
        else:
            print(f"     ⚠️  No analytical stresses computed (no fault mapping)")

        return subsetMesh

    # -------------------------------------------------------------------
    def _savePrincipalStressVTU(self, mesh, time, timestep):
        """
        Save principal stress mesh to VTU file

        Parameters:
            mesh: PyVista mesh with principal stress data
            time: Simulation time
            timestep: Timestep index
        """
        # Create output directory
        self.vtuOutputDir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        vtuFilename = f"principal_stresses_{timestep:05d}.vtu"
        vtuPath = self.vtuOutputDir / vtuFilename

        # Save mesh
        mesh.save(str(vtuPath))

        # Store metadata for PVD
        self.timestepInfo.append({
            'time': time if time is not None else timestep,
            'timestep': timestep,
            'file': vtuFilename
        })

        print(f"     💾 Saved principal stresses: {vtuFilename}")

    # -------------------------------------------------------------------
    def savePVDCollection(self, filename="principal_stresses.pvd"):
        """
        Create PVD file for time series visualization in ParaView

        Parameters:
            filename: Name of PVD file
        """
        if len(self.timestepInfo) == 0:
            print("⚠️  No timestep data to save in PVD")
            return

        pvdPath = self.vtuOutputDir / filename

        print(f"\n💾 Creating PVD collection: {pvdPath}")
        print(f"   Timesteps: {len(self.timestepInfo)}")

        # Create XML structure
        root = Element('VTKFile')
        root.set('type', 'Collection')
        root.set('version', '0.1')
        root.set('byte_order', 'LittleEndian')

        collection = SubElement(root, 'Collection')

        for info in self.timestepInfo:
            dataset = SubElement(collection, 'DataSet')
            dataset.set('timestep', str(info['time']))
            dataset.set('group', '')
            dataset.set('part', '0')
            dataset.set('file', info['file'])

        # Write to file
        tree = ElementTree(root)
        tree.write(str(pvdPath), encoding='utf-8', xml_declaration=True)

        print(f"   ✅ PVD file created successfully")
        print(f"   📂 Output directory: {self.vtuOutputDir}")
        print(f"\n   🎨 To visualize in ParaView:")
        print(f"      1. Open: {pvdPath}")
        print(f"      2. Apply")
        print(f"      3. Color by: sigma1, sigma2, sigma3, meanStress, etc.")
        print(f"      4. Use 'side' filter to show plus/minus/both")

