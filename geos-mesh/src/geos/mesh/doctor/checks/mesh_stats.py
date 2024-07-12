import logging
from typing import Union
import numpy as np
from dataclasses import dataclass
from vtkmodules.util.numpy_support import (
     vtk_to_numpy, )
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
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
    num_elements: int
    num_nodes: int
    num_cell_types: int
    cell_types: list[str]
    cell_type_counts: list[int]
    min_coords: np.array
    max_coords: np.array
    is_empty_point_global_ids: bool
    is_empty_cell_global_ids: bool
    cell_data: MeshComponentData
    point_data: MeshComponentData


def __build_MeshComponentData(
        mesh: vtkUnstructuredGrid, componentType: str = "point"
    ) -> MeshComponentData:
    """Builds a MeshComponentData object for a specific component ("points", "cells")
    If the component type chosen is invalid, chooses "points" by default.

    Args:
        mesh (vtkUnstructuredGrid): An unstructured grid.

    Returns:
        meshCD (MeshComponentData): Object that gathers data regarding a mesh component.
    """
    if componentType not in ["points", "cells"]:
        componentType = "point"
        # raise warning
    if componentType == "point":
        number_arrays_data: int = mesh.GetPointData().GetNumberOfArrays()
    else:
        number_arrays_data = mesh.GetCellData().GetNumberOfArrays()

    meshCD: MeshComponentData = MeshComponentData()
    for i in range(number_arrays_data):
        if componentType == "point":
            data_array = mesh.GetPointData().GetArray(i)
        else:
            data_array = mesh.GetCellData().GetArray(i)
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


# @dataclass( frozen=True )
# class Result:
#     num_elements: int
#     num_nodes: int
#     num_cell_types: int
#     cell_types: list
#     cell_type_counts: list
#     scalar_cell_data_names: list
#     scalar_cell_data_mins: list
#     scalar_cell_data_maxs: list
#     tensor_cell_data_names: list
#     scalar_point_data_names: list
#     scalar_point_data_mins: list
#     scalar_point_data_maxs: list
#     tensor_point_data_names: list
#     is_empty_point_global_ids: bool
#     is_empty_cell_global_ids: bool
#     min_coords: list
#     max_coords: list
#     #TODO: compress this, or just print the stuff here and dont pass it


def __check( mesh, options: Options ) -> Result:

    number_elements: int = mesh.GetNumberOfCells()   
    number_nodes: int = mesh.GetNumberOfPoints()
    number_cell_types: int = mesh.GetDistinctCellTypesArray().GetSize()
    cell_types: list[str] = []
    for cell_type in range(number_cell_types):
        cell_types.append(vtk_utils.vtkid_to_string(mesh.GetCellType(cell_type)))

    cell_type_counts: list[int] = [0]*number_cell_types
    for cell in range(number_elements):
        for cell_type in range(number_cell_types):
            if vtk_utils.vtkid_to_string(mesh.GetCell(cell).GetCellType()) == cell_types[cell_type]:
                cell_type_counts[cell_type] += 1
                break

    cell_data_scalar_names: list[str] = []
    cell_data_scalar_maxs: list[np_hinting] = []
    cell_data_scalar_mins: list[np_hinting] = []
    cell_data_tensor_names: list[str] = []
    cell_data_tensor_maxs: list[np_hinting] = []
    cell_data_tensor_mins: list[np_hinting] = []
    number_cell_data: int = mesh.GetCellData().GetNumberOfArrays()
    for i in range(number_cell_data):
        cell_data = mesh.GetCellData().GetArray(i)
        if cell_data.GetNumberOfComponents() == 1: # assumes scalar cell data for max and min
            cell_data_scalar_names.append(cell_data.GetName())
            cell_data_np = vtk_to_numpy(cell_data)
            cell_data_scalar_maxs.append(cell_data_np.max()) 
            cell_data_scalar_mins.append(cell_data_np.min())
        else:
            cell_data_tensor_names.append(cell_data.GetName())
            cell_data_np = vtk_to_numpy(cell_data)
            max_values = cell_data_np.max(axis=0)
            min_values = cell_data_np.min(axis=0)
            cell_data_tensor_maxs.append(max_values)
            cell_data_tensor_mins.append(min_values)

    point_data_scalar_names: list[str] = []
    point_data_scalar_maxs: list[np_hinting] = []
    point_data_scalar_mins: list[np_hinting] = []
    point_data_tensor_names: list[str] = []
    number_point_data = mesh.GetPointData().GetNumberOfArrays()
    for j in range(number_point_data):
        point_data = mesh.GetPointData().GetArray(j)
        if point_data.GetNumberOfComponents() == 1: # assumes scalar point data for max and min
            point_data_scalar_names.append(point_data.GetName())
            point_data_np = vtk_to_numpy(point_data)
            point_data_scalar_maxs.append(point_data_np.max()) 
            point_data_scalar_mins.append(point_data_np.min()) 
        else:
            point_data_tensor_names.append(point_data.GetName())

    point_ids: bool = bool(mesh.GetPointData().GetGlobalIds())
    cell_ids: bool = bool(mesh.GetCellData().GetGlobalIds())

    coords: np.ndarray = vtk_to_numpy(mesh.GetPoints().GetData())
    min_coords: np.ndarray = coords.min(axis=0)
    max_coords: np.ndarray = coords.max(axis=0)
    # center = (coords.max(axis=0) + coords.min(axis=0))/2

    return Result( num_elements=number_elements, num_nodes=number_nodes, num_cell_types=number_cell_types, cell_types=cell_types, cell_type_counts=cell_type_counts, 
                   scalar_cell_data_names=cell_data_scalar_names, scalar_cell_data_mins=cell_data_scalar_mins, scalar_cell_data_maxs=cell_data_scalar_maxs, tensor_cell_data_names=cell_data_tensor_names,
                   scalar_point_data_names=point_data_scalar_names, scalar_point_data_mins=point_data_scalar_mins, scalar_point_data_maxs=point_data_scalar_maxs, tensor_point_data_names=point_data_tensor_names,
                   has_point_global_ids=point_ids, has_cell_global_ids=cell_ids, min_coords=min_coords, max_coords=max_coords )

def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )
