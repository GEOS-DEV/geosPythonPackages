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
# STRESS TENSOR OPERATIONS
# ============================================================================
class StressTensor:
    """Utility class for stress tensor operations"""

    @staticmethod
    def build_from_array(arr):
        """Convert stress array to 3x3 tensor format"""
        n = arr.shape[0]
        tensors = np.zeros((n, 3, 3))

        if arr.shape[1] == 6:  # Voigt notation
            tensors[:, 0, 0] = arr[:, 0]  # Sxx
            tensors[:, 1, 1] = arr[:, 1]  # Syy
            tensors[:, 2, 2] = arr[:, 2]  # Szz
            tensors[:, 1, 2] = tensors[:, 2, 1] = arr[:, 3]  # Syz
            tensors[:, 0, 2] = tensors[:, 2, 0] = arr[:, 4]  # Sxz
            tensors[:, 0, 1] = tensors[:, 1, 0] = arr[:, 5]  # Sxy
        elif arr.shape[1] == 9:
            tensors = arr.reshape((-1, 3, 3))
        else:
            raise ValueError(f"Unsupported stress shape: {arr.shape}")

        return tensors

    @staticmethod
    def rotate_to_fault_frame(stress_tensor, normal, tangent1, tangent2):
        """Rotate stress tensor to fault local coordinate system"""
        # Verify orthonormality
        assert np.abs(np.linalg.norm(tangent1) - 1.0) < 1e-10
        assert np.abs(np.linalg.norm(tangent2) - 1.0) < 1e-10
        assert np.abs(np.dot(normal, tangent1)) < 1e-10
        assert np.abs(np.dot(normal, tangent2)) < 1e-10

        # Rotation matrix: columns = local directions (n, t1, t2)
        R = np.column_stack((normal, tangent1, tangent2))

        # Rotate tensor
        stress_local = R.T @ stress_tensor @ R

        # Traction on fault plane (normal = [1,0,0] in local frame)  # TODO is it aways that way ?
        traction_local = stress_local @ np.array([1.0, 0.0, 0.0])

        return {
            'stress_local': stress_local,
            'normal_stress': traction_local[0],
            'shear_stress': np.sqrt(traction_local[1]**2 + traction_local[2]**2),
            'shear_strike': traction_local[1],
            'shear_dip': traction_local[2]
        }

