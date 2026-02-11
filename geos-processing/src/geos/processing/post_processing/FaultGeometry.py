# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez
# ============================================================================
# FAULT GEOMETRY
# ============================================================================
import pyvista as pv
import numpy as np
from pathlib import Path
from typing_extensions import Self, Any
from vtkmodules.vtkCommonDataModel import vtkCellLocator
# from vtkmodules.vtkCommonDataModel import vtkIdList
import numpy.typing as npt
from scipy.spatial import cKDTree


__doc__="""


"""


class FaultGeometry:
    """Handles fault surface extraction and normal computation with optimizations."""

    # -------------------------------------------------------------------
    def __init__( self: Self, mesh: pv.DataSet, faultValues: list[ int ], faultAttribute: str,
                  volumeMesh: pv.DataSet, outputDir: str = "." ) -> None:
        """Initialize fault geometry with pre-computed topology.

        Args:
            mesh (pv.DataSet):
            faultValues (list[int]): Config.FAULT_VALUES
            faultAttribute (str): Config.FAULT_ATTRIBUTES
            volumeMesh (pv.DataSet): processor._merge_blocks(dataset)
        """
        self.mesh = mesh
        self.faultValues = faultValues
        self.faultAttribute = faultAttribute
        self.volumeMesh = volumeMesh

        # These will be computed once
        self.faultSurface = None
        self.surfaces = None
        self.adjacencyMapping = None
        self.contributingCells = None
        self.contributingCellsPlus = None
        self.contributingCellsMinus = None

        # NEW: Pre-computed geometric properties
        self.volumeCellVolumes = None  # Volume of each cell
        self.volumeCenters = None  # Center coordinates
        self.distanceToFault = None  # Distance from each volume cell to nearest fault
        self.faultTree = None  # KDTree for fault surface

        # Config
        # self.config = config
        self.outputDir = Path( outputDir )
        self.outputDir.mkdir( parents=True, exist_ok=True )

    # -------------------------------------------------------------------
    def initialize( self: Self,
                    scaleFactor: float = 50.0,
                    processFaultsSeparately: bool = True,
                    showPlot: bool = True,
                    zscale: float = 1.0,
                    showContributionViz: bool = True,
                    saveContributionCells:bool = True ) -> tuple[ pv.DataSet, dict[ int, pv.DataSet ] ]:
        """One-time initialization: compute normals, adjacency topology, and geometric properties."""
        # Extract and compute normals
        self.faultSurface, self.surfaces = self._extractAndComputeNormals( showPlot=showPlot,
                                                                           scaleFactor=scaleFactor,
                                                                           zScale=zscale )

        # Pre-compute adjacency mapping
        print( "\n🔍 Pre-computing volume-fault adjacency topology" )
        print( "   Method: Face-sharing (adaptive epsilon)" )

        self.adjacencyMapping = self._buildAdjacencyMappingFaceSharing(
            processFaultsSeparately=processFaultsSeparately )

        # Mark and optionally save contributing cells
        self._markContributingCells( saveContributionCells )

        # NEW: Pre-compute geometric properties
        self._precomputeGeometricProperties()

        nMapped = len( self.adjacencyMapping )
        nWithBoth = sum( 1 for m in self.adjacencyMapping.values()
                         if len( m[ 'plus' ] ) > 0 and len( m[ 'minus' ] ) > 0 )

        print( "\n✅ Adjacency topology computed:" )
        print( f"   - {nMapped}/{self.faultSurface.n_cells} fault cells mapped" )
        print( f"   - {nWithBoth} cells have neighbors on both sides" )

        # Visualize contributions if requested
        if showContributionViz:
            self._visualizeContributions()

        return self.faultSurface, self.adjacencyMapping

    # -------------------------------------------------------------------
    def _markContributingCells( self: Self, saveContributionCells: bool = True ) -> None:
        """Mark volume cells that contribute to fault stress projection."""
        print( "\n📦 Marking contributing volume cells..." )

        nVolume = self.volumeMesh.n_cells

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
        self.volumeMesh.cell_data[ "contributionSide" ] = contributionSide
        contribMask = contributionSide > 0
        self.volumeMesh.cell_data[ "contribution_to_faults" ] = contribMask.astype( int )

        # Extract subsets
        maskAll = contribMask
        maskPlus = ( contributionSide == 1 ) | ( contributionSide == 3 )
        maskMinus = ( contributionSide == 2 ) | ( contributionSide == 3 )

        self.contributingCells = self.volumeMesh.extract_cells( maskAll )
        self.contributingCellsPlus = self.volumeMesh.extract_cells( maskPlus )
        self.contributingCellsMinus = self.volumeMesh.extract_cells( maskMinus )

        # Statistics
        nContrib = np.sum( maskAll )
        nPlus = np.sum( contributionSide == 1 )
        nMinus = np.sum( contributionSide == 2 )
        nBoth = np.sum( contributionSide == 3 )
        pctContrib = nContrib / nVolume * 100

        print( f"   ✅ Total contributing: {nContrib}/{nVolume} ({pctContrib:.1f}%)" )
        print( f"      Plus side only:  {nPlus} cells" )
        print( f"      Minus side only: {nMinus} cells" )
        print( f"      Both sides:      {nBoth} cells" )

        # Save to files if requested
        if saveContributionCells:
            self._saveContributingCells()

    # -------------------------------------------------------------------
    def _saveContributingCells( self: Self ) -> None:
        """Save contributing volume cells to VTU files.

        Saves three files: all, plus side, minus side.
        """
        # Create output directory if it doesn't exist
        outputDir = self.outputDir

        # Save all contributing cells
        filenameAll = outputDir / "contributing_cells_all.vtu"
        self.contributingCells.save( str( filenameAll ) )
        print( f"\n   💾 All contributing cells saved: {filenameAll}" )
        print( f"      ({self.contributingCells.n_cells} cells, {self.contributingCells.n_points} points)" )

        # Save plus side
        outputDir / "contributingCellsPlus.vtu"
        # self.contributingCellsPlus.save(str(filenamePlus))
        # print(f"   💾 Plus side cells saved: {filenamePlus}")
        print( f"      ({self.contributingCellsPlus.n_cells} cells, {self.contributingCellsPlus.n_points} points)" )

        # Save minus side
        outputDir / "contributingCellsMinus.vtu"
        # self.contributingCellsMinus.save(str(filenameMinus))
        # print(f"   💾 Minus side cells saved: {filenameMinus}")
        print( f"      ({self.contributingCellsMinus.n_cells} cells, {self.contributingCellsMinus.n_points} points)" )

    # -------------------------------------------------------------------
    def getContributingCells( self: Self, side: str = 'all' ) -> pv.UnstructuredGrid:
        """Get the extracted contributing cells.

        Parameters:
            side: 'all', 'plus', or 'minus'

        Returns:
            pyvista.UnstructuredGrid: Contributing volume cells
        """
        if self.contributingCells is None:
            raise ValueError( "Contributing cells not yet computed. Call initialize() first." )

        if side == 'all':
            return self.contributingCells
        elif side == 'plus':
            return self.contributingCellsPlus
        elif side == 'minus':
            return self.contributingCellsMinus
        else:
            raise ValueError( f"Invalid side '{side}'. Must be 'all', 'plus', or 'minus'." )

    # -------------------------------------------------------------------
    def getGeometricProperties( self: Self ) -> dict[ str, Any ]:
        """Get pre-computed geometric properties.

        Returns:
        -------
        dict with keys:
            - 'volumes': ndarray of cell volumes
            - 'centers': ndarray of cell centers (nCells, 3)
            - 'distances': ndarray of distances to nearest fault cell
            - 'faultTree': KDTree for fault surface
        """
        if self.volumeCellVolumes is None:
            raise ValueError( "Geometric properties not computed. Call initialize() first." )

        return {
            'volumes': self.volumeCellVolumes,
            'centers': self.volumeCenters,
            'distances': self.distanceToFault,
            'faultTree': self.faultTree
        }

    # -------------------------------------------------------------------
    def _precomputeGeometricProperties( self: Self ) -> None:
        """Pre-compute geometric properties of volume mesh for efficient stress projection.

        Computes:
        - Cell volumes (for volume-weighted averaging)
        - Cell centers (for distance calculations)
        - Distance from each volume cell to nearest fault cell
        - KDTree for fault surface
        """
        print( "\n📐 Pre-computing geometric properties..." )

        nVolume = self.volumeMesh.n_cells

        # 1. Compute volume centers
        print( "   Computing cell centers..." )
        self.volumeCenters = self.volumeMesh.cell_centers().points

        # 2. Compute cell volumes
        print( "   Computing cell volumes..." )
        volumeWithSizes = self.volumeMesh.compute_cell_sizes( length=False, area=False, volume=True )
        self.volumeCellVolumes = volumeWithSizes.cell_data[ 'Volume' ]

        print( f"      Volume range: [{np.min(self.volumeCellVolumes):.1e}, "
               f"{np.max(self.volumeCellVolumes):.1e}] m³" )

        # 3. Build KDTree for fault surface (for fast distance queries)
        print( "   Building KDTree for fault surface..." )

        faultCenters = self.faultSurface.cell_centers().points
        self.faultTree = cKDTree( faultCenters )

        # 4. Compute distance from each volume cell to nearest fault cell
        print( "   Computing distances to fault..." )
        self.distanceToFault = np.zeros( nVolume )

        # Vectorized query for all points at once (much faster)
        distances, _ = self.faultTree.query( self.volumeCenters )
        self.distanceToFault = distances

        print( f"      Distance range: [{np.min(self.distanceToFault):.1f}, "
               f"{np.max(self.distanceToFault):.1f}] m" )

        # 5. Add these properties to volume mesh for reference
        self.volumeMesh.cell_data[ 'cellVolume' ] = self.volumeCellVolumes  # TODO FIX
        self.volumeMesh.cell_data[ 'distanceToFault' ] = self.distanceToFault

        print( "   ✅ Geometric properties computed and cached" )

    # -------------------------------------------------------------------
    def _buildAdjacencyMappingFaceSharing( self: Self,
                                           processFaultsSeparately: bool = True ) -> dict[ int, pv.DataSet ]:
        """Build adjacency for cells sharing faces with fault.

        Uses adaptive epsilon optimization.
        """
        faultIds = np.unique( self.faultSurface.cell_data[ self.faultAttribute ] )
        nFaults = len( faultIds )
        print( f"  📋 Processing {nFaults} separate faults: {faultIds}" )

        allMappings = {}

        for faultId in faultIds:
            mask = self.faultSurface.cell_data[ self.faultAttribute ] == faultId
            indices = np.where( mask )[ 0 ]
            singleFault = self.faultSurface.extract_cells( indices )

            print( f"  🔧 Mapping Fault {faultId}..." )

            # Build face-sharing mapping with adaptive epsilon
            localMapping = self._findFaceSharingCells( singleFault )

            # Remap local indices to global fault indices
            for localIdx, neighbors in localMapping.items():
                globalIdx = indices[ localIdx ]
                allMappings[ globalIdx ] = neighbors

        return allMappings

    # -------------------------------------------------------------------
    def _findFaceSharingCells( self: Self, faultSurface: pv.DataSet ) -> pv.DataSet:
        """Find volume cells that share a FACE with fault cells.

        Uses FindCell with adaptive epsilon to maximize cells with both neighbors
        """
        volMesh = self.volumeMesh
        volCenters = volMesh.cell_centers().points
        faultNormals = faultSurface.cell_data[ "Normals" ]
        faultCenters = faultSurface.cell_centers().points

        # Determine base epsilon based on mesh size
        volBounds = volMesh.bounds
        typicalSize = np.mean( [
            volBounds[ 1 ] - volBounds[ 0 ], volBounds[ 3 ] - volBounds[ 2 ], volBounds[ 5 ] - volBounds[ 4 ]
        ] ) / 100.0

        # Build VTK cell locator (once)
        locator = vtkCellLocator()
        locator.SetDataSet( volMesh )
        locator.BuildLocator()

        # Try multiple epsilon values and keep the best
        epsilonCandidates = [
            typicalSize * 0.005, typicalSize * 0.01, typicalSize * 0.05, typicalSize * 0.1, typicalSize * 0.2,
            typicalSize * 0.5, typicalSize * 1.0
        ]

        print( f"         Testing {len(epsilonCandidates)} epsilon values..." )

        bestEpsilon = None
        bestMapping = None
        bestScore = -1
        bestStats = None

        for epsilon in epsilonCandidates:
            # Test this epsilon
            mapping, stats = self._testEpsilon( faultSurface, locator, epsilon, faultCenters, faultNormals, volCenters )

            # Score = percentage with both sides + penalty for no neighbors
            score = stats[ 'pctBoth' ] - 2.0 * stats[ 'pctNone' ]

            print( f"            ε={epsilon:.3f}m → Both: {stats['pctBoth']:.1f}%, "
                   f"One: {stats['pctOne']:.1f}%, None: {stats['pctNone']:.1f}%, "
                   f"Avg: {stats['avgNeighbors']:.2f} (score: {score:.1f})" )

            if score > bestScore:
                bestScore = score
                bestEpsilon = epsilon
                bestMapping = mapping
                bestStats = stats

        print( f"\n         ✅ Best epsilon: {bestEpsilon:.6f}m" )
        print( "         ✅ Face-sharing mapping completed:" )
        print( f"            Both sides: {bestStats['nBoth']} ({bestStats['pctBoth']:.1f}%)" )
        print( f"            One side: {bestStats['nOne']} ({bestStats['pctOne']:.1f}%)" )
        print( f"            No neighbors: {bestStats['nNone']} ({bestStats['pctNone']:.1f}%)" )
        print( f"            Average neighbors per fault cell: {bestStats['avgNeighbors']:.2f}" )

        return bestMapping

    # -------------------------------------------------------------------
    def _testEpsilon( self: Self, faultSurface: pv.DataSet, locator: vtkCellLocator, epsilon: list[ float ],
                      faultCenters, faultNormals: npt.NDArray[ np.float64 ], volCenters ):
        """Test a specific epsilon value and return mapping + statistics.

        Statistics include:
            - 'nBoth': nFoundBoth,
            - 'nOne': nFoundOne,
            - 'nNone': nFoundNone,
            - 'pctBoth': nFoundBoth / nCells * 100,
            - 'pctOne': nFoundOne / nCells * 100,
            - 'pctNone': nFoundNone / nCells * 100,
            - 'avgNeighbors': avgNeighbors
        """
        mapping = {}
        nFoundBoth = 0
        nFoundOne = 0
        nFoundNone = 0
        totalNeighbors = 0

        for fid in range( faultSurface.n_cells ):
            fcenter = faultCenters[ fid ]
            fnormal = faultNormals[ fid ]

            plusCells = []
            minusCells = []

            # Search on PLUS side
            pointPlus = fcenter + epsilon * fnormal
            cellIdPlus = locator.FindCell( pointPlus )
            # print( cellIdPlus )
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

        nCells = faultSurface.n_cells
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

    # -------------------------------------------------------------------
    def _visualizeContributions( self: Self, zscale: float = 1.0, showPlots:bool = True ) -> None:
        """Unified visualization of volume contributions to fault surfaces.

        4-panel view combining full context, side classification, clip, and slice.
        """
        print( "\n📊 Creating contribution visualization..." )

        # Create plotter with 4 subplots
        plotter = pv.Plotter( shape=( 2, 2 ), window_size=[ 1800, 1400 ] )

        # ========== PLOT 1: Full context (top-left) ==========
        plotter.subplot( 0, 0 )
        plotter.add_text( "Full Context - Volume & Fault", font_size=14, position='upper_edge' )

        # All volume (transparent)
        plotter.add_mesh( self.mesh, color='lightgray', opacity=0.05, show_edges=False, label='Volume' )

        # Fault surface (red)
        plotter.add_mesh( self.faultSurface, color='red', opacity=1, show_edges=True, label='Fault Surface' )

        plotter.add_legend( loc="upper left" )
        plotter.add_axes()
        plotter.set_scale( zscale=zscale )

        # ========== PLOT 2: Contributing cells by side (top-right) ==========
        plotter.subplot( 0, 1 )
        plotter.add_text( "Contributing Cells", font_size=14, position='upper_edge' )

        if 'contributionSide' in self.volumeMesh.cell_data:
            # Plus side (blue)
            if self.contributingCellsPlus.n_cells > 0:
                plotter.add_mesh( self.contributingCellsPlus,
                                  color='dodgerblue',
                                  opacity=1.0,
                                  show_edges=True,
                                  label=f'Plus side ({self.contributingCellsPlus.n_cells} cells)' )

            # Minus side (orange)
            if self.contributingCellsMinus.n_cells > 0:
                plotter.add_mesh( self.contributingCellsMinus,
                                  color='darkorange',
                                  opacity=1.0,
                                  show_edges=True,
                                  label=f'Minus side ({self.contributingCellsMinus.n_cells} cells)' )

            # Fault surface for reference
            plotter.add_mesh( self.faultSurface, color='red', opacity=1.0, show_edges=True, label='Fault' )

        plotter.add_legend( loc='upper right' )
        plotter.add_axes()
        plotter.set_scale( zscale=zscale )

        # ========== PLOT 3: Clipped view (bottom-left) ==========
        plotter.subplot( 1, 0 )
        plotter.add_text( "Clipped View - Contributing Cells", font_size=14, position='upper_edge' )

        # Determine clip position (middle of fault)
        bounds = self.faultSurface.bounds
        clip_normal = [ 0, 0, -1 ]  # Clip along Z axis
        clip_origin = [ 0, 0, ( bounds[ 4 ] + bounds[ 5 ] ) / 2 ]

        # Clip and show contributing cells
        if self.contributingCells.n_cells > 0:
            plotter.add_mesh_clip_plane( self.contributingCells,
                                         normal=clip_normal,
                                         origin=clip_origin,
                                         color='blue',
                                         opacity=1,
                                         show_edges=True,
                                         label='Contributing (clipped)' )

        # Fault surface
        plotter.add_mesh( self.faultSurface, color='red', opacity=1.0, show_edges=True, label='Fault' )

        plotter.add_legend( loc='upper left' )
        plotter.add_axes()
        plotter.set_scale( zscale=zscale )

        # ========== PLOT 4: Slice view (bottom-right) ==========
        plotter.subplot( 1, 1 )

        # Determine slice position (middle of fault in Z)
        slice_position = ( bounds[ 4 ] + bounds[ 5 ] ) / 2
        plotter.add_text( f"Slice View at Z={slice_position:.1f}m", font_size=14, position='upper_edge' )

        # Create slice of volume
        sliceVol = self.volumeMesh.slice( normal='z', origin=[ 0, 0, slice_position ] )
        sliceFault = self.faultSurface.slice( normal='z', origin=[ 0, 0, slice_position ] )

        # Show contributing vs non-contributing in slice
        if 'contributionSide' in sliceVol.cell_data:
            # Non-contributing cells (gray)
            nonContribMask = sliceVol.cell_data[ 'contributionSide' ] == 0
            if np.sum( nonContribMask ) > 0:
                nonContrib = sliceVol.extract_cells( nonContribMask )
                plotter.add_mesh( nonContrib,
                                  color='lightgray',
                                  opacity=0.15,
                                  show_edges=True,
                                  line_width=1,
                                  label='Non-contributing' )

            # Plus side (blue)
            plusMask = (sliceVol.cell_data['contributionSide'] == 1) | \
                       (sliceVol.cell_data['contributionSide'] == 3)
            if np.sum( plusMask ) > 0:
                plusCells = sliceVol.extract_cells( plusMask )
                plotter.add_mesh( plusCells,
                                  color='dodgerblue',
                                  opacity=0.7,
                                  show_edges=True,
                                  line_width=2,
                                  label='Plus side' )

            # Minus side (orange)
            minusMask = (sliceVol.cell_data['contributionSide'] == 2) | \
                        (sliceVol.cell_data['contributionSide'] == 3)
            if np.sum( minusMask ) > 0:
                minusCells = sliceVol.extract_cells( minusMask )
                plotter.add_mesh( minusCells,
                                  color='darkorange',
                                  opacity=0.7,
                                  show_edges=True,
                                  line_width=2,
                                  label='Minus side' )

        # Fault slice (thick red line)
        if sliceFault.n_cells > 0:
            plotter.add_mesh( sliceFault, color='red', line_width=6, label='Fault', render_lines_as_tubes=True )

        plotter.add_legend( loc='upper right' )
        plotter.add_axes()
        plotter.set_scale( zscale=zscale )
        plotter.view_xy()

        # Link all views for synchronized rotation
        plotter.link_views()

        # Show or save
        if showPlots:
            plotter.show()
        else:
            # Save screenshot
            outputDir = self.outputDir
            screenshot_path = outputDir / "contribution_visualization.png"
            plotter.screenshot( str( screenshot_path ) )
            print( f"   💾 Visualization saved: {screenshot_path}" )
            plotter.close()

    # -------------------------------------------------------------------
    # NORMALS
    # -------------------------------------------------------------------
    def _extractAndComputeNormals( self: Self,
                                   showPlot: bool = False,
                                   scaleFactor: float = 50.0,
                                   zScale: float = 1.0 ) -> tuple[ pv.DataSet, list[ pv.DataSet ] ]:
        """Extract fault surfaces and compute oriented normals/tangents."""
        surfaces = []

        for faultId in self.faultValues:
            # Extract fault cells
            faultMask = self.mesh.cell_data[ self.faultAttribute ] == faultId
            faultCells = self.mesh.extract_cells( faultMask )

            if faultCells.n_cells == 0:
                print( f"⚠️  No cells for fault {faultId}" )
                continue

            # Extract surface
            surf = faultCells.extract_surface()
            if surf.n_cells == 0:
                continue

            # Compute normals
            surf.compute_normals( cell_normals=True, point_normals=True, inplace=True )

            # Orient normals consistently within the fault
            surf = self._orientNormals( surf )

            surfaces.append( surf )

        merged = pv.MultiBlock( surfaces ).combine()
        print( f"✅ Normals computed for {merged.n_cells} fault cells" )

        if showPlot:
            self.plotGeometry( merged, scaleFactor, zScale )

        return merged, surfaces

    # -------------------------------------------------------------------
    def _orientNormals( self: Self, surf: pv.PolyData, rotateNormals: bool = False ) -> pv.DataSet:
        """Ensure normals point in consistent direction within the fault."""
        normals = surf.cell_data[ 'Normals' ]
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

        surf.cell_data[ 'Normals' ] = normals
        surf.cell_data[ 'tangent1' ] = tangents1
        surf.cell_data[ 'tangent2' ] = tangents2

        dip_angles, strike_angles = self.computeDipStrikeFromCellBase( normals, tangents1, tangents2 )

        surf.cell_data[ 'dipAngle' ] = dip_angles
        surf.cell_data[ 'strikeAngle' ] = strike_angles

        return surf

    # -------------------------------------------------------------------
    def computeDipStrikeFromCellBase(
        self: Self, normals: npt.NDArray[ np.float64 ], tangent1: npt.NDArray[ np.float64 ],
        tangent2: npt.NDArray[ np.float64 ]
    ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:  # TODO translate docstring
        """Calcule les angles dip et strike à partir des vecteurs normaux et tangents des cellules.

        Hypothèses :
            - Système de coordonnées : X=Est, Y=Nord, Z=Haut.
            - Vecteurs donnés par cellule (shape: (nCells, 3)).
            - Les vecteurs d'entrée sont supposés orthonormés (n = t1 x t2).

        Retourne :
            dipDeg, strikeDeg (two arrays of shape (nCells,))
        """
        # 1. Identifier le vecteur strike (le plus horizontal)
        t1Horizontal = tangent1 - ( tangent1[ :, 2 ][ :, np.newaxis ] * np.array( [ 0, 0, 1 ] ) )
        t2Horizontal = tangent2 - ( tangent2[ :, 2 ][ :, np.newaxis ] * np.array( [ 0, 0, 1 ] ) )
        normT1Horizontal = np.linalg.norm( t1Horizontal, axis=1 )
        normT2Horizontal = np.linalg.norm( t2Horizontal, axis=1 )

        useT1 = normT1Horizontal > normT2Horizontal
        strikeVector = np.zeros_like( tangent1 )
        strikeVector[ useT1 ] = t1Horizontal[ useT1 ]
        strikeVector[ ~useT1 ] = t2Horizontal[ ~useT1 ]

        # Normaliser
        strikeNorm = np.linalg.norm( strikeVector, axis=1 )
        # Éviter la division par zéro (si la faille est parfaitement verticale, le strike est bien défini par l'autre vecteur)
        strikeNorm[ strikeNorm == 0 ] = 1.0
        strikeVector = strikeVector / strikeNorm[ :, np.newaxis ]

        # 2. Calculer le strike (azimut depuis le Nord, sens horaire)
        strikeRad = np.arctan2( strikeVector[ :, 0 ], strikeVector[ :, 1 ] )  # atan2(E, N)
        strikeDeg = np.degrees( strikeRad )
        strikeDeg = np.where( strikeDeg < 0, strikeDeg + 360, strikeDeg )

        # 3. Calculer le dip
        normHorizontal = np.linalg.norm( normals[ :, :2 ], axis=1 )
        dipRad = np.arcsin( np.clip( normHorizontal, 0, 1 ) )  # clip pour éviter les erreurs d'arrondi
        dipDeg = np.degrees( dipRad )

        return dipDeg, strikeDeg

    # -------------------------------------------------------------------
    def plotGeometry( self: Self, surface: pv.DataSet, scaleFactor: float, zScale: float ) -> None:
        """Visualize fault geometry with normals."""
        plotter = pv.Plotter()
        plotter.add_mesh( self.mesh, color='lightgray', opacity=0.1, label='Volume' )
        plotter.add_mesh( surface, color='darkgray', opacity=0.7, show_edges=True, label='Fault' )

        centers = surface.cell_centers()
        for name, color in [ ( 'Normals', 'red' ), ( 'tangent1', 'green' ), ( 'tangent2', 'blue' ) ]:
            arrows = centers.glyph( orient=name, scale=zScale, factor=scaleFactor )
            plotter.add_mesh( arrows, color=color, label=name )

        plotter.add_legend()
        plotter.add_axes()
        plotter.set_scale( zscale=zScale )
        plotter.show()

    # -------------------------------------------------------------------
    def diagnoseNormals( self: Self, scaleFactor: float = 50.0, zScale: float = 1.0 ) -> pv.DataSet:
        """Diagnostic visualization to check normal quality.

        Shows orthogonality and orientation issues.
        """
        surface = self.faultSurface

        print( "\n🔍 DIAGNOSTIC DES NORMALES" )
        print( "=" * 60 )

        normals = surface.cell_data[ 'Normals' ]
        tangent1 = surface.cell_data[ 'tangent1' ]
        tangent2 = surface.cell_data[ 'tangent2' ]

        nCells = len( normals )

        # Check orthogonality
        dotNormT1 = np.array( [ np.dot( normals[ i ], tangent1[ i ] ) for i in range( nCells ) ] )
        dotNormT2 = np.array( [ np.dot( normals[ i ], tangent2[ i ] ) for i in range( nCells ) ] )
        dotT1T2 = np.array( [ np.dot( tangent1[ i ], tangent2[ i ] ) for i in range( nCells ) ] )

        print( "Orthogonalité (doit être proche de 0):" )
        print( f"  Normal · Tangent1  : max={np.max(np.abs(dotNormT1)):.2e}, mean={np.mean(np.abs(dotNormT1)):.2e}" )
        print( f"  Normal · Tangent2  : max={np.max(np.abs(dotNormT2)):.2e}, mean={np.mean(np.abs(dotNormT2)):.2e}" )
        print( f"  Tangent1 · Tangent2: max={np.max(np.abs(dotT1T2)):.2e}, mean={np.mean(np.abs(dotT1T2)):.2e}" )

        # Check unit vectors
        normN = np.linalg.norm( normals, axis=1 )
        normT1 = np.linalg.norm( tangent1, axis=1 )
        normT2 = np.linalg.norm( tangent2, axis=1 )

        # Check unit vectors
        # normN = np.array( [ np.linalg.norm( normals[ i ] ) for i in range( nCells ) ] ) # TODO
        # normT1 = np.array( [ np.linalg.norm( tangent1[ i ] ) for i in range( nCells ) ] )
        # normT2 = np.array( [ np.linalg.norm( tangent2[ i ] ) for i in range( nCells ) ] )

        print( "\nNormes (doit être proche de 1):" )
        print( f"  Normals  : min={np.min(normN):.6f}, max={np.max(normN):.6f}" )
        print( f"  Tangent1 : min={np.min(normT1):.6f}, max={np.max(normT1):.6f}" )
        print( f"  Tangent2 : min={np.min(normT2):.6f}, max={np.max(normT2):.6f}" )

        # Check orientation consistency
        meanNormal = np.mean( normals, axis=0 )
        meanNormal = meanNormal / np.linalg.norm( meanNormal )

        dotsWithMean = np.array( [ np.dot( normals[ i ], meanNormal ) for i in range( nCells ) ] )
        nReversed = np.sum( dotsWithMean < 0 )

        print( "\nCohérence d'orientation:" )
        print( f"  Normale moyenne: [{meanNormal[0]:.3f}, {meanNormal[1]:.3f}, {meanNormal[2]:.3f}]" )
        print( f"  Normales inversées: {nReversed}/{nCells} ({nReversed/nCells*100:.1f}%)" )

        # Visual check
        if nReversed > nCells * 0.1:
            print( "  ⚠️  Plus de 10% des normales pointent dans la direction opposée!" )
        else:
            print( "  ✅ Orientation cohérente" )

        # Check for problematic cells
        badOrtho = ( np.abs( dotNormT1 ) > 1e-3 ) | ( np.abs( dotNormT2 ) > 1e-3 ) | ( np.abs( dotT1T2 ) > 1e-3 )
        nBad = np.sum( badOrtho )

        if nBad > 0:
            print( f"\n⚠️  {nBad} cellules avec orthogonalité douteuse (|dot| > 1e-3)" )
            surface.cell_data[ 'orthogonality_error' ] = np.maximum.reduce(
                [ np.abs( dotNormT1 ), np.abs( dotNormT2 ),
                  np.abs( dotT1T2 ) ] )
        else:
            print( "\n✅ Toutes les cellules ont une bonne orthogonalité" )

        print( "=" * 60 )

        # Visualization
        plotter = pv.Plotter( shape=( 1, 2 ) )

        # Plot 1: Surface with normals
        plotter.subplot( 0, 0 )
        plotter.add_mesh( surface, color='lightgray', show_edges=True, opacity=0.8 )

        centers = surface.cell_centers()
        arrowsNorm = centers.glyph( orient='Normals', scale=False, factor=scaleFactor )
        plotter.add_mesh( arrowsNorm, color='red', label='Normals' )

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text( "Normales (Rouge)", position='upper_edge' )
        plotter.set_scale( zscale=zScale )

        # Plot 2: All vectors
        plotter.subplot( 0, 1 )
        plotter.add_mesh( surface, color='lightgray', show_edges=True, opacity=0.5 )

        arrowsNorm = centers.glyph( orient='Normals', scale=False, factor=scaleFactor )
        arrowsT1 = centers.glyph( orient='tangent1', scale=False, factor=scaleFactor )
        arrowsT2 = centers.glyph( orient='tangent2', scale=False, factor=scaleFactor )

        plotter.add_mesh( arrowsNorm, color='red', label='Normal' )
        plotter.add_mesh( arrowsT1, color='green', label='Tangent1' )
        plotter.add_mesh( arrowsT2, color='blue', label='Tangent2' )

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text( "Système complet (R,G,B)", position='upper_edge' )
        plotter.set_scale( zscale=zScale )

        plotter.link_views()
        plotter.show()

        return surface
