import logging
from typing import Union
import numpy as np
from dataclasses import dataclass

from vtkmodules.util.numpy_support import (
     vtk_to_numpy, )

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, )

from . import vtk_utils

@dataclass( frozen=True )
class Options:
    info: str

np_hinting = Union[np.float32, np.float64, np.int32, np.int64]

@dataclass( frozen=True )
class MeshComponentData:
    componentType: str
    scalar_names: list[str]
    scalar_min_values: list[np_hinting]
    scalar_max_values: list[np_hinting]
    tensor_names: list[str]
    tensor_min_values: list[np.array[np_hinting]]
    tensor_max_values: list[np.array[np_hinting]]

@dataclass( frozen=True )
class Result:
    number_elements: int
    number_nodes: int
    number_cell_types: int
    cell_types: list[str]
    cell_type_counts: list[int]
    min_coords: np.ndarray
    max_coords: np.ndarray
    is_empty_point_global_ids: bool
    is_empty_cell_global_ids: bool
    point_data: MeshComponentData
    cell_data: MeshComponentData

def get_cell_types_and_counts(
        mesh: vtkUnstructuredGrid
    )-> tuple[int, int, list[str], list[int]]:
    """From an unstructured grid, collects the number of cells,
    the number of cell types, the list of cell types and the counts
    of each cell element.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        tuple[int, int, list[str], list[int]]: In order,
        (number_cells, number_cell_types, cell_types, cell_type_counts)
    """
    number_cells: int = mesh.GetNumberOfCells()
    number_cell_types: int = mesh.GetDistinctCellTypesArray().GetSize()
    cell_types: list[str] = []
    for cell_type in range(number_cell_types):
        cell_types.append(vtk_utils.vtkid_to_string(mesh.GetCellType(cell_type)))

    cell_type_counts: list[int] = [0]*number_cell_types
    for cell in range(number_cells):
        for cell_type in range(number_cell_types):
            if vtk_utils.vtkid_to_string(mesh.GetCell(cell).GetCellType()) == cell_types[cell_type]:
                cell_type_counts[cell_type] += 1
                break

    return (number_cells, number_cell_types, cell_types, cell_type_counts)

def get_coords_min_max(mesh: vtkUnstructuredGrid) -> tuple[np.ndarray]:
    """From an unstructured mesh, returns the coordinates of
    the minimum and maximum points.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        tuple[np.ndarray]: Min and Max coordinates.
    """
    coords: np.ndarray = vtk_to_numpy(mesh.GetPoints().GetData())
    min_coords: np.ndarray = coords.min(axis=0)
    max_coords: np.ndarray = coords.max(axis=0)
    return (min_coords, max_coords)

def build_MeshComponentData(
        mesh: vtkUnstructuredGrid, componentType: str = "point"
    ) -> MeshComponentData:
    """Builds a MeshComponentData object for a specific component ("point", "cell")
    If the component type chosen is invalid, chooses "point" by default.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        meshCD (MeshComponentData): Object that gathers data regarding a mesh component.
    """
    if componentType not in ["point", "cell"]:
        componentType = "point"
        logging.error( f"Invalid component type chosen to build MeshComponentData. Defaulted to point." )
    
    if componentType == "point":
        number_arrays_data: int = mesh.GetPointData().GetNumberOfArrays()
    else:
        number_arrays_data = mesh.GetCellData().GetNumberOfArrays()

    meshCD: MeshComponentData = MeshComponentData()
    meshCD.componentType = componentType
    for i in range(number_arrays_data):
        if componentType == "point":
            data_array = mesh.GetPointData().GetArray(i)
        else:
            data_array = mesh.GetCellData().GetArray(i)
        data_array_name = data_array.GetName()
        data_np_array = vtk_to_numpy(data_array)
        if data_array.GetNumberOfComponents() == 1: # assumes scalar cell data for max and min
            meshCD.scalar_names.append(data_array_name)
            meshCD.scalar_max_values.append(data_np_array.max()) 
            meshCD.scalar_min_values.append(data_np_array.min())
        else:
            meshCD.tensor_names.append(data_array_name)
            meshCD.tensor_max_values.append(data_np_array.max(axis=0))
            meshCD.tensor_min_values.append(data_np_array.min(axis=0))

    return meshCD

def __check( mesh: vtkUnstructuredGrid, options: Options ) -> Result:

    number_points: int = mesh.GetNumberOfPoints()
    cells_info = get_cell_types_and_counts(mesh)
    number_cells: int = cells_info[0]
    number_cell_types: int = cells_info[1]
    cell_types: int = cells_info[2]
    cell_type_counts: int = cells_info[3]
    min_coords, max_coords = get_coords_min_max(mesh)
    point_ids: bool = not bool(mesh.GetPointData().GetGlobalIds())
    cell_ids: bool = not bool(mesh.GetCellData().GetGlobalIds())
    point_data: MeshComponentData = build_MeshComponentData(mesh, "point")
    cell_data: MeshComponentData = build_MeshComponentData(mesh, "cell")

    return Result( number_points=number_points, number_cells=number_cells, number_cell_types=number_cell_types,
                   cell_types=cell_types, cell_type_counts=cell_type_counts, min_coords=min_coords, max_coords=max_coords,
                   is_empty_point_global_ids=point_ids, is_empty_cell_global_ids=cell_ids, 
                   point_data=point_data, cell_data=cell_data)

def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )
