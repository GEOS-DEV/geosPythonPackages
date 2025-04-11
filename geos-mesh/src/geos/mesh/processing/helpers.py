# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
from typing import Sequence

from vtkmodules.util.numpy_support import numpy_to_vtk

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, 
    vtkIncrementalOctreePointLocator
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
    reference,
)

def getBounds(cellPtsCoord: list[npt.NDArray[np.float64]]) -> Sequence[float]:
    """Compute bounding box coordinates of the list of points.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of points

    Returns:
        Sequence[float]: bounding box coordinates (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    bounds: list[float] = [np.inf, -np.inf, np.inf, -np.inf, np.inf, -np.inf,]
    for ptsCoords in cellPtsCoord:
        mins: npt.NDArray[np.float64] = np.min(ptsCoords, axis=0)
        maxs: npt.NDArray[np.float64] = np.max(ptsCoords, axis=0)
        for i in range(3):
            bounds[2 * i] = float(min(bounds[2 * i], mins[i]))
            bounds[2 * i + 1] = float(max(bounds[2 * i + 1], maxs[i]))
    return bounds

def createSingleCellMesh(cellType: int, ptsCoord: npt.NDArray[np.float64]) ->vtkUnstructuredGrid:
    """Create a mesh that consists of a single cell.

    Args:
        cellType (int): cell type
        ptsCoord (1DArray[np.float64]): cell point coordinates

    Returns:
        vtkUnstructuredGrid: output mesh
    """
    nbPoints: int = ptsCoord.shape[0]
    points: npt.NDArray[np.float64] = np.vstack((ptsCoord,))
    # Convert points to vtkPoints object
    vtkpts: vtkPoints = vtkPoints()
    vtkpts.SetData(numpy_to_vtk(points))

    # create cells from point ids
    cellsID: vtkIdList = vtkIdList()
    for j in range( nbPoints ):
        cellsID.InsertNextId(j)

    # add cell to mesh
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    mesh.SetPoints(vtkpts)
    mesh.Allocate(1)
    mesh.InsertNextCell(cellType, cellsID)
    return mesh

def createMultiCellMesh(cellTypes: list[int], 
                        cellPtsCoord: list[npt.NDArray[np.float64]],
                        sharePoints: bool = True
                        ) ->vtkUnstructuredGrid:
    """Create a mesh that consists of multiple cells.

    .. WARNING:: the mesh is not check for conformity.

    Args:
        cellTypes (list[int]): cell type
        cellPtsCoord (list[1DArray[np.float64]]): list of cell point coordinates
        sharePoints (bool): if True, cells share points, else a new point is created fro each cell vertex

    Returns:
        vtkUnstructuredGrid: output mesh
    """
    assert len(cellPtsCoord) == len(cellTypes), "The lists of cell types of point coordinates must be of same size."
    nbCells: int = len(cellPtsCoord)
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    points: vtkPoints
    cellVertexMapAll: list[tuple[int, ...]]
    points, cellVertexMapAll = createVertices(cellPtsCoord, sharePoints)
    assert len(cellVertexMapAll) == len(cellTypes), "The lists of cell types of cell point ids must be of same size."
    mesh.SetPoints(points)
    mesh.Allocate(nbCells)
    # create mesh cells
    for cellType, ptsId in zip(cellTypes, cellVertexMapAll, strict=True):       
        # create cells from point ids
        cellsID: vtkIdList = vtkIdList()
        for ptId in ptsId:
            cellsID.InsertNextId(ptId)    
        mesh.InsertNextCell(cellType, cellsID)
    return mesh

def createVertices(cellPtsCoord: list[npt.NDArray[np.float64]], 
                   shared: bool = True
                  ) -> tuple[vtkPoints, list[tuple[int, ...]]]:
    """Create vertices from cell point coordinates list.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of cell point coordinates
        shared (bool, optional): If True, collocated points are merged. Defaults to True.

    Returns:
        tuple[vtkPoints, list[tuple[int, ...]]]: tuple containing points and the
            map of cell point ids
    """
    # get point bounds
    bounds: list[float] = getBounds(cellPtsCoord)
    points: vtkPoints = vtkPoints()
    # use point locator to check for colocated points
    pointsLocator = vtkIncrementalOctreePointLocator()
    pointsLocator.InitPointInsertion(points, bounds)
    cellVertexMapAll: list[tuple[int, ...]] = []
    ptId: reference = reference(0)
    ptsCoords: npt.NDArray[np.float64]
    for ptsCoords in cellPtsCoord:
        cellVertexMap: list[reference] = []
        pt: npt.NDArray[np.float64] # 1DArray
        for pt in ptsCoords:
            if shared:
                pointsLocator.InsertUniquePoint( pt.tolist(), ptId)
            else:
                pointsLocator.InsertPointWithoutChecking( pt.tolist(), ptId, 1)
            cellVertexMap += [ptId.get()]
        cellVertexMapAll += [tuple(cellVertexMap)]
    return points, cellVertexMapAll