# ============================================================================
# FAULT GEOMETRY
# ============================================================================
class FaultGeometry:

    """Handles fault surface extraction and normal computation with optimizations"""

    # -------------------------------------------------------------------
    def __init__(self, config, mesh, fault_values, fault_attribute, volume_mesh):
        """
        Initialize fault geometry with pre-computed topology.

        Args:
            config (Config):
            mesh (): pv.read(path / config.GRID_FILE) -> "mesh_faulted_reservoir_60_mod.vtu"
            fault_values (list[int]): Config.FAULT_VALUES
            fault_attribute (str): Config.FAULT_ATTRIBUTES
            volume_mesh (): processor._merge_blocks(dataset)
        """
        self.mesh = mesh
        self.fault_values = fault_values
        self.fault_attribute = fault_attribute
        self.volume_mesh = volume_mesh

        # These will be computed once
        self.fault_surface = None
        self.surfaces = None
        self.adjacency_mapping = None
        self.contributing_cells = None
        self.contributing_cells_plus = None
        self.contributing_cells_minus = None

        # NEW: Pre-computed geometric properties
        self.volume_cell_volumes = None  # Volume of each cell
        self.volume_centers = None       # Center coordinates
        self.distance_to_fault = None    # Distance from each volume cell to nearest fault
        self.fault_tree = None           # KDTree for fault surface

        # Config
        self.config = config

    # -------------------------------------------------------------------
    def initialize(self, scale_factor=50.0, process_faults_separately=True):
        """
        One-time initialization: compute normals, adjacency topology, and geometric properties
        """

        # Extract and compute normals
        self.fault_surface, self.surfaces = self._extract_and_compute_normals(
            show_plot=self.config.SHOW_NORMAL_PLOTS,
            scale_factor=scale_factor,
            z_scale=self.config.Z_SCALE)

        # Pre-compute adjacency mapping
        print("\n🔍 Pre-computing volume-fault adjacency topology")
        print("   Method: Face-sharing (adaptive epsilon)")

        self.adjacency_mapping = self._build_adjacency_mapping_face_sharing(
            process_faults_separately=process_faults_separately)

        # Mark and optionally save contributing cells
        self._mark_contributing_cells()

        # NEW: Pre-compute geometric properties
        self._precompute_geometric_properties()

        n_mapped = len(self.adjacency_mapping)
        n_with_both = sum(1 for m in self.adjacency_mapping.values()
                         if len(m['plus']) > 0 and len(m['minus']) > 0)

        print("\n✅ Adjacency topology computed:")
        print(f"   - {n_mapped}/{self.fault_surface.n_cells} fault cells mapped")
        print(f"   - {n_with_both} cells have neighbors on both sides")

        # Visualize contributions if requested
        if self.config.SHOW_CONTRIBUTION_VIZ:
            self._visualize_contributions()

        return self.fault_surface, self.adjacency_mapping

    # -------------------------------------------------------------------
    def _mark_contributing_cells(self):
        """
        Mark volume cells that contribute to fault stress projection
        """
        print("\n📦 Marking contributing volume cells...")

        n_volume = self.volume_mesh.n_cells

        # Collect contributing cells by side
        all_plus = set()
        all_minus = set()

        for fault_idx, neighbors in self.adjacency_mapping.items():
            all_plus.update(neighbors['plus'])
            all_minus.update(neighbors['minus'])

        # Create classification array
        contribution_side = np.zeros(n_volume, dtype=int)

        for idx in all_plus:
            if 0 <= idx < n_volume:
                contribution_side[idx] += 1

        for idx in all_minus:
            if 0 <= idx < n_volume:
                contribution_side[idx] += 2

        # Add classification to volume mesh
        self.volume_mesh.cell_data["contribution_side"] = contribution_side
        contrib_mask = contribution_side > 0
        self.volume_mesh.cell_data["contribution_to_faults"] = contrib_mask.astype(int)

        # Extract subsets
        mask_all = contrib_mask
        mask_plus = (contribution_side == 1) | (contribution_side == 3)
        mask_minus = (contribution_side == 2) | (contribution_side == 3)

        self.contributing_cells = self.volume_mesh.extract_cells(mask_all)
        self.contributing_cells_plus = self.volume_mesh.extract_cells(mask_plus)
        self.contributing_cells_minus = self.volume_mesh.extract_cells(mask_minus)

        # Statistics
        n_contrib = np.sum(mask_all)
        n_plus = np.sum(contribution_side == 1)
        n_minus = np.sum(contribution_side == 2)
        n_both = np.sum(contribution_side == 3)
        pct_contrib = n_contrib / n_volume * 100

        print(f"   ✅ Total contributing: {n_contrib}/{n_volume} ({pct_contrib:.1f}%)")
        print(f"      Plus side only:  {n_plus} cells")
        print(f"      Minus side only: {n_minus} cells")
        print(f"      Both sides:      {n_both} cells")

        # Save to files if requested
        if self.config.SAVE_CONTRIBUTION_CELLS:
            self._save_contributing_cells()

    # -------------------------------------------------------------------
    def _save_contributing_cells(self):
        """
        Save contributing volume cells to VTU files
        Saves three files: all, plus side, minus side
        """
        from pathlib import Path

        # Create output directory if it doesn't exist
        output_dir = Path(self.config.OUTPUT_DIR) if hasattr(self.config, 'OUTPUT_DIR') else Path('.')
        output_dir.mkdir(parents=True, exist_ok=True)

        # Save all contributing cells
        filename_all = output_dir / "contributing_cells_all.vtu"
        self.contributing_cells.save(str(filename_all))
        print(f"\n   💾 All contributing cells saved: {filename_all}")
        print(f"      ({self.contributing_cells.n_cells} cells, {self.contributing_cells.n_points} points)")

        # Save plus side
        filename_plus = output_dir / "contributing_cells_plus.vtu"
        # self.contributing_cells_plus.save(str(filename_plus))
        # print(f"   💾 Plus side cells saved: {filename_plus}")
        print(f"      ({self.contributing_cells_plus.n_cells} cells, {self.contributing_cells_plus.n_points} points)")

        # Save minus side
        filename_minus = output_dir / "contributing_cells_minus.vtu"
        # self.contributing_cells_minus.save(str(filename_minus))
        # print(f"   💾 Minus side cells saved: {filename_minus}")
        print(f"      ({self.contributing_cells_minus.n_cells} cells, {self.contributing_cells_minus.n_points} points)")

    # -------------------------------------------------------------------
    def get_contributing_cells(self, side='all'):
        """
        Get the extracted contributing cells

        Parameters:
            side: 'all', 'plus', or 'minus'

        Returns:
            pyvista.UnstructuredGrid: Contributing volume cells
        """
        if self.contributing_cells is None:
            raise ValueError("Contributing cells not yet computed. Call initialize() first.")

        if side == 'all':
            return self.contributing_cells
        elif side == 'plus':
            return self.contributing_cells_plus
        elif side == 'minus':
            return self.contributing_cells_minus
        else:
            raise ValueError(f"Invalid side '{side}'. Must be 'all', 'plus', or 'minus'.")

    # -------------------------------------------------------------------
    def get_geometric_properties(self):
        """
        Get pre-computed geometric properties

        Returns
        -------
        dict with keys:
            - 'volumes': ndarray of cell volumes
            - 'centers': ndarray of cell centers (n_cells, 3)
            - 'distances': ndarray of distances to nearest fault cell
            - 'fault_tree': KDTree for fault surface
        """
        if self.volume_cell_volumes is None:
            raise ValueError("Geometric properties not computed. Call initialize() first.")

        return {
            'volumes': self.volume_cell_volumes,
            'centers': self.volume_centers,
            'distances': self.distance_to_fault,
            'fault_tree': self.fault_tree
        }

    # -------------------------------------------------------------------
    def _precompute_geometric_properties(self):
        """
        Pre-compute geometric properties of volume mesh for efficient stress projection

        Computes:
        - Cell volumes (for volume-weighted averaging)
        - Cell centers (for distance calculations)
        - Distance from each volume cell to nearest fault cell
        - KDTree for fault surface
        """
        print("\n📐 Pre-computing geometric properties...")

        n_volume = self.volume_mesh.n_cells

        # 1. Compute volume centers
        print("   Computing cell centers...")
        self.volume_centers = self.volume_mesh.cell_centers().points

        # 2. Compute cell volumes
        print("   Computing cell volumes...")
        volume_with_sizes = self.volume_mesh.compute_cell_sizes(
            length=False, area=False, volume=True
        )
        self.volume_cell_volumes = volume_with_sizes.cell_data['Volume']

        print(f"      Volume range: [{np.min(self.volume_cell_volumes):.1e}, "
              f"{np.max(self.volume_cell_volumes):.1e}] m³")

        # 3. Build KDTree for fault surface (for fast distance queries)
        print("   Building KDTree for fault surface...")
        from scipy.spatial import cKDTree

        fault_centers = self.fault_surface.cell_centers().points
        self.fault_tree = cKDTree(fault_centers)

        # 4. Compute distance from each volume cell to nearest fault cell
        print("   Computing distances to fault...")
        self.distance_to_fault = np.zeros(n_volume)

        # Vectorized query for all points at once (much faster)
        distances, _ = self.fault_tree.query(self.volume_centers)
        self.distance_to_fault = distances

        print(f"      Distance range: [{np.min(self.distance_to_fault):.1f}, "
              f"{np.max(self.distance_to_fault):.1f}] m")

        # 5. Add these properties to volume mesh for reference
        self.volume_mesh.cell_data['cell_volume'] = self.volume_cell_volumes
        self.volume_mesh.cell_data['distance_to_fault'] = self.distance_to_fault

        print("   ✅ Geometric properties computed and cached")

    # -------------------------------------------------------------------
    def _build_adjacency_mapping_face_sharing(self, process_faults_separately=True):
        """
        Build adjacency for cells sharing faces with fault
        Uses adaptive epsilon optimization
        """

        fault_ids = np.unique(self.fault_surface.cell_data[self.fault_attribute])
        n_faults = len(fault_ids)
        print(f"  📋 Processing {n_faults} separate faults: {fault_ids}")

        all_mappings = {}

        for fault_id in fault_ids:
            mask = self.fault_surface.cell_data[self.fault_attribute] == fault_id
            indices = np.where(mask)[0]
            single_fault = self.fault_surface.extract_cells(indices)

            print(f"  🔧 Mapping Fault {fault_id}...")

            # Build face-sharing mapping with adaptive epsilon
            local_mapping = self._find_face_sharing_cells(single_fault)

            # Remap local indices to global fault indices
            for local_idx, neighbors in local_mapping.items():
                global_idx = indices[local_idx]
                all_mappings[global_idx] = neighbors

        return all_mappings

    # -------------------------------------------------------------------
    def _find_face_sharing_cells(self, fault_surface):
        """
        Find volume cells that share a FACE with fault cells

        Uses FindCell with adaptive epsilon to maximize cells with both neighbors
        """
        vol_mesh = self.volume_mesh
        vol_centers = vol_mesh.cell_centers().points
        fault_normals = fault_surface.cell_data["Normals"]
        fault_centers = fault_surface.cell_centers().points

        # Determine base epsilon based on mesh size
        vol_bounds = vol_mesh.bounds
        typical_size = np.mean([
            vol_bounds[1] - vol_bounds[0],
            vol_bounds[3] - vol_bounds[2],
            vol_bounds[5] - vol_bounds[4]
        ]) / 100.0

        # Build VTK cell locator (once)
        from vtkmodules.vtkCommonDataModel import vtkCellLocator

        locator = vtkCellLocator()
        locator.SetDataSet(vol_mesh)
        locator.BuildLocator()

        # Try multiple epsilon values and keep the best
        epsilon_candidates = [
            typical_size * 0.005,
            typical_size * 0.01,
            typical_size * 0.05,
            typical_size * 0.1,
            typical_size * 0.2,
            typical_size * 0.5,
            typical_size * 1.0
        ]

        print(f"         Testing {len(epsilon_candidates)} epsilon values...")

        best_epsilon = None
        best_mapping = None
        best_score = -1
        best_stats = None

        for epsilon in epsilon_candidates:
            # Test this epsilon
            mapping, stats = self._test_epsilon(
                fault_surface, locator, epsilon,
                fault_centers, fault_normals, vol_centers
            )

            # Score = percentage with both sides + penalty for no neighbors
            score = stats['pct_both'] - 2.0 * stats['pct_none']

            print(f"            ε={epsilon:.3f}m → Both: {stats['pct_both']:.1f}%, "
                  f"One: {stats['pct_one']:.1f}%, None: {stats['pct_none']:.1f}%, "
                  f"Avg: {stats['avg_neighbors']:.2f} (score: {score:.1f})")

            if score > best_score:
                best_score = score
                best_epsilon = epsilon
                best_mapping = mapping
                best_stats = stats

        print(f"\n         ✅ Best epsilon: {best_epsilon:.6f}m")
        print(f"         ✅ Face-sharing mapping completed:")
        print(f"            Both sides: {best_stats['n_both']} ({best_stats['pct_both']:.1f}%)")
        print(f"            One side: {best_stats['n_one']} ({best_stats['pct_one']:.1f}%)")
        print(f"            No neighbors: {best_stats['n_none']} ({best_stats['pct_none']:.1f}%)")
        print(f"            Average neighbors per fault cell: {best_stats['avg_neighbors']:.2f}")

        return best_mapping

    # -------------------------------------------------------------------
    def _test_epsilon(self, fault_surface, locator, epsilon,
                      fault_centers, fault_normals, vol_centers):
        """
        Test a specific epsilon value and return mapping + statistics
        """
        mapping = {}
        n_found_both = 0
        n_found_one = 0
        n_found_none = 0
        total_neighbors = 0

        for fid in range(fault_surface.n_cells):
            fcenter = fault_centers[fid]
            fnormal = fault_normals[fid]

            plus_cells = []
            minus_cells = []

            # Search on PLUS side
            point_plus = fcenter + epsilon * fnormal
            cell_id_plus = locator.FindCell(point_plus)
            if cell_id_plus >= 0:
                plus_cells.append(cell_id_plus)

            # Search on MINUS side
            point_minus = fcenter - epsilon * fnormal
            cell_id_minus = locator.FindCell(point_minus)
            if cell_id_minus >= 0:
                minus_cells.append(cell_id_minus)

            mapping[fid] = {"plus": plus_cells, "minus": minus_cells}

            # Statistics
            n_neighbors = len(plus_cells) + len(minus_cells)
            total_neighbors += n_neighbors

            if len(plus_cells) > 0 and len(minus_cells) > 0:
                n_found_both += 1
            elif len(plus_cells) > 0 or len(minus_cells) > 0:
                n_found_one += 1
            else:
                n_found_none += 1

        n_cells = fault_surface.n_cells
        avg_neighbors = total_neighbors / n_cells if n_cells > 0 else 0

        stats = {
            'n_both': n_found_both,
            'n_one': n_found_one,
            'n_none': n_found_none,
            'pct_both': n_found_both / n_cells * 100,
            'pct_one': n_found_one / n_cells * 100,
            'pct_none': n_found_none / n_cells * 100,
            'avg_neighbors': avg_neighbors
        }

        return mapping, stats

    # -------------------------------------------------------------------
    def _visualize_contributions(self):
        """
        Unified visualization of volume contributions to fault surfaces
        4-panel view combining full context, side classification, clip, and slice
        """
        import pyvista as pv

        print("\n📊 Creating contribution visualization...")

        # Create plotter with 4 subplots
        plotter = pv.Plotter(shape=(2, 2), window_size=[1800, 1400])

        # ========== PLOT 1: Full context (top-left) ==========
        plotter.subplot(0, 0)
        plotter.add_text("Full Context - Volume & Fault", font_size=14, position='upper_edge')

        # All volume (transparent)
        plotter.add_mesh(self.mesh, color='lightgray', opacity=0.05,
                        show_edges=False, label='Volume')

        # Fault surface (red)
        plotter.add_mesh(self.fault_surface, color='red', opacity=1,
                        show_edges=True, label='Fault Surface')

        plotter.add_legend(loc="upper left")
        plotter.add_axes()
        plotter.set_scale(zscale=self.config.Z_SCALE)

        # ========== PLOT 2: Contributing cells by side (top-right) ==========
        plotter.subplot(0, 1)
        plotter.add_text("Contributing Cells",
                        font_size=14, position='upper_edge')

        if 'contribution_side' in self.volume_mesh.cell_data:
            # Plus side (blue)
            if self.contributing_cells_plus.n_cells > 0:
                plotter.add_mesh(self.contributing_cells_plus, color='dodgerblue',
                                opacity=1.0, show_edges=True,
                                label=f'Plus side ({self.contributing_cells_plus.n_cells} cells)')

            # Minus side (orange)
            if self.contributing_cells_minus.n_cells > 0:
                plotter.add_mesh(self.contributing_cells_minus, color='darkorange',
                                opacity=1.0, show_edges=True,
                                label=f'Minus side ({self.contributing_cells_minus.n_cells} cells)')

            # Fault surface for reference
            plotter.add_mesh(self.fault_surface, color='red', opacity=1.0,
                            show_edges=True, label='Fault')

        plotter.add_legend(loc='upper right')
        plotter.add_axes()
        plotter.set_scale(zscale=self.config.Z_SCALE)

        # ========== PLOT 3: Clipped view (bottom-left) ==========
        plotter.subplot(1, 0)
        plotter.add_text("Clipped View - Contributing Cells",
                        font_size=14, position='upper_edge')

        # Determine clip position (middle of fault)
        bounds = self.fault_surface.bounds
        clip_normal = [0, 0, -1]  # Clip along Z axis
        clip_origin = [0,0, (bounds[4] + bounds[5]) / 2]

        # Clip and show contributing cells
        if self.contributing_cells.n_cells > 0:
            plotter.add_mesh_clip_plane(
                self.contributing_cells,
                normal=clip_normal,
                origin=clip_origin,
                color='blue',
                opacity=1,
                show_edges=True,
                label='Contributing (clipped)'
            )

        # Fault surface
        plotter.add_mesh(self.fault_surface, color='red', opacity=1.0,
                        show_edges=True, label='Fault')

        plotter.add_legend(loc='upper left')
        plotter.add_axes()
        plotter.set_scale(zscale=self.config.Z_SCALE)

        # ========== PLOT 4: Slice view (bottom-right) ==========
        plotter.subplot(1, 1)

        # Determine slice position (middle of fault in Z)
        slice_position = (bounds[4] + bounds[5]) / 2
        plotter.add_text(f"Slice View at Z={slice_position:.1f}m",
                        font_size=14, position='upper_edge')

        # Create slice of volume
        slice_vol = self.volume_mesh.slice(normal='z', origin=[0, 0, slice_position])
        slice_fault = self.fault_surface.slice(normal='z', origin=[0, 0, slice_position])

        # Show contributing vs non-contributing in slice
        if 'contribution_side' in slice_vol.cell_data:
            # Non-contributing cells (gray)
            non_contrib_mask = slice_vol.cell_data['contribution_side'] == 0
            if np.sum(non_contrib_mask) > 0:
                non_contrib = slice_vol.extract_cells(non_contrib_mask)
                plotter.add_mesh(non_contrib, color='lightgray', opacity=0.15,
                                show_edges=True, line_width=1, label='Non-contributing')

            # Plus side (blue)
            plus_mask = (slice_vol.cell_data['contribution_side'] == 1) | \
                       (slice_vol.cell_data['contribution_side'] == 3)
            if np.sum(plus_mask) > 0:
                plus_cells = slice_vol.extract_cells(plus_mask)
                plotter.add_mesh(plus_cells, color='dodgerblue', opacity=0.7,
                                show_edges=True, line_width=2, label='Plus side')

            # Minus side (orange)
            minus_mask = (slice_vol.cell_data['contribution_side'] == 2) | \
                        (slice_vol.cell_data['contribution_side'] == 3)
            if np.sum(minus_mask) > 0:
                minus_cells = slice_vol.extract_cells(minus_mask)
                plotter.add_mesh(minus_cells, color='darkorange', opacity=0.7,
                                show_edges=True, line_width=2, label='Minus side')

        # Fault slice (thick red line)
        if slice_fault.n_cells > 0:
            plotter.add_mesh(slice_fault, color='red', line_width=6,
                            label='Fault', render_lines_as_tubes=True)

        plotter.add_legend(loc='upper right')
        plotter.add_axes()
        plotter.set_scale(zscale=self.config.Z_SCALE)
        plotter.view_xy()

        # Link all views for synchronized rotation
        plotter.link_views()

        # Show or save
        if self.config.SHOW_PLOTS:
            plotter.show()
        else:
            # Save screenshot
            from pathlib import Path
            output_dir = Path(self.config.OUTPUT_DIR) if hasattr(self.config, 'OUTPUT_DIR') else Path('.')
            output_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = output_dir / "contribution_visualization.png"
            plotter.screenshot(str(screenshot_path))
            print(f"   💾 Visualization saved: {screenshot_path}")
            plotter.close()

    # -------------------------------------------------------------------
    # NORMALS
    # -------------------------------------------------------------------
    def _extract_and_compute_normals(self, show_plot=False, scale_factor=50.0, z_scale=1.0):
        """Extract fault surfaces and compute oriented normals/tangents"""
        surfaces = []

        for fault_id in self.fault_values:
            # Extract fault cells
            fault_mask = self.mesh.cell_data[self.fault_attribute] == fault_id
            fault_cells = self.mesh.extract_cells(fault_mask)

            if fault_cells.n_cells == 0:
                print(f"⚠️  No cells for fault {fault_id}")
                continue

            # Extract surface
            surf = fault_cells.extract_surface()
            if surf.n_cells == 0:
                continue

            # Compute normals
            surf.compute_normals(cell_normals=True, point_normals=True, inplace=True)

            # Orient normals consistently within the fault
            surf = self._orient_normals(surf)

            surfaces.append(surf)

        merged = pv.MultiBlock(surfaces).combine()
        print(f"✅ Normals computed for {merged.n_cells} fault cells")

        if show_plot:
            self._plot_geometry(merged, scale_factor, z_scale)

        return merged, surfaces

    # -------------------------------------------------------------------
    def _orient_normals(self, surf):
        """Ensure normals point in consistent direction within the fault"""
        normals = surf.cell_data['Normals']
        mean_normal = np.mean(normals, axis=0)
        mean_normal /= np.linalg.norm(mean_normal)

        n_cells = len(normals)
        tangents1 = np.zeros((n_cells, 3))
        tangents2 = np.zeros((n_cells, 3))

        for i, normal in enumerate(normals):

            # Flip if pointing opposite to mean
            if np.dot(normal, mean_normal) < 0:
                normals[i] = -normal

            if self.config.ROTATE_NORMALS:
                normals[i] = -normal

            # Compute orthogonal tangents
            normal = normals[i]
            if abs(normal[0]) > 1e-6 or abs(normal[1]) > 1e-6:
                t1 = np.array([-normal[1], normal[0], 0])
            else:
                t1 = np.array([0, -normal[2], normal[1]])

            t1 /= np.linalg.norm(t1)
            t2 = np.cross(normal, t1)
            t2 /= np.linalg.norm(t2)

            tangents1[i] = t1
            tangents2[i] = t2

        surf.cell_data['Normals'] = normals
        surf.cell_data['tangent1'] = tangents1
        surf.cell_data['tangent2'] = tangents2

        dip_angles, strike_angles = self.compute_dip_strike_from_cell_base(normals, tangents1, tangents2)

        surf.cell_data['dip_angle'] = dip_angles
        surf.cell_data['strike_angle'] = strike_angles

        return surf

    # -------------------------------------------------------------------
    def compute_dip_strike_from_cell_base(self, normals, tangent1, tangent2):
        """
        Calcule les angles dip et strike à partir des vecteurs normaux et tangents des cellules.
        Hypothèses :
            - Système de coordonnées : X=Est, Y=Nord, Z=Haut.
            - Vecteurs donnés par cellule (shape: (n_cells, 3)).
            - Les vecteurs d'entrée sont supposés orthonormés (n = t1 x t2).

        Retourne :
            dip_deg, strike_deg (two arrays of shape (n_cells,))
        """
        # 1. Identifier le vecteur strike (le plus horizontal)
        t1_horiz = tangent1 - (tangent1[:, 2][:, np.newaxis] * np.array([0, 0, 1]))
        t2_horiz = tangent2 - (tangent2[:, 2][:, np.newaxis] * np.array([0, 0, 1]))
        norm_t1_h = np.linalg.norm(t1_horiz, axis=1)
        norm_t2_h = np.linalg.norm(t2_horiz, axis=1)

        use_t1 = norm_t1_h > norm_t2_h
        strike_vector = np.zeros_like(tangent1)
        strike_vector[use_t1] = t1_horiz[use_t1]
        strike_vector[~use_t1] = t2_horiz[~use_t1]

        # Normaliser
        strike_norm = np.linalg.norm(strike_vector, axis=1)
        # Éviter la division par zéro (si la faille est parfaitement verticale, le strike est bien défini par l'autre vecteur)
        strike_norm[strike_norm == 0] = 1.0
        strike_vector = strike_vector / strike_norm[:, np.newaxis]

        # 2. Calculer le strike (azimut depuis le Nord, sens horaire)
        strike_rad = np.arctan2(strike_vector[:, 0], strike_vector[:, 1]) # atan2(E, N)
        strike_deg = np.degrees(strike_rad)
        strike_deg = np.where(strike_deg < 0, strike_deg + 360, strike_deg)

        # 3. Calculer le dip
        norm_horiz = np.linalg.norm(normals[:, :2], axis=1)
        dip_rad = np.arcsin(np.clip(norm_horiz, 0, 1)) # clip pour éviter les erreurs d'arrondi
        dip_deg = np.degrees(dip_rad)

        return dip_deg, strike_deg

    # -------------------------------------------------------------------
    def _plot_geometry(self, surface, scale_factor, z_scale):
        """Visualize fault geometry with normals"""
        plotter = pv.Plotter()
        plotter.add_mesh(self.mesh, color='lightgray', opacity=0.1, label='Volume')
        plotter.add_mesh(surface, color='darkgray', opacity=0.7, show_edges=True, label='Fault')

        centers = surface.cell_centers()
        for name, color in [('Normals', 'red'), ('tangent1', 'green'), ('tangent2', 'blue')]:
            arrows = centers.glyph(orient=name, scale=z_scale, factor=scale_factor)
            plotter.add_mesh(arrows, color=color, label=name)

        plotter.add_legend()
        plotter.add_axes()
        plotter.set_scale(zscale=z_scale)
        plotter.show()

    # -------------------------------------------------------------------
    def diagnose_normals(self, scale_factor=50.0, z_scale=1.0):
        """
        Diagnostic visualization to check normal quality
        Shows orthogonality and orientation issues
        """
        surface = self.fault_surface

        print("\n🔍 DIAGNOSTIC DES NORMALES")
        print("=" * 60)

        normals = surface.cell_data['Normals']
        tangent1 = surface.cell_data['tangent1']
        tangent2 = surface.cell_data['tangent2']

        n_cells = len(normals)

        # Check orthogonality
        dot_n_t1 = np.array([np.dot(normals[i], tangent1[i]) for i in range(n_cells)])
        dot_n_t2 = np.array([np.dot(normals[i], tangent2[i]) for i in range(n_cells)])
        dot_t1_t2 = np.array([np.dot(tangent1[i], tangent2[i]) for i in range(n_cells)])

        print(f"Orthogonalité (doit être proche de 0):")
        print(f"  Normal · Tangent1  : max={np.max(np.abs(dot_n_t1)):.2e}, mean={np.mean(np.abs(dot_n_t1)):.2e}")
        print(f"  Normal · Tangent2  : max={np.max(np.abs(dot_n_t2)):.2e}, mean={np.mean(np.abs(dot_n_t2)):.2e}")
        print(f"  Tangent1 · Tangent2: max={np.max(np.abs(dot_t1_t2)):.2e}, mean={np.mean(np.abs(dot_t1_t2)):.2e}")

        # Check unit vectors
        norm_n = np.linalg.norm(normals, axis=1)
        norm_t1 = np.linalg.norm(tangent1, axis=1)
        norm_t2 = np.linalg.norm(tangent2, axis=1)

        print(f"\nNormes (doit être proche de 1):")
        print(f"  Normals  : min={np.min(norm_n):.6f}, max={np.max(norm_n):.6f}")
        print(f"  Tangent1 : min={np.min(norm_t1):.6f}, max={np.max(norm_t1):.6f}")
        print(f"  Tangent2 : min={np.min(norm_t2):.6f}, max={np.max(norm_t2):.6f}")

        # Check orientation consistency
        mean_normal = np.mean(normals, axis=0)
        mean_normal = mean_normal / np.linalg.norm(mean_normal)

        dots_with_mean = np.array([np.dot(normals[i], mean_normal) for i in range(n_cells)])
        n_reversed = np.sum(dots_with_mean < 0)

        print(f"\nCohérence d'orientation:")
        print(f"  Normale moyenne: [{mean_normal[0]:.3f}, {mean_normal[1]:.3f}, {mean_normal[2]:.3f}]")
        print(f"  Normales inversées: {n_reversed}/{n_cells} ({n_reversed/n_cells*100:.1f}%)")

        if n_reversed > n_cells * 0.1:
            print(f"  ⚠️  Plus de 10% des normales pointent dans la direction opposée!")
        else:
            print(f"  ✅ Orientation cohérente")

        print("=" * 60)

        # Visualization
        plotter = pv.Plotter(shape=(1, 2))

        # Plot 1: Surface with normals
        plotter.subplot(0, 0)
        plotter.add_mesh(surface, color='lightgray', show_edges=True, opacity=0.8)

        centers = surface.cell_centers()
        arrows_n = centers.glyph(orient='Normals', scale=False, factor=scale_factor)
        plotter.add_mesh(arrows_n, color='red', label='Normals')

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text("Normales (Rouge)", position='upper_edge')
        plotter.set_scale(zscale=z_scale)

        # Plot 2: All vectors
        plotter.subplot(0, 1)
        plotter.add_mesh(surface, color='lightgray', show_edges=True, opacity=0.5)

        arrows_n = centers.glyph(orient='Normals', scale=False, factor=scale_factor)
        arrows_t1 = centers.glyph(orient='tangent1', scale=False, factor=scale_factor)
        arrows_t2 = centers.glyph(orient='tangent2', scale=False, factor=scale_factor)

        plotter.add_mesh(arrows_n, color='red', label='Normal')
        plotter.add_mesh(arrows_t1, color='green', label='Tangent1')
        plotter.add_mesh(arrows_t2, color='blue', label='Tangent2')

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text("Système complet (R,G,B)", position='upper_edge')
        plotter.set_scale(zscale=z_scale)

        plotter.link_views()
        plotter.show()

        return surface


        """
        Diagnostic visualization to check normal quality
        Shows orthogonality and orientation issues
        """
        print("\n🔍 DIAGNOSTIC DES NORMALES")
        print("=" * 60)

        normals = surface.cell_data['Normals']
        tangent1 = surface.cell_data['tangent1']
        tangent2 = surface.cell_data['tangent2']

        n_cells = len(normals)

        # Check orthogonality
        dot_n_t1 = np.array([np.dot(normals[i], tangent1[i]) for i in range(n_cells)])
        dot_n_t2 = np.array([np.dot(normals[i], tangent2[i]) for i in range(n_cells)])
        dot_t1_t2 = np.array([np.dot(tangent1[i], tangent2[i]) for i in range(n_cells)])

        print(f"Orthogonalité (doit être proche de 0):")
        print(f"  Normal · Tangent1  : max={np.max(np.abs(dot_n_t1)):.2e}, mean={np.mean(np.abs(dot_n_t1)):.2e}")
        print(f"  Normal · Tangent2  : max={np.max(np.abs(dot_n_t2)):.2e}, mean={np.mean(np.abs(dot_n_t2)):.2e}")
        print(f"  Tangent1 · Tangent2: max={np.max(np.abs(dot_t1_t2)):.2e}, mean={np.mean(np.abs(dot_t1_t2)):.2e}")

        # Check unit vectors
        norm_n = np.array([np.linalg.norm(normals[i]) for i in range(n_cells)])
        norm_t1 = np.array([np.linalg.norm(tangent1[i]) for i in range(n_cells)])
        norm_t2 = np.array([np.linalg.norm(tangent2[i]) for i in range(n_cells)])

        print(f"\nNormes (doit être proche de 1):")
        print(f"  Normals  : min={np.min(norm_n):.6f}, max={np.max(norm_n):.6f}")
        print(f"  Tangent1 : min={np.min(norm_t1):.6f}, max={np.max(norm_t1):.6f}")
        print(f"  Tangent2 : min={np.min(norm_t2):.6f}, max={np.max(norm_t2):.6f}")

        # Check orientation consistency
        mean_normal = np.mean(normals, axis=0)
        mean_normal = mean_normal / np.linalg.norm(mean_normal)

        dots_with_mean = np.array([np.dot(normals[i], mean_normal) for i in range(n_cells)])
        n_reversed = np.sum(dots_with_mean < 0)

        print(f"\nCohérence d'orientation:")
        print(f"  Normale moyenne: [{mean_normal[0]:.3f}, {mean_normal[1]:.3f}, {mean_normal[2]:.3f}]")
        print(f"  Normales inversées: {n_reversed}/{n_cells} ({n_reversed/n_cells*100:.1f}%)")

        # Visual check
        if n_reversed > n_cells * 0.1:
            print(f"  ⚠️  Plus de 10% des normales pointent dans la direction opposée!")
        else:
            print(f"  ✅ Orientation cohérente")

        # Check for problematic cells
        bad_ortho = (np.abs(dot_n_t1) > 1e-3) | (np.abs(dot_n_t2) > 1e-3) | (np.abs(dot_t1_t2) > 1e-3)
        n_bad = np.sum(bad_ortho)

        if n_bad > 0:
            print(f"\n⚠️  {n_bad} cellules avec orthogonalité douteuse (|dot| > 1e-3)")
            surface.cell_data['orthogonality_error'] = np.maximum.reduce([
                np.abs(dot_n_t1), np.abs(dot_n_t2), np.abs(dot_t1_t2)
            ])
        else:
            print(f"\n✅ Toutes les cellules ont une bonne orthogonalité")

        print("=" * 60)

        # Visualization
        plotter = pv.Plotter(shape=(1, 2))

        # Plot 1: Surface with normals
        plotter.subplot(0, 0)
        plotter.add_mesh(surface, color='lightgray', show_edges=True, opacity=0.8)

        centers = surface.cell_centers()
        arrows_n = centers.glyph(orient='Normals', scale=False, factor=scale_factor)
        plotter.add_mesh(arrows_n, color='red', label='Normals')

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text("Normales (Rouge)", position='upper_edge')
        plotter.set_scale(zscale=z_scale)

        # Plot 2: All vectors (normal + tangents)
        plotter.subplot(0, 1)
        plotter.add_mesh(surface, color='lightgray', show_edges=True, opacity=0.5)

        arrows_n = centers.glyph(orient='Normals', scale=False, factor=scale_factor)
        arrows_t1 = centers.glyph(orient='tangent1', scale=False, factor=scale_factor)
        arrows_t2 = centers.glyph(orient='tangent2', scale=False, factor=scale_factor)

        plotter.add_mesh(arrows_n, color='red', label='Normal')
        plotter.add_mesh(arrows_t1, color='green', label='Tangent1')
        plotter.add_mesh(arrows_t2, color='blue', label='Tangent2')

        plotter.add_legend()
        plotter.add_axes()
        plotter.add_text("Système complet (R,G,B)", position='upper_edge')
        plotter.set_scale(zscale=z_scale)

        plotter.link_views()
        plotter.show()

        return surface


