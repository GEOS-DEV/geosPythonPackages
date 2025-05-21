# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
from matplotlib.figure import Figure
from dataclasses import dataclass
import numpy as np
import pandas as pd
import pytest
from typing import (
    Iterator,
    Optional,
)

from geos.mesh.processing.meshQualityMetricHelpers import (
    getAllCellTypesExtended, )
from geos.mesh.stats.MeshQualityEnhanced import MeshQualityEnhanced
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellData, vtkFieldData, vtkCellTypes, VTK_TRIANGLE,
                                            VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON )
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader

# input data
data_root: str = "/data/pau901/SIM_CS/users/MartinLemay/Data/mesh/"  #os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )
filenames_all: tuple[ str, ...] = (
    "triangulatedSurface.vtu",
    "tetraVolume.vtu",
)
cellTypes_all: set[ int ] = ( VTK_TRIANGLE, VTK_TETRA )
qualityMetrics_all: tuple[ set[ int ], ...] = (
    ( int( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO ), int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE ) ),
    ( int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW ),
      int( vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX ) ),
)
cellTypeCounts_all: tuple[ tuple[ int, ...], ...] = ( (
    26324,
    0,
    0,
    0,
    0,
    0,
    26324,
    0,
), (
    0,
    0,
    368606,
    0,
    0,
    0,
    0,
    368606,
) )
metricsSummary_all = (
    ( ( 1.07, 0.11, 1.00, 1.94, 26324.0 ), ( 1.07, 0.11, 1.00, 1.94, 26324.0 ), ( 64.59, 6.73, 60.00, 110.67,
                                                                                  26324.0 ) ),
    ( ( 1.71, 0.32, 1.02, 3.3, 368606.0 ), ( 1.71, 0.32, 1.02, 3.3, 368606.0 ), ( 0.65, 0.15, 0.05, 0.94, 368606.0 ) ),
)


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: mesh
    mesh: vtkUnstructuredGrid
    cellType: vtkCellTypes
    qualityMetrics: set[ int ]
    cellTypeCounts: tuple[ int ]
    metricsSummary: tuple[ float ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for filename, cellType, qualityMetrics, cellTypeCounts, metricsSummary in zip( filenames_all,
                                                                                   cellTypes_all,
                                                                                   qualityMetrics_all,
                                                                                   cellTypeCounts_all,
                                                                                   metricsSummary_all,
                                                                                   strict=True ):
        path: str = os.path.join( data_root, filename )
        # load mesh
        reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
        reader.SetFileName( path )
        reader.Update()
        mesh: vtkUnstructuredGrid = reader.GetOutputDataObject( 0 )
        yield TestCase( mesh, cellType, qualityMetrics, cellTypeCounts, metricsSummary )


ids: list[ str ] = [ os.path.splitext( name )[ 0 ] for name in filenames_all ]


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_MeshQualityEnhanced( test_case: TestCase ) -> None:
    """Test of CellTypeCounterEnhanced filter.

    Args:
        test_case (TestCase): test case
    """
    filter: MeshQualityEnhanced = MeshQualityEnhanced()
    filter.SetInputDataObject( test_case.mesh )
    if test_case.cellType == VTK_TRIANGLE:
        filter.SetTriangleMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_QUAD:
        filter.SetQuadMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_TETRA:
        filter.SetTetraMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_PYRAMID:
        filter.SetPyramidMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_WEDGE:
        filter.SetWedgeMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_HEXAHEDRON:
        filter.SetHexaMetrics( test_case.qualityMetrics )
    filter.Update()

    # test method getComputedMetricsFromCellType
    for i, cellType in enumerate( getAllCellTypesExtended() ):
        metrics: Optional[ set[ int ] ] = filter.getComputedMetricsFromCellType( cellType )
        if test_case.cellTypeCounts[ i ] > 0:
            assert metrics is not None, f"Metrics from {vtkCellTypes.GetClassNameFromTypeId(cellType)} cells is undefined."

    # test attributes
    outputMesh: vtkUnstructuredGrid = filter.GetOutputDataObject( 0 )
    cellData: vtkCellData = outputMesh.GetCellData()
    assert cellData is not None, "Cell data is undefined."

    nbMetrics: int = len( test_case.qualityMetrics )
    nbCellArrayExp: int = test_case.mesh.GetCellData().GetNumberOfArrays() + nbMetrics
    assert cellData.GetNumberOfArrays() == nbCellArrayExp, f"Number of cell arrays is expected to be {nbCellArrayExp}."

    # test field data
    fieldData: vtkFieldData = outputMesh.GetFieldData()
    assert fieldData is not None, "Field data is undefined."
    tmp = np.array( test_case.cellTypeCounts ) > 0
    nbPolygon: int = np.sum( tmp[ :2 ].astype( int ) )
    nbPolygon = 0 if nbPolygon == 0 else nbPolygon + 1
    nbPolyhedra: int = np.sum( tmp[ 2:6 ].astype( int ) )
    nbPolyhedra = 0 if nbPolyhedra == 0 else nbPolyhedra + 1
    nbFieldArrayExp: int = test_case.mesh.GetFieldData().GetNumberOfArrays() + tmp.size + 4 * nbMetrics * (
        nbPolygon + nbPolyhedra )
    assert fieldData.GetNumberOfArrays(
    ) == nbFieldArrayExp, f"Number of field data arrays is expected to be {nbFieldArrayExp}."

    stats: QualityMetricSummary = filter.GetQualityMetricSummary()
    for i, cellType in enumerate( getAllCellTypesExtended() ):
        # test Counts
        assert stats.getCellTypeCountsOfCellType( cellType ) == test_case.cellTypeCounts[
            i ], f"Number of {vtkCellTypes.GetClassNameFromTypeId(cellType)} cells is expected to be {test_case.cellTypeCounts[i]}"
        if stats.getCellTypeCountsOfCellType( cellType ) == 0:
            continue

        # test metric summary
        for j, metricIndex in enumerate( test_case.qualityMetrics ):
            subStats: pd.Series = stats.getStatsFromMetricAndCellType( metricIndex, cellType )
            assert np.round( subStats, 2 ).tolist() == list(
                test_case.metricsSummary[ j ] ), f"Stats at metric index {j} are wrong."

    fig: Figure = stats.plotSummaryFigure()
    assert len( fig.get_axes() ) == 4, "Number of Axes is expected to be 4."
