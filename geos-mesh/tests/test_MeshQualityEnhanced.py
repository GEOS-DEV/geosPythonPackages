# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from pathlib import Path
from matplotlib.figure import Figure
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pandas as pd
import pytest
from typing import (
    Iterator,
    Optional,
)

from geos.mesh.processing.meshQualityMetricHelpers import (
    QualityMetricEnum,
    getTriangleQualityMeasure,
    getQuadQualityMeasure,
    getTetQualityMeasure,
    getPyramidQualityMeasure,
    getWedgeQualityMeasure,
    getHexQualityMeasure,
    getAllCellTypes,
    getAllCellTypesExtended,
)
from geos.mesh.vtk.helpers import createSingleCellMesh, createMultiCellMesh
from geos.mesh.stats.MeshQualityEnhanced import MeshQualityEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellData,
    vtkFieldData,
    vtkCellTypes,
    vtkCell,
    VTK_TRIANGLE,
    VTK_QUAD,
    VTK_TETRA,
    VTK_PYRAMID,
    VTK_WEDGE,
    VTK_HEXAHEDRON,
    VTK_POLYGON,
    VTK_POLYHEDRON,
)
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader

# input data
data_root: str = "/data/pau901/SIM_CS/users/MartinLemay/Data/mesh/" #os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )
filenames_all: tuple[ str, ...] = ( "triangulatedSurface.vtu", )
qualityMetrics_all: tuple[set[int],...] = (
    (int(vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO), int(vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN), int(vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE)),
)
cellTypeCounts_all: list[int] = [(26324, 0, 0, 0, 0, 0, 26324, 0,)]
metricsSummary_all = (
    ((1.07, 0.11, 1.00, 1.94, 26324.0), (0.91, 0.10, 0.53, 1.00, 26324.0), (64.59, 6.73, 60.00, 110.67, 26324.0)),
)

@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: mesh
    mesh: vtkUnstructuredGrid
    qualityMetrics: set[int]
    cellTypeCounts: list[int]
    metricsSummary: tuple[float]

def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for filename, qualityMetrics, cellTypeCounts, metricsSummary in zip(
        filenames_all, qualityMetrics_all, cellTypeCounts_all, metricsSummary_all, strict=True
    ):
        path: str = os.path.join( data_root, filename )
        # load mesh
        reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
        reader.SetFileName( path )
        reader.Update()
        mesh: vtkUnstructuredGrid = reader.GetOutputDataObject(0)
        yield TestCase( mesh, qualityMetrics, cellTypeCounts, metricsSummary )


ids: list[str] = [ os.path.splitext( name )[ 0 ] for name in filenames_all ]
@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_MeshQualityEnhanced( test_case: TestCase ) -> None:
    """Test of CellTypeCounter filter.

    Args:
        test_case (TestCase): test case
    """
    filter: MeshQualityEnhanced = MeshQualityEnhanced()
    filter.SetInputDataObject(test_case.mesh)
    filter.SetMeshQualityMetrics(triangleMetrics=test_case.qualityMetrics)
    filter.Update()

    # test method getComputedMetricsFromCellType
    for i, cellType in enumerate(getAllCellTypesExtended()):
        metrics: Optional[set[int]] = filter.getComputedMetricsFromCellType(cellType)
        if test_case.cellTypeCounts[i] > 0:
            assert metrics is not None, f"Metrics from {vtkCellTypes.GetClassNameFromTypeId(cellType)} cells is undefined."

    # test attributes
    outputMesh: vtkUnstructuredGrid = filter.GetOutputDataObject(0)
    cellData: vtkCellData = outputMesh.GetCellData()
    assert cellData is not None, "Cell data is undefined."
    print(cellData.GetNumberOfArrays())
    nbMetrics: int = len(test_case.qualityMetrics)
    nbCellArrayExp: int = test_case.mesh.GetCellData().GetNumberOfArrays() + nbMetrics
    assert cellData.GetNumberOfArrays() == nbCellArrayExp, f"Number of cell arrays is expected to be {nbCellArrayExp}."

    # test field data
    fieldData: vtkFieldData = outputMesh.GetFieldData()
    assert fieldData is not None, "Field data is undefined."
    tmp = np.array(test_case.cellTypeCounts) > 0
    nbPolygon: int = np.sum(tmp[:2].astype(int))
    nbPolygon = 0 if nbPolygon == 0 else nbPolygon + 1
    nbPolyhedra: int = np.sum(tmp[2:6].astype(int))
    nbPolyhedra = 0 if nbPolyhedra == 0 else nbPolyhedra + 1
    nbFieldArrayExp: int = test_case.mesh.GetFieldData().GetNumberOfArrays() + tmp.size + 4 * nbMetrics * (nbPolygon + nbPolyhedra)
    assert fieldData.GetNumberOfArrays() == nbFieldArrayExp, f"Number of field data arrays is expected to be {nbFieldArrayExp}."

    stats: QualityMetricSummary = filter.GetQualityMetricSummary()
    for i, cellType in enumerate(getAllCellTypesExtended()):
        # test Counts
        assert stats.getCellTypeCountsOfCellType(cellType) == test_case.cellTypeCounts[i], f"Number of {vtkCellTypes.GetClassNameFromTypeId(cellType)} cells is expected to be {test_case.cellTypeCounts[i]}"

        if stats.getCellTypeCountsOfCellType(cellType) == 0:
            continue

        # test metric summary
        for j, metricIndex in enumerate(test_case.qualityMetrics):
            subStats: pd.Series = stats.getStatsFromMetricAndCellType(metricIndex, cellType)
            assert np.round(subStats, 2).tolist() == list(test_case.metricsSummary[j])

    fig: Figure = stats.plotSummaryFigure()
    assert len(fig.get_axes()) == 4, "Number of Axes is expected to be 4."