# ============================================================================
# STRESS PROJECTION
# ============================================================================
class StressProjector:
    """Projects volume stress onto fault surfaces and tracks principal stresses in VTU"""

    # -------------------------------------------------------------------
    def __init__(self, config, adjacency_mapping, geometric_properties):
        """
        Initialize with pre-computed adjacency mapping and geometric properties

        Parameters
        ----------
        config : Configuration object
        adjacency_mapping : dict
            Pre-computed dict mapping fault cells to volume cells
        geometric_properties : dict
            Pre-computed geometric properties from FaultGeometry:
            - 'volumes': cell volumes
            - 'centers': cell centers
            - 'distances': distances to fault
            - 'fault_tree': KDTree for fault
        """
        self.config = config
        self.adjacency_mapping = adjacency_mapping

        # Store pre-computed geometric properties
        self.volume_cell_volumes = geometric_properties['volumes']
        self.volume_centers = geometric_properties['centers']
        self.distance_to_fault = geometric_properties['distances']
        self.fault_tree = geometric_properties['fault_tree']

        # Storage for time series metadata
        self.timestep_info = []

        # Track which cells to monitor (optional)
        self.monitored_cells = None

        # Output directory for VTU files
        self.vtu_output_dir = None

    # -------------------------------------------------------------------
    def set_monitored_cells(self, cell_indices):
        """
        Set specific cells to monitor (optional)

        Parameters:
            cell_indices: list of volume cell indices to track
                         If None, all contributing cells are tracked
        """
        self.monitored_cells = set(cell_indices) if cell_indices is not None else None

    # -------------------------------------------------------------------
    def project_stress_to_fault(self, volume_data, volume_initial, fault_surface,
                                time=None, timestep=None, weighting_scheme="arithmetic"):
        """
        Project stress and save principal stresses to VTU

        Now uses pre-computed geometric properties for efficiency
        """
        stress_name = self.config.STRESS_NAME
        biot_name = self.config.BIOT_NAME

        if stress_name not in volume_data.array_names:
            raise ValueError(f"No stress data '{stress_name}' in dataset")

        # =====================================================================
        # 1. EXTRACT STRESS DATA
        # =====================================================================
        pressure = volume_data["pressure"] / 1e5
        p_fault = volume_initial["pressure"] / 1e5
        p_init = volume_initial["pressure"] / 1e5
        biot = volume_data[biot_name]

        stress_eff = StressTensor.build_from_array(volume_data[stress_name] / 1e5)
        stress_eff_init = StressTensor.build_from_array(volume_initial[stress_name] / 1e5)

        # Convert effective stress to total stress
        I = np.eye(3)[None, :, :]
        stress_total = stress_eff - biot[:, None, None] * pressure[:, None, None] * I
        stress_total_init = stress_eff_init - biot[:, None, None] * p_init[:, None, None] * I

        # =====================================================================
        # 2. USE PRE-COMPUTED ADJACENCY
        # =====================================================================
        mapping = self.adjacency_mapping

        # =====================================================================
        # 3. PREPARE FAULT GEOMETRY
        # =====================================================================
        normals = fault_surface.cell_data["Normals"]
        tangent1 = fault_surface.cell_data["tangent1"]
        tangent2 = fault_surface.cell_data["tangent2"]

        fault_centers = fault_surface.cell_centers().points
        fault_surface.cell_data['elementCenter'] = fault_centers

        n_fault = fault_surface.n_cells
        n_volume = volume_data.n_cells

        # =====================================================================
        # 4. COMPUTE PRINCIPAL STRESSES FOR CONTRIBUTING CELLS
        # =====================================================================
        if self.config.COMPUTE_PRINCIPAL_STRESS and timestep is not None:

            # Collect all unique contributing cells
            all_contributing_cells = set()
            for fault_idx, neighbors in mapping.items():
                all_contributing_cells.update(neighbors['plus'])
                all_contributing_cells.update(neighbors['minus'])

            # Filter by monitored cells if specified
            if self.monitored_cells is not None:
                cells_to_track = all_contributing_cells.intersection(self.monitored_cells)
            else:
                cells_to_track = all_contributing_cells

            print(f"  📊 Computing principal stresses for {len(cells_to_track)} contributing cells...")

            # Create mesh with only contributing cells
            contributing_mesh = self._create_volumic_contrib_mesh(
                volume_data, fault_surface, cells_to_track, mapping
            )

            # Save to VTU
            if self.vtu_output_dir is None:
                self.vtu_output_dir = Path(self.config.OUTPUT_DIR) / "principal_stresses"

            self._save_principal_stress_vtu(contributing_mesh, time, timestep)

        else:
            contributing_mesh = None

        # =====================================================================
        # 6. PROJECT STRESS FOR EACH FAULT CELL
        # =====================================================================
        sigma_n_arr = np.zeros(n_fault)
        tau_arr = np.zeros(n_fault)
        tau_dip_arr = np.zeros(n_fault)
        tau_strike_arr = np.zeros(n_fault)
        delta_sigma_n_arr = np.zeros(n_fault)
        delta_tau_arr = np.zeros(n_fault)
        n_contributors = np.zeros(n_fault, dtype=int)

        print(f"  🔄 Projecting stress to {n_fault} fault cells...")
        print(f"     Weighting scheme: {weighting_scheme}")

        for fault_idx in range(n_fault):
            if fault_idx not in mapping:
                continue

            vol_plus = mapping[fault_idx]['plus']
            vol_minus = mapping[fault_idx]['minus']
            all_vol = vol_plus + vol_minus

            if len(all_vol) == 0:
                continue

            # ===================================================================
            # CALCULATE WEIGHTS (using pre-computed properties)
            # ===================================================================

            if weighting_scheme == 'arithmetic':
                weights = np.ones(len(all_vol)) / len(all_vol)

            elif weighting_scheme == 'harmonic':
                weights = np.ones(len(all_vol)) / len(all_vol)

            elif weighting_scheme == 'distance':
                # Use pre-computed distances
                dists = np.array([self.distance_to_fault[v] for v in all_vol])
                dists = np.maximum(dists, 1e-6)
                inv_dists = 1.0 / dists
                weights = inv_dists / np.sum(inv_dists)

            elif weighting_scheme == 'volume':
                # Use pre-computed volumes
                vols = np.array([self.volume_cell_volumes[v] for v in all_vol])
                weights = vols / np.sum(vols)

            elif weighting_scheme == 'distance_volume':
                # Use pre-computed volumes and distances
                vols = np.array([self.volume_cell_volumes[v] for v in all_vol])
                dists = np.array([self.distance_to_fault[v] for v in all_vol])
                dists = np.maximum(dists, 1e-6)

                weights = vols / dists
                weights = weights / np.sum(weights)

            elif weighting_scheme == 'inverse_square_distance':
                # Use pre-computed distances
                dists = np.array([self.distance_to_fault[v] for v in all_vol])
                dists = np.maximum(dists, 1e-6)
                inv_sq_dists = 1.0 / (dists ** 2)
                weights = inv_sq_dists / np.sum(inv_sq_dists)

            else:
                raise ValueError(f"Unknown weighting scheme: {weighting_scheme}")

            # ===================================================================
            # ACCUMULATE WEIGHTED CONTRIBUTIONS
            # ===================================================================

            sigma_n = 0.0
            tau = 0.0
            tau_dip = 0.0
            tau_strike = 0.0
            delta_sigma_n = 0.0
            delta_tau = 0.0

            for vol_idx, w in zip(all_vol, weights):

                # Total stress (with pressure)
                sigma_final = stress_total[vol_idx] + p_fault[vol_idx] * np.eye(3)
                sigma_init = stress_total_init[vol_idx] + p_init[vol_idx] * np.eye(3)

                # Rotate to fault frame
                res_f = StressTensor.rotate_to_fault_frame(
                    sigma_final, normals[fault_idx], tangent1[fault_idx], tangent2[fault_idx]
                )

                res_i = StressTensor.rotate_to_fault_frame(
                    sigma_init, normals[fault_idx], tangent1[fault_idx], tangent2[fault_idx]
                )

                # Accumulate weighted contributions
                sigma_n += w * res_f['normal_stress']
                tau += w * res_f['shear_stress']
                tau_dip += w * res_f['shear_dip']
                tau_strike += w * res_f['shear_strike']
                delta_sigma_n += w * (res_f['normal_stress'] - res_i['normal_stress'])
                delta_tau += w * (res_f['shear_stress'] - res_i['shear_stress'])

            sigma_n_arr[fault_idx] = sigma_n
            tau_arr[fault_idx] = tau
            tau_dip_arr[fault_idx] = tau_dip
            tau_strike_arr[fault_idx] = tau_strike
            delta_sigma_n_arr[fault_idx] = delta_sigma_n
            delta_tau_arr[fault_idx] = delta_tau
            n_contributors[fault_idx] = len(all_vol)

        # =====================================================================
        # 7. STORE RESULTS ON FAULT SURFACE
        # =====================================================================
        fault_surface.cell_data["sigma_n_eff"] = sigma_n_arr
        fault_surface.cell_data["tau_eff"] = tau_dip_arr
        fault_surface.cell_data["tau_strike"] = tau_strike_arr
        fault_surface.cell_data["tau_dip"] = tau_dip_arr
        fault_surface.cell_data["delta_sigma_n_eff"] = delta_sigma_n_arr
        fault_surface.cell_data["delta_tau_eff"] = delta_tau_arr

        # =====================================================================
        # 8. STATISTICS
        # =====================================================================
        valid = n_contributors > 0
        n_valid = np.sum(valid)

        print(f"  ✅ Stress projected: {n_valid}/{n_fault} fault cells ({n_valid/n_fault*100:.1f}%)")

        if np.sum(valid) > 0:
            print(f"     Contributors per fault cell: min={np.min(n_contributors[valid])}, "
                  f"max={np.max(n_contributors[valid])}, "
                  f"mean={np.mean(n_contributors[valid]):.1f}")

        return fault_surface, volume_data, contributing_mesh

    # -------------------------------------------------------------------
    @staticmethod
    def compute_principal_stresses(stress_tensor):
        """
        Compute principal stresses and directions

        Convention: Compression is NEGATIVE
        - σ1 = most compressive (most negative)
        - σ3 = least compressive (least negative, or most tensile)

        Returns:
            dict with eigenvalues, eigenvectors, mean_stress, deviatoric_stress
        """
        eigenvalues, eigenvectors = np.linalg.eigh(stress_tensor)

        # Sort from MOST NEGATIVE to LEAST NEGATIVE (most compressive to least)
        # Example: -600 < -450 < -200, so -600 is σ1 (most compressive)
        idx = np.argsort(eigenvalues)  # Ascending order (most negative first)
        eigenvalues_sorted = eigenvalues[idx]
        eigenvectors_sorted = eigenvectors[:, idx]

        return {
            'sigma1': eigenvalues_sorted[0],  # Most compressive (most negative)
            'sigma2': eigenvalues_sorted[1],  # Intermediate
            'sigma3': eigenvalues_sorted[2],  # Least compressive (least negative)
            'mean_stress': np.mean(eigenvalues_sorted),
            'deviatoric_stress': eigenvalues_sorted[0] - eigenvalues_sorted[2],  # σ1 - σ3 (negative - more negative = positive or less negative)
            'direction1': eigenvectors_sorted[:, 0],  # Direction of σ1
            'direction2': eigenvectors_sorted[:, 1],  # Direction of σ2
            'direction3': eigenvectors_sorted[:, 2]   # Direction of σ3
        }

    # -------------------------------------------------------------------
    def _create_volumic_contrib_mesh(self, volume_data, fault_surface, cells_to_track, mapping):
        """
        Create a mesh containing only contributing cells with principal stress data
        and compute analytical normal/shear stresses based on fault dip angle

        Parameters
        ----------
        volume_data : pyvista.UnstructuredGrid
            Volume mesh with stress data (rock_stress or averageStress)
        fault_surface : pyvista.PolyData
            Fault surface with dip_angle and strike_angle per cell
        cells_to_track : set
            Set of volume cell indices to include
        mapping : dict
            Adjacency mapping {fault_idx: {'plus': [...], 'minus': [...]}}
        """

        # ===================================================================
        # EXTRACT STRESS DATA FROM VOLUME
        # ===================================================================
        stress_name = self.config.STRESS_NAME
        biot_name = self.config.BIOT_NAME

        if stress_name not in volume_data.array_names:
            raise ValueError(f"No stress data '{stress_name}' in volume dataset")

        print(f"  📊 Extracting stress from field: '{stress_name}'")

        # Extract effective stress and pressure
        pressure = volume_data["pressure"] / 1e5  # Convert to bar
        biot = volume_data[biot_name]

        stress_eff = StressTensor.build_from_array(volume_data[stress_name] / 1e5)

        # Convert effective stress to total stress
        I = np.eye(3)[None, :, :]
        stress_total = stress_eff - biot[:, None, None] * pressure[:, None, None] * I

        # ===================================================================
        # EXTRACT SUBSET OF CELLS
        # ===================================================================
        cell_indices = sorted(list(cells_to_track))
        cell_mask = np.zeros(volume_data.n_cells, dtype=bool)
        cell_mask[cell_indices] = True

        subset_mesh = volume_data.extract_cells(cell_mask)

        # ===================================================================
        # REBUILD MAPPING: subset_idx -> original_idx
        # ===================================================================
        original_centers = volume_data.cell_centers().points[cell_indices]
        subset_centers = subset_mesh.cell_centers().points

        from scipy.spatial import cKDTree
        tree = cKDTree(original_centers)

        subset_to_original = np.zeros(subset_mesh.n_cells, dtype=int)
        for subset_idx in range(subset_mesh.n_cells):
            dist, idx = tree.query(subset_centers[subset_idx])
            if dist > 1e-6:
                print(f"        WARNING: Cell {subset_idx} not matched (dist={dist})")
            subset_to_original[subset_idx] = cell_indices[idx]

        # ===================================================================
        # MAP VOLUME CELLS TO FAULT DIP/STRIKE ANGLES
        # ===================================================================
        print(f"     📐 Mapping volume cells to fault dip/strike angles...")

        # Check if fault surface has required data
        if 'dip_angle' not in fault_surface.cell_data:
            print(f"        ⚠️ WARNING: 'dip_angle' not found in fault_surface")
            print(f"        Available fields: {list(fault_surface.cell_data.keys())}")
            return None

        if 'strike_angle' not in fault_surface.cell_data:
            print(f"        ⚠️ WARNING: 'strike_angle' not found in fault_surface")

        # Create mapping: volume_cell_id -> [dip_angles, strike_angles]
        volume_to_dip = {}
        volume_to_strike = {}

        for fault_idx, neighbors in mapping.items():
            # Get dip and strike angle from fault cell
            fault_dip = fault_surface.cell_data['dip_angle'][fault_idx]

            # Strike is optional
            if 'strike_angle' in fault_surface.cell_data:
                fault_strike = fault_surface.cell_data['strike_angle'][fault_idx]
            else:
                fault_strike = np.nan

            # Assign to all contributing volume cells (plus and minus)
            for vol_idx in neighbors['plus'] + neighbors['minus']:
                if vol_idx not in volume_to_dip:
                    volume_to_dip[vol_idx] = []
                    volume_to_strike[vol_idx] = []
                volume_to_dip[vol_idx].append(fault_dip)
                volume_to_strike[vol_idx].append(fault_strike)

        # Average if a volume cell contributes to multiple fault cells
        volume_to_dip_avg = {vol_idx: np.mean(dips)
                             for vol_idx, dips in volume_to_dip.items()}
        volume_to_strike_avg = {vol_idx: np.mean(strikes)
                                for vol_idx, strikes in volume_to_strike.items()}

        print(f"        ✅ Mapped {len(volume_to_dip_avg)} volume cells to fault angles")

        # Statistics
        all_dips = [np.mean(dips) for dips in volume_to_dip.values()]
        if len(all_dips) > 0:
            print(f"        Dip angle range: [{np.min(all_dips):.1f}, {np.max(all_dips):.1f}]°")

        # ===================================================================
        # COMPUTE PRINCIPAL STRESSES AND ANALYTICAL FAULT STRESSES
        # ===================================================================
        n_cells = subset_mesh.n_cells

        sigma1_arr = np.zeros(n_cells)
        sigma2_arr = np.zeros(n_cells)
        sigma3_arr = np.zeros(n_cells)
        mean_stress_arr = np.zeros(n_cells)
        deviatoric_stress_arr = np.zeros(n_cells)
        pressure_arr = np.zeros(n_cells)

        direction1_arr = np.zeros((n_cells, 3))
        direction2_arr = np.zeros((n_cells, 3))
        direction3_arr = np.zeros((n_cells, 3))

        # NEW: Analytical fault stresses
        sigma_n_analytical_arr = np.zeros(n_cells)
        tau_analytical_arr = np.zeros(n_cells)
        dip_angle_arr = np.zeros(n_cells)
        strike_angle_arr = np.zeros(n_cells)
        delta_arr = np.zeros(n_cells)

        side_arr = np.zeros(n_cells, dtype=int)
        n_fault_cells_arr = np.zeros(n_cells, dtype=int)

        print(f"     🔢 Computing principal stresses and analytical projections...")

        for subset_idx in range(n_cells):
            orig_idx = subset_to_original[subset_idx]

            # ===============================================================
            # COMPUTE PRINCIPAL STRESSES
            # ===============================================================
            # Total stress = effective stress + pore pressure
            sigma_total_cell = stress_total[orig_idx] + pressure[orig_idx] * np.eye(3)
            principal = self.compute_principal_stresses(sigma_total_cell)

            sigma1_arr[subset_idx] = principal['sigma1']
            sigma2_arr[subset_idx] = principal['sigma2']
            sigma3_arr[subset_idx] = principal['sigma3']
            mean_stress_arr[subset_idx] = principal['mean_stress']
            deviatoric_stress_arr[subset_idx] = principal['deviatoric_stress']
            pressure_arr[subset_idx] = pressure[orig_idx]

            direction1_arr[subset_idx] = principal['direction1']
            direction2_arr[subset_idx] = principal['direction2']
            direction3_arr[subset_idx] = principal['direction3']

            # ===============================================================
            # COMPUTE ANALYTICAL FAULT STRESSES (Anderson formulas)
            # ===============================================================
            if orig_idx in volume_to_dip_avg:
                dip_deg = volume_to_dip_avg[orig_idx]
                dip_angle_arr[subset_idx] = dip_deg

                strike_deg = volume_to_strike_avg.get(orig_idx, np.nan)
                strike_angle_arr[subset_idx] = strike_deg

                # δ = 90° - dip (angle from horizontal)
                delta_deg = 90.0 - dip_deg
                delta_rad = np.radians(delta_deg)
                delta_arr[subset_idx] = delta_deg

                # Extract principal stresses (compression negative)
                sigma1 = principal['sigma1']  # Most compressive (most negative)
                sigma3 = principal['sigma3']  # Least compressive (least negative)

                # Anderson formulas (1951)
                # σ_n = (σ1 + σ3)/2 - (σ1 - σ3)/2 * cos(2δ)
                # τ = |(σ1 - σ3)/2 * sin(2δ)|

                sigma_mean = (sigma1 + sigma3) / 2.0
                sigma_diff = (sigma1 - sigma3) / 2.0

                sigma_n_analytical = sigma_mean - sigma_diff * np.cos(2 * delta_rad)
                tau_analytical = sigma_diff * np.sin(2 * delta_rad)

                sigma_n_analytical_arr[subset_idx] = sigma_n_analytical
                tau_analytical_arr[subset_idx] = np.abs(tau_analytical)
            else:
                # No fault association - set to NaN
                dip_angle_arr[subset_idx] = np.nan
                strike_angle_arr[subset_idx] = np.nan
                delta_arr[subset_idx] = np.nan
                sigma_n_analytical_arr[subset_idx] = np.nan
                tau_analytical_arr[subset_idx] = np.nan

            # ===============================================================
            # DETERMINE SIDE (plus/minus/both)
            # ===============================================================
            is_plus = False
            is_minus = False
            fault_cell_count = 0

            for fault_idx, neighbors in mapping.items():
                if orig_idx in neighbors['plus']:
                    is_plus = True
                    fault_cell_count += 1
                if orig_idx in neighbors['minus']:
                    is_minus = True
                    fault_cell_count += 1

            if is_plus and is_minus:
                side_arr[subset_idx] = 3  # both
            elif is_plus:
                side_arr[subset_idx] = 1  # plus
            elif is_minus:
                side_arr[subset_idx] = 2  # minus
            else:
                side_arr[subset_idx] = 0  # none (should not happen)

            n_fault_cells_arr[subset_idx] = fault_cell_count

        # ===================================================================
        # ADD DATA TO MESH
        # ===================================================================
        subset_mesh.cell_data['sigma1'] = sigma1_arr
        subset_mesh.cell_data['sigma2'] = sigma2_arr
        subset_mesh.cell_data['sigma3'] = sigma3_arr
        subset_mesh.cell_data['mean_stress'] = mean_stress_arr
        subset_mesh.cell_data['deviatoric_stress'] = deviatoric_stress_arr
        subset_mesh.cell_data['pressure_bar'] = pressure_arr

        subset_mesh.cell_data['sigma1_direction'] = direction1_arr
        subset_mesh.cell_data['sigma2_direction'] = direction2_arr
        subset_mesh.cell_data['sigma3_direction'] = direction3_arr

        # Analytical fault stresses
        subset_mesh.cell_data['sigma_n_analytical'] = sigma_n_analytical_arr
        subset_mesh.cell_data['tau_analytical'] = tau_analytical_arr
        subset_mesh.cell_data['dip_angle'] = dip_angle_arr
        subset_mesh.cell_data['strike_angle'] = strike_angle_arr
        subset_mesh.cell_data['delta_angle'] = delta_arr

        # ===================================================================
        # COMPUTE SCU ANALYTICALLY (Mohr-Coulomb)
        # ===================================================================
        if hasattr(self.config, 'FRICTION_ANGLE') and hasattr(self.config, 'COHESION'):
            mu = np.tan(np.radians(self.config.FRICTION_ANGLE))
            cohesion = self.config.COHESION

            # τ_crit = C - σ_n * μ
            # Note: σ_n is negative (compression), so -σ_n * μ is positive
            tau_crit_arr = cohesion - sigma_n_analytical_arr * mu

            # SCU = τ / τ_crit
            SCU_analytical_arr = np.divide(
                tau_analytical_arr,
                tau_crit_arr,
                out=np.zeros_like(tau_analytical_arr),
                where=tau_crit_arr != 0
            )

            subset_mesh.cell_data['tau_crit_analytical'] = tau_crit_arr
            subset_mesh.cell_data['SCU_analytical'] = SCU_analytical_arr

            # CFS (Coulomb Failure Stress)
            CFS_analytical_arr = tau_analytical_arr - mu * (-sigma_n_analytical_arr)
            subset_mesh.cell_data['CFS_analytical'] = CFS_analytical_arr

        subset_mesh.cell_data['side'] = side_arr
        subset_mesh.cell_data['n_fault_cells'] = n_fault_cells_arr
        subset_mesh.cell_data['original_cell_id'] = subset_to_original

        # ===================================================================
        # STATISTICS
        # ===================================================================
        valid_analytical = ~np.isnan(sigma_n_analytical_arr)
        n_valid = np.sum(valid_analytical)

        if n_valid > 0:
            print(f"     📊 Analytical fault stresses computed for {n_valid}/{n_cells} cells")
            print(f"        σ_n range: [{np.nanmin(sigma_n_analytical_arr):.1f}, {np.nanmax(sigma_n_analytical_arr):.1f}] bar")
            print(f"        τ range: [{np.nanmin(tau_analytical_arr):.1f}, {np.nanmax(tau_analytical_arr):.1f}] bar")
            print(f"        Dip angle range: [{np.nanmin(dip_angle_arr):.1f}, {np.nanmax(dip_angle_arr):.1f}]°")

            if hasattr(self.config, 'FRICTION_ANGLE') and hasattr(self.config, 'COHESION'):
                print(f"        SCU range: [{np.nanmin(SCU_analytical_arr[valid_analytical]):.2f}, {np.nanmax(SCU_analytical_arr[valid_analytical]):.2f}]")
                n_critical = np.sum((SCU_analytical_arr >= 0.8) & (SCU_analytical_arr < 1.0))
                n_unstable = np.sum(SCU_analytical_arr >= 1.0)
                print(f"        Critical cells (SCU≥0.8): {n_critical} ({n_critical/n_valid*100:.1f}%)")
                print(f"        Unstable cells (SCU≥1.0): {n_unstable} ({n_unstable/n_valid*100:.1f}%)")
        else:
            print(f"     ⚠️  No analytical stresses computed (no fault mapping)")

        return subset_mesh

    # -------------------------------------------------------------------
    def _save_principal_stress_vtu(self, mesh, time, timestep):
        """
        Save principal stress mesh to VTU file

        Parameters:
            mesh: PyVista mesh with principal stress data
            time: Simulation time
            timestep: Timestep index
        """
        # Create output directory
        self.vtu_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        vtu_filename = f"principal_stresses_{timestep:05d}.vtu"
        vtu_path = self.vtu_output_dir / vtu_filename

        # Save mesh
        mesh.save(str(vtu_path))

        # Store metadata for PVD
        self.timestep_info.append({
            'time': time if time is not None else timestep,
            'timestep': timestep,
            'file': vtu_filename
        })

        print(f"     💾 Saved principal stresses: {vtu_filename}")

    # -------------------------------------------------------------------
    def save_pvd_collection(self, filename="principal_stresses.pvd"):
        """
        Create PVD file for time series visualization in ParaView

        Parameters:
            filename: Name of PVD file
        """
        if len(self.timestep_info) == 0:
            print("⚠️  No timestep data to save in PVD")
            return

        pvd_path = self.vtu_output_dir / filename

        print(f"\n💾 Creating PVD collection: {pvd_path}")
        print(f"   Timesteps: {len(self.timestep_info)}")

        # Create XML structure
        root = Element('VTKFile')
        root.set('type', 'Collection')
        root.set('version', '0.1')
        root.set('byte_order', 'LittleEndian')

        collection = SubElement(root, 'Collection')

        for info in self.timestep_info:
            dataset = SubElement(collection, 'DataSet')
            dataset.set('timestep', str(info['time']))
            dataset.set('group', '')
            dataset.set('part', '0')
            dataset.set('file', info['file'])

        # Write to file
        tree = ElementTree(root)
        tree.write(str(pvd_path), encoding='utf-8', xml_declaration=True)

        print(f"   ✅ PVD file created successfully")
        print(f"   📂 Output directory: {self.vtu_output_dir}")
        print(f"\n   🎨 To visualize in ParaView:")
        print(f"      1. Open: {pvd_path}")
        print(f"      2. Apply")
        print(f"      3. Color by: sigma1, sigma2, sigma3, mean_stress, etc.")
        print(f"      4. Use 'side' filter to show plus/minus/both")


