# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import unittest
from typing_extensions import Self

from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

import vtk
from vtkmodules.util.numpy_support import (numpy_to_vtk, numpy_to_vtkIdTypeArray,
                                    vtk_to_numpy)

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, 
    vtkCellArray,
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
)

# create test mesh
ID_TYPE = np.int32
if vtk.VTK_ID_TYPE == 12:
    ID_TYPE = np.int64

offset = np.array([0, 4], np.int8)
cells = np.array([0, 1, 2, 3, 4, 5, 6, 7, 8,])
cell_type = np.array([vtk.VTK_TETRA, vtk.VTK_TETRA], np.int32)

cell1 = np.array([[0, 0, 0],
                  [1, 0, 0],
                  [0, 0, 1],
                  [0, 1, 0]])
cell2 = np.array([[1, 0, 0],
                  [1, 1, 0],
                  [0, 0, 1],
                  [0, 1, 0]])

points = np.vstack((cell1, cell2)).astype(np.float64)

if offset.dtype != ID_TYPE:
    offset = offset.astype(ID_TYPE)

if cells.dtype != ID_TYPE:
    cells = cells.astype(ID_TYPE)

if not cells.flags['C_CONTIGUOUS']:
    cells = np.ascontiguousarray(cells)

if cells.ndim != 1:
    cells = cells.ravel()

if cell_type.dtype != np.uint8:
    cell_type = cell_type.astype(np.uint8)

# Get number of cells
ncells = cell_type.size

# Convert to vtk arrays
cell_type = numpy_to_vtk(cell_type)
offset = numpy_to_vtkIdTypeArray(offset)

vtkcells = vtk.vtkCellArray()
vtkcells.SetCells(ncells, numpy_to_vtkIdTypeArray(cells.ravel()))

# Convert points to vtkPoints object
vtkpts = vtk.vtkPoints()
vtkpts.SetData(numpy_to_vtk(points))

inputMesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
inputMesh.SetPoints(vtkpts)
inputMesh.SetCells(cell_type, offset, vtkcells)


class TestsMergeColocatedPoints( unittest.TestCase ):

    def test_init( self: Self ) -> None:
        """Test init method."""
        filter :MergeColocatedPoints = MergeColocatedPoints()
        input = filter.GetInputDataObject(0, 0)
        self.assertIsNone(input, "Input mesh should be undefined.")

    
    def test_SetInputDataObject( self: Self ) -> None:
        """Test SetInputDataObject method."""
        filter :MergeColocatedPoints = MergeColocatedPoints()
        filter.SetInputDataObject(inputMesh)
        input = filter.GetInputDataObject(0, 0)
        self.assertIsNotNone(input, "Input mesh is undefined.")
        output = filter.GetOutputDataObject(0)
        self.assertIsNone(output, "Output mesh should be undefined.")


    def test_Update( self: Self ) -> None:
        """Test Update method."""
        filter :MergeColocatedPoints = MergeColocatedPoints()
        filter.SetInputDataObject(inputMesh)
        filter.Update()
        output :vtkUnstructuredGrid = filter.GetOutputDataObject(0)
        self.assertIsNotNone(output, "Output mesh is undefined.")
        pointsOut: vtkPoints = output.GetPoints()
        self.assertIsNotNone(pointsOut, "Points from output mesh are undefined.")
        self.assertEqual(pointsOut.GetNumberOfPoints(), 5)
        pointCoords: npt.NDArray[np.float64] = vtk_to_numpy(pointsOut.GetData())
        print(pointCoords)

        cellsOut: vtkCellArray = inputMesh.GetCells()
        self.assertIsNotNone(cellsOut, "Cells from output mesh are undefined.")
        cellsPtIds: npt.NDArray[np.int8] = vtk_to_numpy(cellsOut.GetData())
        print(cellsPtIds)  
        self.assertTrue(False, "Manual fail")    
        
