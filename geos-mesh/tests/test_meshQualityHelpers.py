# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pytest
from typing import (
    Iterator,
)

from geos.mesh.vtk.helpers import createMultiCellMesh
from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellArray,
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON, VTK_POLYGON, VTK_POLYHEDRON
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
)

from geos.mesh.processing.meshQualityMetricHelpers import (
    QualityMetricEnum,
    getQualityMeasureFromCellType,
    getTriangleQualityMeasure,
    getQuadQualityMeasure,
    getTetQualityMeasure,
    getPyramidQualityMeasure,
    getWedgeQualityMeasure,
    getHexQualityMeasure,
    getCommonPolygonQualityMeasure,
    getCommonPolyhedraQualityMeasure,
    getQualityMeasureNameFromIndex,
    getQualityMeasureIndexFromName,
    getAllCellTypesExtended,
)

triangleQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.AREA,
    vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,
    vtkMeshQuality.QualityMeasureTypes.ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.CONDITION,
    vtkMeshQuality.QualityMeasureTypes.DISTORTION,
    vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE,
    vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,
    vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS,
    vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,
    vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE
}

quadQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.AREA,
    vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,
    vtkMeshQuality.QualityMeasureTypes.CONDITION,
    vtkMeshQuality.QualityMeasureTypes.DISTORTION,
    vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.MAX_EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.MAX_ANGLE,
    vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,
    vtkMeshQuality.QualityMeasureTypes.ODDY,
    vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,
    vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,
    vtkMeshQuality.QualityMeasureTypes.SHEAR,
    vtkMeshQuality.QualityMeasureTypes.SHEAR_AND_SIZE,
    vtkMeshQuality.QualityMeasureTypes.SKEW,
    vtkMeshQuality.QualityMeasureTypes.STRETCH,
    vtkMeshQuality.QualityMeasureTypes.TAPER,
    vtkMeshQuality.QualityMeasureTypes.WARPAGE,
}

tetQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.ASPECT_GAMMA,
    vtkMeshQuality.QualityMeasureTypes.ASPECT_RATIO,
    vtkMeshQuality.QualityMeasureTypes.COLLAPSE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.CONDITION,
    vtkMeshQuality.QualityMeasureTypes.DISTORTION,
    vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.EQUIVOLUME_SKEW,
    vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.MEAN_RATIO,
    vtkMeshQuality.QualityMeasureTypes.MIN_ANGLE,
    vtkMeshQuality.QualityMeasureTypes.NORMALIZED_INRADIUS,
    vtkMeshQuality.QualityMeasureTypes.RADIUS_RATIO,
    vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,
    vtkMeshQuality.QualityMeasureTypes.SQUISH_INDEX,
    vtkMeshQuality.QualityMeasureTypes.VOLUME,
}

pyrQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.VOLUME,
}

wedgeQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.CONDITION,
    vtkMeshQuality.QualityMeasureTypes.DISTORTION,
    vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.MAX_STRETCH,
    vtkMeshQuality.QualityMeasureTypes.MEAN_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.VOLUME,
}

hexQualityMeasureExp: set[int] = {
    vtkMeshQuality.QualityMeasureTypes.CONDITION,
    vtkMeshQuality.QualityMeasureTypes.DIAGONAL,
    vtkMeshQuality.QualityMeasureTypes.DIMENSION,
    vtkMeshQuality.QualityMeasureTypes.DISTORTION,
    vtkMeshQuality.QualityMeasureTypes.EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.EQUIANGLE_SKEW,
    vtkMeshQuality.QualityMeasureTypes.JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.MAX_EDGE_RATIO,
    vtkMeshQuality.QualityMeasureTypes.MAX_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.MED_ASPECT_FROBENIUS,
    vtkMeshQuality.QualityMeasureTypes.NODAL_JACOBIAN_RATIO,
    vtkMeshQuality.QualityMeasureTypes.ODDY,
    vtkMeshQuality.QualityMeasureTypes.RELATIVE_SIZE_SQUARED,
    vtkMeshQuality.QualityMeasureTypes.SCALED_JACOBIAN,
    vtkMeshQuality.QualityMeasureTypes.SHAPE,
    vtkMeshQuality.QualityMeasureTypes.SHAPE_AND_SIZE,
    vtkMeshQuality.QualityMeasureTypes.SHEAR,
    vtkMeshQuality.QualityMeasureTypes.SHEAR_AND_SIZE,
    vtkMeshQuality.QualityMeasureTypes.SKEW,
    vtkMeshQuality.QualityMeasureTypes.STRETCH,
    vtkMeshQuality.QualityMeasureTypes.TAPER,
    vtkMeshQuality.QualityMeasureTypes.VOLUME,
}

@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: input mesh
    qualityMetricIndex: int
    #: expected points
    qualityMetricName: str

def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for metric in list(QualityMetricEnum):
        yield TestCase( metric.metricIndex, metric.metricName )

def test_QualityMetricEnumOrder() ->None:
    """Test QualityMetricEnum ordering is correct."""
    for i, metric in enumerate(list(QualityMetricEnum)):
        assert metric.metricIndex == i

