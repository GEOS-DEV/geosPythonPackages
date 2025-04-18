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

from geos.mesh.processing.helpers import createSingleCellMesh

from vtkmodules.util.numpy_support import vtk_to_numpy

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellArray,
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
)

# inputs
data_root: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

data_filename_all: tuple[str,...] = ("triangle_cell.csv", "quad_cell.csv", "tetra_cell.csv", "pyramid_cell.csv", "hexa_cell.csv")
cell_type_all: tuple[int, ...] = (VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON)


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: VTK cell type
    cellType: int
    #: cell point coordinates
    cellPoints: npt.NDArray[np.float64]

def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, path in zip(
        cell_type_all, data_filename_all,
        strict=True):
        cell: npt.NDArray[np.float64] = np.loadtxt(os.path.join(data_root, path), dtype=float, delimiter=',')
        yield TestCase( cellType, cell )


ids: list[str] = [vtkCellTypes.GetClassNameFromTypeId(cellType) for cellType in cell_type_all]
@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_createSingleCellMesh( test_case: TestCase ) ->None:
    """Test of createSingleCellMesh method.

    Args:
        test_case (TestCase): test case
    """
    cellTypeName: str = vtkCellTypes.GetClassNameFromTypeId(test_case.cellType)
    output: vtkUnstructuredGrid = createSingleCellMesh(test_case.cellType, test_case.cellPoints)

    assert output is not None, "Output mesh is undefined."
    pointsOut: vtkPoints = output.GetPoints()
    nbPtsExp: int = len(test_case.cellPoints)
    assert pointsOut is not None, "Points from output mesh are undefined."
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[np.float64] = vtk_to_numpy(pointsOut.GetData())
    print("Points coords: ", cellTypeName, pointCoords.tolist())
    assert np.array_equal(pointCoords.ravel(), test_case.cellPoints.ravel()), "Points coordinates are wrong."

    cellsOut: vtkCellArray = output.GetCells()
    typesArray0: npt.NDArray[np.int64] = vtk_to_numpy(output.GetDistinctCellTypesArray())
    print("typesArray0", cellTypeName, typesArray0)

    assert cellsOut is not None, "Cells from output mesh are undefined."
    assert cellsOut.GetNumberOfCells() == 1, "Number of cells is expected to be 1."
    # check cell types
    types: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes(types)
    assert types is not None, "Cell types must be defined"
    typesArray: npt.NDArray[np.int64] = vtk_to_numpy(types.GetCellTypesArray())

    print("typesArray", cellTypeName, typesArray)
    assert (typesArray.size == 1) and (typesArray[0] == test_case.cellType), f"Cell must be {cellTypeName}"

    ptIds = vtkIdList()
    cellsOut.GetCellAtId(0, ptIds)
    cellsOutObs: list[int] = [ptIds.GetId(j) for j in range(ptIds.GetNumberOfIds())]

    print("cell type", cellTypeName, vtkCellTypes.GetClassNameFromTypeId(types.GetCellType(0)))
    print("cellsOutObs: ", cellTypeName, cellsOutObs)
    assert ptIds is not None, "Point ids must be defined"
    assert ptIds.GetNumberOfIds() == nbPtsExp, f"Cells must be defined by {nbPtsExp} points."
    assert cellsOutObs == list(range(nbPtsExp)), "Cell point ids are wrong."

