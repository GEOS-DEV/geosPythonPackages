# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
from matplotlib.figure import Figure
from dataclasses import dataclass
import numpy as np
import pandas as pd
from typing import Optional
import pytest

from geos.mesh.stats.meshQualityMetricHelpers import getAllCellTypesExtended
from geos.processing.pre_processing.MeshQualityEnhanced import MeshQualityEnhanced
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellData, vtkFieldData, vtkCellTypes, VTK_TRIANGLE,
                                            VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON )

# input data
meshName_all: tuple[ str, ...] = (
    "extractAndMergeVolume",
    "extractAndMergeFault",
    "hexs3_tets36_pyrs18",
    "quads2_tris4",
)
cellTypes_all: tuple[ tuple[ int, ...], ...] = (
    { VTK_HEXAHEDRON, },
    { VTK_TRIANGLE, },
    { VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID },
    { VTK_TRIANGLE, VTK_QUAD },
)
qualityMetrics_all: tuple[ tuple[ int, ...], ...] = (
    ( int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW ),
      int( vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX ) ),
    ( int( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO ),
      int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE ) ),
    ( int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW ),
      int( vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX ) ),
    ( int( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO ),
      int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE ) ),
)
# yapf: disable
cellTypeCounts_all: tuple[ tuple[ int, ...], ...] = (
    ( 0, 0, 0, 0, 0, 6000, 0, 6000, ),
    ( 126, 0, 0, 0, 0, 0, 126, 0, ),
    ( 0, 0, 36, 18, 0, 3, 0, 57, ),
    ( 4, 2, 0, 0, 0, 0, 6, 0, ),
)
metricsSummary_all: tuple[ tuple[ tuple[ float, ...], ...], ...] = (
    ( ( 1.0, 0.0, 1.0, 1.0, 6000.0 ), ( 0.0, 0.0, 0.0, 0.0, 6000.0 ), ( 0.0, 0.0, 0.0, 0.0, 6000.0 ) ),
    ( ( 378.23, 305.04, 9.55, 693.11, 126.0 ), ( 0.01, 0.02, 0.0, 0.07, 126.0 ), ( 90.0, 0.0, 90.0, 90.0, 126.0 ) ),
    ( ( 0.58, 0.0, 0.58, 0.58, 36.0 ), ( 0.45, 0.0, 0.45, 0.45, 36.0 ), ( 0.7, 0.0, 0.7, 0.7, 36.0 ),
      ( 0.82, 0.0, 0.82, 0.82, 18.0 ), ( 0.09, 0.0, 0.09, 0.09, 18.0 ), ( 0.61, 0.0, 0.61, 0.61, 18.0 ),
      ( 1.0, 0.0, 1.0, 1.0, 3.0 ), ( 0.0, 0.0, 0.0, 0.0, 3.0 ), ( 0.0, 0.0, 0.0, 0.0, 3.0 ),
      ( 0.68, 0.13, 0.58, 1.0, 57.0 ), ( 0.31, 0.18, 0.0, 0.45, 57.0 ), ( 0.63, 0.15, 0.0, 0.7, 57.0 ) ),
    ( ( 1.39, 0.0, 1.39, 1.39, 4.0 ), ( 0.82, 0.0, 0.82, 0.82, 4.0 ), ( 90.0, 0.0, 90.0, 90.0, 4.0 ),
      ( 1.0, 0.0, 1.0, 1.0, 2.0 ), ( 1.0, 0.0, 1.0, 1.0, 2.0 ), ( 90.0, 0.0, 90.0, 90.0, 2.0 ),
      ( 1.26, 0.19, 1.0, 1.39, 6.0 ), ( 0.88, 0.09, 0.82, 1.0, 6.0 ), ( 90.0, 0.0, 90.0, 90.0, 6.0 ) ),
)
# yapf: enable


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: mesh
    mesh: vtkUnstructuredGrid
    cellType: tuple[ int, ...]
    qualityMetrics: tuple[ int, ...]
    cellTypeCounts: tuple[ int, ...]
    metricsSummary: tuple[ tuple[ float, ...], ...]