# ============================================================================
# MOHR COULOMB
# ============================================================================
class MohrCoulomb:
    """Mohr-Coulomb failure criterion analysis"""

    @staticmethod
    def analyze(surface, cohesion, friction_angle_deg, time=0, verbose=True):
        """
        Perform Mohr-Coulomb stability analysis

        Parameters:
            surface: fault surface with stress data
            cohesion: cohesion in bar
            friction_angle_deg: friction angle in degrees
            time: simulation time
            verbose: print statistics
        """
        mu = np.tan(np.radians(friction_angle_deg))

        # Extract stress components
        sigma_n = surface.cell_data["sigma_n_eff"]
        tau = surface.cell_data["tau_eff"]
        d_sigma_n = surface.cell_data['delta_sigma_n_eff']
        d_tau = surface.cell_data['delta_tau_eff']

        # Mohr-Coulomb failure envelope
        tau_crit = cohesion - sigma_n * mu

        # Coulomb Failure Stress
        CFS = tau - mu * sigma_n
        # delta_CFS = d_tau - mu * d_sigma_n

        # Shear Capacity Utilization: SCU = τ / τ_crit
        SCU = np.divide(tau, tau_crit, out=np.zeros_like(tau), where=tau_crit != 0)

        if "SCU_initial" not in surface.cell_data:
            # First timestep: store as initial reference
            SCU_initial = SCU.copy()
            CFS_initial = CFS.copy()
            delta_SCU = np.zeros_like(SCU)
            delta_CFS = np.zeros_like(CFS)

            surface.cell_data["SCU_initial"] = SCU_initial
            surface.cell_data["CFS_initial"] = CFS_initial

            is_initial = True
        else:
            # Subsequent timesteps: calculate change from initial
            SCU_initial = surface.cell_data["SCU_initial"]
            CFS_initial = surface.cell_data['CFS_initial']
            delta_SCU = SCU - SCU_initial
            delta_CFS = CFS - CFS_initial
            is_initial = False

        # Stability classification
        stability = np.zeros_like(tau, dtype=int)
        stability[SCU >= 0.8] = 1  # Critical
        stability[SCU >= 1.0] = 2  # Unstable

        # Failure probability (sigmoid)
        k = 10.0
        failure_prob = 1.0 / (1.0 + np.exp(-k * (SCU - 1.0)))

        # Safety margin
        safety = tau_crit - tau

        # Store results
        surface.cell_data.update({
            "mohr_cohesion": np.full(surface.n_cells, cohesion),
            "mohr_friction_angle": np.full(surface.n_cells, friction_angle_deg),
            "mohr_friction_coefficient": np.full(surface.n_cells, mu),
            "mohr_critical_shear_stress": tau_crit,
            "SCU": SCU,
            "delta_SCU": delta_SCU,
            "CFS" : CFS,
            "delta_CFS": delta_CFS,
            "safety_margin": safety,
            "stability_state": stability,
            "failure_probability": failure_prob
        })

        if verbose:
            n_stable = np.sum(stability == 0)
            n_critical = np.sum(stability == 1)
            n_unstable = np.sum(stability == 2)

            # Additional info on delta_SCU
            if not is_initial:
                mean_delta = np.mean(np.abs(delta_SCU))
                max_increase = np.max(delta_SCU)
                max_decrease = np.min(delta_SCU)
                print(f"  ✅ Mohr-Coulomb: {n_unstable} unstable, {n_critical} critical, "
                      f"{n_stable} stable cells")
                print(f"     ΔSCU: mean={mean_delta:.3f}, max_increase={max_increase:.3f}, "
                      f"max_decrease={max_decrease:.3f}")
            else:
                print(f"  ✅ Mohr-Coulomb (initial): {n_unstable} unstable, {n_critical} critical, "
                      f"{n_stable} stable cells")

        return surface


# ============================================================================
# TIME SERIES PROCESSING
# ============================================================================
class TimeSeriesProcessor:
    """Process multiple time steps from PVD file"""

    # -------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)

    # -------------------------------------------------------------------
    def process(self, path, fault_geometry, pvd_file):
        """
        Process all time steps using pre-computed fault geometry

        Parameters:
            path: base path for input files
            fault_geometry: FaultGeometry object with initialized topology
            pvd_file: PVD file name
        """
        pvd_reader = pv.PVDReader(path / pvd_file)
        time_values = np.array(pvd_reader.time_values)

        if self.config.TIME_INDEX:
            time_values = time_values[self.config.TIME_INDEX]

        output_files = []
        data_initial = None
        SCU_initial_reference = None

        # Get pre-computed data from fault_geometry
        surface = fault_geometry.fault_surface
        adjacency_mapping = fault_geometry.adjacency_mapping
        geometric_properties = fault_geometry.get_geometric_properties()

        # Initialize projector with pre-computed topology
        projector = StressProjector(self.config, adjacency_mapping, geometric_properties)


        print('\n')
        print("=" * 60)
        print("TIME SERIES PROCESSING")
        print("=" * 60)

        for i, time in enumerate(time_values):
            print(f"\n→ Step {i+1}/{len(time_values)}: {time/(365.25*24*3600):.2f} years")

            # Read time step
            idx = self.config.TIME_INDEX[i] if self.config.TIME_INDEX else i
            pvd_reader.set_active_time_point(idx)
            dataset = pvd_reader.read()

            # Merge blocks
            volume_data = self._merge_blocks(dataset)

            if data_initial is None:
                data_initial = volume_data

            # -----------------------------------
            # Projection using pre-computed topology
            # -----------------------------------
            # Projection
            surface_result, volume_marked, contributing_cells = projector.project_stress_to_fault(
                volume_data,
                data_initial,
                surface,
                time=time_values[i],                            # Simulation time
                timestep=i,                                     # Timestep index
                weighting_scheme=self.config.WEIGHTING_SCHEME
            )

            # -----------------------------------
            # Mohr-Coulomb analysis
            # -----------------------------------
            cohesion = self.config.COHESION
            friction_angle = self.config.FRICTION_ANGLE
            surface_result = MohrCoulomb.analyze(surface_result, cohesion, friction_angle, time)

            # -----------------------------------
            # Visualize
            # -----------------------------------
            self._plot_results(surface_result, contributing_cells, time, self.output_dir)

            # -----------------------------------
            # Sensitivity analysis
            # -----------------------------------
            if self.config.RUN_SENSITIVITY:
                analyzer = SensitivityAnalyzer(self.config)
                sensitivity_results = analyzer.run_analysis(surface_result, time)

            # Save
            filename = f'fault_analysis_{i:04d}.vtu'
            surface_result.save(self.output_dir / filename)
            output_files.append((time, filename))
            print(f"  💾 Saved: {filename}")

        # Create master PVD
        self._create_pvd(output_files)

        return surface_result

    # -------------------------------------------------------------------
    def _merge_blocks(self, dataset):
        """Merge multi-block dataset - descente automatique jusqu'aux données"""

        # -----------------------------------------------
        def extract_leaf_blocks(block, path="", depth=0):
            """
            Descend récursivement dans la structure MultiBlock jusqu'aux feuilles avec données

            Returns:
                list of (block, path, bounds) tuples
            """
            leaves = []

            # Cas 1: C'est un MultiBlock avec des sous-blocs
            if hasattr(block, 'n_blocks') and block.n_blocks > 0:
                for i in range(block.n_blocks):
                    sub_block = block.GetBlock(i)
                    block_name = block.get_block_name(i) if hasattr(block, 'get_block_name') else f"Block{i}"
                    new_path = f"{path}/{block_name}" if path else block_name

                    if sub_block is not None:
                        # Récursion
                        leaves.extend(extract_leaf_blocks(sub_block, new_path, depth + 1))

            # Cas 2: C'est un dataset final (feuille)
            elif hasattr(block, 'n_cells') and block.n_cells > 0:
                bounds = block.bounds
                leaves.append((block, path, bounds))

            return leaves

        print(f"  📦 Extracting volume blocks")

        # Extraire toutes les feuilles
        all_blocks = extract_leaf_blocks(dataset)

        # Filtrer et afficher
        merged = []
        blocks_with_pressure = 0
        blocks_without_pressure = 0

        for block, path, bounds in all_blocks:
            has_pressure = 'pressure' in block.cell_data

            if has_pressure:
                blocks_with_pressure += 1
                merged.append(block)
            else:
                blocks_without_pressure += 1

        # Combiner
        combined = pv.MultiBlock(merged).combine()

        return combined

    # -------------------------------------------------------------------
    def _plot_results(self, surface, contributing_cells, time, path):

        Visualizer.plot_mohr_coulomb_diagram( surface, time, path,
                                              show=self.config.SHOW_PLOTS,
                                              save=self.config.SAVE_PLOTS )

        # Profils verticaux automatiques
        if self.config.SHOW_DEPTH_PROFILES:
            Visualizer.plot_depth_profiles(
                self,
                surface, time, path,
                show=self.config.SHOW_PLOTS,
                save=self.config.SAVE_PLOTS,
                profile_start_points=self.config.PROFILE_START_POINTS )

        visualizer = Visualizer(self.config)

        if self.config.COMPUTE_PRINCIPAL_STRESS:

            # Plot principal stress from volume cells
            visualizer.plot_volume_stress_profiles(
                volume_mesh=contributing_cells,
                fault_surface=surface,
                time=time,
                path=path,
                profile_start_points=self.config.PROFILE_START_POINTS )

            # Visualize comparison analytical/numerical
            visualizer.plot_analytical_vs_numerical_comparison(
                volume_mesh=contributing_cells,
                fault_surface=surface,
                time=time,
                path=path,
                show=self.config.SHOW_PLOTS,
                save=self.config.SAVE_PLOTS,
                profile_start_points=self.config.PROFILE_START_POINTS)

    # -------------------------------------------------------------------
    def _create_pvd(self, output_files):
        """Create PVD collection file"""
        pvd_path = self.output_dir / 'fault_analysis.pvd'
        with open(pvd_path, 'w') as f:
            f.write('<VTKFile type="Collection" version="0.1">\n')
            f.write('  <Collection>\n')
            for t, fname in output_files:
                f.write(f'    <DataSet timestep="{t}" file="{fname}"/>\n')
            f.write('  </Collection>\n')
            f.write('</VTKFile>\n')
        print(f"\n✅ PVD created: {pvd_path}")


