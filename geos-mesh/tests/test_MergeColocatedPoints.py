# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pytest
from typing_extensions import Self
from typing import (
    Iterator,
)

from geos.mesh.processing.helpers import create_single_cell_mesh
from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

from vtkmodules.util.numpy_support import vtk_to_numpy

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, 
    vtkCellArray,
    vtkCellData,
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID,
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
    vtkDataArray,
)


#from vtkmodules.vtkFiltersSources import vtkCubeSource


data_root: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")



data_filename_all = (tetra_path, hexa_path, pyramid_path, triangle_path, quad_path)
cell_types_all = (tetra_cell_type, hexa_cell_type, pyramid_cell_type, triangle_cell_type, quad_cell_type)
points_out_all = (tetra_points_out, hexa_points_out, pyramid_points_out, triangle_points_out, quad_points_out)
cells_out_all = (tetra_cells_out, hexa_cells_out, pyramid_cells_out, triangle_cells_out, quad_cells_out)

@dataclass( frozen=True )
class TestCase:
    """Test case"""
    __test__ = False
    #: VTK cell type
    cellType: int
    #: mesh
    mesh: vtkUnstructuredGrid
    #: expected new point coordinates
    pointsExp: npt.NDArray[np.float64]
    #: expected new cell point ids
    cellsExp: list[int]
    

def __generate_split_mesh_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, data_path, pointsExp, cellsExp in zip(
        cell_types_all, data_filename_all, points_out_all, cells_out_all,
        strict=True):
        ptsCoord: npt.NDArray[np.float64] = np.loadtxt(os.path.join(data_root, data_path), dtype=float, delimiter=',')
        mesh: vtkUnstructuredGrid = create_single_cell_mesh(cellType, ptsCoord)
        yield TestCase( cellType, mesh, pointsExp, cellsExp )
  

ids = [vtkCellTypes.GetClassNameFromTypeId(cellType) for cellType in cell_types_all]
@pytest.mark.parametrize( "test_case", __generate_split_mesh_test_data(), ids=ids )
def test_single_cell_split( test_case: TestCase ):
    """Test of SplitMesh filter with meshes composed of a single cell.

    Args:
        test_case (TestCase): test case
    """
    cellTypeName: str = vtkCellTypes.GetClassNameFromTypeId(test_case.cellType)
    filter :MergeColocatedPoints = MergeColocatedPoints()
    filter.SetInputDataObject(test_case.mesh)
    filter.Update()
    output :vtkUnstructuredGrid = filter.GetOutputDataObject(0)
    assert output is not None, "Output mesh is undefined."
    pointsOut: vtkPoints = output.GetPoints()
    assert pointsOut is not None, "Points from output mesh are undefined."
    assert pointsOut.GetNumberOfPoints() == test_case.pointsExp.shape[0], f"Number of points is expected to be {test_case.pointsExp.shape[0]}."
    pointCoords: npt.NDArray[np.float64] = vtk_to_numpy(pointsOut.GetData())
    print("Points coords: ", cellTypeName, pointCoords.tolist())
    assert np.array_equal(pointCoords.ravel(), test_case.pointsExp.ravel()), "Points coordinates mesh are wrong."

    cellsOut: vtkCellArray = output.GetCells()
    typesArray0: npt.NDArray[np.int64] = vtk_to_numpy(output.GetDistinctCellTypesArray())
    print("typesArray0", cellTypeName, typesArray0)

    assert cellsOut is not None, "Cells from output mesh are undefined."
    assert cellsOut.GetNumberOfCells() == len(test_case.cellsExp), f"Number of cells is expected to be {len(test_case.cellsExp)}."
    # check cell types
    types: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes(types)
    assert types is not None, "Cell types must be defined"
    typesArray: npt.NDArray[np.int64] = vtk_to_numpy(types.GetCellTypesArray())
    
    print("typesArray", cellTypeName, typesArray)
    assert (typesArray.size == 1) and (typesArray[0] == test_case.cellType), f"All cells must be {cellTypeName}"
    
    for i in range(cellsOut.GetNumberOfCells()):
        ptIds = vtkIdList()
        cellsOut.GetCellAtId(i, ptIds)
        cellsOutObs: list[int] = [ptIds.GetId(j) for j in range(ptIds.GetNumberOfIds())]
        nbPtsExp: int = len(test_case.cellsExp[i])
        print("cell type", cellTypeName, i, vtkCellTypes.GetClassNameFromTypeId(types.GetCellType(i)))
        print("cellsOutObs: ", cellTypeName, i, cellsOutObs)
        assert ptIds is not None, "Point ids must be defined"
        assert ptIds.GetNumberOfIds() == nbPtsExp, f"Cells must be defined by {nbPtsExp} points."
        assert cellsOutObs == test_case.cellsExp[i], "Cell point ids are wrong."

    # test originalId array was created
    cellData: vtkCellData = output.GetCellData()
    assert cellData is not None, "Cell data should be defined."
    array: vtkDataArray = cellData.GetArray("OriginalID")
    assert array is not None, "OriginalID array should be defined."

    # test other arrays were transferred
    cellDataInput: vtkCellData = test_case.mesh.GetCellData()
    assert cellDataInput is not None, "Cell data from input mesh should be defined."
    nbArrayInput: int = cellDataInput.GetNumberOfArrays()
    nbArraySplited: int = cellData.GetNumberOfArrays()
    assert nbArraySplited == nbArrayInput + 1, f"Number of arrays should be {nbArrayInput + 1}"
  
        
