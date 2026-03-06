# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
import logging
import numpy as np
from pathlib import Path
from typing_extensions import Self, Any
import numpy.typing as npt
from scipy.spatial import cKDTree

from vtkmodules.vtkCommonDataModel import vtkCellLocator, vtkMultiBlockDataSet, vtkUnstructuredGrid
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from geos.mesh.utils.arrayModifiers import ( createAttribute, updateAttribute )
from geos.mesh.utils.arrayHelpers import ( getArrayInObject, computeCellCenterCoordinates )
from geos.mesh.utils.multiblockModifiers import ( mergeBlocks )
from geos.mesh.utils.genericHelpers import ( extractCellSelection, extractSurface, computeNormals, computeCellVolumes )
from geos.utils.pieceEnum import ( Piece )

from geos.mesh.io.vtkIO import ( writeMesh, VtkOutput )
from geos.utils.Logger import ( Logger, getLogger )

loggerTitle: str = "Fault Geometry"


class FaultGeometry:
    """Handles fault surface extraction and normal computation with optimizations."""

    def __init__( self: Self,
                  mesh: vtkUnstructuredGrid,
                  faultValues: list[ int | float ],
                  faultAttribute: str,
                  volumeMesh: vtkUnstructuredGrid,
                  outputDir: str = ".",
                  logger: logging.Logger | None = None ) -> None:
        """Initialize fault geometry with pre-computed topology.

        Args:
            mesh (vtkUnstructuredGrid): Pre-simulation mesh
            faultValues (list[int]): Values of fault attribute to consider
            faultAttribute (str): Fault attribute name in the mesh
            volumeMesh (vtkUnstructuredGrid): Volumic mesh
            outputDir (str, optional): Output directory
                    Defaults is ".".
            logger (Union[Logger, None], optional): A logger to manage the output messages.
                    Defaults to None, an internal logger is used.

        """
        self.initialized = False
        self.mesh = mesh
        self.faultValues = faultValues
        self.faultAttribute = faultAttribute
        self.volumeMesh = volumeMesh

        self.faultSurface: vtkUnstructuredGrid
        self.surfaces: list[ vtkUnstructuredGrid ] = []
        self.adjacencyMapping: dict[ int, dict[ str, list[ int ] ] ]
        self.contributingCells: vtkUnstructuredGrid
        self.contributingCellsPlus: vtkUnstructuredGrid
        self.contributingCellsMinus: vtkUnstructuredGrid

        # NEW: Pre-computed geometric properties
        self.volumeCellVolumes: npt.NDArray[ np.float64 ]  # Volume of each cell
        self.volumeCenters: npt.NDArray[ np.float64 ]  # Center coordinates
        self.distanceToFault: npt.NDArray[ np.float64 ]  # Distance from each volume cell to nearest fault
        self.faultTree: cKDTree  # KDTree for fault surface

        # Config
        self.outputDir = Path( outputDir )
        self.outputDir.mkdir( parents=True, exist_ok=True )

        # Logger
        self.logger: Logger
        if logger is None:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( f"{logger.name}" )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def initialize( self: Self, processFaultsSeparately: bool = True, saveContributionCells: bool = True ) -> None:
        """One-time initialization: compute normals, adjacency topology, and geometric properties.

        Args:
            processFaultsSeparately (bool): Flag to process faults separately or not.
                    Defaults is True.
            saveContributionCells (bool): Save the contributing cells as VTU.
                    Defaults is True.
        """
        # Extract and compute normals
        self.faultSurface, self.surfaces = self._extractAndComputeNormals()

        # Pre-compute adjacency mapping
        self.logger.info( "🔍 Pre-computing volume-fault adjacency topology\n"
                          "   Method: Face-sharing (adaptive epsilon)\n" )

        self.adjacencyMapping = self._buildAdjacencyMappingFaceSharing(
            processFaultsSeparately=processFaultsSeparately )

        # Mark and optionally save contributing cells
        self._markContributingCells( saveContributionCells )

        # NEW: Pre-compute geometric properties
        self._precomputeGeometricProperties()

        nMapped = len( self.adjacencyMapping )
        nWithBoth = sum( 1 for m in self.adjacencyMapping.values()
                         if len( m[ 'plus' ] ) > 0 and len( m[ 'minus' ] ) > 0 )

        self.logger.info( "✅ Adjacency topology computed:\n"
                          f"   - {nMapped}/{self.faultSurface.GetNumberOfCells()} fault cells mapped\n"
                          f"   - {nWithBoth} cells have neighbors on both sides\n" )

        self.initialized = True

    def _markContributingCells( self: Self, saveContributionCells: bool = True ) -> None:
        """Mark volume cells that contribute to fault stress projection.

        Args:
            saveContributionCells (bool): Save contributing cells as VTU.
                Defaults is True.
        """
        self.logger.info( "📦 Marking contributing volume cells..." )

        nVolume = self.volumeMesh.GetNumberOfCells()

        # Collect contributing cells by side
        allPlus = set()
        allMinus = set()

        for _faultIdx, neighbors in self.adjacencyMapping.items():
            allPlus.update( neighbors[ 'plus' ] )
            allMinus.update( neighbors[ 'minus' ] )

        # Create classification array
        contributionSide = np.zeros( nVolume, dtype=int )

        for idx in allPlus:
            if 0 <= idx < nVolume:
                contributionSide[ idx ] += 1

        for idx in allMinus:
            if 0 <= idx < nVolume:
                contributionSide[ idx ] += 2

        # Add classification to volume mesh
        contribMask = contributionSide > 0
        contribMask = contribMask.astype( int )

        createAttribute( self.volumeMesh, contributionSide, "contributionSide", logger=self.logger )
        createAttribute( self.volumeMesh, contribMask, "contributionToFaults", logger=self.logger )

        # Extract subsets
        maskAll = np.where( contribMask )[ 0 ]
        maskPlus = np.where( ( contributionSide == 1 ) | ( contributionSide == 3 ) )[ 0 ]
        maskMinus = np.where( ( contributionSide == 2 ) | ( contributionSide == 3 ) )[ 0 ]

        self.contributingCells = extractCellSelection( self.volumeMesh, maskAll )
        self.contributingCellsPlus = extractCellSelection( self.volumeMesh, maskPlus )
        self.contributingCellsMinus = extractCellSelection( self.volumeMesh, maskMinus )

        # Statistics
        nContrib = np.sum( maskAll )
        nPlus = np.sum( contributionSide == 1 )
        nMinus = np.sum( contributionSide == 2 )
        nBoth = np.sum( contributionSide == 3 )
        pctContrib = nContrib / nVolume * 100

        self.logger.info( f"   ✅ Total contributing: {nContrib}/{nVolume} ({pctContrib:.1f}%)\n"
                          f"      Plus side only:  {nPlus} cells\n"
                          f"      Minus side only: {nMinus} cells\n"
                          f"      Both sides:      {nBoth} cells\n" )

        # Save to files if requested
        if saveContributionCells:
            self._saveContributingCells()

    def _saveContributingCells( self: Self ) -> None:
        """Save contributing volume cells to VTU files.

        Saves three files: all, plus side, minus side.
        """
        # Save all contributing cells
        filenameAll = self.outputDir / "contributing_cells_all.vtu"

        writeMesh( mesh=self.contributingCells, vtkOutput=VtkOutput( filenameAll ), canOverwrite=True )
        self.logger.info(
            f"   💾 All contributing cells saved: {filenameAll}\n"
            f"      ({self.contributingCells.GetNumberOfCells()} cells, {self.contributingCells.GetNumberOfPoints()} points)"
        )

        # Save plus side
        filenamePlus = self.outputDir / "contributingCellsPlus.vtu"
        self.logger.info( f"   💾 Plus side cells saved: {filenamePlus}" )
        writeMesh( mesh=self.contributingCellsPlus, vtkOutput=VtkOutput( filenamePlus ), canOverwrite=True )
        self.logger.info(
            f"      ({self.contributingCellsPlus.GetNumberOfCells()} cells, {self.contributingCellsPlus.GetNumberOfPoints()} points)"
        )

        # Save minus side
        filenameMinus = self.outputDir / "contributingCellsMinus.vtu"
        self.logger.info( f"   💾 Minus side cells saved: {filenameMinus}" )
        writeMesh( mesh=self.contributingCellsMinus, vtkOutput=VtkOutput( filenameMinus ), canOverwrite=True )
        self.logger.info(
            f"      ({self.contributingCellsMinus.GetNumberOfCells()} cells, {self.contributingCellsMinus.GetNumberOfPoints()} points)"
        )

    def getContributingCells( self: Self, side: str = 'all' ) -> vtkUnstructuredGrid:
        """Get the extracted contributing cells.

        Args:
            side (str): 'all', 'plus', or 'minus'

        Returns:
            vtkUnstructuredGrid: Contributing volume cells

        Raises:
            ValueError: Contributed cells not computed
            ValueError: Invalid requested side
        """
        if not self.initialized:
            raise ValueError( "Contributing cells not yet computed. Call initialize() first." )

        if side == 'all':
            return self.contributingCells
        elif side == 'plus':
            return self.contributingCellsPlus
        elif side == 'minus':
            return self.contributingCellsMinus
        else:
            raise ValueError( f"Invalid side '{side}'. Must be 'all', 'plus', or 'minus'." )

    def getGeometricProperties( self: Self ) -> dict[ str, Any ]:
        """Get pre-computed geometric properties.

        Properties include:
            - 'volumes': ndarray of cell volumes
            - 'centers': ndarray of cell centers (nCells, 3)
            - 'distances': ndarray of distances to nearest fault cell
            - 'faultTree': KDTree for fault surface

        Returns:
            dict[ str, Any ]: geometric properties
        """
        if not self.initialized:
            raise ValueError( "Geometric properties not computed. Call initialize() first." )

        return {
            'volumes': self.volumeCellVolumes,
            'centers': self.volumeCenters,
            'distances': self.distanceToFault,
            'faultTree': self.faultTree
        }

    def _precomputeGeometricProperties( self: Self ) -> None:
        """Pre-compute geometric properties of volume mesh for efficient stress projection.

        Computes:
            - Cell volumes (for volume-weighted averaging)
            - Cell centers (for distance calculations)
            - Distance from each volume cell to nearest fault cell
            - KDTree for fault surface
        """
        self.logger.info( "📐 Pre-computing geometric properties..." )

        nVolume = self.volumeMesh.GetNumberOfCells()

        # 1. Compute volume centers
        self.logger.info( "   Computing cell centers..." )
        self.volumeCenters = vtk_to_numpy( computeCellCenterCoordinates( self.volumeMesh ) )

        # 2. Compute cell volumes
        self.logger.info( "   Computing cell volumes..." )
        volumeWithSizes = computeCellVolumes( self.volumeMesh )
        self.volumeCellVolumes = getArrayInObject( volumeWithSizes, 'Volume', Piece.CELLS )

        self.logger.info( f"      Volume range: [{np.min(self.volumeCellVolumes):.1e}, \n"
                          f"{np.max(self.volumeCellVolumes):.1e}] m³" )

        # 3. Build KDTree for fault surface (for fast distance queries)
        self.logger.info( "   Building KDTree for fault surface..." )

        faultCenters = computeCellCenterCoordinates( self.faultSurface )
        self.faultTree = cKDTree( faultCenters )

        # 4. Compute distance from each volume cell to nearest fault cell
        self.logger.info( "   Computing distances to fault..." )
        self.distanceToFault = np.zeros( nVolume )

        # Vectorized query for all points at once (much faster)
        distances, _ = self.faultTree.query( self.volumeCenters )
        self.distanceToFault = distances

        self.logger.info( f"      Distance range: [{np.min(self.distanceToFault):.1f}, \n"
                          f"{np.max(self.distanceToFault):.1f}] m" )

        # 5. Add these properties to volume mesh for reference
        createAttribute( self.volumeMesh, self.volumeCellVolumes, 'cellVolume', Piece.CELLS, logger=self.logger )
        createAttribute( self.volumeMesh, self.distanceToFault, 'distanceToFault', Piece.CELLS, logger=self.logger )

        self.logger.info( "   ✅ Geometric properties computed and cached" )

    def _buildAdjacencyMappingFaceSharing( self: Self,
                                           processFaultsSeparately: bool = True
                                          ) -> dict[ int, dict[ str, list[ int ] ] ]:
        """Build adjacency for cells sharing faces with fault.

        Uses adaptive epsilon optimization.
        """
        faultIds = np.unique( getArrayInObject( self.faultSurface, self.faultAttribute, Piece.CELLS ) )
        nFaults = len( faultIds )
        self.logger.info( f"  📋 Processing {nFaults} separate faults: {faultIds}\n" )

        allMappings: dict[ int, dict[ str, list[ int ] ] ] = {}

        for faultId in faultIds:
            mask = getArrayInObject( self.faultSurface, self.faultAttribute, Piece.CELLS ) == faultId
            indices = np.where( mask )[ 0 ]
            singleFault = extractCellSelection( self.faultSurface, indices )

            self.logger.info( f"  🔧 Mapping Fault {faultId}..." )

            # Build face-sharing mapping with adaptive epsilon
            localMapping = self._findFaceSharingCells( singleFault )

            # Remap local indices to global fault indices
            for localIdx, neighbors in localMapping.items():
                globalIdx = indices[ localIdx ]
                allMappings[ globalIdx ] = neighbors

        return allMappings

    def _findFaceSharingCells( self: Self, faultSurface: vtkUnstructuredGrid ) -> dict[ int, dict[ str, list[ int ] ] ]:
        """Find volume cells that share a FACE with fault cells.

        Uses FindCell with adaptive epsilon to maximize cells with both neighbors

        Args:
            faultSurface (vtkUnstructuredGrid): Fault surface mesh

        Returns:
            dict[int, dict[str, list[int]]] : Mapping from the best epsilon found.
        """
        volCenters = vtk_to_numpy( computeCellCenterCoordinates( self.volumeMesh ) )
        faultNormals = vtk_to_numpy( faultSurface.GetCellData().GetNormals() )
        faultCenters = vtk_to_numpy( computeCellCenterCoordinates( faultSurface ) )

        # Determine base epsilon based on mesh size
        volBounds = self.volumeMesh.bounds
        typicalSize = np.mean( [
            volBounds[ 1 ] - volBounds[ 0 ], volBounds[ 3 ] - volBounds[ 2 ], volBounds[ 5 ] - volBounds[ 4 ]
        ] ) / 100.0

        # Build VTK cell locator (once)
        locator = vtkCellLocator()
        locator.SetDataSet( self.volumeMesh )
        locator.BuildLocator()

        # Try multiple epsilon values and keep the best
        epsilonCandidates = [
            typicalSize * 0.005, typicalSize * 0.01, typicalSize * 0.05, typicalSize * 0.1, typicalSize * 0.2,
            typicalSize * 0.5, typicalSize * 1.0
        ]

        self.logger.info( f"         Testing {len(epsilonCandidates)} epsilon values..." )

        bestEpsilon: float
        bestMapping: dict
        bestScore: float = -1
        bestStats: dict = {}

        for epsilon in epsilonCandidates:
            # Test this epsilon
            mapping, stats = self._testEpsilon( faultSurface, locator, epsilon, faultCenters, faultNormals, volCenters )

            # Score = percentage with both sides + penalty for no neighbors
            score = stats[ 'pctBoth' ] - 2.0 * stats[ 'pctNone' ]

            self.logger.info( f"            ε={epsilon:.3f}m → Both: {stats['pctBoth']:.1f}%, "
                              f"One: {stats['pctOne']:.1f}%, None: {stats['pctNone']:.1f}%, "
                              f"Avg: {stats['avgNeighbors']:.2f} (score: {score:.1f})" )

            if score > bestScore:
                bestScore = score
                bestEpsilon = epsilon
                bestMapping = mapping
                bestStats = stats

        self.logger.info( f"         ✅ Best epsilon: {bestEpsilon:.6f}m\n"
                          "         ✅ Face-sharing mapping completed:\n"
                          f"            Both sides: {bestStats['nBoth']} ({bestStats['pctBoth']:.1f}%)\n"
                          f"            One side: {bestStats['nOne']} ({bestStats['pctOne']:.1f}%)\n"
                          f"            No neighbors: {bestStats['nNone']} ({bestStats['pctNone']:.1f}%)\n"
                          f"            Average neighbors per fault cell: {bestStats['avgNeighbors']:.2f}" )

        return bestMapping

    def _testEpsilon(
        self: Self, faultSurface: vtkUnstructuredGrid, locator: vtkCellLocator, epsilon: float,
        faultCenters: npt.NDArray[ np.float64 ], faultNormals: npt.NDArray[ np.float64 ],
        volCenters: npt.NDArray[ np.float64 ]
    ) -> tuple[ dict[ int, dict[ str, list[ int ] ] ], dict[ str, float | int ] ]:
        """Test a specific epsilon value and return mapping and statistics.

        Statistics include:
            - 'nBoth': nFoundBoth,
            - 'nOne': nFoundOne,
            - 'nNone': nFoundNone,
            - 'pctBoth': nFoundBoth / nCells * 100,
            - 'pctOne': nFoundOne / nCells * 100,
            - 'pctNone': nFoundNone / nCells * 100,
            - 'avgNeighbors': avgNeighbors

        Args:
            faultSurface (vtkUnstructuredGrid): Fault mesh
            locator (vtkCellLocator): Cell locator
            epsilon (float): Epsilon to consider
            faultCenters (npt.NDArray[np.float64]): Fault mesh cells centers
            faultNormals: npt.NDArray[ np.float64 ]: Fault mesh normals
            volCenters (npt.NDArray[np.float64]): Volumic mesh cells centers

        Returns:
            tuple[ dict[int, dict[str, list[int]]], dict[  str, float | int ]]]: Mapping of plus and minus cells, statistics
        """
        mapping = {}
        nFoundBoth = 0
        nFoundOne = 0
        nFoundNone = 0
        totalNeighbors = 0

        for fid in range( faultSurface.GetNumberOfCells() ):
            fcenter = faultCenters[ fid ]
            fnormal = faultNormals[ fid ]

            plusCells = []
            minusCells = []

            # Search on PLUS side
            pointPlus = fcenter + epsilon * fnormal
            cellIdPlus = locator.FindCell( pointPlus )
            if cellIdPlus >= 0:
                plusCells.append( cellIdPlus )

            # Search on MINUS side
            pointMinus = fcenter - epsilon * fnormal
            cellIdMinus = locator.FindCell( pointMinus )
            if cellIdMinus >= 0:
                minusCells.append( cellIdMinus )

            mapping[ fid ] = { "plus": plusCells, "minus": minusCells }

            # Statistics
            nNeighbors = len( plusCells ) + len( minusCells )
            totalNeighbors += nNeighbors

            if len( plusCells ) > 0 and len( minusCells ) > 0:
                nFoundBoth += 1
            elif len( plusCells ) > 0 or len( minusCells ) > 0:
                nFoundOne += 1
            else:
                nFoundNone += 1

        nCells = faultSurface.GetNumberOfCells()
        if nCells <= 0:
            raise ValueError( "No cell in the fault surface." )

        avgNeighbors = totalNeighbors / nCells if nCells > 0 else 0

        stats = {
            'nBoth': nFoundBoth,
            'nOne': nFoundOne,
            'nNone': nFoundNone,
            'pctBoth': nFoundBoth / nCells * 100,
            'pctOne': nFoundOne / nCells * 100,
            'pctNone': nFoundNone / nCells * 100,
            'avgNeighbors': avgNeighbors
        }

        return mapping, stats

    def _extractAndComputeNormals( self: Self ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
        """Extract fault surfaces and compute oriented normals/tangents.

        Returns:
            tuple[vtkUnstructuredGrid, list[vtkUnstructuredGrid]]: Merged mesh containing all fault surfaces, list containing fault meshes.
        """
        surfaces = []
        mb = vtkMultiBlockDataSet()
        mb.SetNumberOfBlocks( len( self.faultValues ) )

        for i, faultId in enumerate( self.faultValues ):
            # Extract fault cells
            faultMask = np.where(
                getArrayInObject( self.mesh, self.faultAttribute, piece=Piece.CELLS ) == faultId )[ 0 ]
            faultCells = extractCellSelection( self.mesh, ids=faultMask )

            if faultCells.GetNumberOfCells() == 0:
                self.logger.warning( f"⚠️  No cells for fault {faultId}" )
                continue

            # Extract surface
            surf = extractSurface( faultCells )
            if surf.GetNumberOfCells() == 0:
                self.logger.warning( f"⚠️ No cells found during surface extraction of fault {faultId}" )
                continue

            # Compute normals
            surf = computeNormals( surf, pointNormals=True )

            # Orient normals consistently within the fault
            surf = self._orientNormals( surf )

            mb.SetBlock( i, surf )
            surfaces.append( surf )

        merged = mergeBlocks( mb, keepPartialAttributes=True )
        self.logger.info( f"✅ Normals computed for {merged.GetNumberOfCells()} fault cells" )

        return merged, surfaces

    def _orientNormals( self: Self, surf: vtkUnstructuredGrid, rotateNormals: bool = False ) -> vtkUnstructuredGrid:
        """Ensure normals point in consistent direction within the fault.

        Args:
            surf (vtkUnstructuredGrid): Fault mesh
            rotateNormals (bool, optional): Flag to flip the normals.
                    Defaults is False.

        Returns:
            vtkUnstructuredGrid: Fault mesh with normals and tangents attributes appended.
        """
        normals = vtk_to_numpy( surf.GetCellData().GetNormals() )
        meanNormal = np.mean( normals, axis=0 )
        meanNormal /= np.linalg.norm( meanNormal )

        nCells = len( normals )
        tangents1 = np.zeros( ( nCells, 3 ) )
        tangents2 = np.zeros( ( nCells, 3 ) )

        for i, normal in enumerate( normals ):

            # Flip if pointing opposite to mean
            if np.dot( normal, meanNormal ) < 0:
                normals[ i ] = -normal

            if rotateNormals:
                normals[ i ] = -normal

            # Compute orthogonal tangents
            normal = normals[ i ]
            if abs( normal[ 0 ] ) > 1e-6 or abs( normal[ 1 ] ) > 1e-6:
                t1 = np.array( [ -normal[ 1 ], normal[ 0 ], 0 ] )
            else:
                t1 = np.array( [ 0, -normal[ 2 ], normal[ 1 ] ] )

            t1 /= np.linalg.norm( t1 )
            t2 = np.cross( normal, t1 )
            t2 /= np.linalg.norm( t2 )

            tangents1[ i ] = t1
            tangents2[ i ] = t2

        surf.GetCellData().SetNormals( numpy_to_vtk( normals.ravel() ) )

        createAttribute( surf, tangents1, "Tangents1" )
        createAttribute( surf, tangents2, "Tangents2" )
        surf.GetCellData().SetActiveTangents( "Tangents1" )

        dipAngles, strikeAngles = self.computeDipStrikeFromCellBase( normals, tangents1, tangents2 )

        createAttribute( surf, dipAngles, "dipAngle" )
        createAttribute( surf, strikeAngles, "strikeAngle" )

        return surf

    def computeDipStrikeFromCellBase(
            self: Self, normals: npt.NDArray[ np.float64 ], tangent1: npt.NDArray[ np.float64 ],
            tangent2: npt.NDArray[ np.float64 ] ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:
        """Compute dip and strike angles from cell normal and tangent vectors.

        Assumptions:
            * Coordinate system: X = East, Y = North, Z = Up.
            * Vectors are provided per cell (shape: (nCells, 3)).
            * Input vectors are assumed to be orthonormal (n = t1 × t2).

        Args:
            normals (npt.NDArray[np.float64]): Normal vectors
            tangent1 (npt.NDArray[np.float64]): First tangent vector
            tangent2 (npt.NDArray[np.float64]): Second tangent vector

        Returns:
            tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]: Dip and strike.
        """
        # 1. Identify the strike vector (the most horizontal tangent)
        t1Horizontal = tangent1 - ( tangent1[ :, 2 ][ :, np.newaxis ] * np.array( [ 0, 0, 1 ] ) )
        t2Horizontal = tangent2 - ( tangent2[ :, 2 ][ :, np.newaxis ] * np.array( [ 0, 0, 1 ] ) )
        normT1Horizontal = np.linalg.norm( t1Horizontal, axis=1 )
        normT2Horizontal = np.linalg.norm( t2Horizontal, axis=1 )

        useT1 = normT1Horizontal > normT2Horizontal
        strikeVector = np.zeros_like( tangent1 )
        strikeVector[ useT1 ] = t1Horizontal[ useT1 ]
        strikeVector[ ~useT1 ] = t2Horizontal[ ~useT1 ]

        # Normalize
        strikeNorm = np.linalg.norm( strikeVector, axis=1 )

        strikeNorm[ strikeNorm == 0 ] = 1.0
        strikeVector = strikeVector / strikeNorm[ :, np.newaxis ]

        # 2. Compute the strike (azimuth clockwise from North)
        strikeRad = np.arctan2( strikeVector[ :, 0 ], strikeVector[ :, 1 ] )  # atan2(E, N)
        strikeDeg = np.degrees( strikeRad )
        strikeDeg = np.where( strikeDeg < 0, strikeDeg + 360, strikeDeg )

        # 3. Compute the dip
        normHorizontal = np.linalg.norm( normals[ :, :2 ], axis=1 )
        dipRad = np.arcsin( np.clip( normHorizontal, 0, 1 ) )  # clip to prevent rounding errors
        dipDeg = np.degrees( dipRad )

        return dipDeg, strikeDeg

    def diagnoseNormals( self: Self ) -> vtkUnstructuredGrid:
        """Diagnostic visualization to check normal quality.

        Shows orthogonality and orientation issues.

        Returns:
            vtkUnstructuredGrid: The input surface, possibly annotated with an
            additional field indicating orthogonality errors.
        """
        surface = self.faultSurface

        self.logger.info( "🔍 DIAGNOSTIC OF NORMALS" )
        self.logger.info( "=" * 60 )

        normals = surface.GetCellData().GetNormals()
        tangent1 = surface.GetCellData().GetTangents()
        tangent2 = surface.GetCellData().GetArray( "Tangents2" )

        nCells = len( normals )

        # Check orthogonality
        dotNormT1 = np.array( [ np.dot( normals[ i ], tangent1[ i ] ) for i in range( nCells ) ] )
        dotNormT2 = np.array( [ np.dot( normals[ i ], tangent2[ i ] ) for i in range( nCells ) ] )
        dotT1T2 = np.array( [ np.dot( tangent1[ i ], tangent2[ i ] ) for i in range( nCells ) ] )

        self.logger.info(
            "Orthogonality (should be close to 0):\n"
            f"  Normal · Tangent1  : max={np.max(np.abs(dotNormT1)):.2e}, mean={np.mean(np.abs(dotNormT1)):.2e}\n"
            f"  Normal · Tangent2  : max={np.max(np.abs(dotNormT2)):.2e}, mean={np.mean(np.abs(dotNormT2)):.2e}\n"
            f"  Tangent1 · Tangent2: max={np.max(np.abs(dotT1T2)):.2e}, mean={np.mean(np.abs(dotT1T2)):.2e}\n" )

        # Check vector norms (should be unit length)
        normN = np.linalg.norm( normals, axis=1 )
        normT1 = np.linalg.norm( tangent1, axis=1 )
        normT2 = np.linalg.norm( tangent2, axis=1 )

        self.logger.info( "Norms (should be close to 1):\n"
                          f"  Normals  : min={np.min(normN):.6f}, max={np.max(normN):.6f}\n"
                          f"  Tangent1 : min={np.min(normT1):.6f}, max={np.max(normT1):.6f}\n"
                          f"  Tangent2 : min={np.min(normT2):.6f}, max={np.max(normT2):.6f}\n" )

        # Check orientation consistency
        meanNormal = np.mean( normals, axis=0 )
        meanNormal = meanNormal / np.linalg.norm( meanNormal )

        dotsWithMean = np.array( [ np.dot( normals[ i ], meanNormal ) for i in range( nCells ) ] )
        nReversed = np.sum( dotsWithMean < 0 )

        self.logger.info( "Orientation consistency:\n"
                          f"  Mean normal: [{meanNormal[0]:.3f}, {meanNormal[1]:.3f}, {meanNormal[2]:.3f}]\n"
                          f"  Reversed normals: {nReversed}/{nCells} ({nReversed/nCells*100:.1f}%)\n" )

        # Visual consistency check
        if nReversed > nCells * 0.1:
            self.logger.warning( "  ⚠️  More than 10% of normals point in the opposite direction!" )
        else:
            self.logger.info( "  ✅ Orientation is consistent" )

        # Identify problematic cells (poor orthogonality)
        badOrtho = ( ( np.abs( dotNormT1 ) > 1e-3 ) | ( np.abs( dotNormT2 ) > 1e-3 ) | ( np.abs( dotT1T2 ) > 1e-3 ) )
        nBad = np.sum( badOrtho )

        if nBad > 0:
            self.logger.warning( f"\n⚠️  {nBad} cells with poor orthogonality (|dot| > 1e-3)" )
            updateAttribute( surface,
                             np.maximum.reduce( [ np.abs( dotNormT1 ),
                                                  np.abs( dotNormT2 ),
                                                  np.abs( dotT1T2 ) ] ), "orthogonalityError", Piece.CELLS )
        else:
            self.logger.info( "\n✅ All cells have good orthogonality" )

        self.logger.info( "=" * 60 )

        return surface