@pytest.mark.parametrize( "case", [
    ( 0 ),
    ( 1 ),
    ( 2 ),
    ( 3 ),
] )
def test_MeshQualityEnhanced( dataSetTest: vtkUnstructuredGrid, case: int ) -> None:
    """Test of MeshQualityEnhanced filter."""
    test_case: TestCase = TestCase( dataSetTest( meshName_all[ case ] ), cellTypes_all[ case ], qualityMetrics_all[ case ], cellTypeCounts_all[ case ], metricsSummary_all[ case ] )
    mesh: vtkUnstructuredGrid = test_case.mesh
    meshQualityEnhancedFilter: MeshQualityEnhanced = MeshQualityEnhanced( mesh )
    if VTK_TRIANGLE in test_case.cellType:
        meshQualityEnhancedFilter.SetTriangleMetrics( test_case.qualityMetrics )
    if VTK_QUAD in test_case.cellType:
        meshQualityEnhancedFilter.SetQuadMetrics( test_case.qualityMetrics )
    if VTK_TETRA in test_case.cellType:
        meshQualityEnhancedFilter.SetTetraMetrics( test_case.qualityMetrics )
    if VTK_PYRAMID in test_case.cellType:
        meshQualityEnhancedFilter.SetPyramidMetrics( test_case.qualityMetrics )
    if VTK_WEDGE in test_case.cellType:
        meshQualityEnhancedFilter.SetWedgeMetrics( test_case.qualityMetrics )
    if VTK_HEXAHEDRON in test_case.cellType:
        meshQualityEnhancedFilter.SetHexaMetrics( test_case.qualityMetrics )
    meshQualityEnhancedFilter.applyFilter()

    # test method getComputedMetricsFromCellType
    for i, cellType in enumerate( getAllCellTypesExtended() ):
        metrics: Optional[ set[ int ] ] = meshQualityEnhancedFilter.getComputedMetricsFromCellType( cellType )
        if test_case.cellTypeCounts[ i ] > 0:
            assert metrics is not None, f"Metrics from { vtkCellTypes.GetClassNameFromTypeId( cellType ) } cells is undefined."

    # test attributes
    outputMesh: vtkUnstructuredGrid = meshQualityEnhancedFilter.getOutput()
    cellData: vtkCellData = outputMesh.GetCellData()
    assert cellData is not None, "Cell data is undefined."

    nbMetrics: int = len( test_case.qualityMetrics )
    nbCellArrayExp: int = mesh.GetCellData().GetNumberOfArrays() + nbMetrics
    assert cellData.GetNumberOfArrays() == nbCellArrayExp, f"Number of cell arrays is expected to be { nbCellArrayExp }."

    # test field data
    fieldData: vtkFieldData = outputMesh.GetFieldData()
    assert fieldData is not None, "Field data is undefined."
    tmp = np.array( test_case.cellTypeCounts ) > 0
    nbPolygon: int = np.sum( tmp[ :2 ].astype( int ) )
    nbPolygon = 0 if nbPolygon == 0 else nbPolygon + 1
    nbPolyhedra: int = np.sum( tmp[ 2:6 ].astype( int ) )
    nbPolyhedra = 0 if nbPolyhedra == 0 else nbPolyhedra + 1
    nbFieldArrayExp: int = mesh.GetFieldData().GetNumberOfArrays() + tmp.size + 4 * nbMetrics * ( nbPolygon +
                                                                                                nbPolyhedra )
    assert fieldData.GetNumberOfArrays(
    ) == nbFieldArrayExp, f"Number of field data arrays is expected to be { nbFieldArrayExp }."

    stats: QualityMetricSummary = meshQualityEnhancedFilter.GetQualityMetricSummary()
    cpt: int = 0
    for i, cellType in enumerate( getAllCellTypesExtended() ):
        # test Counts
        assert stats.getCellTypeCountsOfCellType( cellType ) == test_case.cellTypeCounts[
            i ], f"Number of { vtkCellTypes.GetClassNameFromTypeId( cellType ) } cells is expected to be { test_case.cellTypeCounts[ i ] }"
        if stats.getCellTypeCountsOfCellType( cellType ) == 0:
            continue

        # test metric summary
        for j, metricIndex in enumerate( test_case.qualityMetrics ):
            subStats: pd.Series = stats.getStatsFromMetricAndCellType( metricIndex, cellType )
            if len( test_case.cellType ) > 1: # for meshes with multiple cell type
                j= cpt
                cpt += 1
            assert np.round( subStats, 2 ).tolist() == list(
                test_case.metricsSummary[ j ] ), f"Stats at metric index { j } are wrong."


    fig: Figure = stats.plotSummaryFigure()
    assert len( fig.get_axes() ) == 6, "Number of Axes is expected to be 6."
