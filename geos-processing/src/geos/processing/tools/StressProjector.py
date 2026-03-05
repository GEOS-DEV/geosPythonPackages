# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import logging
from pathlib import Path
import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Any, Union, Set
from scipy.spatial import cKDTree
from xml.etree.ElementTree import ElementTree, Element, SubElement
from enum import Enum

from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.util.numpy_support import vtk_to_numpy

from geos.geomechanics.model.StressTensor import ( StressTensor )

from geos.mesh.io.vtkIO import ( writeMesh, VtkOutput )
from geos.mesh.utils.genericHelpers import ( extractCellSelection )
from geos.mesh.utils.arrayHelpers import ( isAttributeInObject, getArrayInObject, computeCellCenterCoordinates )
from geos.mesh.utils.arrayModifiers import ( createAttribute, updateAttribute )
from geos.utils.pieceEnum import ( Piece )

from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.GeosOutputsConstants import ( GeosMeshOutputsEnum, PostProcessingOutputsEnum )

loggerTitle = "Stress Projector"


class StressProjectorWeightingScheme( str, Enum ):
    """Enum for weighting scheme."""
    ARITHMETIC = "arithmetic"
    HARM = "harmonic"
    DIST = "distance"
    VOL = "volume"
    DIST_VOL = "distanceVolume"
    INV_SQ_DIST = "inverseSquareDistance"