ids: list[str] = [metric.metricName for metric in list(QualityMetricEnum)]
@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_getQualityMeasureNameFromIndex( test_case: TestCase ) ->None:
    """Test of getQualityMeasureNameFromIndex method."""
    name: str = getQualityMeasureNameFromIndex(test_case.qualityMetricIndex)
    assert name == test_case.qualityMetricName

ids: list[str] = [metric.metricName for metric in list(QualityMetricEnum)]
@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_getQualityMeasureIndexFromName( test_case: TestCase ) ->None:
    """Test of getQualityMeasureIndexFromName method."""
    index: int = getQualityMeasureIndexFromName(test_case.qualityMetricName)
    assert index == test_case.qualityMetricIndex

def test_getQualityMeasureFromCellType_exception() ->None:
    """Test of supported cell type from getQualityMeasureFromCellType method."""
    for i in range(20):
        if i in (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON, VTK_POLYGON, VTK_POLYHEDRON):
            assert len(getQualityMeasureFromCellType(i)) > 0
        else:
            with pytest.raises(ValueError) as pytest_wrapped_e:
                getQualityMeasureFromCellType(i)
            assert pytest_wrapped_e.type is ValueError

def test_getTriangleQualityMeasure() -> None:
    """Test of getTriangleQualityMeasure method."""
    obs: set[int] = getTriangleQualityMeasure()
    diffAdditional: set[int] = obs.difference(triangleQualityMeasureExp)
    diffMissing: set[int] = triangleQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(triangleQualityMeasureExp)]
    assert sorted(obs) == sorted(triangleQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getQuadQualityMeasure() -> None:
    """Test of getQuadQualityMeasure method."""
    obs: set[int] = getQuadQualityMeasure()
    diffAdditional: set[int] = obs.difference(quadQualityMeasureExp)
    diffMissing: set[int] = quadQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(quadQualityMeasureExp)]
    assert sorted(obs) == sorted(quadQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getCommonPolygonQualityMeasure() -> None:
    """Test of getCommonPolygonQualityMeasure method."""
    obs: set[int] = getCommonPolygonQualityMeasure()
    exp: set[int] = quadQualityMeasureExp.intersection(triangleQualityMeasureExp)
    diffAdditional: set[int] = obs.difference(exp)
    diffMissing: set[int] = exp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(exp)]
    assert sorted(obs) == sorted(exp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getTetQualityMeasure() -> None:
    """Test of getTetQualityMeasure method."""
    obs: set[int] = getTetQualityMeasure()
    diffAdditional: set[int] = obs.difference(tetQualityMeasureExp)
    diffMissing: set[int] = tetQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(tetQualityMeasureExp)]
    assert sorted(obs) == sorted(tetQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getPyramidQualityMeasure() -> None:
    """Test of getPyramidQualityMeasure method."""
    obs: set[int] = getPyramidQualityMeasure()
    diffAdditional: set[int] = obs.difference(pyrQualityMeasureExp)
    diffMissing: set[int] = pyrQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(pyrQualityMeasureExp)]
    assert sorted(obs) == sorted(pyrQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getWedgeQualityMeasure() -> None:
    """Test of getWedgeQualityMeasure method."""
    obs: set[int] = getWedgeQualityMeasure()
    diffAdditional: set[int] = obs.difference(wedgeQualityMeasureExp)
    diffMissing: set[int] = wedgeQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(wedgeQualityMeasureExp)]
    assert sorted(obs) == sorted(wedgeQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getHexQualityMeasure() -> None:
    """Test of getHexQualityMeasure method."""
    obs: set[int] = getHexQualityMeasure()
    diffAdditional: set[int] = obs.difference(hexQualityMeasureExp)
    diffMissing: set[int] = hexQualityMeasureExp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(hexQualityMeasureExp)]
    assert sorted(obs) == sorted(hexQualityMeasureExp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getCommonPolyhedraQualityMeasure() -> None:
    """Test of getCommonPolyhedraQualityMeasure method."""
    obs: set[int] = getCommonPolyhedraQualityMeasure()
    exp: set[int] = tetQualityMeasureExp.intersection(pyrQualityMeasureExp).intersection(wedgeQualityMeasureExp).intersection(hexQualityMeasureExp)
    diffAdditional: set[int] = obs.difference(exp)
    diffMissing: set[int] = exp.difference(obs)
    messAdditional: str = f"{len(diffAdditional)} additional elements"
    if len(diffAdditional) > 0:
        messAdditional += f" including {[getQualityMeasureNameFromIndex(index) for index in diffAdditional]}"
    messMissing: str = f" and {len(diffMissing)} missing elements"
    if len(diffMissing):
        messMissing += f" including {[getQualityMeasureNameFromIndex(index) for index in diffMissing]}"
    expNames: list[str] = [getQualityMeasureNameFromIndex(index) for index in sorted(exp)]
    assert sorted(obs) == sorted(exp), f"Expected metrics are {expNames}. Observed metrics contains " + messAdditional + messMissing

def test_getAllCellTypesExtended() ->None:
    """Test of getAllCellTypesExtended method."""
    cellTypesExp: list[int] = [VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON, VTK_POLYGON, VTK_POLYHEDRON]
    assert cellTypesExp == getAllCellTypesExtended(), "Cell types differ."
