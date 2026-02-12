# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pandas as pd
import random as rd
import pytest
from typing import Iterator
from matplotlib.figure import Figure

from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE,
                                            VTK_POLYGON, VTK_POLYHEDRON )

# inputs
statTypes: tuple[ StatTypes, ...] = tuple( StatTypes )
size: int = 100
nbNan: int = 5
expectedStatTypes_all: tuple[ float | int, ...] = ( 0.5957, 0.6508, -2.2055, 1.6259, size - nbNan )

cellType_all: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON,
                                   VTK_POLYGON, VTK_POLYHEDRON )
cellMetricIndexes_all: tuple[ int, ...] = (
    ( vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA,
      vtkMeshQuality.QualityMeasureTypes.CONDITION ),
    ( vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS, vtkMeshQuality.QualityMeasureTypes.AREA,
      vtkMeshQuality.QualityMeasureTypes.CONDITION ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME,
      vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME,
      vtkMeshQuality.QualityMeasureTypes.JACOBIAN, 100 ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME,
      vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS, 100 ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME,
      vtkMeshQuality.QualityMeasureTypes.ODDY, 100 ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.AREA ),
    ( vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME ),
)

metricIndexesFail_all: tuple[ int, ...] = (
    ( vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS, vtkMeshQuality.QualityMeasureTypes.VOLUME, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS, vtkMeshQuality.QualityMeasureTypes.VOLUME, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.ODDY, vtkMeshQuality.QualityMeasureTypes.AREA, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.VOLUME, 200 ),
    ( vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA, 100, 200 ),
)


@dataclass( frozen=True )
class TestCase_StatsType:
    """Test case."""
    __test__ = False
    statType: StatTypes
    values: tuple[ float, ...]
    expected: int | float


def __generate_test_data_for_StatsType() -> Iterator[ TestCase_StatsType ]:
    """Generate test cases for StatsType.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases for StatsType
    """
    rd.seed( 10 )
    np.random.seed( 10 )
    for statType, expected in zip( statTypes, expectedStatTypes_all, strict=True ):
        loc: float = rd.random()
        scale: float = rd.random()
        values: npt.NDArray[ np.float64 ] = np.random.normal( loc, scale, size )
        # insert nan values
        for _ in range( nbNan ):
            index = rd.randint( 0, size )
            values[ index ] = np.nan
        yield TestCase_StatsType( statType, values, expected )


ids = [ statType.getString() for statType in statTypes ]