class StressProjector:
    """Projects volume stress onto fault surfaces and tracks principal stresses in VTU."""

    def __init__( self: Self,
                  adjacencyMapping: dict[ int, dict[ str, list[ int ] ] ],
                  geometricProperties: dict[ str, Any ],
                  outputDir: str = ".",
                  logger: Union[ Logger, None ] = None ) -> None:
        """Initialize with pre-computed adjacency mapping and geometric properties.

        Args:
            adjacencyMapping (dict[int, list[ vtkUnstructuredGrid]]): Pre-computed dict mapping fault cells to volume cells
            geometricProperties (dict[str, Any]): Pre-computed geometric properties from FaultGeometry:
                - 'volumes': cell volumes
                - 'centers': cell centers
                - 'distances': distances to fault
                - 'faultTree': KDTree for fault
            outputDir (str, optional): Output directory to save plots.
                Defaults is current directory
            logger (Union[Logger, None], optional): A logger to manage the output messages.
                    Defaults to None, an internal logger is used.
        """
        self.adjacencyMapping = adjacencyMapping
        self.stressName: str = GeosMeshOutputsEnum.AVERAGE_STRESS.value
        self.biotName: str = PostProcessingOutputsEnum.BIOT_COEFFICIENT.value

        # Store pre-computed geometric properties
        self.volumeCellVolumes = geometricProperties[ 'volumes' ]
        self.volumeCenters = geometricProperties[ 'centers' ]
        self.distanceToFault = geometricProperties[ 'distances' ]
        self.faultTree = geometricProperties[ 'faultTree' ]

        # Storage for time series metadata
        self.timestepInfo: list[ dict[ str, Any ] ] = []

        # Track which cells to monitor (optional)
        self.monitoredCells: set[ int ] | None = set()

        # Output directory for VTU files
        self.vtuOutputDir = Path( outputDir ) / "principal_stresses"

        # Logger
        self.logger: Logger
        if logger is None:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( f"{logger.name}" )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setMonitoredCells( self: Self, cellIndices: list[ int ] ) -> None:
        """Set specific cells to monitor (optional).

        Args:
            cellIndices (list[int], optional): List of volume cell indices to track.
                         If None, all contributing cells are tracked
        """
        if len( cellIndices ) != 0:
            self.monitoredCells = set( cellIndices )

    def projectStressToFault(
            self: Self,
            volumeData: vtkUnstructuredGrid,
            volumeInitial: vtkUnstructuredGrid,
            faultSurface: vtkUnstructuredGrid,
            time: float,
            timestep: int | None = None,
            weightingScheme: StressProjectorWeightingScheme = StressProjectorWeightingScheme.ARITHMETIC,
            computePrincipalStresses: bool = False,
            frictionAngle: float = 10,
            cohesion: float = 0 ) -> tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid, vtkUnstructuredGrid | None ]:
        """Project stress and save principal stresses to VTU.

        Now uses pre-computed geometric properties for efficiency

        Args:
            volumeData (vtkUnstructuredGrid): Volumic mesh.
            volumeInitial (vtkUnstructuredGrid): Pre-simulation mesh
            faultSurface (vtkUnstructureGrid): Fault mesh.
            time (float): Time.
            timestep (int | None, optional): Timestep considered. Defaults is None.
            weightingScheme (StressProjectorWeightingScheme, optional): Weighting scheme for projection. Defaults is "arithmetic".
            computePrincipalStresses (bool, optional): Flag to compute principal stresses.
                Defaults is False.
            frictionAngle (float, optional): Friction angle in degrees.
                Defaults is 10 degrees.
            cohesion (float, optional): Rock cohesion in bar.
                Defaults is 0 bar.

        Returns:
            tuple[vtkUnstructuredGrid, vtkUnstructuredGrid, vtkUnstructuredGrid]: Fault mesh, volumic mesh, cell contributing mesh.
        """
        if not isAttributeInObject( volumeData, self.stressName, Piece.CELLS ):
            raise ValueError( f"No stress data '{self.stressName}' in dataset" )

        # =====================================================================
        # 1. EXTRACT STRESS DATA
        # =====================================================================
        pressure = getArrayInObject( volumeData, "pressure", Piece.CELLS ) / 1e5
        pressureFault = getArrayInObject( volumeInitial, "pressure", Piece.CELLS ) / 1e5
        pressureInitial = getArrayInObject( volumeInitial, "pressure", Piece.CELLS ) / 1e5
        biot = getArrayInObject( volumeData, self.biotName, Piece.CELLS )

        stressEffective = StressTensor.buildFromArray(
            getArrayInObject( volumeData, self.stressName, Piece.CELLS ) / 1e5 )
        stressEffectiveInitial = StressTensor.buildFromArray(
            getArrayInObject( volumeInitial, self.stressName, Piece.CELLS ) / 1e5 )

        # Convert effective stress to total stress
        arrI = np.eye( 3 )[ None, :, : ]
        stressTotal = stressEffective - biot[ :, None, None ] * pressure[ :, None, None ] * arrI
        stressTotalInitial = stressEffectiveInitial - biot[ :, None, None ] * pressureInitial[ :, None, None ] * arrI

        # =====================================================================
        # 3. PREPARE FAULT GEOMETRY
        # =====================================================================
        normals = vtk_to_numpy( faultSurface.GetCellData().GetNormals() )
        tangent1 = vtk_to_numpy( faultSurface.GetCellData().GetArray( "Tangents1" ) )
        tangent2 = vtk_to_numpy( faultSurface.GetCellData().GetArray( "Tangents2" ) )

        faultCenters = vtk_to_numpy( computeCellCenterCoordinates( faultSurface ) )
        updateAttribute( faultSurface, faultCenters, 'elementCenter', Piece.CELLS )

        nFault = faultSurface.GetNumberOfCells()

        # =====================================================================
        # 4. COMPUTE PRINCIPAL STRESSES FOR CONTRIBUTING CELLS
        # =====================================================================
        if computePrincipalStresses and timestep is not None:

            # Collect all unique contributing cells
            allContributingCells: Set[ int ] = set()
            for _faultIdx, neighbors in self.adjacencyMapping.items():
                allContributingCells.update( neighbors[ 'plus' ] )
                allContributingCells.update( neighbors[ 'minus' ] )

            # Filter by monitored cells if specified
            if self.monitoredCells is not None:
                cellsToTrack = allContributingCells.intersection( self.monitoredCells )
            else:
                cellsToTrack = allContributingCells

            self.logger.info( f"  📊 Computing principal stresses for {len(cellsToTrack)} contributing cells..." )

            # Create mesh with only contributing cells
            contributingMesh = self._createVolumicContribMesh( volumeData,
                                                               faultSurface,
                                                               cellsToTrack,
                                                               self.adjacencyMapping,
                                                               computePrincipalStresses=computePrincipalStresses,
                                                               frictionAngle=frictionAngle,
                                                               cohesion=cohesion )

            self._savePrincipalStressVTU( contributingMesh, time, timestep )

        else:
            contributingMesh = None

        # =====================================================================
        # 6. PROJECT STRESS FOR EACH FAULT CELL
        # =====================================================================
        sigmaNArr = np.zeros( nFault )
        tauArr = np.zeros( nFault )
        tauDipArr = np.zeros( nFault )
        tauStrikeArr = np.zeros( nFault )
        deltaSigmaNArr = np.zeros( nFault )
        deltaTauArr = np.zeros( nFault )
        nContributors = np.zeros( nFault, dtype=int )

        self.logger.info( f"  🔄 Projecting stress to {nFault} fault cells...\n"
                          f"     Weighting scheme: {weightingScheme}" )

        for faultIdx in range( nFault ):
            if faultIdx not in self.adjacencyMapping:
                continue

            volPlus = self.adjacencyMapping[ faultIdx ][ 'plus' ]
            volMinus = self.adjacencyMapping[ faultIdx ][ 'minus' ]
            allVol = volPlus + volMinus

            if len( allVol ) == 0:
                continue

            # ===================================================================
            # CALCULATE WEIGHTS (using pre-computed properties)
            # ===================================================================

            if weightingScheme == StressProjectorWeightingScheme.ARITHMETIC or weightingScheme == StressProjectorWeightingScheme.HARM:
                weights = np.ones( len( allVol ) ) / len( allVol )

            elif weightingScheme == StressProjectorWeightingScheme.DIST:
                # Use pre-computed distances
                dists = np.array( [ self.distanceToFault[ v ] for v in allVol ] )
                dists = np.maximum( dists, 1e-6 )
                invDists = 1.0 / dists
                weights = invDists / np.sum( invDists )

            elif weightingScheme == StressProjectorWeightingScheme.VOL:
                # Use pre-computed volumes
                vols = np.array( [ self.volumeCellVolumes[ v ] for v in allVol ] )
                weights = vols / np.sum( vols )

            elif weightingScheme == StressProjectorWeightingScheme.DIST_VOL:
                # Use pre-computed volumes and distances
                vols = np.array( [ self.volumeCellVolumes[ v ] for v in allVol ] )
                dists = np.array( [ self.distanceToFault[ v ] for v in allVol ] )
                dists = np.maximum( dists, 1e-6 )

                weights = vols / dists
                weights = weights / np.sum( weights )

            elif weightingScheme == StressProjectorWeightingScheme.INV_SQ_DIST:
                # Use pre-computed distances
                dists = np.array( [ self.distanceToFault[ v ] for v in allVol ] )
                dists = np.maximum( dists, 1e-6 )
                invSquareDistance = 1.0 / ( dists**2 )
                weights = invSquareDistance / np.sum( invSquareDistance )

            else:
                raise ValueError( f"Unknown weighting scheme: {weightingScheme}" )

            # ===================================================================
            # ACCUMULATE WEIGHTED CONTRIBUTIONS
            # ===================================================================

            sigmaN = 0.0
            tau = 0.0
            tauDip = 0.0
            tauStrike = 0.0
            deltaSigmaN = 0.0
            deltaTau = 0.0

            for volIdx, w in zip( allVol, weights ):

                # Total stress (with pressure)
                sigmaFinal = stressTotal[ volIdx ] + pressureFault[ volIdx ] * np.eye( 3 )
                sigmaInit = stressTotalInitial[ volIdx ] + pressureInitial[ volIdx ] * np.eye( 3 )

                # Rotate to fault frame
                resFinal = StressTensor.rotateToFaultFrame( sigmaFinal, normals[ faultIdx ], tangent1[ faultIdx ],
                                                            tangent2[ faultIdx ] )

                resInitial = StressTensor.rotateToFaultFrame( sigmaInit, normals[ faultIdx ], tangent1[ faultIdx ],
                                                              tangent2[ faultIdx ] )

                # Accumulate weighted contributions
                sigmaN += w * resFinal[ 'normalStress' ]
                tau += w * resFinal[ 'shearStress' ]
                tauDip += w * resFinal[ 'shearDip' ]
                tauStrike += w * resFinal[ 'shearStrike' ]
                deltaSigmaN += w * ( resFinal[ 'normalStress' ] - resInitial[ 'normalStress' ] )
                deltaTau += w * ( resFinal[ 'shearStress' ] - resInitial[ 'shearStress' ] )

            sigmaNArr[ faultIdx ] = sigmaN
            tauArr[ faultIdx ] = tau
            tauDipArr[ faultIdx ] = tauDip
            tauStrikeArr[ faultIdx ] = tauStrike
            deltaSigmaNArr[ faultIdx ] = deltaSigmaN
            deltaTauArr[ faultIdx ] = deltaTau
            nContributors[ faultIdx ] = len( allVol )

        # =====================================================================
        # 7. STORE RESULTS ON FAULT SURFACE
        # =====================================================================
        for attributeName, value in zip(
            [ "sigmaNEffective", "tauEffective", "tauStrike", "tauDip", "deltaSigmaNEffective", "deltaTauEffective" ],
            [ sigmaNArr, tauDipArr, tauStrikeArr, tauDipArr, deltaSigmaNArr, deltaTauArr ] ):
            updateAttribute( faultSurface, value, attributeName, Piece.CELLS )

        # =====================================================================
        # 8. STATISTICS
        # =====================================================================
        valid = nContributors > 0
        nValid = np.sum( valid )

        self.logger.info( f"  ✅ Stress projected: {nValid}/{nFault} fault cells ({nValid/nFault*100:.1f}%)" )

        if np.sum( valid ) > 0:
            self.logger.info( f"     Contributors per fault cell: min={np.min(nContributors[valid])}, "
                              f"max={np.max(nContributors[valid])}, "
                              f"mean={np.mean(nContributors[valid]):.1f}" )

        return faultSurface, volumeData, contributingMesh

    @staticmethod
    def computePrincipalStresses( stressTensor: StressTensor ) -> dict[ str, npt.NDArray[ np.float64 ] ]:
        """Compute principal stresses and directions.

        Convention: Compression is NEGATIVE
        - σ1 = most compressive (most negative)
        - σ3 = least compressive (least negative, or most tensile)

        Args:
            stressTensor (StressTensor): Stress tensor object

        Returns:
            dict[str, npt.NDArray[ np.float64]]: dict with eigenvalues, eigenvectors, meanStress, deviatoricStress
        """
        eigenvalues, eigenvectors = np.linalg.eigh( stressTensor )

        # Sort from MOST NEGATIVE to LEAST NEGATIVE (most compressive to least)
        # Example: -600 < -450 < -200, so -600 is σ1 (most compressive)
        idx = np.argsort( eigenvalues )  # Ascending order (most negative first)
        eigenvaluesSorted = eigenvalues[ idx ]
        eigenVectorsSorted = eigenvectors[ :, idx ]

        return {
            'sigma1': eigenvaluesSorted[ 0 ],  # Most compressive (most negative)
            'sigma2': eigenvaluesSorted[ 1 ],  # Intermediate
            'sigma3': eigenvaluesSorted[ 2 ],  # Least compressive (least negative)
            'meanStress': np.mean( eigenvaluesSorted ),
            'deviatoricStress': eigenvaluesSorted[ 0 ] -
            eigenvaluesSorted[ 2 ],  # σ1 - σ3 (negative - more negative = positive or less negative)
            'direction1': eigenVectorsSorted[ :, 0 ],  # Direction of σ1
            'direction2': eigenVectorsSorted[ :, 1 ],  # Direction of σ2
            'direction3': eigenVectorsSorted[ :, 2 ]  # Direction of σ3
        }

    def _createVolumicContribMesh( self: Self,
                                   volumeData: vtkUnstructuredGrid,
                                   faultSurface: vtkUnstructuredGrid,
                                   cellsToTrack: set[ int ],
                                   mapping: dict[ int, dict[ str, list[ int ] ] ],
                                   computePrincipalStresses: bool = False,
                                   frictionAngle: float = 10,
                                   cohesion: float = 0 ) -> vtkUnstructuredGrid:
        """Create a mesh containing only contributing cells with principal stress data and compute analytical normal/shear stresses based on fault dip angle.

        Args:
            volumeData (vtkUnstructuredGrid): Volume mesh with stress data (rock_stress or averageStress)
            faultSurface (vtkUnstructuredGrid): Fault surface with dipAngle and strikeAngle per cell
            cellsToTrack (set[int]): Set of volume cell indices to include
            mapping (dict[int, list[ vtkUnstructuredGrid]]): Adjacency mapping {faultIdx: {'plus': [...], 'minus': [...]}}
            computePrincipalStresses (bool): Flag to compute principal stresses
            frictionAngle (float): Friction angle in degrees.
            cohesion (float): Cohesion in bar.

        Returns:
            vtkUnstructuredGrid: Mesh subset from contributing cells with new/updated arrays.
        """
        # ===================================================================
        # EXTRACT STRESS DATA FROM VOLUME
        # ===================================================================

        if not isAttributeInObject( volumeData, self.stressName, Piece.CELLS ):
            raise ValueError( f"No stress data '{self.stressName}' in volume dataset" )

        self.logger.info( f"  📊 Extracting stress from field: '{self.stressName}'" )

        # Extract effective stress and pressure
        pressure = getArrayInObject( volumeData, "pressure", Piece.CELLS ) / 1e5  # Convert to bar
        biot = getArrayInObject( volumeData, self.biotName, Piece.CELLS )

        stressEffective = StressTensor.buildFromArray(
            getArrayInObject( volumeData, self.stressName, Piece.CELLS ) / 1e5 )

        # Convert effective stress to total stress
        arrI = np.eye( 3 )[ None, :, : ]
        stressTotal = stressEffective - biot[ :, None, None ] * pressure[ :, None, None ] * arrI

        # ===================================================================
        # EXTRACT SUBSET OF CELLS
        # ===================================================================
        cellIndices = sorted( cellsToTrack )
        cellMask = np.zeros( volumeData.GetNumberOfCells(), dtype=bool )
        cellMask[ cellIndices ] = True

        subsetMesh = extractCellSelection( cellMask )

        # ===================================================================
        # REBUILD MAPPING: subsetIdx -> originalIdx
        # ===================================================================
        originalCenters = vtk_to_numpy( computeCellCenterCoordinates( volumeData ) )[ cellIndices ]
        subsetCenters = vtk_to_numpy( computeCellCenterCoordinates( subsetMesh ) )

        tree = cKDTree( originalCenters )

        subsetToOriginal = np.zeros( subsetMesh.GetNumberOfCells(), dtype=int )
        for subsetIdx in range( subsetMesh.GetNumberOfCells() ):
            dist, idx = tree.query( subsetCenters[ subsetIdx ] )
            if dist > 1e-6:
                self.logger.warning( f"        WARNING: Cell {subsetIdx} not matched (dist={dist})" )
            subsetToOriginal[ subsetIdx ] = cellIndices[ idx ]

        # ===================================================================
        # MAP VOLUME CELLS TO FAULT DIP/STRIKE ANGLES
        # ===================================================================
        self.logger.info( "     📐 Mapping volume cells to fault dip/strike angles..." )

        # Check if fault surface has required data
        if not faultSurface.GetCellData().HasArray( 'dipAngle' ):
            raise AttributeError( "        ⚠️ WARNING: 'dipAngle' not found in faultSurface\n"
                                  f"        Available fields: {list(faultSurface.cell_data.keys())}" )

        if not faultSurface.GetCellData().HasArray( 'strikeAngle' ):
            raise AttributeError( "        ⚠️ WARNING: 'strikeAngle' not found in faultSurface" )

        # Create mapping: volume_cell_id -> [dipAngles, strikeAngles]
        volumeToDip: dict[ int, list[ np.float64 ] ] = {}
        volumeToStrike: dict[ int, list[ np.float64 ] ] = {}

        for faultIdx, neighbors in mapping.items():
            # Get dip and strike angle from fault cell
            faultDip = getArrayInObject( faultSurface, 'dipAngle', Piece.CELLS )[ faultIdx ]

            # Strike is optional
            if isAttributeInObject( faultSurface, 'strikeAngle', Piece.CELLS ):
                faultStrike = getArrayInObject( faultSurface, 'strikeAngle', Piece.CELLS )[ faultIdx ]
            else:
                faultStrike = np.nan

            # Assign to all contributing volume cells (plus and minus)
            for volIdx in neighbors[ 'plus' ] + neighbors[ 'minus' ]:
                if volIdx not in volumeToDip:
                    volumeToDip[ volIdx ] = []
                    volumeToStrike[ volIdx ] = []
                volumeToDip[ volIdx ].append( faultDip )
                volumeToStrike[ volIdx ].append( faultStrike )

        # Average if a volume cell contributes to multiple fault cells
        volumeToDipAvg = { volIdx: np.mean( dips ) for volIdx, dips in volumeToDip.items() }
        volumeToStrikeAvg = { volIdx: np.mean( strikes ) for volIdx, strikes in volumeToStrike.items() }

        self.logger.info( f"        ✅ Mapped {len(volumeToDipAvg)} volume cells to fault angles" )

        # Statistics
        allDips = [ np.mean( dips ) for dips in volumeToDip.values() ]
        if len( allDips ) > 0:
            self.logger.info( f"        Dip angle range: [{np.min(allDips):.1f}, {np.max(allDips):.1f}]°" )

        # ===================================================================
        # COMPUTE PRINCIPAL STRESSES AND ANALYTICAL FAULT STRESSES
        # ===================================================================
        nCells = subsetMesh.GetNumberOfCells()

        sigma1Arr = np.zeros( nCells )
        sigma2Arr = np.zeros( nCells )
        sigma3Arr = np.zeros( nCells )
        meanStressArr = np.zeros( nCells )
        deviatoricStressArr = np.zeros( nCells )
        pressureArr = np.zeros( nCells )

        direction1Arr = np.zeros( ( nCells, 3 ) )
        direction2Arr = np.zeros( ( nCells, 3 ) )
        direction3Arr = np.zeros( ( nCells, 3 ) )

        # NEW: Analytical fault stresses
        sigmaNAnalyticalArr = np.zeros( nCells )
        tauAnalyticalArr = np.zeros( nCells )
        dipAngleArr = np.zeros( nCells )
        strikeAngleArr = np.zeros( nCells )
        deltaArr = np.zeros( nCells )

        sideArr = np.zeros( nCells, dtype=int )
        nFaultCellsArr = np.zeros( nCells, dtype=int )

        self.logger.info( "     🔢 Computing principal stresses and analytical projections..." )

        for subsetIdx in range( nCells ):
            origIdx = subsetToOriginal[ subsetIdx ]

            # ===============================================================
            # COMPUTE PRINCIPAL STRESSES
            # ===============================================================
            # Total stress = effective stress + pore pressure
            sigmaTotalCell = stressTotal[ origIdx ] + pressure[ origIdx ] * np.eye( 3 )
            principal = self.computePrincipalStresses( sigmaTotalCell )

            sigma1Arr[ subsetIdx ] = principal[ 'sigma1' ]
            sigma2Arr[ subsetIdx ] = principal[ 'sigma2' ]
            sigma3Arr[ subsetIdx ] = principal[ 'sigma3' ]
            meanStressArr[ subsetIdx ] = principal[ 'meanStress' ]
            deviatoricStressArr[ subsetIdx ] = principal[ 'deviatoricStress' ]
            pressureArr[ subsetIdx ] = pressure[ origIdx ]

            direction1Arr[ subsetIdx ] = principal[ 'direction1' ]
            direction2Arr[ subsetIdx ] = principal[ 'direction2' ]
            direction3Arr[ subsetIdx ] = principal[ 'direction3' ]

            # ===============================================================
            # COMPUTE ANALYTICAL FAULT STRESSES (Anderson formulas)
            # ===============================================================
            if origIdx in volumeToDipAvg:
                dipDeg = volumeToDipAvg[ origIdx ]
                dipAngleArr[ subsetIdx ] = dipDeg

                strikeDeg = volumeToStrikeAvg.get( origIdx, np.nan )
                strikeAngleArr[ subsetIdx ] = strikeDeg

                # δ = 90° - dip (angle from horizontal)
                deltaDeg = 90.0 - dipDeg
                deltaRad = np.radians( deltaDeg )
                deltaArr[ subsetIdx ] = deltaDeg

                # Extract principal stresses (compression negative)
                sigma1 = principal[ 'sigma1' ]  # Most compressive (most negative)
                sigma3 = principal[ 'sigma3' ]  # Least compressive (least negative)

                # Anderson formulas (1951)
                # σ_n = (σ1 + σ3)/2 - (σ1 - σ3)/2 * cos(2δ)
                # τ = |(σ1 - σ3)/2 * sin(2δ)|

                sigmaMean = ( sigma1 + sigma3 ) / 2.0
                sigmaDiff = ( sigma1 - sigma3 ) / 2.0

                sigmaNAnalytical = sigmaMean - sigmaDiff * np.cos( 2 * deltaRad )
                tauAnalytical = sigmaDiff * np.sin( 2 * deltaRad )

                sigmaNAnalyticalArr[ subsetIdx ] = sigmaNAnalytical
                tauAnalyticalArr[ subsetIdx ] = np.abs( tauAnalytical )
            else:
                # No fault association - set to NaN
                dipAngleArr[ subsetIdx ] = np.nan
                strikeAngleArr[ subsetIdx ] = np.nan
                deltaArr[ subsetIdx ] = np.nan
                sigmaNAnalyticalArr[ subsetIdx ] = np.nan
                tauAnalyticalArr[ subsetIdx ] = np.nan

            # ===============================================================
            # DETERMINE SIDE (plus/minus/both)
            # ===============================================================
            isPlus = False
            isMinus = False
            faultCellCount = 0

            for _faultIdx, neighbors in mapping.items():
                if origIdx in neighbors[ 'plus' ]:
                    isPlus = True
                    faultCellCount += 1
                if origIdx in neighbors[ 'minus' ]:
                    isMinus = True
                    faultCellCount += 1

            if isPlus and isMinus:
                sideArr[ subsetIdx ] = 3  # both
            elif isPlus:
                sideArr[ subsetIdx ] = 1  # plus
            elif isMinus:
                sideArr[ subsetIdx ] = 2  # minus
            else:
                sideArr[ subsetIdx ] = 0  # none (should not happen)

            nFaultCellsArr[ subsetIdx ] = faultCellCount

        # ===================================================================
        # ADD DATA TO MESH
        # ===================================================================
        for attributeName, attributeArray in zip( (
                'sigma1',
                'sigma2',
                'sigma3',
                'meanStress',
                'deviatoricStress',
                'pressure_bar',
                'sigma1Direction',
                'sigma2Direction',
                'sigma3Direction',
                'sigmaNAnalytical',
                'tauAnalytical',
                'dipAngle',
                'strikeAngle',
                'deltaAngle',
        ), ( sigma1Arr, sigma2Arr, sigma3Arr, meanStressArr, deviatoricStressArr, pressureArr, direction1Arr,
             direction2Arr, direction3Arr, sigmaNAnalyticalArr, tauAnalyticalArr, dipAngleArr, strikeAngleArr,
             deltaArr ) ):
            updateAttribute( subsetMesh, attributeArray, attributeName, piece=Piece.CELLS )

        # ===================================================================
        # COMPUTE SCU ANALYTICALLY (Mohr-Coulomb)
        # ===================================================================
        mu = np.tan( np.radians( frictionAngle ) )

        # τ_crit = C - σ_n * μ
        # Note: σ_n is negative (compression), so -σ_n * μ is positive
        tauCriticalArr: npt.NDArray[ np.float64 ] = cohesion - sigmaNAnalyticalArr * mu
        # SCU = τ / τ_crit
        SCUAnalyticalArr: npt.NDArray[ np.float64 ] = np.divide( tauAnalyticalArr,
                                                                 tauCriticalArr,
                                                                 out=np.zeros_like( tauAnalyticalArr ),
                                                                 where=tauCriticalArr != 0 )

        for attributeName, attributeArray in zip(
            ( 'tauCriticalAnalytical', 'SCUAnalytical', 'side', 'nFaultCells', 'originalCellIds' ),
            ( tauCriticalArr, SCUAnalyticalArr, sideArr, nFaultCellsArr, subsetToOriginal ) ):
            createAttribute( subsetMesh, attributeArray, attributeName, piece=Piece.CELLS )

        # ===================================================================
        # STATISTICS
        # ===================================================================
        validAnalytical = ~np.isnan( sigmaNAnalyticalArr )
        nValid = np.sum( validAnalytical )
        nCritical = np.sum( ( SCUAnalyticalArr >= 0.8 ) & ( SCUAnalyticalArr < 1.0 ) )
        nUnstable = np.sum( SCUAnalyticalArr >= 1.0 )

        if nValid > 0:
            self.logger.info(
                f"     📊 Analytical fault stresses computed for {nValid}/{nCells} cells"
                f"        σ_n range: [{np.nanmin(sigmaNAnalyticalArr):.1f}, {np.nanmax(sigmaNAnalyticalArr):.1f}] bar"
                f"        τ range: [{np.nanmin(tauAnalyticalArr):.1f}, {np.nanmax(tauAnalyticalArr):.1f}] bar"
                f"        Dip angle range: [{np.nanmin(dipAngleArr):.1f}, {np.nanmax(dipAngleArr):.1f}]°"
                f"        SCU range: [{np.nanmin(SCUAnalyticalArr[validAnalytical]):.2f}, {np.nanmax(SCUAnalyticalArr[validAnalytical]):.2f}]"
                f"        Critical cells (SCU≥0.8): {nCritical} ({nCritical/nValid*100:.1f}%)"
                f"        Unstable cells (SCU≥1.0): {nUnstable} ({nUnstable/nValid*100:.1f}%)" )
        else:
            self.logger.warning( "     ⚠️  No analytical stresses computed (no fault mapping)" )

        return subsetMesh

    def _savePrincipalStressVTU( self: Self, mesh: vtkUnstructuredGrid, time: float, timestep: int ) -> None:
        """Save principal stress mesh to VTU file.

        Parameters:
            mesh: PyVista mesh with principal stress data
            time: Simulation time
            timestep: Timestep index
        """
        # Create output directory
        self.vtuOutputDir.mkdir( parents=True, exist_ok=True )

        # Generate filename
        vtuFilename = f"principal_stresses_{timestep:05d}.vtu"
        vtuPath = self.vtuOutputDir / vtuFilename

        # Save mesh
        writeMesh( mesh=mesh, vtkOutput=VtkOutput( vtuPath ) )

        # Store metadata for PVD
        self.timestepInfo.append( {
            'time': time if time is not None else timestep,
            'timestep': timestep,
            'file': vtuFilename
        } )

        self.logger.info( f"     💾 Saved principal stresses: {vtuFilename}" )

    def savePVDCollection( self: Self, filename: str = "principal_stresses.pvd" ) -> None:
        """Create PVD file for time series visualization in ParaView.

        Args:
            filename: Name of PVD file.
                Defaults is "principal_stresses.pvd".
        """
        if len( self.timestepInfo ) == 0:
            self.logger.error( "⚠️  No timestep data to save in PVD" )
            return

        pvdPath = self.vtuOutputDir / filename

        self.logger.info( f"\n💾 Creating PVD collection: {pvdPath}"
                          f"   Timesteps: {len(self.timestepInfo)}" )

        # Create XML structure
        root = Element( 'VTKFile' )
        root.set( 'type', 'Collection' )
        root.set( 'version', '0.1' )
        root.set( 'byte_order', 'LittleEndian' )

        collection = SubElement( root, 'Collection' )

        for info in self.timestepInfo:
            dataset = SubElement( collection, 'DataSet' )
            dataset.set( 'timestep', str( info[ 'time' ] ) )
            dataset.set( 'group', '' )
            dataset.set( 'part', '0' )
            dataset.set( 'file', info[ 'file' ] )

        # Write to file
        tree = ElementTree( root )
        tree.write( str( pvdPath ), encoding='utf-8', xml_declaration=True )

        self.logger.info( "   ✅ PVD file created successfully"
                          f"   📂 Output directory: {self.vtuOutputDir}"
                          "\n   🎨 To visualize in ParaView:"
                          f"      1. Open: {pvdPath}"
                          "      2. Apply"
                          "      3. Color by: sigma1, sigma2, sigma3, meanStress, etc."
                          "      4. Use 'side' filter to show plus/minus/both" )

    def setStressName( self: Self, stressName: str ) -> None:
        """Set the stress attribute name.

        Args:
            stressName (str): Stress attribute name in the input mesh.
        """
        if stressName != "None":
            self.stressName = stressName

    def setBiotCoefficientName( self: Self, biotName: str ) -> None:
        """Set the stress attribute name.

        Args:
            biotName (str): Biot coefficient attribute name in the input mesh.
        """
        if biotName != "None":
            self.biotName = biotName
