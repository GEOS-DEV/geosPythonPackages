# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
from dataclasses import dataclass
import numpy as np
import pandas as pd
import random as rd
import pytest
from typing import Iterator

from geos.mesh.model.QualityMetricSummary import QualityMetricSummary, StatTypes

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID,
                                            VTK_HEXAHEDRON, VTK_WEDGE, VTK_POLYGON, VTK_POLYHEDRON )
from geos.mesh.processing.meshQualityMetricHelpers import getQualityMeasureNameFromIndex

# inputs
statTypes: tuple[StatTypes,...] = (StatTypes.COUNT, StatTypes.MEAN, StatTypes.STD_DEV, StatTypes.MIN, StatTypes.MAX)

cellType_all: tuple[int,...] = (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON, VTK_POLYGON, VTK_POLYHEDRON)
metricIndexes_all: tuple[int,...] = (
    (vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO, vtkMeshQuality.QualityMeasureTypes.AREA, vtkMeshQuality.QualityMeasureTypes.CONDITION),
    (vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS, vtkMeshQuality.QualityMeasureTypes.AREA, vtkMeshQuality.QualityMeasureTypes.CONDITION),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME, vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME, vtkMeshQuality.QualityMeasureTypes.JACOBIAN),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME, vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME, vtkMeshQuality.QualityMeasureTypes.ODDY),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.AREA),
    (vtkMeshQuality.QualityMeasureTypes.SHAPE, vtkMeshQuality.QualityMeasureTypes.VOLUME),
)

metricIndexesFail_all: tuple[int,...] = (
    (vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS, vtkMeshQuality.QualityMeasureTypes.VOLUME),
    (vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS, vtkMeshQuality.QualityMeasureTypes.VOLUME),
    (vtkMeshQuality.QualityMeasureTypes.ODDY, vtkMeshQuality.QualityMeasureTypes.AREA),
    (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.AREA),
    (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.AREA),
    (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.AREA),
    (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.VOLUME),
    (vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX, vtkMeshQuality.QualityMeasureTypes.AREA),
)

@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    metricIndexes: tuple[int,...]
    cellType: int
    statTypes: StatTypes
    values: float


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for metricIndexes, cellType in zip( metricIndexes_all,
                                      cellType_all,
                                      strict=True ):
        values: tuple[int, float, float, float, float] = (
            rd.randint(1, 100000), rd.uniform(0.0, 5.0), rd.uniform(0.0, 5.0), rd.uniform(0.0, 5.0), rd.uniform(0.0, 5.0)
        )
        yield TestCase( metricIndexes, cellType, statTypes, values )

def __generate_failed_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for metricIndex, cellType in zip( metricIndexesFail_all,
                                      cellType_all,
                                      strict=True ):
        values: tuple[int, float, float, float, float] = (0, 0., 0., 0., 0., 0.)
        yield TestCase( metricIndex, cellType, statTypes, values )

def test_QualityMetricSummary_init() -> None:
    """Test of QualityMetricSummary init method."""
    stats: QualityMetricSummary = QualityMetricSummary()
    assert stats.getAllStats() is not None, "Stats member is undefined."
    assert (stats.getAllStats().shape[0] == 5) and stats.getAllStats().shape[1] == 115, "Stats shape is wrong."

@pytest.mark.parametrize( "test_case", __generate_failed_test_data() )
def test_QualityMetricSummary_setter( test_case: TestCase ) -> None:
    """Test of setStatsToMetricAndCellType method.

    Args:
        test_case (TestCase): test case
    """
    stats: QualityMetricSummary = QualityMetricSummary()
    statType: StatTypes = StatTypes.COUNT
    val: float = 1.0
    for metricIndex in test_case.metricIndexes:
        with pytest.raises( IndexError ) as pytest_wrapped_e:
            stats.setStatValueToMetricAndCellType(metricIndex, test_case.cellType, statType, val)
    assert pytest_wrapped_e.type is IndexError

@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_QualityMetricSummary_setterGetter( test_case: TestCase ) -> None:
    """Test of setter and getter methods.

    Args:
        test_case (TestCase): test case
    """
    stats: QualityMetricSummary = QualityMetricSummary()
    for metricIndex in test_case.metricIndexes:
        for statType, value in zip(test_case.statTypes, test_case.values, strict=True):
            print(metricIndex, test_case.cellType, statType)
            stats.setStatValueToMetricAndCellType(metricIndex, test_case.cellType, statType, value)

    assert np.any(stats.getAllStats().to_numpy() > 0), "Stats values were not corretcly set."
    for metricIndex in test_case.metricIndexes:
        for statType, val in zip(test_case.statTypes, test_case.values, strict=True):
            subSet: pd.DataFrame = stats.getStatsFromCellType(test_case.cellType)
            assert subSet[metricIndex][statType.getIndex()] == val, f"Stats at ({metricIndex}, {test_case.cellType}, {statType}) from getStatsFromCellType is exepected to be equal to {val}."

            subSet2: pd.DataFrame = stats.getStatsFromMetric(metricIndex)
            assert subSet2[test_case.cellType][statType.getIndex()] == val, f"Stats at ({metricIndex}, {test_case.cellType}, {statType}) from getStatsFromMetric is exepected to be equal to {val}."

            subSet3: pd.Series = stats.getStatsFromMetricAndCellType(metricIndex, test_case.cellType)
            assert subSet3[statType.getIndex()] == val, f"Stats at ({metricIndex}, {test_case.cellType}, {statType}) from getStatsFromMetricAndCellType is exepected to be equal to {val}."

            valObs: float = stats.getStatValueToMetricAndCellType(metricIndex, test_case.cellType, statType)
            assert valObs == val, f"Stats at ({metricIndex}, {test_case.cellType}, {statType}) from getStatValueFromMetricAndCellType is exepected to be equal to {val}."