@pytest.mark.parametrize( "test_case", __generate_test_data_for_StatsType(), ids=ids )
def test_StatsType_compute( test_case: TestCase_StatsType ) -> None:
    """Test of StatsType compute method.

    Args:
        test_case (TestCase_StatsType): Test case
    """
    obs: int | float = test_case.statType.compute( test_case.values )
    assert abs(
        obs - test_case.expected
    ) < 1e-4, f"Observed value is {round(obs, 4)} whereas expected value is {test_case.expected} for {test_case.statType.getString()}."


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    cellMetricIndexes: tuple[ int, ...]
    otherMetricIndexes: tuple[ int, ...]
    cellType: int
    statTypes: StatTypes
    values: tuple[ float, float, float, float, int ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases
    """
    rd.seed( 10 )
    for cellMetricIndexes, cellType in zip( cellMetricIndexes_all, cellType_all, strict=True ):
        values: tuple[ float, float, float, float, int ] = (
            rd.uniform( 0.0, 5.0 ),
            rd.uniform( 0.0, 5.0 ),
            rd.uniform( 0.0, 5.0 ),
            rd.uniform( 0.0, 5.0 ),
            rd.randint( 1, 100000 ),
        )
        otherMetricIndexes: tuple[ int, ...] = ( 200, )
        yield TestCase( cellMetricIndexes, otherMetricIndexes, cellType, statTypes, values )


def __generate_failed_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases
    """
    for metricIndexes, cellType in zip( metricIndexesFail_all, cellType_all, strict=True ):
        otherMetricIndexes: tuple = ()
        values: tuple[ float, float, float, float, int ] = ( 0., 0., 0., 0., 0., 0 )
        yield TestCase( metricIndexes, otherMetricIndexes, cellType, statTypes, values )


def test_QualityMetricSummary_init() -> None:
    """Test of QualityMetricSummary init method."""
    stats: QualityMetricSummary = QualityMetricSummary()
    assert stats.getAllCellStats() is not None, "Stats member is undefined."
    assert ( stats.getAllCellStats().shape[ 0 ]
             == 5 ) and stats.getAllCellStats().shape[ 1 ] == 123, "Stats shape is wrong."


@pytest.mark.parametrize( "test_case", __generate_failed_test_data() )
def test_QualityMetricSummary_setter( test_case: TestCase ) -> None:
    """Test of setStatsToMetricAndCellType method for IndexError.

    Args:
        test_case (TestCase): Test case
    """
    stats: QualityMetricSummary = QualityMetricSummary()
    statType: StatTypes = StatTypes.COUNT
    val: float = 1.0
    for cellMetricIndex in test_case.cellMetricIndexes:
        with pytest.raises( IndexError ) as pytest_wrapped_e:
            stats.setCellStatValueFromStatMetricAndCellType( cellMetricIndex, test_case.cellType, statType, val )
    assert pytest_wrapped_e.type is IndexError


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_QualityMetricSummary_setterGetter( test_case: TestCase ) -> None:
    """Test of setter and getter methods.

    Args:
        test_case (TestCase): Test case
    """
    stats: QualityMetricSummary = QualityMetricSummary()
    for cellMetricIndex in test_case.cellMetricIndexes:
        for statType, value in zip( test_case.statTypes, test_case.values, strict=True ):
            stats.setCellStatValueFromStatMetricAndCellType( cellMetricIndex, test_case.cellType, statType, value )

    for otherMetricIndex in test_case.otherMetricIndexes:
        for statType, value in zip( test_case.statTypes, test_case.values, strict=True ):
            stats.setOtherStatValueFromMetric( otherMetricIndex, statType, value )

    assert np.any( stats.getAllCellStats().to_numpy() > 0 ), "Stats values were not correctly set."
    for cellMetricIndex in test_case.cellMetricIndexes:
        for statType, val in zip( test_case.statTypes, test_case.values, strict=True ):
            subSet: pd.DataFrame = stats.getCellStatsFromCellType( test_case.cellType )
            assert subSet[ cellMetricIndex ][ statType.getIndex(
            ) ] == val, f"Stats at ({cellMetricIndex}, {test_case.cellType}, {statType}) from getCellStatsFromCellType is expected to be equal to {val}."

            subSet2: pd.DataFrame = stats.getStatsFromMetric( cellMetricIndex )
            assert subSet2[ test_case.cellType ][ statType.getIndex(
            ) ] == val, f"Stats at ({cellMetricIndex}, {test_case.cellType}, {statType}) from getStatsFromMetric is expected to be equal to {val}."

            subSet3: pd.Series = stats.getStatsFromMetricAndCellType( cellMetricIndex, test_case.cellType )
            assert subSet3[ statType.getIndex(
            ) ] == val, f"Stats at ({cellMetricIndex}, {test_case.cellType}, {statType}) from getStatsFromMetricAndCellType is expected to be equal to {val}."

            valObs: float = stats.getCellStatValueFromStatMetricAndCellType( cellMetricIndex, test_case.cellType,
                                                                             statType )
            assert valObs == val, f"Stats at ({cellMetricIndex}, {test_case.cellType}, {statType}) from getStatValueFromMetricAndCellType is expected to be equal to {val}."

    for cellMetricIndex in test_case.otherMetricIndexes:
        for statType, val in zip( test_case.statTypes, test_case.values, strict=True ):
            subSet4: pd.DataFrame = stats.getStatsFromMetric( cellMetricIndex )
            assert subSet4[ statType.getIndex(
            ) ] == val, f"Stats at ({cellMetricIndex}, {statType}) from getStatsFromMetric is expected to be equal to {val}."


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_QualityMetricSummary_plotSummaryFigure( test_case: TestCase ) -> None:
    """Test of plotSummaryFigure method.

    Args:
        test_case (TestCase): Test case
    """
    stats: QualityMetricSummary = QualityMetricSummary()
    for cellMetricIndex in test_case.cellMetricIndexes:
        for statType, value in zip( test_case.statTypes, test_case.values, strict=True ):
            stats.setCellStatValueFromStatMetricAndCellType( cellMetricIndex, test_case.cellType, statType, value )

    for otherMetricIndex in test_case.otherMetricIndexes:
        for statType, value in zip( test_case.statTypes, test_case.values, strict=True ):
            stats.setOtherStatValueFromMetric( otherMetricIndex, statType, value )

    fig: Figure = stats.plotSummaryFigure()
    assert fig is not None, "Figure is undefined"
    # metrics + global counts + cell count + legend
    nbAxesExp: int = len( test_case.cellMetricIndexes ) + len( test_case.otherMetricIndexes ) + 3
    assert len( fig.get_axes() ) == nbAxesExp, f"Number of Axes is expected to be {nbAxesExp}."