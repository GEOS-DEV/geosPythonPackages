# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Bertrand Denel, Paloma Martinez
import logging
import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from geos.utils.Logger import ( Logger, getLogger )
import vtk
import numpy as np
import sys
import matplotlib

from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.util.numpy_support import vtk_to_numpy
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.patches import Rectangle
import seaborn as sns

__doc__ = """
TetQualityAnalysis module is a filter that performs an an analysis of tetrahedras of one or several meshes and plot a summary.
"""

loggerName: str = "Tetrahedra Quality Analysis"

class TetQualityAnalysis:

    def __init__(
        self: Self,
        meshes: dict[str, vtkDataSet],
        speHandler: bool = False
    ) -> None:

        self.meshes: dict[ str, vtkDataSet ] = meshes
        # self.meshes = Set(  )
        self.analyzedMesh: dict[ Any ] = {}
        self.issues: dict[ Any ] = {}
        self.overallQualityScore: dict[ Any] = {}
        self.validMetrics: dict[Any] = {}
        self.sample = {}

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerName, True )
        else:
            self.logger = logging.getLogger( loggerName )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False


    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        self.handler = handler
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler'"
                                 " to True during the filter initialization." )


    def applyFilter( self: Self) -> None:
        self.logger.info( f"Apply filter { self.logger.name }." )

        self.__loggerSection( "MESH COMPARISON DASHBOARD" )

        for n, (filename1, mesh1) in enumerate( self.meshes.items() ):
            # print( n, filename1 )
            coords1 = self.get_coordinates_double_precision(mesh1)
            tet_ids1, tet_conn1 = self.extract_tet_connectivity(mesh1)
            n_tets1 = len( tet_ids1 )

            self.logger.info( f" Mesh {n} info: " )
            self.logger.info( f"  Name: {filename1}" )
            self.logger.info( f"  Total cells: {mesh1.GetNumberOfCells()}" )
            self.logger.info( f"  Tetrahedra: {n_tets1}" )
            self.logger.info( f"  Points: {mesh1.GetNumberOfPoints()}" )

            # Analyze both meshes
            print(f"\nAnalyzing Mesh {n} (double precision)...")
            # metrics1 = self.analyze_all_tets_vectorized(n, coords1, tet_conn1)
            self.analyze_all_tets_vectorized(n, coords1, tet_conn1)
            metrics1 = self.analyzedMesh[ n ]
            self.analyzedMesh[n]["tet"] = n_tets1

            # Extract data with consistent filtering
            ar_valid1 = np.isfinite(metrics1['aspect_ratio'])
            rr_valid1 = np.isfinite(metrics1['radius_ratio'])

            # Combined valid mask
            valid1 = ar_valid1 & rr_valid1

            ar1 = metrics1['aspect_ratio'][valid1]
            rr1 = metrics1['radius_ratio'][valid1]
            fr1 = metrics1['flatness_ratio'][valid1]
            vol1 = metrics1['volumes'][valid1]
            sq1 = metrics1['shape_quality'][valid1]

            # Edge length data
            min_edge1 = metrics1['min_edge'][valid1]
            max_edge1 = metrics1['max_edge'][valid1]

            # Edge length ratio
            edge_ratio1 = max_edge1 / np.maximum(min_edge1, 1e-15)

            # Dihedral angles
            min_dih1 = metrics1['min_dihedral'][valid1]
            max_dih1 = metrics1['max_dihedral'][valid1]
            dih_range1 = metrics1['dihedral_range'][valid1]

            score1 = compute_quality_score(ar1, sq1, edge_ratio1, min_dih1)

            # Store all values
            self.validMetrics[n] = { 'aspect_ratio' : ar1, 'radius_ratio': rr1, 'flatness_ratio': fr1, 'volume': vol1, 'shape_quality': sq1, 'min_edge': min_edge1, 'max_edge': max_edge1, 'edge_ratio': edge_ratio1, 'min_dihedral': min_dih1, 'max_dihedral': max_dih1, 'dihedral_range': dih_range1, 'quality_score': score1}

            # # ==================== Print Distribution Statistics ====================

            # Problem element counts

            high_ar1 = np.sum(ar1 > 100)
            low_sq1 = np.sum(sq1 < 0.3)
            low_flat1 = np.sum(fr1 < 0.01)
            high_edge_ratio1 = np.sum(edge_ratio1 > 10)
            critical_dih1 = np.sum(min_dih1 < 5)
            critical_max_dih1 = np.sum(max_dih1 > 175)
            problem1 = np.sum((ar1 > 100) & (sq1 < 0.3))
            critical_combo1 = np.sum((ar1 > 100) & (sq1 < 0.3) & (min_dih1 < 5))

            self.issues[n] = { "high_aspect_ratio": high_ar1, "low_shape_quality": low_sq1, "low_flatness": low_flat1, "high_edge_ratio": high_edge_ratio1, "critical_dihedral": critical_dih1, "critical_max_dihedral": critical_max_dih1, "combined": problem1, "critical_combo": critical_combo1 }

            # Overall quality scores

            excellent1 = np.sum(score1 > 80) / len(score1) * 100
            good1 = np.sum((score1 > 60) & (score1 <= 80)) / len(score1) * 100
            fair1 = np.sum((score1 > 30) & (score1 <= 60)) / len(score1) * 100
            poor1 = np.sum(score1 <= 30) / len(score1) * 100

            self.overallQualityScore[n] = { 'excellent': excellent1, 'good': good1, 'fair': fair1, 'poor': poor1 }

            extreme_ar1 = ar1 > 1e4
            self.issues[ n ][ "extreme_aspect_ratio" ] = extreme_ar1

            # Nearly degenerate elements
            degenerate1 = (min_dih1 < 0.1) | (max_dih1 > 179.9)
            self.issues[ n ][ "degenerate" ] = degenerate1

            print("\n" + "="*80 + "\n")

            # ==================== Create Dashboard ====================

        # ==================== Print Distribution Statistics ====================
        self.__orderMeshes()

        self.printDistributionStatistics()

        # Percentile information
        self.printPercentileAnalysis()

        self.printQualityIssueSummary()

        self.printExtremeOutlierAnalysis()

        self.printComparisonSummary()
        self.computeDeltasFromBest()

        self.createComparisonDashboard()


    def get_coordinates_double_precision( self, mesh ):
        points = mesh.GetPoints()
        n_points = points.GetNumberOfPoints()

        coords = np.zeros((n_points, 3), dtype=np.float64)
        for i in range(n_points):
            point = points.GetPoint(i)
            coords[i] = [point[0], point[1], point[2]]

        return coords

    def extract_tet_connectivity( self, mesh ):
        """Extract connectivity for all tetrahedra."""
        n_cells = mesh.GetNumberOfCells()
        tet_ids = []
        tet_connectivity = []

        for cell_id in range(n_cells):
            if mesh.GetCellType(cell_id) == vtk.VTK_TETRA:
                cell = mesh.GetCell(cell_id)
                point_ids = cell.GetPointIds()
                conn = [point_ids.GetId(i) for i in range(4)]
                tet_ids.append(cell_id)
                tet_connectivity.append(conn)

        return np.array(tet_ids), np.array(tet_connectivity)





    def analyze_all_tets_vectorized(self, n, coords, connectivity) -> dict:
        """Vectorized analysis of all tetrahedra."""
        n_tets = connectivity.shape[0]

        # Get coordinates for all vertices
        v0 = coords[connectivity[:, 0]]
        v1 = coords[connectivity[:, 1]]
        v2 = coords[connectivity[:, 2]]
        v3 = coords[connectivity[:, 3]]

        # Compute edges
        e01 = v1 - v0
        e02 = v2 - v0
        e03 = v3 - v0
        e12 = v2 - v1
        e13 = v3 - v1
        e23 = v3 - v2

        # Edge lengths
        l01 = np.linalg.norm(e01, axis=1)
        l02 = np.linalg.norm(e02, axis=1)
        l03 = np.linalg.norm(e03, axis=1)
        l12 = np.linalg.norm(e12, axis=1)
        l13 = np.linalg.norm(e13, axis=1)
        l23 = np.linalg.norm(e23, axis=1)

        all_edges = np.stack([l01, l02, l03, l12, l13, l23], axis=1)
        min_edge = np.min(all_edges, axis=1)
        max_edge = np.max(all_edges, axis=1)

        # Volumes
        cross_product = np.cross(e01, e02)
        volumes = np.abs(np.sum(cross_product * e03, axis=1) / 6.0)

        # Face areas
        face_012 = 0.5 * np.linalg.norm(np.cross(e01, e02), axis=1)
        face_013 = 0.5 * np.linalg.norm(np.cross(e01, e03), axis=1)
        face_023 = 0.5 * np.linalg.norm(np.cross(e02, e03), axis=1)
        face_123 = 0.5 * np.linalg.norm(np.cross(e12, e13), axis=1)

        all_faces = np.stack([face_012, face_013, face_023, face_123], axis=1)
        max_face_area = np.max(all_faces, axis=1)
        total_surface_area = np.sum(all_faces, axis=1)

        # Aspect ratio
        min_altitude = 3.0 * volumes / np.maximum(max_face_area, 1e-15)
        aspect_ratio = max_edge / np.maximum(min_altitude, 1e-15)
        aspect_ratio[volumes < 1e-15] = np.inf

        # Radius ratio
        inradius = 3.0 * volumes / np.maximum(total_surface_area, 1e-15)
        circumradius = (max_edge ** 3) / np.maximum(24.0 * volumes, 1e-15)
        radius_ratio = circumradius / np.maximum(inradius, 1e-15)

        # Flatness ratio
        flatness_ratio = volumes / np.maximum(max_face_area * min_edge, 1e-15)

        # Shape quality
        sum_edge_sq = np.sum(all_edges ** 2, axis=1)
        shape_quality = 12.0 * (3.0 * volumes) ** (2.0/3.0) / np.maximum(sum_edge_sq, 1e-15)
        shape_quality[volumes < 1e-15] = 0.0

        # Dihedral angles
        def compute_dihedral_angle(normal1, normal2):
            """Compute dihedral angle between two face normals."""
            n1_norm = normal1 / np.maximum(np.linalg.norm(normal1, axis=1, keepdims=True), 1e-15)
            n2_norm = normal2 / np.maximum(np.linalg.norm(normal2, axis=1, keepdims=True), 1e-15)
            cos_angle = np.sum(n1_norm * n2_norm, axis=1)
            cos_angle = np.clip(cos_angle, -1.0, 1.0)
            angle = np.arccos(cos_angle) * 180.0 / np.pi
            return angle

        # Face normals
        normal_012 = np.cross(e01, e02)
        normal_013 = np.cross(e01, e03)
        normal_023 = np.cross(e02, e03)
        normal_123 = np.cross(e12, e13)

        # Dihedral angles for each edge
        dihedral_01 = compute_dihedral_angle(normal_012, normal_013)
        dihedral_02 = compute_dihedral_angle(normal_012, normal_023)
        dihedral_03 = compute_dihedral_angle(normal_013, normal_023)
        dihedral_12 = compute_dihedral_angle(normal_012, normal_123)
        dihedral_13 = compute_dihedral_angle(normal_013, normal_123)
        dihedral_23 = compute_dihedral_angle(normal_023, normal_123)

        all_dihedrals = np.stack([dihedral_01, dihedral_02, dihedral_03,
                                dihedral_12, dihedral_13, dihedral_23], axis=1)

        min_dihedral = np.min(all_dihedrals, axis=1)
        max_dihedral = np.max(all_dihedrals, axis=1)
        dihedral_range = max_dihedral - min_dihedral

        self.analyzedMesh[ n ] = {
            'volumes': volumes,
            'aspect_ratio': aspect_ratio,
            'radius_ratio': radius_ratio,
            'flatness_ratio': flatness_ratio,
            'shape_quality': shape_quality,
            'min_edge': min_edge,
            'max_edge': max_edge,
            'min_dihedral': min_dihedral,
            'max_dihedral': max_dihedral,
            'dihedral_range': dihedral_range
        }

        return {
            'volumes': volumes,
            'aspect_ratio': aspect_ratio,
            'radius_ratio': radius_ratio,
            'flatness_ratio': flatness_ratio,
            'shape_quality': shape_quality,
            'min_edge': min_edge,
            'max_edge': max_edge,
            'min_dihedral': min_dihedral,
            'max_dihedral': max_dihedral,
            'dihedral_range': dihedral_range
        }

    def printDistributionStatistics( self: Self, fmt='.2e'):
        self.__loggerSection( "DISTRIBUTION STATISTICS (MIN / MEDIAN / MAX)" )

        def print_metric_stats( metricName, dataName, fmt='.2e'):
            """Helper function to print min/median/max for a metric."""
            # self.logger.info(f"\n{metricName}:")
            self.logger.info(f"{metricName}:")
            for n, _ in enumerate( self.meshes.items() ):
                data = self.validMetrics[ n ][ dataName ]
                self.logger.info(f"  Mesh {n}: Min={data.min():{fmt}}  Median={np.median(data):{fmt}}  Max={data.max():{fmt}}")


        print_metric_stats( "Aspect Ratio", 'aspect_ratio' )
        print_metric_stats( "Radius Ratio", 'radius_ratio' )
        print_metric_stats( "Flatness Ratio", 'flatness_ratio' )
        print_metric_stats( "Shape Quality", 'shape_quality', fmt='.4f' )
        print_metric_stats( "Volume", 'volume' )
        print_metric_stats( "Min Edge Length", 'min_edge' )
        print_metric_stats( "Max Edge Length", 'max_edge' )
        print_metric_stats( "Edge Length Ratio", 'edge_ratio', fmt='.2f' )
        print_metric_stats( "Min Dihedral Angle (degrees)", 'min_dihedral', fmt='.2f' )
        print_metric_stats( "Max Dihedral Angle (degrees)", 'max_dihedral', fmt='.2f' )
        print_metric_stats( "Dihedral Range (degrees)", 'dihedral_range',fmt='.2f' )
        print_metric_stats( "Overall Quality Score (0-100)", 'quality_score', fmt='.2f' )


    def printPercentileAnalysis( self: Self, fmt='.2f' ):
        self.__loggerSection( "PERCENTILE ANALYSIS (25th / 75th / 90th / 99th)" )

        def print_percentiles(metricName, dataName, fmt='.2f'):
            """Helper function to print percentiles."""
            self.logger.info(f"{metricName}:")
            # self.logger.info(f"\n{metricName}:")
            for n, _ in enumerate( self.meshes.items() ):
                data = self.validMetrics[ n ][ dataName ]
                p1 = np.percentile(data, [25, 75, 90, 99])
                self.logger.info(f"  Mesh {n}: 25th={p1[0]:{fmt}}  75th={p1[1]:{fmt}}  90th={p1[2]:{fmt}}  99th={p1[3]:{fmt}}")

        print_percentiles( "Aspect Ratio", 'aspect_ratio' )
        print_percentiles( "Shape Quality", 'shape_quality' )
        print_percentiles( "Edge Length Ratio", 'edge_ratio' )
        print_percentiles( "Min Dihedral Angle (degrees)", 'min_dihedral' )
        print_percentiles( "Overall Quality Score", 'quality_score' )


    def printQualityIssueSummary( self: Self ):
        self.__loggerSection( "QUALITY ISSUE SUMMARY" )

        def print_issue(meshID, metricName, issueDataName, dataName ):
            pb = self.issues[ meshID ][ issueDataName ]
            m = len( self.validMetrics[ meshID ][ dataName ] )
            fmt = '.2f'
            self.logger.info(f"  {metricName:20}:        {pb:,} ({(pb/m*100):{fmt}}%)")

        for n, _ in enumerate( self.meshes.items() ):
            # self.logger.info( f"\nMesh {n} Issues:" )
            self.logger.info( f"Mesh {n} Issues:" )
            print_issue( n, "Aspect Ratio > 100", "high_aspect_ratio", 'aspect_ratio' )
            print_issue( n, "Shape Quality < 0.3", "low_shape_quality", 'shape_quality' )
            print_issue( n, "Flatness < 0.01", "low_flatness", "flatness_ratio" )
            print_issue( n, "Edge Ratio > 10", "high_edge_ratio", "edge_ratio" )
            print_issue( n, "Min Dihedral < 5°", "critical_dihedral", "min_dihedral" )
            print_issue( n, "Max Dihedral > 175°", "critical_max_dihedral",'max_dihedral' )
            print_issue( n, "Combined (AR>100 & Q<0.3)", "combined" ,'aspect_ratio' )
            print_issue( n, "CRITICAL (AR>100 & Q<0.3 & MinDih<5°", "critical_combo", 'aspect_ratio' )

        self.compareIssuesFromBest()

        self.printOverallQualityScore()


    def printOverallQualityScore( self: Self ):
        # self.logger.info( f"\nOverall Quality Score Distribution:" )
        self.logger.info( f"Overall Quality Score Distribution:" )
        for n, _ in enumerate( self.meshes.items() ):
            qualityScore = self.overallQualityScore[ n ]
            self.logger.info(f"  Mesh {n}: Excellent (>80): {qualityScore[ 'excellent' ]:.1f}%  Good (60-80): {qualityScore[ 'good' ]:.1f}%  Fair (30-60): {qualityScore[ 'fair' ]:.1f}%  Poor (≤30): {qualityScore[ 'poor' ]:.1f}%")

    def printExtremeOutlierAnalysis( self: Self ):
        #TODO : info in warning if bad ?
        self.__loggerSection( "EXTREME OUTLIER ANALYSIS" )

        # self.logger.warning( f"\n🚨 Elements with Aspect Ratio > 10,000:" )
        self.logger.warning( f"🚨 Elements with Aspect Ratio > 10,000:" )
        for n, _ in enumerate( self.meshes ):
            extreme_ar = self.issues[n][ 'extreme_aspect_ratio' ]
            data = self.analyzedMesh[n]
            ar1 = data[ 'aspect_ratio' ]
            self.logger.info(f"  Mesh {n}: {np.sum(extreme_ar):,} elements ({np.sum(extreme_ar)/len(ar1)*100:.3f}%)")

            if np.sum(extreme_ar) > 0:
                vol1 = data[ "volume" ]
                min_dih1 = data[ "min_dihedral" ]
                sq1 = data[ "shape_quality" ]
                self.logger.info(f"    Worst AR:        {ar1[extreme_ar].max():.2e}")
                self.logger.info(f"    Avg volume:      {vol1[extreme_ar].mean():.2e}")
                self.logger.info(f"    Min dihedral:    {min_dih1[extreme_ar].min():.2f}° - {min_dih1[extreme_ar].mean():.2f}° (avg)")
                self.logger.info(f"    Shape quality:   {sq1[extreme_ar].min():.4f} - {sq1[extreme_ar].mean():.4f} (avg)")

            if np.sum(extreme_ar) > 10:
                # self.logger.warning(f"\n💡 Recommendation: Investigate/remove {np.sum(extreme_ar):,} extreme elements in Mesh {n}")
                self.logger.warning(f"💡 Recommendation: Investigate/remove {np.sum(extreme_ar):,} extreme elements in Mesh {n}")
                self.logger.warning(f"   These are likely artifacts from mesh generation or geometry issues.")

        # Nearly degenerate elements
        # self.logger.warning( f"\n🚨 Nearly Degenerate Elements (dihedral < 0.1° or > 179.9°):")
        self.logger.warning( f"🚨 Nearly Degenerate Elements (dihedral < 0.1° or > 179.9°):")
        for n, _ in enumerate( self.meshes ):
            degenerate = self.issues[ n ][ "degenerate" ]
            data = self.validMetrics[ n ][ "min_dihedral" ]
            self.logger.warning( f"  Mesh {n}: {np.sum(degenerate):,} elements ({np.sum(degenerate)/len(data)*100:.3f}%)")


    def printComparisonSummary( self: Self):
        self.__loggerSection( "COMPARISON SUMMARY" )

        for n, _ in enumerate( self.meshes ):
            name = f"Mesh {n}"
            if n == self.best:
                name += " [BEST]"
            elif n == self.worst:
                name += " [LEAST GOOD]"

            ar1_med = np.median( self.validMetrics[n]["aspect_ratio"] )
            sq1_med = np.median( self.validMetrics[n]["shape_quality"] )
            vol1_med = np.median(self.validMetrics[n]["volume"] )
            min_edge1_med = np.median(self.validMetrics[n]["min_edge"] )
            max_edge1_med = np.median(self.validMetrics[n]["max_edge"] )
            edge_ratio1_med = np.median(self.validMetrics[n]["edge_ratio"] )
            min_dih1_med = np.median( self.validMetrics[n]["min_dihedral"] )
            max_dih1_med = np.median( self.validMetrics[n]["max_dihedral"] )
            score1_med = np.median( self.validMetrics[n]["quality_score"] )

            self.logger.info(f"{name}")
            self.logger.info(f"  Tetrahedra: {self.analyzedMesh[n]['tet']:,}")
            self.logger.info(f"  Median Aspect Ratio: {ar1_med:.2f}")
            self.logger.info(f"  Median Shape Quality: {sq1_med:.4f}")
            self.logger.info(f"  Median Volume: {vol1_med:.2e}")
            self.logger.info(f"  Median Min Edge: {min_edge1_med:.2e}")
            self.logger.info(f"  Median Max Edge: {max_edge1_med:.2e}")
            self.logger.info(f"  Median Edge Ratio: {edge_ratio1_med:.2f}")
            self.logger.info(f"  Median Min Dihedral: {min_dih1_med:.1f}°")
            self.logger.info(f"  Median Max Dihedral: {max_dih1_med:.1f}°")
            self.logger.info(f"  Median Quality Score: {score1_med:.1f}/100")

        self.logger.info("\n" + "="*80)



    def computeDeltasFromBest( self: Self ):
        self.logger.info( f"Best mesh : Mesh {self.best}")
        self.deltas = {}

        n_tets_best = self.analyzedMesh[self.best][ 'tet']
        ar_med_best = np.median( self.validMetrics[self.best]["aspect_ratio"] )
        sq_med_best = np.median(self.validMetrics[self.best]["shape_quality"])
        vol_med_best = np.median(self.validMetrics[self.best]["volume"])
        min_edge_med_best = np.median(self.validMetrics[self.best]["min_edge"])
        max_edge_med_best = np.median(self.validMetrics[self.best]["max_edge"])
        edge_ratio_med_best = np.median(self.validMetrics[self.best]["edge_ratio"])

        for n, _ in enumerate( self.meshes ):
            n_tets = self.analyzedMesh[n][ 'tet']
            ar_med = np.median( self.validMetrics[n]["aspect_ratio"] )
            sq_med = np.median(self.validMetrics[n]["shape_quality"])
            vol_med = np.median(self.validMetrics[n]["volume"])
            min_edge_med = np.median(self.validMetrics[n]["min_edge"])
            max_edge_med = np.median(self.validMetrics[n]["max_edge"])
            edge_ratio_med = np.median(self.validMetrics[n]["edge_ratio"])


            delta_tets = ((n_tets - n_tets_best) / n_tets_best * 100) if n_tets_best > 0 else 0
            delta_ar = ((ar_med - ar_med_best) / ar_med_best * 100) if ar_med_best > 0 else 0
            delta_sq = ((sq_med - sq_med_best) / sq_med_best * 100) if sq_med_best > 0 else 0
            delta_vol = ((vol_med - vol_med_best) / vol_med_best * 100) if vol_med_best > 0 else 0
            delta_min_edge = ((min_edge_med - min_edge_med_best) / min_edge_med_best * 100) if min_edge_med_best > 0 else 0
            delta_max_edge = ((max_edge_med - max_edge_med_best) / max_edge_med_best * 100) if max_edge_med_best > 0 else 0
            delta_edge_ratio = ((edge_ratio_med - edge_ratio_med_best) / edge_ratio_med_best * 100) if edge_ratio_med_best > 0 else 0
            self.deltas[ n ] = { "tetrahedra": delta_tets, "aspect_ratio": delta_ar, "shape_quality": delta_sq, "volume": delta_vol, "min_edge": delta_min_edge, "max_edge": delta_max_edge, "edge_ratio": delta_edge_ratio }


        dtets = [ f"{self.deltas[ n ][ 'tetrahedra' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        dar = [ f"{self.deltas[ n ][ 'aspect_ratio' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        dsq = [ f"{self.deltas[ n ][ 'shape_quality' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        dvol = [ f"{self.deltas[ n ][ 'volume' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        d_min_edge = [ f"{self.deltas[ n ][ 'min_edge' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        d_max_edge = [ f"{self.deltas[ n ][ 'max_edge' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        d_edge_ratio = [ f"{self.deltas[ n ][ 'edge_ratio' ]:+15,.1f}%" for n, _ in self.sorted[1:] ]
        names = [ f"{f'Mesh {n}':16}" for n, _ in self.sorted[1:]]

        self.logger.info(f"Changes vs Mesh {self.best} [BEST]:")
        self.logger.info(f"{'  Mesh:':25}{('').join( names )}")
        self.logger.info(f"{'  Tetrahedra:':25} {('').join(dtets)}%")
        self.logger.info(f"{'  Aspect Ratio:':25}{('').join(  dar)}%")
        self.logger.info(f"{'  Shape Quality:':25}{('').join(  dsq)}%")
        self.logger.info(f"{'  Volume:':25}{('').join(  dvol)}%")
        self.logger.info(f"{'  Min Edge Length:':25}{('').join(  d_min_edge)}%")
        self.logger.info(f"{'  Max Edge Length:':25}{('').join(  d_max_edge)}%")
        self.logger.info(f"{'  Edge Length Ratio:':25}{('').join( d_edge_ratio)}%")



    def createComparisonDashboard( self: Self ):
        lbl = [ f'Mesh {n}' for n, _ in enumerate( self.meshes ) ]
        # Determine smart plot limits

        ar_99 = []
        for n, _ in enumerate( self.meshes ):
            ar_99.append( np.percentile( self.validMetrics[n]["aspect_ratio"], 99 ) )

        ar_99_max = np.max( np.array( ar_99 ) )

        # ar_99_1 = np.percentile(ar1, 99)
        # # ar_99_2 = np.percentile(ar2, 99)
        # # ar_99_max = max(ar_99_1, ar_99_2)
        # ar_99_max = ar_99_1

        if ar_99_max < 10:
            ar_plot_limit = 100
        elif ar_99_max < 100:
            ar_plot_limit = 1000
        else:
            ar_plot_limit = 10000

        # print(f"Using AR plot limit: {ar_plot_limit} (99th percentiles: M1={ar_99_1:.1f}, M2={ar_99_2:.1f})")
        # print(f"Using AR plot limit: {ar_plot_limit} (99th percentiles: M1={ar_99_1:.1f}")

        # Set style
        sns.set_style("whitegrid")
        plt.rcParams['figure.facecolor'] = 'white'
        plt.rcParams.update({
            'font.size': 9,
            'axes.titlesize': 10,
            'axes.labelsize': 9,
            'xtick.labelsize': 8,
            'ytick.labelsize': 8,
            'legend.fontsize': 8
        })

        # Create figure with flexible layout
        fig = plt.figure(figsize=(25, 20))

        # Row 1: Executive Summary (3 columns - wider)
        gs_row1 = gridspec.GridSpec(1, 3, figure=fig, left=0.05, right=0.95,
                                    top=0.96, bottom=0.84, wspace=0.20)

        # Rows 2-5: Main dashboard (5 columns each)
        gs_main = gridspec.GridSpec(4, 5, figure=fig, left=0.05, right=0.95,
                                    top=0.82, bottom=0.05, hspace=0.35, wspace=0.30)

        # Title
        # mesh1_name = filename1.split('/')[-1]
        # mesh2_name = filename2.split('/')[-1]
        suptitle = 'Mesh Quality Comparison Dashboard (Progressive Detail Layout)\n'
        for n, _ in enumerate( self.meshes ):
            # suptitle += f'Mesh {n}: {n_tets1:,} tets\t'
            suptitle += f'Mesh {n}: tets\t'
        fig.suptitle( suptitle,
                    fontsize=16, fontweight='bold', y=0.99)
        # fig.suptitle(f'Mesh Quality Comparison Dashboard (Progressive Detail Layout)\n' +
        #             f'Mesh 1: {mesh1_name} ({n_tets1:,} tets)',
        #             # f'Mesh 1: {mesh1_name} ({n_tets1:,} tets)  vs  Mesh 2: {mesh2_name} ({n_tets2:,} tets)',
        #             fontsize=16, fontweight='bold', y=0.99)

        # Color scheme
        # color = matplotlib.colormaps[ 'tab20' ]
        # def color[n]:
        #     nn = np.linspace(0,20)
        #     return matplotlib.colormaps[ 'tab20' ][nn]
        color = matplotlib.pyplot.cm.tab10( np.arange(20))

        # ==================== ROW 1: EXECUTIVE SUMMARY ====================

        # 1. Overall Quality Score Distribution
        ax1 = fig.add_subplot(gs_row1[0, 0])
        bins = np.linspace(0, 100, 40)
        for n, _ in enumerate( self.meshes ):
            score1 = self.validMetrics[n][ 'quality_score' ]
            ax1.hist(score1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
            ax1.axvline(np.median(score1), color=color[n], linestyle='--', linewidth=2.5, alpha=0.9)

        # Add quality zones
        ax1.axvspan(0, 30, alpha=0.15, color='red', zorder=0)
        ax1.axvspan(30, 60, alpha=0.15, color='yellow', zorder=0)
        ax1.axvspan(60, 80, alpha=0.15, color='lightgreen', zorder=0)
        ax1.axvspan(80, 100, alpha=0.15, color='darkgreen', zorder=0)

        # Add median lines
        # ax1.axvline(np.median(score1), color=color1, linestyle='--', linewidth=2.5, alpha=0.9)
        # ax1.axvline(np.median(score2), color=color2, linestyle='--', linewidth=2.5, alpha=0.9)

        # Add summary text   #### ONLY BEST AND WORST MESH?
        # TODO
        # ax1.text(0.98, 0.98,
        #         f'Median Score:\nM1: {np.median(score1):.1f}\n\n' +
        #         f'Excellent (>80):\nM1: {excellent1:.1f}%',
        #         # f'Median Score:\nM1: {np.median(score1):.1f}\nM2: {np.median(score2):.1f}\n\n' +
        #         # f'Excellent (>80):\nM1: {excellent1:.1f}%\nM2: {excellent2:.1f}%',
        #         transform=ax1.transAxes, va='top', ha='right',
        #         bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.9),
        #         fontsize=9, fontweight='bold')

        ax1.set_xlabel('Combined Quality Score', fontweight='bold')
        ax1.set_ylabel('Count', fontweight='bold')
        ax1.set_title('OVERALL MESH QUALITY VERDICT', fontsize=12, fontweight='bold',
                    color='darkblue', pad=10)
        ax1.legend(loc='upper left', fontsize=9)
        ax1.grid(True, alpha=0.3)

        # Add zone labels
        ax1.text(15, ax1.get_ylim()[1]*0.95, 'Poor', ha='center', fontsize=8, color='darkred')
        ax1.text(45, ax1.get_ylim()[1]*0.95, 'Fair', ha='center', fontsize=8, color='orange')
        ax1.text(70, ax1.get_ylim()[1]*0.95, 'Good', ha='center', fontsize=8, color='green')
        ax1.text(90, ax1.get_ylim()[1]*0.95, 'Excellent', ha='center', fontsize=8, color='darkgreen')

        # 2. Shape Quality vs Aspect Ratio
        ax2 = fig.add_subplot(gs_row1[0, 1])

        # Create sample for plotting
        for n, _ in enumerate( self.meshes ):
            ar1 = self.validMetrics[n]["aspect_ratio"]
            sq1 = self.validMetrics[n]["shape_quality"]
            self.setSampleForPlot( ar1, n )

            idx = self.sample[n]

            mask1_plot = ar1[idx] < ar_plot_limit

            ax2.scatter(ar1[idx][mask1_plot], sq1[idx][mask1_plot], alpha=0.4, s=5,
                    color=color[n], label=f'Mesh {n}', edgecolors='none')

        # Add quality threshold lines
        ax2.axhline(y=0.3, color='red', linestyle='--', linewidth=2,
                    alpha=0.8, label='Poor (Q < 0.3)', zorder=5)
        ax2.axhline(y=0.7, color='green', linestyle='--', linewidth=2,
                    alpha=0.8, label='Good (Q > 0.7)', zorder=5)
        ax2.axvline(x=100, color='orange', linestyle='--', linewidth=2,
                    alpha=0.8, label='High AR (> 100)', zorder=5)

        # Highlight problem zone
        problem_zone = Rectangle((100, 0), ar_plot_limit-100, 0.3,
                                alpha=0.2, facecolor='red', edgecolor='none', zorder=0)
        ax2.add_patch(problem_zone)

        # Count ALL elements
        problem1_all = np.sum((ar1 > 100) & (sq1 < 0.3))
        extreme1 = np.sum(ar1 > ar_plot_limit)

        # Problem annotation
        #TODO
        # ax2.text(0.98, 0.02,
        #         f'PROBLEM ELEMENTS\n(AR>100 & Q<0.3):\n\n' +
        #         f'M1: {problem1_all:,}\n\n',
        #         # f'Change: {((problem2_all-problem1_all)/max(problem1_all,1)*100):+.1f}%',
        #         # f'M1: {problem1_all:,}\nM2: {problem2_all:,}\n\n' +
        #         transform=ax2.transAxes, va='bottom', ha='right',
        #         bbox=dict(boxstyle='round', facecolor='#ffcccc', alpha=0.95,
        #                 edgecolor='darkred', linewidth=2),
        #         fontsize=9, fontweight='bold')

        # # Outlier warning
        # if extreme1 + extreme2 > 100:
        #     ax2.text(0.02, 0.98,
        #             f'⚠️ AR > {ar_plot_limit}\n(not shown):\n' +
        #             f'M1: {extreme1:,}\nM2: {extreme2:,}',
        #             transform=ax2.transAxes, va='top', ha='left',
        #             bbox=dict(boxstyle='round', facecolor='#ffe6cc', alpha=0.9),
        #             fontsize=7)

        ax2.set_xscale('log')
        ax2.set_xlabel('Aspect Ratio', fontweight='bold')
        ax2.set_ylabel('Shape Quality', fontweight='bold')
        ax2.set_title('KEY QUALITY INDICATOR: Shape Quality vs Aspect Ratio',
                    fontsize=12, fontweight='bold', color='darkred', pad=10)
        ax2.set_xlim([1, ar_plot_limit])
        ax2.set_ylim([0, 1.05])
        ax2.legend(loc='upper right', fontsize=7, framealpha=0.95)
        ax2.grid(True, alpha=0.3)

        # 3. Critical Issues Summary Table
        ax3 = fig.add_subplot(gs_row1[0, 2])
        ax3.axis('off')

        summary_stats = []
        summary_stats.append(['CRITICAL ISSUE', 'WORST', 'BEST', 'Change'])
        summary_stats.append(['─' * 18, '─' * 10, '─' * 10, '─' * 10])

        critical_combo1 = self.issues[ self.best ][ "critical_combo" ]
        critical_combo2 = self.issues[ self.worst ][ "critical_combo" ]
        ar1 = self.validMetrics[self.best][ "aspect_ratio" ]
        ar2 = self.validMetrics[self.worst][ "aspect_ratio" ]

        high_ar1 = self.issues[ self.best ][ "high_aspect_ratio" ]
        high_ar2 = self.issues[ self.worst ][ "high_aspect_ratio" ]

        low_sq1 = self.issues[self.best ][ "low_shape_quality" ]
        low_sq2 = self.issues[self.worst][ "low_shape_quality" ]

        critical_dih1 = self.issues[self.best]["critical_dihedral"]
        critical_dih2 = self.issues[self.worst]["critical_dihedral"]

        critical_max_dih1 = self.issues[self.best][ "critical_max_dihedral" ]
        critical_max_dih2 = self.issues[self.worst][ "critical_max_dihedral" ]

        high_edge_ratio1 = self.issues[self.best][ "high_edge_ratio" ]
        high_edge_ratio2 = self.issues[self.worst][ "high_edge_ratio" ]


        summary_stats.append(['CRITICAL Combo', f'{critical_combo1:,}', f'{critical_combo2:,}',
                            f'{((critical_combo2-critical_combo1)/max(critical_combo1,1)*100):+.1f}%' if critical_combo1 > 0 else 'N/A'])
        summary_stats.append(['(AR>100 & Q<0.3', f'({critical_combo1/len(ar1)*100:.2f}%)',
                            f'({critical_combo2/len(ar2)*100:.2f}%)', ''])
        summary_stats.append([' & MinDih<5°)', '', '', ''])

        summary_stats.append(['', '', '', ''])
        summary_stats.append(['AR > 100', f'{high_ar1:,}', f'{high_ar2:,}',
                            f'{((high_ar2-high_ar1)/max(high_ar1,1)*100):+.1f}%'])

        summary_stats.append(['Quality < 0.3', f'{low_sq1:,}', f'{low_sq2:,}',
                            f'{((low_sq2-low_sq1)/max(low_sq1,1)*100):+.1f}%'])

        summary_stats.append(['MinDih < 5°', f'{critical_dih1:,}', f'{critical_dih2:,}',
                            f'{((critical_dih2-critical_dih1)/max(critical_dih1,1)*100):+.1f}%' if critical_dih1 > 0 else 'N/A'])

        summary_stats.append(['MaxDih > 175°', f'{critical_max_dih1:,}', f'{critical_max_dih2:,}',
                            f'{((critical_max_dih2-critical_max_dih1)/max(critical_max_dih1,1)*100):+.1f}%' if critical_max_dih1 > 0 else 'N/A'])

        summary_stats.append(['Edge Ratio > 10', f'{high_edge_ratio1:,}', f'{high_edge_ratio2:,}',
                            f'{((high_edge_ratio2-high_edge_ratio1)/max(high_edge_ratio1,1)*100):+.1f}%'])

        summary_stats.append(['─' * 18, '─' * 10, '─' * 10, '─' * 10])
        summary_stats.append(['Quality Grade', '', '', ''])
        excellent1 = self.overallQualityScore[self.best]["excellent"]
        excellent2 = self.overallQualityScore[self.worst]["excellent"]
        good1 = self.overallQualityScore[self.best]["good"]
        good2 = self.overallQualityScore[self.worst]["good"]
        poor1 = self.overallQualityScore[self.best]["poor"]
        poor2 = self.overallQualityScore[self.worst]["poor"]


        summary_stats.append(['  Excellent (>80)', f'{excellent1:.1f}%', f'{excellent2:.1f}%',
                            f'{excellent2-excellent1:+.1f}%'])
        summary_stats.append(['  Good (60-80)', f'{good1:.1f}%', f'{good2:.1f}%',
                            f'{good2-good1:+.1f}%'])
        summary_stats.append(['  Poor (≤30)', f'{poor1:.1f}%', f'{poor2:.1f}%',
                            f'{poor2-poor1:+.1f}%'])

        table = ax3.table(cellText=summary_stats, cellLoc='left',
                        bbox=[0, 0, 1, 1], edges='open')
        table.auto_set_font_size(False)
        table.set_fontsize(8)

        # Style header
        for i in range(4):
            table[(0, i)].set_facecolor('#34495e')
            table[(0, i)].set_text_props(weight='bold', color='white', fontsize=9)

        # Highlight CRITICAL row
        for col in range(4):
            table[(2, col)].set_facecolor('#fadbd8')
            table[(2, col)].set_text_props(weight='bold', fontsize=9)

        # Color code changes
        for row in [2, 6, 7, 8, 9, 10, 13, 14, 15]:
            if row < len(summary_stats):
                change_text = summary_stats[row][3]
                if '%' in change_text and change_text != 'N/A':
                    try:
                        val = float(change_text.replace('%', '').replace('+', ''))
                        if row in [2, 6, 7, 8, 9, 10, 15]:  # Lower is better
                            if val < -10:
                                table[(row, 3)].set_facecolor('#d5f4e6')  # Green
                            elif val > 10:
                                table[(row, 3)].set_facecolor('#fadbd8')  # Red
                        else:  # Higher is better (excellent, good)
                            if val > 10:
                                table[(row, 3)].set_facecolor('#d5f4e6')
                            elif val < -10:
                                table[(row, 3)].set_facecolor('#fadbd8')
                    except:
                        pass

        ax3.set_title('CRITICAL ISSUES SUMMARY', fontsize=12, fontweight='bold',
                    color='darkgreen', pad=10)

        # ==================== ROW 2: QUALITY DISTRIBUTIONS ====================

        # 4. Shape Quality Histogram
        ax4 = fig.add_subplot(gs_main[0, 0])
        bins = np.linspace(0, 1, 40)
        for n, _ in enumerate( self.meshes ):
            sq1 = self.validMetrics[n][ "shape_quality" ]
            ax4.hist(sq1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax4.set_xlabel('Shape Quality', fontweight='bold')
        ax4.set_ylabel('Count', fontweight='bold')
        ax4.set_title('Shape Quality Distribution', fontweight='bold')
        ax4.legend()
        ax4.grid(True, alpha=0.3)

        # 5. Aspect Ratio Histogram
        ax5 = fig.add_subplot(gs_main[0, 1])
        # bins = np.logspace(0, np.log10(min(ar_plot_limit, ar1.max(), ar2.max())), 40)
        ar_max = np.array( [ self.validMetrics[n]["aspect_ratio"].max() for n, _ in enumerate( self.meshes )] )

        bins = np.logspace(0, np.log10(min(ar_plot_limit, ar_max.max())), 40)
        for n, _ in enumerate( self.meshes ):
            ar1 = self.validMetrics[n]['aspect_ratio']
            ax5.hist(ar1[ar1 < ar_plot_limit], bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax5.set_xscale('log')
        ax5.set_xlabel('Aspect Ratio', fontweight='bold')
        ax5.set_ylabel('Count', fontweight='bold')
        ax5.set_title('Aspect Ratio Distribution', fontweight='bold')
        ax5.legend()
        ax5.grid(True, alpha=0.3)

        # 6. Min Dihedral Histogram
        ax6 = fig.add_subplot(gs_main[0, 2])
        bins = np.linspace(0, 90, 40)
        for n, _ in enumerate( self.meshes ):
            min_dih1 = self.validMetrics[ n ]["min_dihedral"]
            ax6.hist(min_dih1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax6.axvline(5, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax6.set_xlabel('Min Dihedral Angle (degrees)', fontweight='bold')
        ax6.set_ylabel('Count', fontweight='bold')
        ax6.set_title('Min Dihedral Angle Distribution', fontweight='bold')
        ax6.legend()
        ax6.grid(True, alpha=0.3)

        # 7. Edge Ratio Histogram
        ax7 = fig.add_subplot(gs_main[0, 3])
        bins = np.logspace(0, 3, 40)
        for n, _ in enumerate( self.meshes ):
            edge_ratio1 = self.validMetrics[ n ][ "edge_ratio" ]
            ax7.hist(edge_ratio1[edge_ratio1 < 1000], bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax7.set_xscale('log')
        ax7.axvline(1, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
        ax7.set_xlabel('Edge Length Ratio', fontweight='bold')
        ax7.set_ylabel('Count', fontweight='bold')
        ax7.set_title('Edge Length Ratio Distribution', fontweight='bold')
        ax7.legend()
        ax7.grid(True, alpha=0.3)

        # 8. Volume Histogram
        ax8 = fig.add_subplot(gs_main[0, 4])
        vol_min = np.array( [ self.validMetrics[n]["volume"].min() for n, _ in enumerate( self.meshes )] ).min()
        vol_max = np.array( [ self.validMetrics[n]["volume"].max() for n, _ in enumerate( self.meshes )] ).max()


        bins = np.logspace(np.log10(vol_min), np.log10(vol_max), 40)
        for n, _ in enumerate( self.meshes ):
            vol1 = self.validMetrics[n][ "volume" ]
            ax8.hist(vol1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax8.set_xscale('log')
        ax8.set_xlabel('Volume', fontweight='bold')
        ax8.set_ylabel('Count', fontweight='bold')
        ax8.set_title('Volume Distribution', fontweight='bold')
        ax8.legend()
        ax8.grid(True, alpha=0.3)

        # ==================== ROW 3: STATISTICAL COMPARISON (BOX PLOTS) ====================

        # 9. Shape Quality Box Plot
        ax9 = fig.add_subplot(gs_main[1, 0])
        sq = [ self.validMetrics[n][ "shape_quality" ] for n, _ in enumerate( self.meshes ) ]
        bp1 = ax9.boxplot( sq, labels=lbl,
                patch_artist=True, showfliers=False)
        ax9.set_ylabel('Shape Quality', fontweight='bold')
        ax9.set_title('Shape Quality Comparison', fontweight='bold')
        ax9.grid(True, alpha=0.3, axis='y')

        # 10. Aspect Ratio Box Plot
        ax10 = fig.add_subplot(gs_main[1, 1])
        ar = [ self.validMetrics[n][ "aspect_ratio" ] for n, _ in enumerate( self.meshes ) ]
        bp2 = ax10.boxplot( ar, labels=lbl,
                patch_artist=True, showfliers=False)
        ax10.set_yscale('log')
        ax10.set_ylabel('Aspect Ratio (log)', fontweight='bold')
        ax10.set_title('Aspect Ratio Comparison', fontweight='bold')
        ax10.grid(True, alpha=0.3, axis='y')

        # 11. Min Dihedral Box Plot
        ax11 = fig.add_subplot(gs_main[1, 2])
        min_dih1 = [ self.validMetrics[n][ "min_dihedral" ] for n, _ in enumerate( self.meshes ) ]
        bp3 = ax11.boxplot( min_dih1, labels=lbl,
                        patch_artist=True, showfliers=False)
        ax11.set_ylabel('Min Dihedral Angle (degrees)', fontweight='bold')
        ax11.set_title('Min Dihedral Comparison', fontweight='bold')
        ax11.grid(True, alpha=0.3, axis='y')

        # 12. Edge Ratio Box Plot
        ax12 = fig.add_subplot(gs_main[1, 3])
        edge_ratio = [ self.validMetrics[n][ "edge_ratio" ] for n, _ in enumerate( self.meshes ) ]
        bp4 = ax12.boxplot(edge_ratio, labels=lbl,
            patch_artist=True, showfliers=False)
        ax12.set_yscale('log')
        ax12.set_ylabel('Edge Length Ratio (log)', fontweight='bold')
        ax12.set_title('Edge Ratio Comparison', fontweight='bold')
        ax12.grid(True, alpha=0.3, axis='y')

        # 13. Volume Box Plot
        ax13 = fig.add_subplot(gs_main[1, 4])
        vol = [ self.validMetrics[n][ "volume" ] for n, _ in enumerate( self.meshes ) ]
        bp5 = ax13.boxplot( vol, labels=lbl,
            patch_artist=True, showfliers=False)
        ax13.set_yscale('log')
        ax13.set_ylabel('Volume (log)', fontweight='bold')
        ax13.set_title('Volume Comparison', fontweight='bold')
        ax13.grid(True, alpha=0.3, axis='y')

        for n, _ in enumerate( self.meshes ):
            bp1['boxes'][n].set_facecolor(color[n])
            bp1['medians'][n].set_color("black")
            bp2['boxes'][n].set_facecolor(color[n])
            bp2['medians'][n].set_color("black")
            bp3['boxes'][n].set_facecolor(color[n])
            bp3['medians'][n].set_color("black")
            bp4['boxes'][n].set_facecolor(color[n])
            bp4['medians'][n].set_color("black")
            bp5['boxes'][n].set_facecolor(color[n])
            bp5['medians'][n].set_color("black")

        # ==================== ROW 4: CORRELATION ANALYSIS (SCATTER PLOTS) ====================

        # Use existing idx1, idx2 from executive summary

        # 14. Shape Quality vs Aspect Ratio (duplicate for detail)
        ax14 = fig.add_subplot(gs_main[2, 0])
        for n, _ in enumerate( self.meshes ):
            idx = self.sample[n]
            ar1 = self.validMetrics[n][ 'aspect_ratio']
            sq1 = self.validMetrics[n][ 'shape_quality']
            mask1 = ar1[idx] < ar_plot_limit
            ax14.scatter(ar1[idx][mask1], sq1[idx][mask1], alpha=0.4, s=5,
                    color=color[n], label=f'Mesh {n}', edgecolors='none')
        ax14.set_xscale('log')
        ax14.set_xlabel('Aspect Ratio', fontweight='bold')
        ax14.set_ylabel('Shape Quality', fontweight='bold')
        ax14.set_title('Shape Quality vs Aspect Ratio', fontweight='bold')
        ax14.set_xlim([1, ar_plot_limit])
        ax14.set_ylim([0, 1.05])
        ax14.legend(loc='upper right', fontsize=7)
        ax14.grid(True, alpha=0.3)

        # 15. Aspect Ratio vs Flatness
        ax15 = fig.add_subplot(gs_main[2, 1])
        for n, _ in enumerate( self.meshes ):
            idx = self.sample[n]
            ar1 = self.validMetrics[n]["aspect_ratio"]
            fr1 = self.validMetrics[n][ 'flatness_ratio' ]
            mask1 = ar1[idx] < ar_plot_limit
            ax15.scatter(ar1[idx][mask1], fr1[idx][mask1], alpha=0.4, s=5,
                color=color[n], label=f'Mesh {n}', edgecolors='none')
        ax15.set_xscale('log')
        ax15.set_yscale('log')
        ax15.set_xlabel('Aspect Ratio', fontweight='bold')
        ax15.set_ylabel('Flatness Ratio', fontweight='bold')
        ax15.set_title('Aspect Ratio vs Flatness', fontweight='bold')
        ax15.set_xlim([1, ar_plot_limit])
        ax15.legend(loc='upper right', fontsize=7)
        ax15.grid(True, alpha=0.3)

        # 16. Volume vs Aspect Ratio
        ax16 = fig.add_subplot(gs_main[2, 2])
        for n, _ in enumerate( self.meshes ):
            idx = self.sample[n]
            ar1 = self.validMetrics[n]["aspect_ratio"]
            vol1 = self.validMetrics[n][ 'volume' ]
            mask1 = ar1[idx] < ar_plot_limit
            ax16.scatter(vol1[idx][mask1], ar1[idx][mask1], alpha=0.4, s=5,
                    color=color[n], label=f'Mesh {n}', edgecolors='none')
        ax16.set_xscale('log')
        ax16.set_yscale('log')
        ax16.set_xlabel('Volume', fontweight='bold')
        ax16.set_ylabel('Aspect Ratio', fontweight='bold')
        ax16.set_title('Volume vs Aspect Ratio', fontweight='bold')
        ax16.set_ylim([1, ar_plot_limit])
        ax16.legend(loc='upper right', fontsize=7)
        ax16.grid(True, alpha=0.3)

        # 17. Volume vs Shape Quality
        ax17 = fig.add_subplot(gs_main[2, 3])
        for n, _ in enumerate( self.meshes ):
            idx = self.sample[n]
            vol1 = self.validMetrics[n][ 'volume' ]
            sq1 = self.validMetrics[n][ 'shape_quality']
            ax17.scatter(vol1[idx], sq1[idx], alpha=0.4, s=5,
                    color=color[n], label=f'Mesh {n}', edgecolors='none')
        ax17.set_xscale('log')
        ax17.set_xlabel('Volume', fontweight='bold')
        ax17.set_ylabel('Shape Quality', fontweight='bold')
        ax17.set_title('Volume vs Shape Quality', fontweight='bold')
        ax17.legend(loc='upper right', fontsize=7)
        ax17.grid(True, alpha=0.3)

        # 18. Edge Ratio vs Volume
        ax18 = fig.add_subplot(gs_main[2, 4])
        for n, _ in enumerate( self.meshes ):
            idx = self.sample[n]
            vol1 = self.validMetrics[n][ 'volume' ]
            edge_ratio = self.validMetrics[n][ 'edge_ratio' ]
            ax18.scatter(vol1[idx], edge_ratio[idx], alpha=0.4, s=5,
                    color=color[n], label=f'Mesh {n}', edgecolors='none')
        ax18.axhline(y=1, color='green', linestyle='--', linewidth=1.5, alpha=0.7)
        ax18.set_xscale('log')
        ax18.set_yscale('log')
        ax18.set_xlabel('Volume', fontweight='bold')
        ax18.set_ylabel('Edge Length Ratio', fontweight='bold')
        ax18.set_title('Edge Ratio vs Volume', fontweight='bold')
        ax18.legend(loc='upper right', fontsize=7)
        ax18.grid(True, alpha=0.3)

        # ==================== ROW 5: DETAILED DIAGNOSTICS ====================

        # 19. Min Edge Length Histogram
        ax19 = fig.add_subplot(gs_main[3, 0])
        edge_min = np.array( [ self.validMetrics[n]["min_edge"].min() for n,_ in enumerate( self.meshes ) ] ).min()
        edge_max_min = np.array( [ self.validMetrics[n]["min_edge"].max() for n,_ in enumerate( self.meshes ) ] ).min()

        bins = np.logspace(np.log10(edge_min), np.log10(edge_max_min), 40)

        for n, _ in enumerate( self.meshes ):
        # edge_min = min(min_edge1.min(), min_edge2.min())
        # edge_max_min = max(min_edge1.max(), min_edge2.max())
        # bins = np.logspace(np.log10(edge_min), np.log10(edge_max_min), 40)
            min_edge = self.validMetrics[n]['min_edge']
            ax19.hist(min_edge, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
            ax19.axvline(np.median(min_edge), color=color[n], linestyle=':', linewidth=2, alpha=0.8)
        ax19.set_xscale('log')

        ax19.set_xlabel('Minimum Edge Length', fontweight='bold')
        ax19.set_ylabel('Count', fontweight='bold')
        ax19.set_title('Min Edge Length Distribution', fontweight='bold')
        ax19.legend()
        ax19.grid(True, alpha=0.3)

        # 20. Max Edge Length Histogram
        ax20 = fig.add_subplot(gs_main[3, 1])
        edge_max = np.array( [ self.validMetrics[n]["max_edge"].max() for n,_ in enumerate( self.meshes ) ] ).max()
        edge_min_max = np.array( [ self.validMetrics[n]["max_edge"].min() for n,_ in enumerate( self.meshes ) ] ).min()

        # edge_max = max(max_edge1.max(), max_edge2.max())
        # edge_min_max = min(max_edge1.min(), max_edge2.min())
        bins = np.logspace(np.log10(edge_min_max), np.log10(edge_max), 40)
        for n, _ in enumerate( self.meshes ):
            max_edge1 = self.validMetrics[n]["max_edge"]
            ax20.hist(max_edge1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                    color=color[n], edgecolor='black', linewidth=0.5)
            ax20.axvline(np.median(max_edge1), color=color[n], linestyle=':', linewidth=2, alpha=0.8)
        ax20.set_xscale('log')
        ax20.set_xlabel('Maximum Edge Length', fontweight='bold')
        ax20.set_ylabel('Count', fontweight='bold')
        ax20.set_title('Max Edge Length Distribution', fontweight='bold')
        ax20.legend()
        ax20.grid(True, alpha=0.3)

        # 21. Max Dihedral Histogram
        ax21 = fig.add_subplot(gs_main[3, 2])
        bins = np.linspace(90, 180, 40)
        for n, _ in enumerate( self.meshes ):
            max_dih1 = self.validMetrics[n][ "max_dihedral" ]
            ax21.hist(max_dih1, bins=bins, alpha=0.6, label=f'Mesh {n}',
                color=color[n], edgecolor='black', linewidth=0.5)
        ax21.axvline(175, color='red', linestyle='--', linewidth=1.5, alpha=0.7)
        ax21.set_xlabel('Max Dihedral Angle (degrees)', fontweight='bold')
        ax21.set_ylabel('Count', fontweight='bold')
        ax21.set_title('Max Dihedral Angle Distribution', fontweight='bold')
        ax21.legend()
        ax21.grid(True, alpha=0.3)

        # 22. Dihedral Range Box Plot
        ax22 = fig.add_subplot(gs_main[3, 3])
        nmesh = len( self.meshes )
        positions = np.delete( np.arange( 1, nmesh*2+2 ), nmesh )
        dih = [ self.validMetrics[n]["min_dihedral"] for n, _ in enumerate( self.meshes )] +  [ self.validMetrics[n]["max_dihedral"] for n, _ in enumerate( self.meshes )]
        lbl_boxplot = [ f'M{n}Min' for n, _ in enumerate( self.meshes )] + [ f'M{n}Max' for n, _ in enumerate( self.meshes )]
        boxplot_color = [ n for n, _ in enumerate( self.meshes ) ] + [ n for n, _ in enumerate( self.meshes ) ]
        bp_dih = ax22.boxplot(dih,
                            positions=positions,
                            labels=lbl_boxplot,
                            patch_artist=True, showfliers=False, widths=0.6)
        for m in range( len(self.meshes)*2 ):
            bp_dih['boxes'][m].set_facecolor( color[ boxplot_color[m] ])

        ax22.axhline(5, color='red', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        ax22.axhline(175, color='red', linestyle='--', linewidth=1, alpha=0.5, zorder=0)
        ax22.axhline(70.5, color='green', linestyle=':', linewidth=1, alpha=0.5, zorder=0)
        ax22.set_ylabel('Dihedral Angle (degrees)', fontweight='bold')
        ax22.set_title('Dihedral Angle Comparison', fontweight='bold')
        ax22.grid(True, alpha=0.3, axis='y')

        # 23. Shape Quality CDF
        ax23 = fig.add_subplot(gs_main[3, 4])
        for n, _ in enumerate( self.meshes ):
            sq1 = self.validMetrics[n][ "shape_quality"]
            sorted_sq1 = np.sort(sq1)
            cdf_sq1 = np.arange(1, len(sorted_sq1) + 1) / len(sorted_sq1) * 100
            ax23.plot(sorted_sq1, cdf_sq1, color=color[n], linewidth=2, label=f'Mesh {n}')

        ax23.axvline(0.3, color='red', linestyle='--', linewidth=1, alpha=0.5)
        ax23.axvline(0.7, color='green', linestyle='--', linewidth=1, alpha=0.5)
        ax23.axhline(50, color='gray', linestyle='--', linewidth=1, alpha=0.5)
        ax23.set_xlabel('Shape Quality', fontweight='bold')
        ax23.set_ylabel('Cumulative %', fontweight='bold')
        ax23.set_title('Cumulative Distribution - Shape Quality', fontweight='bold')
        ax23.legend(loc='lower right')
        ax23.grid(True, alpha=0.3)

        # Save figure
        output_png = 'mesh_comparison.png'
        print(f"\nSaving dashboard to: {output_png}")
        plt.savefig(output_png, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"Dashboard saved successfully!")




    def __loggerSection( self: Self, sectionName: str ):
        # self.logger.info("\n" + "="*80)
        self.logger.info("="*80)
        self.logger.info( sectionName )
        self.logger.info("="*80)


    def __orderMeshes( self: Self ):
        """Proposition of ordering as fonction of median quality score"""
        self.logger.info( "Ordering the meshes" )
        median_score = { n :  np.median( self.validMetrics[n]["quality_score"] )  for n, _ in enumerate (self.meshes) }

        sorted_meshes = sorted( median_score.items(), key=lambda x:x[1], reverse = True )
        self.sorted = sorted_meshes
        self.best = sorted_meshes[ 0 ][0]
        self.worst = sorted_meshes[ -1 ][0]

        self.logger.info( f"Best Mesh: Mesh {self.best} vs worst Mesh [{self.worst}]")

        self.logger.info( f"Mesh order from median quality score:" )
        top = [ f"Mesh {m[0]} ({m[1]:.2f})" for m in sorted_meshes ]
        toprint = (" > ").join( top )
        self.logger.info( " [+] " + toprint + " [-]" )

    def compareIssuesFromBest( self: Self ):
        high_ar1 = self.issues[ self.best ][ "high_aspect_ratio" ]
        critical_dih1 = self.issues[ self.best ]["critical_dihedral"]
        low_sq1 = self.issues[ self.best ]["low_shape_quality"]
        critical_combo1 = self.issues[ self.best ]["critical_combo"]

        def getPercentChangeFromBest( data, ref ):
            return (data - ref) / max( ref, 1)*100

        self.logger.info (f"Change from BEST [Mesh {self.best}]" )
        high_ar = [ f"{getPercentChangeFromBest( self.issues[ n ][ 'high_aspect_ratio' ], high_ar1 ):+15,.1f}%" for n, _ in self.sorted ]
        low_sq = [ f"{getPercentChangeFromBest( self.issues[ n ][ 'low_shape_quality' ], low_sq1 ):+15,.1f}%" for n, _ in self.sorted ]
        critical_dih = [ f"{getPercentChangeFromBest( self.issues[ n ][ 'critical_dihedral' ], critical_dih1 ):+15,.1f}%" if critical_dih1 > 0 else f"{'N/A':16}" for n, _ in self.sorted]
        critical_combo = [ f"{getPercentChangeFromBest( self.issues[ n ][ 'critical_combo' ], critical_combo1 ):+15,.1f}%"  if critical_combo1 > 0 else f"{'N/A':16}" for n, _ in self.sorted]

        self.logger.info( f"{'  AR > 100:':25}{('').join( high_ar )}" )
        self.logger.info( f"{'  Quality < 0.3:':25}{('').join( low_sq )}" )
        self.logger.info( f"{'  MinDih < 5°:':25}{('').join( critical_dih )}" )
        self.logger.info( f"{'  CRITICAL combo:':25}{('').join( critical_combo )}" )


    def setSampleForPlot( self: Self, data, n ):
        n_sample = min(10000, len( data ))
        self.sample[n] = np.random.choice(len(data), n_sample, replace=False)

# Combined quality score
def compute_quality_score(aspectRatio, shapeQuality, edgeRatio, minDihedralAngle):
    """Compute combined quality score (0-100)."""
    ar_norm = np.clip(1.0 / (aspectRatio / 1.73), 0, 1)
    sq_norm = shapeQuality
    er_norm = np.clip(1.0 / edgeRatio, 0, 1)
    dih_norm = np.clip(minDihedralAngle / 60.0, 0, 1)
    score = (0.3 * ar_norm + 0.4 * sq_norm + 0.2 * er_norm + 0.1 * dih_norm) * 100
    return score