# ============================================================================
# SENSITIVITY ANALYSIS
# ============================================================================
class SensitivityAnalyzer:
    """Performs sensitivity analysis on Mohr-Coulomb parameters"""

    # -------------------------------------------------------------------
    def __init__(self, config):
        self.config = config
        self.output_dir = Path(config.SENSITIVITY_OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        self.results = []

    # -------------------------------------------------------------------
    def run_analysis(self, surface_with_stress, time):
        """Run sensitivity analysis for multiple friction angles and cohesions"""
        friction_angles = self.config.SENSITIVITY_FRICTION_ANGLES
        cohesions = self.config.SENSITIVITY_COHESIONS

        print("\n" + "=" * 60)
        print("SENSITIVITY ANALYSIS")
        print("=" * 60)
        print(f"Friction angles: {friction_angles}")
        print(f"Cohesions: {cohesions}")
        print(f"Total combinations: {len(friction_angles) * len(cohesions)}")

        results = []

        for friction_angle in friction_angles:
            for cohesion in cohesions:
                print(f"\n→ Testing φ={friction_angle}°, C={cohesion} bar")

                surface_copy = surface_with_stress.copy()

                surface_analyzed = MohrCoulomb.analyze(
                    surface_copy, cohesion, friction_angle, time, verbose=False)

                stats = self._extract_statistics(surface_analyzed, friction_angle, cohesion)
                results.append(stats)

                print(f"   Unstable: {stats['n_unstable']}, "
                      f"Critical: {stats['n_critical']}, "
                      f"Stable: {stats['n_stable']}")

        self.results = results

        # Generate plots
        self._plot_sensitivity_results(results, time)

        # Plot SCU vs depth
        self._plot_scu_depth_profiles(results, time, surface_with_stress)

        return results

    # -------------------------------------------------------------------
    def _extract_statistics(self, surface, friction_angle, cohesion):
        """Extract statistical metrics from analyzed surface"""
        stability = surface.cell_data["stability_state"]
        SCU = surface.cell_data["SCU"]
        failure_prob = surface.cell_data["failure_probability"]
        safety_margin = surface.cell_data["safety_margin"]

        stats = {
            'friction_angle': friction_angle,
            'cohesion': cohesion,
            'n_cells': surface.n_cells,
            'n_stable': np.sum(stability == 0),
            'n_critical': np.sum(stability == 1),
            'n_unstable': np.sum(stability == 2),
            'pct_unstable': np.sum(stability == 2) / surface.n_cells * 100,
            'pct_critical': np.sum(stability == 1) / surface.n_cells * 100,
            'pct_stable': np.sum(stability == 0) / surface.n_cells * 100,
            'mean_SCU': np.mean(SCU),
            'max_SCU': np.max(SCU),
            'mean_failure_prob': np.mean(failure_prob),
            'mean_safety_margin': np.mean(safety_margin),
            'min_safety_margin': np.min(safety_margin)
        }

        return stats

    # -------------------------------------------------------------------
    def _plot_sensitivity_results(self, results, time):
        """Create comprehensive sensitivity analysis plots"""
        import pandas as pd

        df = pd.DataFrame(results)

        fig, axes = plt.subplots(2, 2, figsize=(16, 12))

        # Plot heatmaps
        self._plot_heatmap(df, 'pct_unstable', 'Unstable Cells [%]', axes[0, 0])
        self._plot_heatmap(df, 'pct_critical', 'Critical Cells [%]', axes[0, 1])
        self._plot_heatmap(df, 'mean_SCU', 'Mean SCU [-]', axes[1, 0])
        self._plot_heatmap(df, 'mean_safety_margin', 'Mean Safety Margin [bar]', axes[1, 1])

        plt.tight_layout()

        years = time / (365.25 * 24 * 3600)
        filename = f'sensitivity_analysis_{years:.0f}y.png'
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        print(f"\n📊 Sensitivity plot saved: {filename}")

        if self.config.SHOW_PLOTS:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    def _plot_heatmap(self, df, column, title, ax):
        """Create a single heatmap for sensitivity analysis"""
        pivot = df.pivot(index='cohesion', columns='friction_angle', values=column)

        im = ax.imshow(pivot.values, cmap='RdYlGn_r', aspect='auto', origin='lower')

        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)

        ax.set_xlabel('Friction Angle [°]')
        ax.set_ylabel('Cohesion [bar]')
        ax.set_title(title)

        # Add values in cells
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                value = pivot.values[i, j]
                text_color = 'white' if value > pivot.values.max() * 0.5 else 'black'
                ax.text(j, i, f'{value:.1f}', ha='center', va='center',
                       color=text_color, fontsize=9)

        plt.colorbar(im, ax=ax)

    # -------------------------------------------------------------------
    def _plot_scu_depth_profiles(self, results, time, surface_with_stress):
        """
        Plot SCU depth profiles for all parameter combinations
        Each (cohesion, friction) pair gets a unique color
        Uses profile points from config.PROFILE_START_POINTS
        """
        import pandas as pd
        from matplotlib.colors import Normalize
        from matplotlib.cm import ScalarMappable

        print("\n  📊 Creating SCU sensitivity depth profiles...")

        # Extract depth data
        centers = surface_with_stress.cell_data['elementCenter']
        depth = centers[:, 2]

        # Get profile points from config
        profile_start_points = self.config.PROFILE_START_POINTS

        # Auto-generate if not provided
        if profile_start_points is None:
            print("  ⚠️  No PROFILE_START_POINTS in config, auto-generating...")
            x_min, x_max = np.min(centers[:, 0]), np.max(centers[:, 0])
            y_min, y_max = np.min(centers[:, 1]), np.max(centers[:, 1])

            x_range = x_max - x_min
            y_range = y_max - y_min

            if x_range > y_range:
                # Fault oriented in X, sample at mid-Y
                x_pos = (x_min + x_max) / 2
                y_pos = (y_min + y_max) / 2
            else:
                # Fault oriented in Y, sample at mid-X
                x_pos = (x_min + x_max) / 2
                y_pos = (y_min + y_max) / 2

            profile_start_points = [(x_pos, y_pos)]

        # Get search radius from config or auto-compute
        search_radius = getattr(self.config, 'PROFILE_SEARCH_RADIUS', None)
        if search_radius is None:
            x_min, x_max = np.min(centers[:, 0]), np.max(centers[:, 0])
            y_min, y_max = np.min(centers[:, 1]), np.max(centers[:, 1])
            x_range = x_max - x_min
            y_range = y_max - y_min
            search_radius = min(x_range, y_range) * 0.15

        print(f"  📍 Using {len(profile_start_points)} profile point(s) from config")
        print(f"     Search radius: {search_radius:.1f}m")

        # Create colormap for parameter combinations
        n_combinations = len(results)
        cmap = plt.cm.viridis
        norm = Normalize(vmin=0, vmax=n_combinations-1)
        sm = ScalarMappable(norm=norm, cmap=cmap)

        # Create figure with subplots for each profile point
        n_profiles = len(profile_start_points)
        fig, axes = plt.subplots(1, n_profiles, figsize=(8*n_profiles, 10))

        # Handle single subplot case
        if n_profiles == 1:
            axes = [axes]

        # Plot each profile point
        for profile_idx, (x_pos, y_pos, z_pos) in enumerate(profile_start_points):
            ax = axes[profile_idx]

            print(f"\n  → Profile {profile_idx+1} at ({x_pos:.1f}, {y_pos:.1f}, {z_pos:.1f}):")


            # Plot each parameter combination
            for idx, params in enumerate(results):
                friction_angle = params['friction_angle']
                cohesion = params['cohesion']

                # Re-analyze surface with these parameters
                surface_copy = surface_with_stress.copy()
                surface_analyzed = MohrCoulomb.analyze(
                    surface_copy, cohesion, friction_angle, time, verbose=False
                )

                # Extract SCU
                SCU = np.abs(surface_analyzed.cell_data["SCU"])

                # Extract profile using adaptive method
                # depths_SCU, profile_SCU, _, _ = ProfileExtractor.extract_vertical_profile_topology_based(
                #         surface_analyzed, 'SCU', x_pos, y_pos, z_pos, verbose=False)
                depths_SCU, profile_SCU, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers, SCU, x_pos, y_pos, search_radius)

                if len(depths_SCU) >= 3:
                    color = cmap(norm(idx))
                    label = f'φ={friction_angle}°, C={cohesion} bar'
                    ax.plot(profile_SCU, depths_SCU,
                           color=color, label=label,
                           linewidth=2, alpha=0.8)

                    if idx == 0:  # Print info only once per profile
                        print(f"     ✅ {len(depths_SCU)} points extracted")
                else:
                    if idx == 0:
                        print(f"     ⚠️  Insufficient points ({len(depths_SCU)})")

            # Add critical lines
            ax.axvline(x=0.8, color='forestgreen', linestyle='--',
                      linewidth=2, label='Critical (SCU=0.8)', zorder=100)
            ax.axvline(x=1.0, color='red', linestyle='--',
                      linewidth=2, label='Failure (SCU=1.0)', zorder=100)

            # Configure plot
            ax.set_xlabel('Shear Capacity Utilization (SCU) [-]', fontsize=14, weight='bold')
            ax.set_ylabel('Depth [m]', fontsize=14, weight='bold')
            ax.set_title(f'Profile {profile_idx+1} @ ({x_pos:.0f}, {y_pos:.0f})',
                        fontsize=14, weight='bold')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.set_xlim(left=0)

            # Change verticale scale
            if hasattr(self.config, 'MAX_DEPTH_PROFILES') and self.config.MAX_DEPTH_PROFILES is not None:
                ax.set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

            # Légende en dehors à droite
            ax.legend(loc='center left', bbox_to_anchor=(1, 0.5), fontsize=9, ncol=1)

            ax.tick_params(labelsize=12)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle('SCU Depth Profiles - Sensitivity Analysis',
                    fontsize=16, weight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save
        filename = f'sensitivity_scu_profiles_{years:.0f}y.png'
        plt.savefig(self.output_dir / filename, dpi=300, bbox_inches='tight')
        print(f"\n  💾 SCU sensitivity profiles saved: {filename}")

        if self.config.SHOW_PLOTS:
            plt.show()
        else:
            plt.close()


# ============================================================================
# PROFILE EXTRACTOR
# ============================================================================
class ProfileExtractor:
    """Utility class for extracting profiles along fault surfaces"""

    # -------------------------------------------------------------------
    @staticmethod
    def extract_adaptive_profile(centers, values, x_start, y_start, z_start=None,
                                 search_radius=None, step_size=20.0, max_steps=500,
                                 verbose=True, fault_bounds=None, cell_data=None):
        """
        Extraction de profil vertical par COUCHES DE PROFONDEUR avec détection automatique de faille.

        Stratégie:
        1. Trouver le point de départ le plus proche
        2. Identifier automatiquement la faille via cell_data (attribute, FaultMask, etc.)
        3. FILTRER pour ne garder QUE les cellules de cette faille
        4. Diviser en tranches Z
        5. Pour chaque tranche, prendre la cellule la plus proche en XY

        Parameters
        ----------
        centers : ndarray
            Cell centers (n_cells, 3)
        values : ndarray
            Values at cells (n_cells,)
        x_start, y_start : float
            Starting XY position
        z_start : float, optional
            Starting Z position (if None, uses highest point near XY)
        search_radius : float, optional
            Not used (kept for compatibility)
        cell_data : dict, optional
            Dictionary with cell data fields (e.g., {'attribute': array, 'FaultMask': array})
            Used to automatically detect and filter by fault ID
        verbose : bool
            Print detailed information

        Returns
        -------
        depths, profile_values, path_x, path_y : ndarrays
            Extracted profile data
        """

        from scipy.spatial import cKDTree

        # Convert to np arrays
        centers = np.asarray(centers)
        values = np.asarray(values)

        if len(centers) == 0:
            if verbose:
                print(f"        ⚠️ No cells provided")
            return np.array([]), np.array([]), np.array([]), np.array([])

        # ===================================================================
        # ÉTAPE 1: TROUVER LE POINT DE DÉPART
        # ===================================================================

        if z_start is None:
            # Chercher en 2D (XY), prendre le plus haut
            if verbose:
                print(f"        Searching near ({x_start:.1f}, {y_start:.1f})")

            d_xy = np.sqrt((centers[:, 0] - x_start)**2 + (centers[:, 1] - y_start)**2)
            closest_indices = np.argsort(d_xy)[:20]

            if len(closest_indices) == 0:
                print(f"        ⚠️ No cells found near start point")
                return np.array([]), np.array([]), np.array([]), np.array([])

            # Prendre le plus haut (plus grand Z)
            closest_depths = centers[closest_indices, 2]
            start_idx = closest_indices[np.argmax(closest_depths)]
        else:
            # Chercher en 3D
            if verbose:
                print(f"        Searching near ({x_start:.1f}, {y_start:.1f}, {z_start:.1f})")

            d_3d = np.sqrt((centers[:, 0] - x_start)**2 +
                          (centers[:, 1] - y_start)**2 +
                          (centers[:, 2] - z_start)**2)
            start_idx = np.argmin(d_3d)

        start_point = centers[start_idx]

        if verbose:
            print(f"        Starting point: ({start_point[0]:.1f}, {start_point[1]:.1f}, {start_point[2]:.1f})")
            print(f"        Starting cell index: {start_idx}")

        # ===================================================================
        # ÉTAPE 2: DÉTECTER AUTOMATIQUEMENT L'ID DE LA FAILLE
        # ===================================================================

        fault_ids = None
        target_fault_id = None

        if cell_data is not None:
            # Chercher dans l'ordre de priorité
            fault_field_names = ['attribute', 'FaultMask', 'fault_id', 'region']

            for field_name in fault_field_names:
                if field_name in cell_data:
                    fault_ids = np.asarray(cell_data[field_name])

                    if len(fault_ids) != len(centers):
                        if verbose:
                            print(f"        ⚠️ Field '{field_name}' length mismatch, skipping")
                        continue

                    # Récupérer l'ID au point de départ
                    target_fault_id = fault_ids[start_idx]

                    if verbose:
                        unique_ids = np.unique(fault_ids)
                        print(f"        Found fault field: '{field_name}'")
                        print(f"        Available fault IDs: {unique_ids}")
                        print(f"        Target fault ID at start point: {target_fault_id}")

                    break

        # ===================================================================
        # ÉTAPE 3: FILTRER PAR FAILLE SI DÉTECTÉE
        # ===================================================================

        if target_fault_id is not None:
            # FILTRER: garder SEULEMENT cette faille
            mask_same_fault = (fault_ids == target_fault_id)
            n_total = len(centers)
            n_on_fault = np.sum(mask_same_fault)

            if verbose:
                print(f"        Filtering to fault ID={target_fault_id}: {n_on_fault}/{n_total} cells ({n_on_fault/n_total*100:.1f}%)")

            if n_on_fault == 0:
                print(f"        ⚠️ No cells found on target fault")
                return np.array([]), np.array([]), np.array([]), np.array([])

            # REMPLACER centers et values par le subset filtré
            centers = centers[mask_same_fault].copy()
            values = values[mask_same_fault].copy()

            # Trouver le nouvel index de départ dans le subset
            d_to_start = np.sqrt(np.sum((centers - start_point)**2, axis=1))
            start_idx = np.argmin(d_to_start)

            if verbose:
                print(f"        ✅ Profile will stay on fault ID={target_fault_id}")
        else:
            if verbose:
                print(f"        ⚠️ No fault identification field found")
                if cell_data is not None:
                    print(f"        Available fields: {list(cell_data.keys())}")
                else:
                    print(f"        cell_data not provided")
                print(f"        Profile may jump between faults!")

        # À partir d'ici, centers/values ne contiennent QUE la faille cible

        # ===================================================================
        # ÉTAPE 4: POSITION DE RÉFÉRENCE
        # ===================================================================

        ref_x = centers[start_idx, 0]
        ref_y = centers[start_idx, 1]

        if verbose:
            print(f"        Reference XY: ({ref_x:.1f}, {ref_y:.1f})")

        # ===================================================================
        # ÉTAPE 5: GÉOMÉTRIE DE LA FAILLE
        # ===================================================================

        x_range = np.max(centers[:, 0]) - np.min(centers[:, 0])
        y_range = np.max(centers[:, 1]) - np.min(centers[:, 1])
        z_range = np.max(centers[:, 2]) - np.min(centers[:, 2])

        if z_range <= 0:
            print(f"        ⚠️ Invalid z_range: {z_range}")
            return np.array([]), np.array([]), np.array([]), np.array([])

        lateral_extent = max(x_range, y_range)
        xy_tolerance = max(lateral_extent * 0.3, 100.0)

        if verbose:
            print(f"        Fault extent: X={x_range:.1f}m, Y={y_range:.1f}m, Z={z_range:.1f}m")
            print(f"        XY tolerance: {xy_tolerance:.1f}m")

        # ===================================================================
        # ÉTAPE 6: CALCUL DES TRANCHES
        # ===================================================================

        z_coords_sorted = np.sort(centers[:, 2])
        z_diffs = np.diff(z_coords_sorted)
        z_diffs_positive = z_diffs[z_diffs > 1e-6]

        if len(z_diffs_positive) == 0:
            if verbose:
                print(f"        ⚠️ All cells at same Z")

            d_xy = np.sqrt((centers[:, 0] - ref_x)**2 + (centers[:, 1] - ref_y)**2)
            sorted_indices = np.argsort(d_xy)

            return (centers[sorted_indices, 2],
                    values[sorted_indices],
                    centers[sorted_indices, 0],
                    centers[sorted_indices, 1])

        median_z_spacing = np.median(z_diffs_positive)

        # Vérifier que median_z_spacing est raisonnable
        if median_z_spacing <= 0 or median_z_spacing > z_range:
            median_z_spacing = z_range / 100  # Fallback

        # Taille de tranche = espacement médian
        slice_thickness = median_z_spacing

        z_min = np.min(centers[:, 2])
        z_max = np.max(centers[:, 2])

        n_slices = int(np.ceil(z_range / slice_thickness))
        n_slices = min(n_slices, 10000)  # Limiter à 10k tranches max

        if n_slices <= 0:
            print(f"        ⚠️ Invalid n_slices: {n_slices}")
            return np.array([]), np.array([]), np.array([]), np.array([])

        if verbose:
            print(f"        Median Z spacing: {median_z_spacing:.1f}m")
            print(f"        Creating {n_slices} slices")

        try:
            z_slices = np.linspace(z_max, z_min, n_slices + 1)
        except (MemoryError, ValueError) as e:
            print(f"        ⚠️ Error creating slices: {e}")
            return np.array([]), np.array([]), np.array([]), np.array([])

        # ===================================================================
        # ÉTAPE 7: EXTRACTION PAR TRANCHES
        # ===================================================================

        profile_indices = []

        for i in range(len(z_slices) - 1):
            z_top = z_slices[i]
            z_bottom = z_slices[i + 1]

            # Cellules dans cette tranche
            mask_in_slice = (centers[:, 2] <= z_top) & (centers[:, 2] >= z_bottom)
            indices_in_slice = np.where(mask_in_slice)[0]

            if len(indices_in_slice) == 0:
                continue

            # Distance XY à la référence
            d_xy_in_slice = np.sqrt(
                (centers[indices_in_slice, 0] - ref_x)**2 +
                (centers[indices_in_slice, 1] - ref_y)**2
            )

            # Ne garder que celles dans la tolérance XY
            valid_mask = d_xy_in_slice < xy_tolerance

            if not np.any(valid_mask):
                # Aucune dans la tolérance → prendre la plus proche
                closest_in_slice = indices_in_slice[np.argmin(d_xy_in_slice)]
            else:
                # Prendre la plus proche parmi celles dans la tolérance
                valid_indices = indices_in_slice[valid_mask]
                d_xy_valid = d_xy_in_slice[valid_mask]
                closest_in_slice = valid_indices[np.argmin(d_xy_valid)]

            profile_indices.append(closest_in_slice)

        # ===================================================================
        # ÉTAPE 8: SUPPRIMER DOUBLONS ET TRIER
        # ===================================================================

        # Supprimer doublons
        seen = set()
        unique_indices = []
        for idx in profile_indices:
            if idx not in seen:
                seen.add(idx)
                unique_indices.append(idx)

        if len(unique_indices) == 0:
            if verbose:
                print(f"        ⚠️ No points extracted")
            return np.array([]), np.array([]), np.array([]), np.array([])

        profile_indices = np.array(unique_indices)

        # Trier par profondeur décroissante (haut → bas)
        sort_order = np.argsort(-centers[profile_indices, 2])
        profile_indices = profile_indices[sort_order]

        # Extraire résultats
        depths = centers[profile_indices, 2]
        profile_values = values[profile_indices]
        path_x = centers[profile_indices, 0]
        path_y = centers[profile_indices, 1]

        # ===================================================================
        # STATISTIQUES
        # ===================================================================

        if verbose:
            depth_coverage = (depths.max() - depths.min()) / z_range * 100 if z_range > 0 else 0
            xy_displacement = np.sqrt((path_x[-1] - path_x[0])**2 + (path_y[-1] - path_y[0])**2)

            print(f"        ✅ Extracted {len(profile_indices)} points")
            print(f"           Depth range: [{depths.max():.1f}, {depths.min():.1f}]m")
            print(f"           Coverage: {depth_coverage:.1f}% of fault depth")
            print(f"           XY displacement: {xy_displacement:.1f}m")

        return (depths, profile_values, path_x, path_y)

    # -------------------------------------------------------------------
    @staticmethod
    def extract_vertical_profile_topology_based(surface_mesh, field_name, x_start, y_start, z_start=None,
                                               max_steps=500, verbose=True):
        """
        Extraction de profil vertical en utilisant la TOPOLOGIE du maillage de surface.
        """

        import pyvista as pv

        if field_name not in surface_mesh.cell_data:
            print(f"        ⚠️ Field '{field_name}' not found in mesh")
            return np.array([]), np.array([]), np.array([]), np.array([])

        centers = surface_mesh.cell_centers().points
        values = surface_mesh.cell_data[field_name]

        # ===================================================================
        # ÉTAPE 1: TROUVER LA CELLULE DE DÉPART
        # ===================================================================

        if z_start is None:
            if verbose:
                print(f"        Searching near ({x_start:.1f}, {y_start:.1f})")

            d_xy = np.sqrt((centers[:, 0] - x_start)**2 + (centers[:, 1] - y_start)**2)
            closest_indices = np.argsort(d_xy)[:20]

            if len(closest_indices) == 0:
                print(f"        ⚠️ No cells found")
                return np.array([]), np.array([]), np.array([]), np.array([])

            closest_depths = centers[closest_indices, 2]
            start_idx = closest_indices[np.argmax(closest_depths)]
        else:
            if verbose:
                print(f"        Searching near ({x_start:.1f}, {y_start:.1f}, {z_start:.1f})")

            d_3d = np.sqrt((centers[:, 0] - x_start)**2 +
                          (centers[:, 1] - y_start)**2 +
                          (centers[:, 2] - z_start)**2)
            start_idx = np.argmin(d_3d)

        start_point = centers[start_idx]

        if verbose:
            print(f"        Starting cell: {start_idx}")
            print(f"        Starting point: ({start_point[0]:.1f}, {start_point[1]:.1f}, {start_point[2]:.1f})")

        # ===================================================================
        # ÉTAPE 2: IDENTIFIER LA FAILLE
        # ===================================================================

        target_fault_id = None
        fault_ids = None
        fault_field_names = ['attribute', 'FaultMask', 'fault_id', 'region']

        for field_name_check in fault_field_names:
            if field_name_check in surface_mesh.cell_data:
                fault_ids = surface_mesh.cell_data[field_name_check]
                target_fault_id = fault_ids[start_idx]

                if verbose:
                    unique_ids = np.unique(fault_ids)
                    print(f"        Fault field: '{field_name_check}'")
                    print(f"        Target fault ID: {target_fault_id} (from {unique_ids})")

                break

        if target_fault_id is None and verbose:
            print(f"        ⚠️ No fault ID found - will use all cells")

        # ===================================================================
        # ÉTAPE 3: CONSTRUIRE LA CONNECTIVITÉ (VOISINS TOPOLOGIQUES)
        # ===================================================================

        if verbose:
            print(f"        Building cell connectivity...")

        n_cells = surface_mesh.n_cells
        connectivity = [[] for _ in range(n_cells)]

        # Construire un dictionnaire arête -> cellules
        edge_to_cells = {}

        for cell_id in range(n_cells):
            cell = surface_mesh.get_cell(cell_id)
            n_points = cell.n_points

            # Pour chaque arête de la cellule
            for i in range(n_points):
                p1 = cell.point_ids[i]
                p2 = cell.point_ids[(i + 1) % n_points]

                # Arête normalisée (ordre canonique)
                edge = tuple(sorted([p1, p2]))

                if edge not in edge_to_cells:
                    edge_to_cells[edge] = []
                edge_to_cells[edge].append(cell_id)

        # Pour chaque cellule, trouver ses voisins via arêtes partagées
        for cell_id in range(n_cells):
            cell = surface_mesh.get_cell(cell_id)
            n_points = cell.n_points

            neighbors_set = set()

            for i in range(n_points):
                p1 = cell.point_ids[i]
                p2 = cell.point_ids[(i + 1) % n_points]
                edge = tuple(sorted([p1, p2]))

                # Toutes les cellules partageant cette arête sont voisines
                for neighbor_id in edge_to_cells[edge]:
                    if neighbor_id != cell_id:
                        neighbors_set.add(neighbor_id)

            connectivity[cell_id] = list(neighbors_set)

        if verbose:
            avg_neighbors = np.mean([len(c) for c in connectivity])
            max_neighbors = np.max([len(c) for c in connectivity])
            print(f"        Connectivity built: avg={avg_neighbors:.1f} neighbors/cell, max={max_neighbors}")

        # ===================================================================
        # ÉTAPE 4: ALGORITHME DE DESCENTE PAR VOISINAGE TOPOLOGIQUE
        # ===================================================================

        profile_indices = [start_idx]
        visited = {start_idx}
        current_idx = start_idx

        ref_xy = start_point[:2]  # Position XY de référence

        if verbose:
            print(f"        Starting descent from Z={start_point[2]:.1f}m...")

        stuck_count = 0
        max_stuck = 3

        for step in range(max_steps):
            current_z = centers[current_idx, 2]

            # Obtenir les voisins topologiques
            neighbor_indices = connectivity[current_idx]

            # Filtrer les voisins:
            # 1. Non visités
            # 2. Même faille (si détectée)
            # 3. Plus bas en Z
            candidates = []

            for idx in neighbor_indices:
                if idx in visited:
                    continue

                # Vérifier la faille
                if target_fault_id is not None and fault_ids is not None:
                    if fault_ids[idx] != target_fault_id:
                        continue

                # Vérifier qu'on descend
                if centers[idx, 2] >= current_z:
                    continue

                candidates.append(idx)

            if len(candidates) == 0:
                # Si bloqué, essayer de regarder les voisins des voisins
                stuck_count += 1

                if stuck_count >= max_stuck:
                    if verbose:
                        print(f"        Reached bottom at Z={current_z:.1f}m after {step+1} steps (no more neighbors)")
                    break

                # Essayer niveau 2 (voisins des voisins)
                extended_candidates = []
                for neighbor_idx in neighbor_indices:
                    if neighbor_idx in visited:
                        continue

                    for second_neighbor_idx in connectivity[neighbor_idx]:
                        if second_neighbor_idx in visited:
                            continue

                        if target_fault_id is not None and fault_ids is not None:
                            if fault_ids[second_neighbor_idx] != target_fault_id:
                                continue

                        if centers[second_neighbor_idx, 2] < current_z:
                            extended_candidates.append(second_neighbor_idx)

                if len(extended_candidates) == 0:
                    if verbose:
                        print(f"        Reached bottom at Z={current_z:.1f}m (extended search failed)")
                    break

                candidates = extended_candidates
                if verbose:
                    print(f"        Used extended search at step {step+1}")
            else:
                stuck_count = 0

            # Parmi les candidats, choisir celui le plus proche en XY de la référence
            best_idx = None
            best_distance_xy = float('inf')

            for idx in candidates:
                pos = centers[idx]
                d_xy = np.sqrt((pos[0] - ref_xy[0])**2 + (pos[1] - ref_xy[1])**2)

                if d_xy < best_distance_xy:
                    best_distance_xy = d_xy
                    best_idx = idx

            if best_idx is None:
                if verbose:
                    print(f"        No valid neighbor at Z={current_z:.1f}m")
                break

            # Ajouter au profil
            profile_indices.append(best_idx)
            visited.add(best_idx)
            current_idx = best_idx

            # Debug
            if verbose and (step + 1) % 100 == 0:
                print(f"        Step {step+1}: Z={centers[current_idx, 2]:.1f}m, XY=({centers[current_idx, 0]:.1f}, {centers[current_idx, 1]:.1f})")

        # ===================================================================
        # ÉTAPE 5: EXTRAIRE LES RÉSULTATS
        # ===================================================================

        if len(profile_indices) == 0:
            if verbose:
                print(f"        ⚠️ No profile extracted")
            return np.array([]), np.array([]), np.array([]), np.array([])

        profile_indices = np.array(profile_indices)

        depths = centers[profile_indices, 2]
        profile_values = values[profile_indices]
        path_x = centers[profile_indices, 0]
        path_y = centers[profile_indices, 1]

        # ===================================================================
        # STATISTIQUES
        # ===================================================================

        if verbose:
            z_range = np.max(centers[:, 2]) - np.min(centers[:, 2])
            depth_coverage = (depths.max() - depths.min()) / z_range * 100 if z_range > 0 else 0
            xy_displacement = np.sqrt((path_x[-1] - path_x[0])**2 + (path_y[-1] - path_y[0])**2)

            print(f"        ✅ {len(profile_indices)} points extracted")
            print(f"           Depth range: [{depths.max():.1f}, {depths.min():.1f}]m")
            print(f"           Coverage: {depth_coverage:.1f}% of fault depth")
            print(f"           XY displacement: {xy_displacement:.1f}m")

        return (depths, profile_values, path_x, path_y)

    # -------------------------------------------------------------------
    @staticmethod
    def plot_profile_path_3d(surface, path_x, path_y, path_z, profile_values=None,
                             scalar_name='SCU', save_path=None, show=True):
        """
        Visualize the extracted profile path on the fault surface in 3D using PyVista.

        Parameters
        ----------
        surface : pyvista.PolyData
            Fault surface mesh
        path_x, path_y, path_z : array-like
            Coordinates of the profile path
        profile_values : array-like, optional
            Values along the profile (for coloring the path)
        scalar_name : str
            Name of the scalar to display on the surface
        save_path : Path or str, optional
            Path to save the screenshot
        show : bool
            Whether to display the plot interactively
        """
        import pyvista as pv

        if len(path_x) == 0:
            print("        ⚠️ No path to plot (empty profile)")
            return

        print(f"        📊 Creating 3D visualization of profile path ({len(path_x)} points)")

        # Create plotter
        plotter = pv.Plotter(window_size=[1600, 1200])

        # Add fault surface with scalar field
        if scalar_name in surface.cell_data:
            plotter.add_mesh(
                surface,
                scalars=scalar_name,
                cmap='RdYlGn_r',
                opacity=0.7,
                show_edges=False,
                lighting=True,
                smooth_shading=True,
                scalar_bar_args={
                    'title': scalar_name,
                    'title_font_size': 20,
                    'label_font_size': 16,
                    'n_labels': 5,
                    'italic': False,
                    'fmt': '%.2f',
                    'font_family': 'arial',
                }
            )
        else:
            plotter.add_mesh(
                surface,
                color='lightgray',
                opacity=0.5,
                show_edges=True
            )

        # Create path as a polyline
        path_points = np.column_stack([path_x, path_y, path_z])
        path_polyline = pv.PolyData(path_points)

        # Add connectivity for line
        n_points = len(path_points)
        lines = np.full((n_points - 1, 3), 2, dtype=np.int_)
        lines[:, 1] = np.arange(n_points - 1)
        lines[:, 2] = np.arange(1, n_points)
        path_polyline.lines = lines.ravel()

        # Color the path by profile values or depth
        if profile_values is not None:
            path_polyline['profile_value'] = profile_values
            color_field = 'profile_value'
            cmap_path = 'viridis'
        else:
            path_polyline['depth'] = path_z
            color_field = 'depth'
            cmap_path = 'turbo_r'

        # Add path as thick tube
        path_tube = path_polyline.tube(radius=10.0)  # Adjust radius as needed
        plotter.add_mesh(
            path_tube,
            scalars=color_field,
            cmap=cmap_path,
            line_width=8,
            render_lines_as_tubes=True,
            lighting=True,
            scalar_bar_args={
                'title': 'Path ' + color_field,
                'title_font_size': 20,
                'label_font_size': 16,
                'position_x': 0.85,
                'position_y': 0.05,
            }
        )

        # Add start and end markers
        start_point = pv.Sphere(radius=30, center=path_points[0])
        end_point = pv.Sphere(radius=30, center=path_points[-1])

        plotter.add_mesh(start_point, color='lime', label='Start (Top)')
        plotter.add_mesh(end_point, color='red', label='End (Bottom)')

        # Add axes and labels
        plotter.add_axes(
            xlabel='X [m]',
            ylabel='Y [m]',
            zlabel='Z [m]',
            line_width=3,
            labels_off=False
        )

        # Add legend
        plotter.add_legend(
            labels=[('Start (Top)', 'lime'), ('End (Bottom)', 'red')],
            bcolor='white',
            border=True,
            size=(0.15, 0.1),
            loc='upper left'
        )

        # Set camera and lighting
        plotter.camera_position = 'iso'
        plotter.add_light(pv.Light(position=(1, 1, 1), intensity=0.8))

        # Add title
        path_length = np.sum(np.sqrt(np.sum(np.diff(path_points, axis=0)**2, axis=1)))
        depth_range = path_z.max() - path_z.min()
        title = f'Profile Path Extraction\n'
        title += f'Points: {len(path_x)} | Length: {path_length:.1f}m | Depth range: {depth_range:.1f}m'
        plotter.add_text(title, position='upper_edge', font_size=14, color='black')

        # Save screenshot
        # if save_path is not None:
            # screenshot_path = save_path / 'profile_path_3d.png'
            # plotter.screenshot(str(screenshot_path))
            # print(f"        💾 Screenshot saved: {screenshot_path}")

        # Show
        if show:
            plotter.show()
        else:
            plotter.close()


# ============================================================================
# VISUALIZATION
# ============================================================================
class Visualizer:
    """Visualization utilities"""

    # -------------------------------------------------------------------
    def __init__(self, config):
        self.config = config

    # -------------------------------------------------------------------
    @staticmethod
    def plot_mohr_coulomb_diagram(surface, time, path, show=True, save=True):
        """Create Mohr-Coulomb diagram with depth coloring"""

        sigma_n = -surface.cell_data["sigma_n_eff"]
        tau = np.abs(surface.cell_data["tau_eff"])
        SCU = np.abs(surface.cell_data["SCU"])
        depth = surface.cell_data['elementCenter'][:, 2]

        cohesion = surface.cell_data["mohr_cohesion"][0]
        mu = surface.cell_data["mohr_friction_coefficient"][0]
        phi = surface.cell_data['mohr_friction_angle'][0]

        fig, axes = plt.subplots(1, 2, figsize=(16, 8))

        # Plot 1: τ vs σ_n
        ax1 = axes[0]
        sc1 = ax1.scatter(sigma_n, tau, c=depth, cmap='turbo_r', s=20, alpha=0.8)
        sigma_range = np.linspace(0, np.max(sigma_n), 100)
        tau_crit = cohesion + mu * sigma_range
        ax1.plot(sigma_range, tau_crit, 'k--', linewidth=2,
                label=f'M-C (C={cohesion} bar, φ={phi}°)')
        ax1.set_xlabel('Normal Stress [bar]')
        ax1.set_ylabel('Shear Stress [bar]')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        ax1.set_title('Mohr-Coulomb Diagram')

        # Plot 2: SCU vs σ_n
        ax2 = axes[1]
        sc2 = ax2.scatter(sigma_n, SCU, c=depth, cmap='turbo_r', s=20, alpha=0.8)
        ax2.axhline(y=1.0, color='r', linestyle='--', label='Failure (SCU=1)')
        ax2.set_xlabel('Normal Stress [bar]')
        ax2.set_ylabel('SCU [-]')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_title('Shear Capacity Utilization')
        ax2.set_ylim(bottom=0)

        plt.colorbar(sc2, ax=ax2, label='Depth [m]')
        plt.tight_layout()

        if save:
            years = time / (365.25 * 24 * 3600)
            filename = f'mohr_coulomb_phi{phi}_c{cohesion}_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  📊 Plot saved: {filename}")

        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    @staticmethod
    def load_reference_data(time, script_dir=None, profile_id=1):
        """
        Load GEOS and analytical reference data for comparison

        Parameters
        ----------
        time : float
            Current simulation time in seconds
        script_dir : str or Path, optional
            Directory containing reference data files. If None, uses current directory.
        profile_id : int, optional
            Profile ID to extract from Excel (default: 1)

        Returns
        -------
        dict
            Dictionary with keys 'geos' and 'analytical', each containing numpy arrays or None
            Format: {'geos': array or None, 'analytical': array or None}

            For GEOS data from Excel, the array has columns:
            [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU, X_coordinate_m, Y_coordinate_m]
        """
        import pandas as pd

        if script_dir is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))

        result = {'geos': None, 'analytical': None}

        # ===================================================================
        # LOAD GEOS DATA - Try Excel first, then CSV
        # ===================================================================

        geos_file_xlsx = 'geos_data_numerical.xlsx'
        geos_file_csv = 'geos_data_numerical.csv'

        # Try Excel format with time-based sheets
        geos_xlsx_path = os.path.join(script_dir, geos_file_xlsx)

        if os.path.exists(geos_xlsx_path):
            try:
                # Generate sheet name based on current time
                # Format: t_1.00e+02s
                sheet_name = f"t_{time:.2e}s"

                print(f"     📂 Loading GEOS data from Excel sheet: '{sheet_name}'")

                # Try to read the specific sheet
                try:
                    df = pd.read_excel(geos_xlsx_path, sheet_name=sheet_name)

                    # Filter by Profile_ID if column exists
                    if 'Profile_ID' in df.columns:
                        df_profile = df[df['Profile_ID'] == profile_id]

                        if len(df_profile) == 0:
                            print(f"        ⚠️  Profile_ID {profile_id} not found in sheet '{sheet_name}'")
                            print(f"        Available Profile_IDs: {sorted(df['Profile_ID'].unique())}")
                            # Take first profile as fallback
                            available_ids = sorted(df['Profile_ID'].unique())
                            if len(available_ids) > 0:
                                fallback_id = available_ids[0]
                                print(f"        → Using Profile_ID {fallback_id} instead")
                                df_profile = df[df['Profile_ID'] == fallback_id]
                        else:
                            print(f"        ✅ Loaded Profile_ID {profile_id}: {len(df_profile)} points")

                        # Extract relevant columns in the expected order
                        # Expected: [Depth, Normal_Stress, Shear_Stress, SCU, ...]
                        columns_to_extract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']

                        # Check which columns exist
                        available_columns = [col for col in columns_to_extract if col in df_profile.columns]

                        if len(available_columns) > 0:
                            result['geos'] = df_profile[available_columns].values
                            print(f"        Extracted columns: {available_columns}")
                        else:
                            print(f"        ⚠️  No expected columns found in DataFrame")
                            print(f"        Available columns: {list(df_profile.columns)}")
                    else:
                        # No Profile_ID column, use all data
                        print(f"        ℹ️  No Profile_ID column, using all data")
                        columns_to_extract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']
                        available_columns = [col for col in columns_to_extract if col in df.columns]

                        if len(available_columns) > 0:
                            result['geos'] = df[available_columns].values
                            print(f"        ✅ Loaded {len(result['geos'])} points")

                except ValueError:
                    # Sheet not found, try to find closest time
                    print(f"        ⚠️  Sheet '{sheet_name}' not found, searching for closest time...")

                    # Read all sheet names
                    xl_file = pd.ExcelFile(geos_xlsx_path)
                    sheet_names = xl_file.sheet_names

                    # Extract times from sheet names
                    sheet_times = []
                    for sname in sheet_names:
                        if sname.startswith('t_') and sname.endswith('s'):
                            try:
                                # Extract time: t_1.00e+02s -> 100.0
                                time_str = sname[2:-1]  # Remove 't_' and 's'
                                sheet_time = float(time_str)
                                sheet_times.append((sheet_time, sname))
                            except:
                                continue

                    if sheet_times:
                        # Find closest time
                        sheet_times.sort(key=lambda x: abs(x[0] - time))
                        closest_time, closest_sheet = sheet_times[0]
                        time_diff = abs(closest_time - time)

                        print(f"        → Using closest sheet: '{closest_sheet}' (Δt={time_diff:.2e}s)")
                        df = pd.read_excel(geos_xlsx_path, sheet_name=closest_sheet)

                        # Filter by Profile_ID
                        if 'Profile_ID' in df.columns:
                            df_profile = df[df['Profile_ID'] == profile_id]

                            if len(df_profile) == 0:
                                # Fallback to first profile
                                available_ids = sorted(df['Profile_ID'].unique())
                                if len(available_ids) > 0:
                                    df_profile = df[df['Profile_ID'] == available_ids[0]]
                                    print(f"        → Using Profile_ID {available_ids[0]}")

                            columns_to_extract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']
                            available_columns = [col for col in columns_to_extract if col in df_profile.columns]

                            if len(available_columns) > 0:
                                result['geos'] = df_profile[available_columns].values
                                print(f"        ✅ Loaded {len(result['geos'])} points")
                        else:
                            # Use all data
                            columns_to_extract = ['Depth_m', 'Normal_Stress_bar', 'Shear_Stress_bar', 'SCU']
                            available_columns = [col for col in columns_to_extract if col in df.columns]

                            if len(available_columns) > 0:
                                result['geos'] = df[available_columns].values
                                print(f"        ✅ Loaded {len(result['geos'])} points")
                    else:
                        print(f"        ⚠️  No valid time sheets found in Excel file")

            except ImportError:
                print(f"        ⚠️  pandas not available, cannot read Excel file")
            except Exception as e:
                print(f"        ⚠️  Error reading Excel: {e}")
                import traceback
                traceback.print_exc()

        # Fallback to CSV if Excel not found or failed
        if result['geos'] is None:
            geos_csv_path = os.path.join(script_dir, geos_file_csv)
            if os.path.exists(geos_csv_path):
                try:
                    result['geos'] = np.loadtxt(geos_csv_path, delimiter=',', skiprows=1)
                    print(f"     ✅ GEOS data loaded from CSV: {len(result['geos'])} points")
                except Exception as e:
                    print(f"     ⚠️  Error reading CSV: {e}")

        # ===================================================================
        # LOAD ANALYTICAL DATA
        # ===================================================================

        analytical_file = 'analytical_data.csv'
        analytical_path = os.path.join(script_dir, analytical_file)

        if os.path.exists(analytical_path):
            try:
                result['analytical'] = np.loadtxt(analytical_path, delimiter=',', skiprows=1)
                print(f"     ✅ Analytical data loaded: {len(result['analytical'])} points")
            except Exception as e:
                print(f"     ⚠️  Error loading analytical data: {e}")

        return result

    # -------------------------------------------------------------------
    @staticmethod
    def plot_depth_profiles(self, surface, time, path, show=True, save=True,
        profile_start_points=None,
        max_profile_points=1000,
        reference_profile_id=1
        ):

        """
        Plot vertical profiles along the fault showing stress and SCU vs depth
        """

        print("  📊 Creating depth profiles ")

        # Extract data
        centers = surface.cell_data['elementCenter']
        depth = centers[:, 2]
        sigma_n = surface.cell_data['sigma_n_eff']
        tau = surface.cell_data['tau_eff']
        SCU = surface.cell_data['SCU']
        SCU = np.sqrt(SCU**2)
        delta_SCU = surface.cell_data['delta_SCU']

        # Extraire les IDs de faille
        fault_ids = None
        if 'FaultMask' in surface.cell_data:
            fault_ids = surface.cell_data['FaultMask']
            print(f"  📋 Detected {len(np.unique(fault_ids[fault_ids > 0]))} distinct faults")
        elif 'attribute' in surface.cell_data:
            fault_ids = surface.cell_data['attribute']
            print(f"  📋 Using 'attribute' field for fault identification")
        else:
            print(f"  ⚠️ No fault IDs found - profiles may jump between faults")

        # ===================================================================
        # LOAD REFERENCE DATA (GEOS + Analytical)
        # ===================================================================
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reference_data = Visualizer.load_reference_data(
            time,
            script_dir,
            profile_id=reference_profile_id
        )

        geos_data = reference_data['geos']
        analytical_data = reference_data['analytical']

        # ===================================================================
        # PROFILE EXTRACTION SETUP
        # ===================================================================

        # Get fault bounds
        x_min, x_max = np.min(centers[:, 0]), np.max(centers[:, 0])
        y_min, y_max = np.min(centers[:, 1]), np.max(centers[:, 1])
        z_min, z_max = np.min(depth), np.max(depth)

        # Auto-compute search radius if not provided
        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min

        if self.config.PROFILE_SEARCH_RADIUS is not None:
            search_radius = self.config.PROFILE_SEARCH_RADIUS
        else:
            search_radius = min(x_range, y_range) * 0.15


        # Auto-generate profile points if not provided
        if profile_start_points is None:
            print("  ⚠️  No profile_start_points provided, auto-generating 5 profiles...")
            n_profiles = 5

            # Determine dominant fault direction
            if x_range > y_range:
                coord_name = 'X'
                fixed_value = (y_min + y_max) / 2
                sample_positions = np.linspace(x_min, x_max, n_profiles)
                profile_start_points = [(x, fixed_value) for x in sample_positions]
            else:
                coord_name = 'Y'
                fixed_value = (x_min + x_max) / 2
                sample_positions = np.linspace(y_min, y_max, n_profiles)
                profile_start_points = [(fixed_value, y) for y in sample_positions]

            print(f"     Auto-generated {n_profiles} profiles along {coord_name} direction")

        n_profiles = len(profile_start_points)

        # ===================================================================
        # CREATE FIGURE
        # ===================================================================

        fig, axes = plt.subplots(1, 4, figsize=(24, 12))
        colors = plt.cm.RdYlGn(np.linspace(0, 1, n_profiles))

        print(f"  📍 Processing {n_profiles} profiles:")
        print(f"     Depth range: [{z_min:.1f}, {z_max:.1f}]m")

        successful_profiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES
        # ===================================================================

        for i, (x_pos, y_pos, z_pos) in enumerate(profile_start_points):
            print(f"     → Profile {i+1}: starting at ({x_pos:.1f}, {y_pos:.1f}, {z_pos:.1f})")

            # depths_sigma, profile_sigma_n, path_x_s, path_y_s = ProfileExtractor.extract_vertical_profile_topology_based(
            #         surface, 'sigma_n_eff', x_pos, y_pos, z_pos, verbose=True)

            # depths_tau, profile_tau, _, _ = ProfileExtractor.extract_vertical_profile_topology_based(
            #         surface, 'tau_eff', x_pos, y_pos, z_pos, verbose=False)

            # depths_SCU, profile_SCU, _, _ = ProfileExtractor.extract_vertical_profile_topology_based(
            #         surface, 'SCU', x_pos, y_pos, z_pos, verbose=False)

            # depths_deltaSCU, profile_deltaSCU, _, _ = ProfileExtractor.extract_vertical_profile_topology_based(
            #         surface, 'delta_SCU', x_pos, y_pos, z_pos, verbose=False)

            depths_sigma, profile_sigma_n, path_x_s, path_y_s = ProfileExtractor.extract_adaptive_profile(
                centers, sigma_n, x_pos, y_pos, search_radius)

            depths_tau, profile_tau, _, _ = ProfileExtractor.extract_adaptive_profile(
                centers, tau, x_pos, y_pos, search_radius)

            depths_SCU, profile_SCU, _, _ = ProfileExtractor.extract_adaptive_profile(
                centers, SCU, x_pos, y_pos, search_radius)

            depths_deltaSCU, profile_deltaSCU, _, _ = ProfileExtractor.extract_adaptive_profile(
                centers, SCU, x_pos, y_pos, search_radius)

            # Calculate path length
            if len(path_x_s) > 1:
                path_length = np.sum(np.sqrt(
                    np.diff(path_x_s)**2 +
                    np.diff(path_y_s)**2 +
                    np.diff(depths_sigma)**2
                ))
                print(f"        Path length: {path_length:.1f}m (horizontal displacement: {np.abs(path_x_s[-1] - path_x_s[0]):.1f}m)")

                if self.config.SHOW_PROFILE_EXTRACTOR:
                    ProfileExtractor.plot_profile_path_3d(
                        surface=surface,
                        path_x=path_x_s,
                        path_y=path_y_s,
                        path_z=depths_sigma,
                        profile_values=profile_sigma_n,
                        scalar_name='SCU',
                        save_path=path,
                        show=show
                    )

            # Check if we have enough points
            min_points = 3
            n_points = len(depths_sigma)

            if n_points >= min_points:
                label = f'Profile {i+1} → ({x_pos:.0f}, {y_pos:.0f})'

                # Plot 1: Normal stress vs depth
                axes[0].plot(profile_sigma_n, depths_sigma,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 2: Shear stress vs depth
                axes[1].plot(profile_tau, depths_tau,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 3: SCU vs depth
                axes[2].plot(profile_SCU, depths_SCU,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                # Plot 4: Detla SCU vs depth
                axes[3].plot(profile_deltaSCU, depths_deltaSCU,
                            color=colors[i], label=label, linewidth=2.5, alpha=0.8,
                            marker='o', markersize=3, markevery=2)

                successful_profiles += 1
                print(f"        ✅ {n_points} points found")
            else:
                print(f"        ⚠️  Insufficient points ({n_points}), skipping")

        if successful_profiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # ADD REFERENCE DATA (GEOS + Analytical) - Only once
        # ===================================================================

        if geos_data is not None:
            # Colonnes: [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU]
            # Index:    [0,       1,                 2,                 3]

            axes[0].plot(geos_data[:, 1] *10, geos_data[:, 0], 'o',
                        color='blue', markersize=6, label='GEOS Contact Solver',
                        alpha=0.7, mec='k', mew=1, fillstyle='none')

            axes[1].plot(geos_data[:, 2] *10, geos_data[:, 0], 'o',
                        color='blue', markersize=6, label='GEOS Contact Solver',
                        alpha=0.7, mec='k', mew=1, fillstyle='none')

            if geos_data.shape[1] > 3:  # SCU column exists
                axes[2].plot(geos_data[:, 3], geos_data[:, 0], 'o',
                            color='blue', markersize=6, label='GEOS Contact Solver',
                            alpha=0.7, mec='k', mew=1, fillstyle='none')

        if analytical_data is not None:
            # Format analytique (peut varier)
            axes[0].plot(analytical_data[:, 1] * 10, analytical_data[:, 0], '--',
                        color='darkorange', linewidth=2, label='Analytical', alpha=0.8)
            if analytical_data.shape[1] > 2:
                axes[1].plot(analytical_data[:, 2] * 10, analytical_data[:, 0], '--',
                            color='darkorange', linewidth=2, label='Analytical', alpha=0.8)

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 1: Normal Stress
        axes[0].set_xlabel('Normal Stress σₙ [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].set_title('Normal Stress Profile', fontsize=fsize+2, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='upper left', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-2)

        # Plot 2: Shear Stress
        axes[1].set_xlabel('Shear Stress τ [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].set_title('Shear Stress Profile', fontsize=fsize+2, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='upper left', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-2)

        # Plot 3: SCU
        axes[2].set_xlabel('SCU [-]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].set_title('Shear Capacity Utilization', fontsize=fsize+2, weight="bold")
        axes[2].axvline(x=0.8, color='forestgreen', linestyle='--', linewidth=2, label='Critical (0.8)')
        axes[2].axvline(x=1.0, color='red', linestyle='--', linewidth=2, label='Failure (1.0)')
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='upper right', fontsize=fsize-2)
        axes[2].tick_params(labelsize=fsize-2)
        axes[2].set_xlim(left=0)

        # Plot 4: Delta SCU
        axes[3].set_xlabel('Δ SCU [-]', fontsize=fsize, weight="bold")
        axes[3].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[3].set_title('Delta SCU', fontsize=fsize+2, weight="bold")
        axes[3].grid(True, alpha=0.3, linestyle='--')
        axes[3].legend(loc='upper right', fontsize=fsize-2)
        axes[3].tick_params(labelsize=fsize-2)
        axes[3].set_xlim(left=0, right=2)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Fault Depth Profiles - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save
        if save:
            filename = f'depth_profiles_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  💾 Depth profiles saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    def plot_volume_stress_profiles(self, volume_mesh, fault_surface, time, path,
                                    show=True, save=True,
                                    profile_start_points=None,
                                    max_profile_points=1000):
        """
        Plot stress profiles in volume cells adjacent to the fault
        Extracts profiles through contributing cells on BOTH sides of the fault
        Shows plus side and minus side on the same plots for comparison

        NOTE: Cette fonction utilise extract_adaptive_profile pour les VOLUMES
        car volume_mesh n'est PAS un maillage surfacique.
        La méthode topologique (extract_vertical_profile_topology_based)
        est réservée aux maillages SURFACIQUES (fault_surface).
        """

        print("  📊 Creating volume stress profiles (both sides)")

        # ===================================================================
        # CHECK IF REQUIRED DATA EXISTS
        # ===================================================================

        required_fields = ['sigma1', 'sigma2', 'sigma3', 'side', 'elementCenter']

        for field in required_fields:
            if field not in volume_mesh.cell_data:
                print(f"  ⚠️  Missing required field: {field}")
                return

        # Check for pressure
        if 'pressure_bar' in volume_mesh.cell_data:
            pressure_field = 'pressure_bar'
            pressure = volume_mesh.cell_data[pressure_field]
        elif 'pressure' in volume_mesh.cell_data:
            pressure_field = 'pressure'
            pressure = volume_mesh.cell_data[pressure_field] / 1e5
            print("  ℹ️  Converting pressure from Pa to bar")
        else:
            print("  ⚠️  No pressure field found")
            pressure = None

        # Extract volume data
        centers = volume_mesh.cell_data['elementCenter']
        sigma1 = volume_mesh.cell_data['sigma1']
        sigma2 = volume_mesh.cell_data['sigma2']
        sigma3 = volume_mesh.cell_data['sigma3']
        side_data = volume_mesh.cell_data['side']

        # ===================================================================
        # FILTER CELLS BY SIDE (BOTH PLUS AND MINUS)
        # ===================================================================

        # Plus side (side = 1 or 3)
        mask_plus = (side_data == 1) | (side_data == 3)
        centers_plus = centers[mask_plus]
        sigma1_plus = sigma1[mask_plus]
        sigma2_plus = sigma2[mask_plus]
        sigma3_plus = sigma3[mask_plus]
        if pressure is not None:
            pressure_plus = pressure[mask_plus]

        # Créer subset de cell_data pour le côté plus
        cell_data_plus = {}
        for key in volume_mesh.cell_data.keys():
            cell_data_plus[key] = volume_mesh.cell_data[key][mask_plus]

        # Minus side (side = 2 or 3)
        mask_minus = (side_data == 2) | (side_data == 3)
        centers_minus = centers[mask_minus]
        sigma1_minus = sigma1[mask_minus]
        sigma2_minus = sigma2[mask_minus]
        sigma3_minus = sigma3[mask_minus]
        if pressure is not None:
            pressure_minus = pressure[mask_minus]

        # Créer subset de cell_data pour le côté minus
        cell_data_minus = {}
        for key in volume_mesh.cell_data.keys():
            cell_data_minus[key] = volume_mesh.cell_data[key][mask_minus]

        print(f"  📍 Plus side: {len(centers_plus):,} cells")
        print(f"  📍 Minus side: {len(centers_minus):,} cells")

        if len(centers_plus) == 0 and len(centers_minus) == 0:
            print("  ⚠️  No contributing cells found!")
            return

        # ===================================================================
        # GET FAULT BOUNDS
        # ===================================================================

        fault_centers = fault_surface.cell_data['elementCenter']

        x_min, x_max = np.min(fault_centers[:, 0]), np.max(fault_centers[:, 0])
        y_min, y_max = np.min(fault_centers[:, 1]), np.max(fault_centers[:, 1])
        z_min, z_max = np.min(fault_centers[:, 2]), np.max(fault_centers[:, 2])

        x_range = x_max - x_min
        y_range = y_max - y_min
        z_range = z_max - z_min

        # Search radius (pour extract_adaptive_profile sur volumes)
        if self.config.PROFILE_SEARCH_RADIUS is not None:
            search_radius = self.config.PROFILE_SEARCH_RADIUS
        else:
            search_radius = min(x_range, y_range) * 0.2

        # ===================================================================
        # AUTO-GENERATE PROFILE POINTS IF NOT PROVIDED
        # ===================================================================

        if profile_start_points is None:
            print("  ⚠️  No profile_start_points provided, auto-generating...")
            n_profiles = 3

            if x_range > y_range:
                coord_name = 'X'
                fixed_value = (y_min + y_max) / 2
                sample_positions = np.linspace(x_min, x_max, n_profiles)
                profile_start_points = [(x, fixed_value, z_max) for x in sample_positions]
            else:
                coord_name = 'Y'
                fixed_value = (x_min + x_max) / 2
                sample_positions = np.linspace(y_min, y_max, n_profiles)
                profile_start_points = [(fixed_value, y, z_max) for y in sample_positions]

            print(f"     Auto-generated {n_profiles} profiles along {coord_name}")

        n_profiles = len(profile_start_points)

        # ===================================================================
        # CREATE FIGURE WITH 5 SUBPLOTS
        # ===================================================================

        fig, axes = plt.subplots(1, 5, figsize=(22, 10))

        # Colors: different for plus and minus sides
        colors_plus = plt.cm.Reds(np.linspace(0.4, 0.9, n_profiles))
        colors_minus = plt.cm.Blues(np.linspace(0.4, 0.9, n_profiles))

        print(f"  📍 Processing {n_profiles} volume profiles:")
        print(f"     Depth range: [{z_min:.1f}, {z_max:.1f}]m")

        successful_profiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES FOR BOTH SIDES
        # ===================================================================

        for i, (x_pos, y_pos, z_pos) in enumerate(profile_start_points):
            print(f"\n     → Profile {i+1}: starting at ({x_pos:.1f}, {y_pos:.1f}, {z_pos:.1f})")

            # ================================================================
            # PLUS SIDE
            # ================================================================
            if len(centers_plus) > 0:
                print(f"        Processing PLUS side...")

                # Pour VOLUMES, utiliser extract_adaptive_profile avec cell_data
                depths_s1_p, profile_s1_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_plus, sigma1_plus, x_pos, y_pos, z_pos,
                    search_radius, verbose=True, cell_data=cell_data_plus)

                depths_s2_p, profile_s2_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_plus, sigma2_plus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False, cell_data=cell_data_plus)

                depths_s3_p, profile_s3_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_plus, sigma3_plus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False, cell_data=cell_data_plus)

                if pressure is not None:
                    depths_p_p, profile_p_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                        centers_plus, pressure_plus, x_pos, y_pos, z_pos,
                        search_radius, verbose=False, cell_data=cell_data_plus)

                if len(depths_s1_p) >= 3:
                    label_plus = f'Plus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[0].plot(profile_p_p, depths_p_p,
                                    color=colors_plus[i], label=label_plus if i == 0 else '',
                                    linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ1
                    axes[1].plot(profile_s1_p, depths_s1_p,
                                color=colors_plus[i], label=label_plus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ2
                    axes[2].plot(profile_s2_p, depths_s2_p,
                                color=colors_plus[i], label=label_plus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot σ3
                    axes[3].plot(profile_s3_p, depths_s3_p,
                                color=colors_plus[i], label=label_plus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='o', markersize=3, markevery=2)

                    # Plot All stresses
                    axes[4].plot(profile_s1_p, depths_s1_p,
                                color=colors_plus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="o", markersize=2, markevery=2)
                    axes[4].plot(profile_s2_p, depths_s2_p,
                                color=colors_plus[i], linewidth=2.0, alpha=0.6,
                                linestyle='-', marker="s", markersize=2, markevery=2)
                    axes[4].plot(profile_s3_p, depths_s3_p,
                                color=colors_plus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="v", markersize=2, markevery=2)

                    print(f"        ✅ PLUS: {len(depths_s1_p)} points")
                    successful_profiles += 1

            # ================================================================
            # MINUS SIDE
            # ================================================================
            if len(centers_minus) > 0:
                print(f"        Processing MINUS side...")

                # Pour VOLUMES, utiliser extract_adaptive_profile avec cell_data
                depths_s1_m, profile_s1_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_minus, sigma1_minus, x_pos, y_pos, z_pos,
                    search_radius, verbose=True, cell_data=cell_data_minus)

                depths_s2_m, profile_s2_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_minus, sigma2_minus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False, cell_data=cell_data_minus)

                depths_s3_m, profile_s3_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_minus, sigma3_minus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False, cell_data=cell_data_minus)

                if pressure is not None:
                    depths_p_m, profile_p_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                        centers_minus, pressure_minus, x_pos, y_pos, z_pos,
                        search_radius, verbose=False, cell_data=cell_data_minus)

                if len(depths_s1_m) >= 3:
                    label_minus = f'Minus side'

                    # Plot Pressure
                    if pressure is not None:
                        axes[0].plot(profile_p_m, depths_p_m,
                                    color=colors_minus[i], label=label_minus if i == 0 else '',
                                    linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ1
                    axes[1].plot(profile_s1_m, depths_s1_m,
                                color=colors_minus[i], label=label_minus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ2
                    axes[2].plot(profile_s2_m, depths_s2_m,
                                color=colors_minus[i], label=label_minus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot σ3
                    axes[3].plot(profile_s3_m, depths_s3_m,
                                color=colors_minus[i], label=label_minus if i == 0 else '',
                                linewidth=2.5, alpha=0.8, marker='s', markersize=3, markevery=2)

                    # Plot All stresses
                    axes[4].plot(profile_s1_m, depths_s1_m,
                                color=colors_minus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker="o", markersize=2, markevery=2)
                    axes[4].plot(profile_s2_m, depths_s2_m,
                                color=colors_minus[i], linewidth=2.0, alpha=0.6,
                                linestyle='-', marker="s", markersize=2, markevery=2)
                    axes[4].plot(profile_s3_m, depths_s3_m,
                                color=colors_minus[i], linewidth=2.5, alpha=0.8,
                                linestyle='-', marker='v', markersize=2, markevery=2)

                    print(f"        ✅ MINUS: {len(depths_s1_m)} points")
                    successful_profiles += 1

        if successful_profiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 0: Pressure
        axes[0].set_xlabel('Pressure [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='best', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-2)

        if pressure is None:
            axes[0].text(0.5, 0.5, 'No pressure data available',
                        ha='center', va='center', transform=axes[0].transAxes,
                        fontsize=fsize, style='italic', color='gray')

        # Plot 1: σ1 (Maximum principal stress)
        axes[1].set_xlabel('σ₁ (Max Principal) [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='best', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-2)

        # Plot 2: σ2 (Intermediate principal stress)
        axes[2].set_xlabel('σ₂ (Inter Principal) [bar]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='best', fontsize=fsize-2)
        axes[2].tick_params(labelsize=fsize-2)

        # Plot 3: σ3 (Min principal stress)
        axes[3].set_xlabel('σ₃ (Min Principal) [bar]', fontsize=fsize, weight="bold")
        axes[3].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[3].grid(True, alpha=0.3, linestyle='--')
        axes[3].legend(loc='best', fontsize=fsize-2)
        axes[3].tick_params(labelsize=fsize-2)

        # Plot 4: All stresses together
        axes[4].set_xlabel('Principal Stresses [bar]', fontsize=fsize, weight="bold")
        axes[4].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[4].grid(True, alpha=0.3, linestyle='--')
        axes[4].tick_params(labelsize=fsize-2)

        # Add legend for line styles
        from matplotlib.lines import Line2D
        custom_lines = [
            Line2D([0], [0], color='red', linewidth=2.5, marker=None, label='Plus side', alpha=0.5),
            Line2D([0], [0], color='blue', linewidth=2.5, marker=None, label='Minus side', alpha=0.5),
            Line2D([0], [0], color='gray', linewidth=2.5, linestyle='-', marker='o', label='σ₁ (max)'),
            Line2D([0], [0], color='gray', linewidth=2.0, linestyle='-', marker='s', label='σ₂ (inter)'),
            Line2D([0], [0], color='gray', linewidth=2.5, linestyle='-', marker='v', label='σ₃ (min)')
        ]
        axes[4].legend(handles=custom_lines, loc='best', fontsize=fsize-3, ncol=1)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Volume Stress Profiles - Both Sides Comparison - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.98)

        plt.tight_layout(rect=[0, 0, 1, 0.96])

        # Save
        if save:
            filename = f'volume_stress_profiles_both_sides_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"  💾 Volume profiles saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()

    # -------------------------------------------------------------------
    def plot_analytical_vs_numerical_comparison(self, volume_mesh, fault_surface, time, path,
                                               show=True, save=True,
                                               profile_start_points=None,
                                               reference_profile_id=1):
        """
        Plot comparison between analytical fault stresses (Anderson formulas)
        and numerical tensor projection - COMBINED PLOTS ONLY

        Parameters
        ----------
        volume_mesh : pyvista.UnstructuredGrid
            Volume mesh with principal stresses AND analytical stresses
        fault_surface : pyvista.PolyData
            Fault surface mesh with projected stresses
        time : float
            Simulation time
        path : Path
            Output directory
        show : bool
            Show plot interactively
        save : bool
            Save plot to file
        profile_start_points : list of tuples
            Starting points (x, y, z) for profiles
        reference_profile_id : int
            Which profile ID to load from Excel reference data
        """

        print("\n  📊 Creating Analytical vs Numerical Comparison")

        # ===================================================================
        # CHECK IF ANALYTICAL DATA EXISTS
        # ===================================================================

        required_analytical = ['sigma_n_analytical', 'tau_analytical', 'side', 'elementCenter']

        for field in required_analytical:
            if field not in volume_mesh.cell_data:
                print(f"  ⚠️  Missing analytical field: {field}")
                print(f"      Analytical stresses not computed in volume mesh")
                return

        # Check numerical data on fault surface
        if 'sigma_n_eff' not in fault_surface.cell_data:
            print(f"  ⚠️  Missing numerical stress data on fault surface")
            return

        # ===================================================================
        # LOAD REFERENCE DATA (GEOS Contact Solver)
        # ===================================================================

        print("  📂 Loading GEOS Contact Solver reference data...")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        reference_data = Visualizer.load_reference_data(
            time,
            script_dir,
            profile_id=reference_profile_id
        )

        geos_contact_data = reference_data.get('geos', None)

        if geos_contact_data is not None:
            print(f"     ✅ Loaded {len(geos_contact_data)} reference points from GEOS Contact Solver")
        else:
            print(f"     ⚠️  No GEOS Contact Solver reference data found")

        # Extraire les IDs de faille
        fault_ids_volume = None
        fault_ids_surface = None

        if 'fault_id' in volume_mesh.cell_data:
            fault_ids_volume = volume_mesh.cell_data['fault_id']

        if 'FaultMask' in fault_surface.cell_data:
            fault_ids_surface = fault_surface.cell_data['FaultMask']
        elif 'attribute' in fault_surface.cell_data:
            fault_ids_surface = fault_surface.cell_data['attribute']

        # ===================================================================
        # EXTRACT DATA
        # ===================================================================

        # Volume analytical data
        centers_volume = volume_mesh.cell_data['elementCenter']
        side_data = volume_mesh.cell_data['side']
        sigma_n_analytical = volume_mesh.cell_data['sigma_n_analytical']
        tau_analytical = volume_mesh.cell_data['tau_analytical']

        # Optional: SCU if available
        has_SCU_analytical = 'SCU_analytical' in volume_mesh.cell_data
        if has_SCU_analytical:
            SCU_analytical = volume_mesh.cell_data['SCU_analytical']

        # Fault numerical data
        centers_fault = fault_surface.cell_data['elementCenter']
        sigma_n_numerical = fault_surface.cell_data['sigma_n_eff']
        tau_numerical = fault_surface.cell_data['tau_eff']

        # Optional: SCU numerical
        has_SCU_numerical = 'SCU' in fault_surface.cell_data
        if has_SCU_numerical:
            SCU_numerical = fault_surface.cell_data['SCU']

        # Filter volume by side
        mask_plus = (side_data == 1) | (side_data == 3)
        mask_minus = (side_data == 2) | (side_data == 3)

        centers_plus = centers_volume[mask_plus]
        sigma_n_analytical_plus = sigma_n_analytical[mask_plus]
        tau_analytical_plus = tau_analytical[mask_plus]
        if has_SCU_analytical:
            SCU_analytical_plus = SCU_analytical[mask_plus]

        centers_minus = centers_volume[mask_minus]
        sigma_n_analytical_minus = sigma_n_analytical[mask_minus]
        tau_analytical_minus = tau_analytical[mask_minus]
        if has_SCU_analytical:
            SCU_analytical_minus = SCU_analytical[mask_minus]

        print(f"  📍 Plus side: {len(centers_plus):,} cells with analytical data")
        print(f"  📍 Minus side: {len(centers_minus):,} cells with analytical data")
        print(f"  📍 Fault surface: {len(centers_fault):,} cells with numerical data")

        # ===================================================================
        # GET FAULT BOUNDS AND PROFILE SETUP
        # ===================================================================

        x_min, x_max = np.min(centers_fault[:, 0]), np.max(centers_fault[:, 0])
        y_min, y_max = np.min(centers_fault[:, 1]), np.max(centers_fault[:, 1])
        z_min, z_max = np.min(centers_fault[:, 2]), np.max(centers_fault[:, 2])

        x_range = x_max - x_min
        y_range = y_max - y_min

        # Search radius
        if self.config.PROFILE_SEARCH_RADIUS is not None:
            search_radius = self.config.PROFILE_SEARCH_RADIUS
        else:
            search_radius = min(x_range, y_range) * 0.2

        # Auto-generate profile points if not provided
        if profile_start_points is None:
            print("  ⚠️  No profile_start_points provided, auto-generating...")
            n_profiles = 3

            if x_range > y_range:
                coord_name = 'X'
                fixed_value = (y_min + y_max) / 2
                sample_positions = np.linspace(x_min, x_max, n_profiles)
                profile_start_points = [(x, fixed_value, z_max) for x in sample_positions]
            else:
                coord_name = 'Y'
                fixed_value = (x_min + x_max) / 2
                sample_positions = np.linspace(y_min, y_max, n_profiles)
                profile_start_points = [(fixed_value, y, z_max) for y in sample_positions]

            print(f"     Auto-generated {n_profiles} profiles along {coord_name}")

        n_profiles = len(profile_start_points)

        # ===================================================================
        # CREATE FIGURE: COMBINED PLOTS ONLY
        # 3 columns (σ_n, τ, SCU) x 1 row
        # ===================================================================

        fig, axes = plt.subplots(1, 3, figsize=(18, 10))

        print(f"  📍 Processing {n_profiles} profiles for comparison:")

        successful_profiles = 0

        # ===================================================================
        # EXTRACT AND PLOT PROFILES
        # ===================================================================

        for i, (x_pos, y_pos, z_pos) in enumerate(profile_start_points):
            print(f"\n     → Profile {i+1}: starting at ({x_pos:.1f}, {y_pos:.1f}, {z_pos:.1f})")

            # ================================================================
            # PLUS SIDE - ANALYTICAL
            # ================================================================
            if len(centers_plus) > 0:
                depths_sn_ana_p, profile_sn_ana_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_plus, sigma_n_analytical_plus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False)

                depths_tau_ana_p, profile_tau_ana_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_plus, tau_analytical_plus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False)

                if has_SCU_analytical:
                    depths_scu_ana_p, profile_scu_ana_p, _, _ = ProfileExtractor.extract_adaptive_profile(
                        centers_plus, SCU_analytical_plus, x_pos, y_pos, z_pos,
                        search_radius, verbose=False, )

                if len(depths_sn_ana_p) >= 3:
                    # Plot σ_n
                    axes[0].plot(profile_sn_ana_p, depths_sn_ana_p,
                               color='red', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

                    # Plot τ
                    axes[1].plot(profile_tau_ana_p, depths_tau_ana_p,
                               color='red', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

                    # Plot SCU if available
                    if has_SCU_analytical and len(depths_scu_ana_p) >= 3:
                        axes[2].plot(profile_scu_ana_p, depths_scu_ana_p,
                                   color='red', linestyle='-', linewidth=2,
                                   alpha=0.3, label='Analytical Side +' if i == 0 else '', marker=None)

            # ================================================================
            # MINUS SIDE - ANALYTICAL
            # ================================================================
            if len(centers_minus) > 0:
                depths_sn_ana_m, profile_sn_ana_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_minus, sigma_n_analytical_minus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False)

                depths_tau_ana_m, profile_tau_ana_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_minus, tau_analytical_minus, x_pos, y_pos, z_pos,
                    search_radius, verbose=False)

                if has_SCU_analytical:
                    depths_scu_ana_m, profile_scu_ana_m, _, _ = ProfileExtractor.extract_adaptive_profile(
                        centers_minus, SCU_analytical_minus, x_pos, y_pos, z_pos,
                        search_radius, verbose=False)

                if len(depths_sn_ana_m) >= 3:
                    # Plot σ_n
                    axes[0].plot(profile_sn_ana_m, depths_sn_ana_m,
                               color='blue', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

                    # Plot τ
                    axes[1].plot(profile_tau_ana_m, depths_tau_ana_m,
                               color='blue', linestyle='-', linewidth=2,
                               alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

                    # Plot SCU if available
                    if has_SCU_analytical and len(depths_scu_ana_m) >= 3:
                        axes[2].plot(profile_scu_ana_m, depths_scu_ana_m,
                                   color='blue', linestyle='-', linewidth=2,
                                   alpha=0.3, label='Analytical Side -' if i == 0 else '', marker=None)

            # ================================================================
            # AVERAGES - ANALYTICAL (only for first profile to avoid clutter)
            # ================================================================
            if i == 0 and len(depths_sn_ana_m) >= 3 and len(depths_sn_ana_p) >= 3:
                # Arithmetic average
                avg_sn_arith = (profile_sn_ana_m + profile_sn_ana_p) / 2
                avg_tau_arith = (profile_tau_ana_m + profile_tau_ana_p) / 2

                axes[0].plot(avg_sn_arith, depths_sn_ana_m,
                           color='darkorange', linestyle='-', linewidth=2,
                           alpha=0.6, label='Arithmetic average')

                axes[1].plot(avg_tau_arith, depths_sn_ana_m,
                           color='darkorange', linestyle='-', linewidth=2,
                           alpha=0.6, label='Arithmetic average')

                # Geometric average
                avg_tau_geom = np.sqrt(profile_tau_ana_m * profile_tau_ana_p)

                axes[1].plot(avg_tau_geom, depths_sn_ana_m,
                           color='purple', linestyle='-', linewidth=2,
                           alpha=0.6, label='Geometric average')

                # Harmonic average
                avg_sn_harm = 2 / (1/profile_sn_ana_m + 1/profile_sn_ana_p)
                avg_tau_harm = 2 / (1/profile_tau_ana_m + 1/profile_tau_ana_p)

                axes[0].plot(avg_sn_harm, depths_sn_ana_m,
                           color='green', linestyle='-', linewidth=2,
                           alpha=0.6, label='Harmonic average')

                axes[1].plot(avg_tau_harm, depths_sn_ana_m,
                           color='green', linestyle='-', linewidth=2,
                           alpha=0.6, label='Harmonic average')

            # ================================================================
            # NUMERICAL DATA FROM FAULT SURFACE (Continuum)
            # ================================================================
            print(f"        Extracting numerical data from fault surface...")

            depths_sn_num, profile_sn_num, _, _ = ProfileExtractor.extract_adaptive_profile(
                centers_fault, sigma_n_numerical, x_pos, y_pos, z_pos,
                search_radius, verbose=False)

            depths_tau_num, profile_tau_num, _, _ = ProfileExtractor.extract_adaptive_profile(
                centers_fault, tau_numerical, x_pos, y_pos, z_pos,
                search_radius, verbose=False)

            if has_SCU_numerical:
                depths_scu_num, profile_scu_num, _, _ = ProfileExtractor.extract_adaptive_profile(
                    centers_fault, SCU_numerical, x_pos, y_pos, z_pos,
                    search_radius, verbose=False)

            if len(depths_sn_num) >= 3:
                # Plot numerical with distinct style
                axes[0].plot(profile_sn_num, depths_sn_num,
                           color='black', linestyle='-', linewidth=2,
                           alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                           marker='x', markersize=5, markevery=3)

                axes[1].plot(profile_tau_num, depths_tau_num,
                           color='black', linestyle='-', linewidth=2,
                           alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                           marker='x', markersize=5, markevery=3)

                if has_SCU_numerical and len(depths_scu_num) >= 3:
                    axes[2].plot(profile_scu_num, depths_scu_num,
                               color='black', linestyle='-', linewidth=2,
                               alpha=0.7, label='GEOS Continuum' if i == 0 else '',
                               marker='x', markersize=5, markevery=3)

            successful_profiles += 1

        if successful_profiles == 0:
            print("  ❌ No valid profiles found!")
            plt.close()
            return

        # ===================================================================
        # ADD GEOS CONTACT SOLVER REFERENCE DATA (only once)
        # ===================================================================

        if geos_contact_data is not None:
            # Format: [Depth_m, Normal_Stress_bar, Shear_Stress_bar, SCU]
            # Index:  [0,       1,                 2,                 3]

            print("  📊 Adding GEOS Contact Solver reference data...")

            # Normal stress
            axes[0].plot(geos_contact_data[:, 1], geos_contact_data[:, 0],
                        marker='o', color='black', markersize=7,
                        label='GEOS Contact Solver', linestyle='none',
                        alpha=0.8, mec='black', mew=1.5, fillstyle='none')

            # Shear stress
            axes[1].plot(geos_contact_data[:, 2], geos_contact_data[:, 0],
                        marker='o', color='black', markersize=7,
                        label='GEOS Contact Solver', linestyle='none',
                        alpha=0.8, mec='black', mew=1.5, fillstyle='none')

            # SCU (if available)
            if geos_contact_data.shape[1] > 3:
                axes[2].plot(geos_contact_data[:, 3], geos_contact_data[:, 0],
                            marker='o', color='black', markersize=7,
                            label='GEOS Contact Solver', linestyle='none',
                            alpha=0.8, mec='black', mew=1.5, fillstyle='none')

        # ===================================================================
        # CONFIGURE PLOTS
        # ===================================================================

        fsize = 14

        # Plot 0: Normal Stress
        axes[0].set_xlabel('Normal Stress σₙ [bar]', fontsize=fsize, weight="bold")
        axes[0].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[0].grid(True, alpha=0.3, linestyle='--')
        axes[0].legend(loc='best', fontsize=fsize-2)
        axes[0].tick_params(labelsize=fsize-1)

        # Plot 1: Shear Stress
        axes[1].set_xlabel('Shear Stress τ [bar]', fontsize=fsize, weight="bold")
        axes[1].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[1].grid(True, alpha=0.3, linestyle='--')
        axes[1].legend(loc='best', fontsize=fsize-2)
        axes[1].tick_params(labelsize=fsize-1)

        # Plot 2: SCU
        axes[2].set_xlabel('SCU [-]', fontsize=fsize, weight="bold")
        axes[2].set_ylabel('Depth [m]', fontsize=fsize, weight="bold")
        axes[2].axvline(x=0.8, color='forestgreen', linestyle='--', linewidth=2,
                       alpha=0.5, label='Critical (0.8)')
        axes[2].axvline(x=1.0, color='red', linestyle='--', linewidth=2,
                       alpha=0.5, label='Failure (1.0)')
        axes[2].grid(True, alpha=0.3, linestyle='--')
        axes[2].legend(loc='upper right', fontsize=fsize-2, ncol=1)
        axes[2].tick_params(labelsize=fsize-1)
        axes[2].set_xlim(left=0)

        # Overall title
        years = time / (365.25 * 24 * 3600)
        fig.suptitle(f'Analytical (Anderson) vs Numerical (GEOS Continuum & Contact) - t={years:.1f} years',
                    fontsize=fsize+2, fontweight='bold', y=0.995)

        # Change verticale scale
        if self.config.MAX_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(bottom=self.config.MAX_DEPTH_PROFILES)

        if self.config.MIN_DEPTH_PROFILES != None :
            for i in range(len(axes)):
                axes[i].set_ylim(top=self.config.MIN_DEPTH_PROFILES)

        plt.tight_layout(rect=[0, 0, 1, 0.99])

        # Save
        if save:
            filename = f'analytical_vs_numerical_comparison_{years:.0f}y.png'
            plt.savefig(path / filename, dpi=300, bbox_inches='tight')
            print(f"\n  💾 Comparison plot saved: {filename}")

        # Show
        if show:
            plt.show()
        else:
            plt.close()


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
    pvd_reader = pv.PVDReader(path / config.PVD_FILE)
    pvd_reader.set_active_time_point(0)
    dataset = pvd_reader.read()

    # IMPORTANT : Utiliser le même merge que dans la boucle
    processor = TimeSeriesProcessor(config)
    volume_mesh = processor._merge_blocks(dataset)
    print(f"✅ Volume mesh extracted: {volume_mesh.n_cells} cells")


    # Initialize fault geometry with topology pre-computation
    print("\n📐 Initialize fault geometry")
    fault_geometry = FaultGeometry(
        config = config,
        mesh=mesh,
        fault_values=config.FAULT_VALUES,
        fault_attribute=config.FAULT_ATTRIBUTE,
        volume_mesh=volume_mesh)


    # Compute normals and adjacency topology (done once!)
    print("🔧 Computing normals and adjacency topology")
    fault_surface, adjacency_mapping = fault_geometry.initialize( scale_factor=50.0 )


    # Process time series
    processor = TimeSeriesProcessor(config)
    processor.process(path, fault_geometry, config.PVD_FILE)

    print("\n" + "=" * 60)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
