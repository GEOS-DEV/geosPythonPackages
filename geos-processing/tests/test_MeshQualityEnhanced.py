# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
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
from geos.mesh.utils.genericHelpers import createMultiCellMesh
from geos.mesh.stats.meshQualityMetricHelpers import (
    getAllCellTypesExtended, )
from geos.processing.pre_processing.MeshQualityEnhanced import MeshQualityEnhanced
from geos.mesh.model.QualityMetricSummary import QualityMetricSummary

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellData, vtkFieldData, vtkCellTypes, VTK_TRIANGLE,
                                            VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON )
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader

# input data
meshName_all: tuple[ str, ...] = (
    "polydata",
    "tetra_mesh",
)
cellTypes_all: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_TETRA )
qualityMetrics_all: tuple[ tuple[ int, ...], ...] = (
    ( int( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO ),
      int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE ) ),
    ( int( vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN ),
      int( vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW ),
      int( vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX ) ),
)
# yapf: disable
cellTypeCounts_all: tuple[ tuple[ int, ...], ...] = (
    ( 26324, 0, 0, 0, 0, 0, 26324, 0, ),
    ( 0, 0, 8, 0, 0, 0, 0, 8,)
)
metricsSummary_all: tuple[ tuple[ tuple[ float, ...], ...], ...] = (
    ( ( 1.07, 0.11, 1.0, 1.94, 26324.0 ), ( 0.91, 0.1, 0.53, 1.0, 26324.0 ), ( 64.59, 6.73, 60.00, 110.67, 26324.0 ) ),
    ( ( -0.28, 0.09, -0.49, -0.22, 8.0 ), ( 0.7, 0.1, 0.47, 0.79, 8.0 ), ( 0.8, 0.12, 0.58, 0.95, 8.0 ) ),
)
# yapf: enable


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: mesh
    mesh: vtkUnstructuredGrid
    cellType: int
    qualityMetrics: tuple[ int, ...]
    cellTypeCounts: tuple[ int, ...]
    metricsSummary: tuple[ tuple[ float, ...], ...]


def __get_tetra_dataset() -> vtkUnstructuredGrid:
    """Extract tetrahedra dataset from csv and add some deformations."""
    # Get tetra mesh
    data_root: str = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )
    filename: str = "tetra_mesh.csv"
    nbPtsCell: int = 4

    ptsCoord: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, filename ), dtype=float, delimiter=',' )

    # Intentional deformation of the mesh
    ptsCoord[ :, 0 ][ ptsCoord[ :, 0 ] == 0.5 ] = 0.2
    ptsCoord[ :, 2 ][ ptsCoord[ :, 2 ] == 0.5 ] = 0.7

    cellPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
        ptsCoord[ i:i + nbPtsCell ] for i in range( 0, ptsCoord.shape[ 0 ], nbPtsCell )
    ]
    nbCells: int = int( ptsCoord.shape[ 0 ] / nbPtsCell )
    cellTypes = nbCells * [ VTK_TETRA ]
    mesh: vtkUnstructuredGrid = createMultiCellMesh( cellTypes, cellPtsCoords )

    return mesh


def __get_dataset( meshName ) -> vtkUnstructuredGrid:
    # Get the dataset from external vtk file
    if meshName == "polydata":
        reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
        vtkFilename: str = "data/triangulatedSurface.vtu"

    datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
    reader.SetFileName( datapath )
    reader.Update()

    return reader.GetOutput()


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases
    """
    for meshName, cellType, qualityMetrics, cellTypeCounts, metricsSummary in zip( meshName_all,
                                                                                   cellTypes_all,
                                                                                   qualityMetrics_all,
                                                                                   cellTypeCounts_all,
                                                                                   metricsSummary_all,
                                                                                   strict=True ):
        mesh: vtkUnstructuredGrid
        if meshName == "tetra_mesh":
            mesh = __get_tetra_dataset()
        else:
            mesh = __get_dataset( meshName )

        yield TestCase( mesh, cellType, qualityMetrics, cellTypeCounts, metricsSummary )


ids: list[ str ] = [ os.path.splitext( name )[ 0 ] for name in meshName_all ]


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_MeshQualityEnhanced( test_case: TestCase ) -> None:
    """Test of CellTypeCounterEnhanced filter.

    Args:
        test_case (TestCase): Test case
    """
    mesh = test_case.mesh
    meshQualityEnhancedFilter: MeshQualityEnhanced = MeshQualityEnhanced()
    meshQualityEnhancedFilter.SetInputDataObject( mesh )
    if test_case.cellType == VTK_TRIANGLE:
        meshQualityEnhancedFilter.SetTriangleMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_QUAD:
        meshQualityEnhancedFilter.SetQuadMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_TETRA:
        meshQualityEnhancedFilter.SetTetraMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_PYRAMID:
        meshQualityEnhancedFilter.SetPyramidMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_WEDGE:
        meshQualityEnhancedFilter.SetWedgeMetrics( test_case.qualityMetrics )
    elif test_case.cellType == VTK_HEXAHEDRON:
        meshQualityEnhancedFilter.SetHexaMetrics( test_case.qualityMetrics )
    meshQualityEnhancedFilter.Update()

    # test method getComputedMetricsFromCellType
    for i, cellType in enumerate( getAllCellTypesExtended() ):
        print(cellType)
        metrics: Optional[ set[ int ] ] = meshQualityEnhancedFilter.getComputedMetricsFromCellType( cellType )
        if test_case.cellTypeCounts[ i ] > 0:
            assert metrics is not None, f"Metrics from {vtkCellTypes.GetClassNameFromTypeId(cellType)} cells is undefined."

    # test attributes
    outputMesh: vtkUnstructuredGrid = meshQualityEnhancedFilter.GetOutputDataObject( 0 )
    cellData: vtkCellData = outputMesh.GetCellData()
    assert cellData is not None, "Cell data is undefined."

    nbMetrics: int = len( test_case.qualityMetrics )
    nbCellArrayExp: int = mesh.GetCellData().GetNumberOfArrays() + nbMetrics
    assert cellData.GetNumberOfArrays() == nbCellArrayExp, f"Number of cell arrays is expected to be {nbCellArrayExp}."

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
    ) == nbFieldArrayExp, f"Number of field data arrays is expected to be {nbFieldArrayExp}."

    stats: QualityMetricSummary = meshQualityEnhancedFilter.GetQualityMetricSummary()
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
    assert len( fig.get_axes() ) == 6, "Number of Axes is expected to be 6."
