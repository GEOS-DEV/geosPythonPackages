import logging
from dataclasses import dataclass
from vtkmodules.util.numpy_support import (
    numpy_to_vtk,
     vtk_to_numpy, )

from . import vtk_utils

@dataclass( frozen=True )
class Options:
    info: str


@dataclass( frozen=True )
class Result:
    num_elements: int
    num_nodes: int
    num_cell_types: int
    cell_types: list
    cell_type_counts: list
    scalar_cell_data_names: list
    scalar_cell_data_mins: list
    scalar_cell_data_maxs: list
    tensor_cell_data_names: list
    scalar_point_data_names: list
    scalar_point_data_mins: list
    scalar_point_data_maxs: list
    tensor_point_data_names: list
    has_point_global_ids: bool
    has_cell_global_ids: bool
    min_coords: list
    max_coords: list
    #TODO: compress this, or just print the stuff here and dont pass it


def __check( mesh, options: Options ) -> Result:

    ne=mesh.GetNumberOfCells()   
    nn=mesh.GetNumberOfPoints()
    nct = mesh.GetDistinctCellTypesArray().GetSize()
    cts = []
    for ct in range(nct):
        cts.append(vtk_utils.vtkid_to_string(mesh.GetCellType(ct)))

    ct_counts = [0]*nct
    for c in range(ne):
        for ct in range(nct):
            if vtk_utils.vtkid_to_string(mesh.GetCell(c).GetCellType()) == cts[ct]:
                ct_counts[ct] += 1
                break

    cd_scalar_names = []
    cd_scalar_maxs = []
    cd_scalar_mins = []
    ncd = mesh.GetCellData().GetNumberOfArrays()
    for cdi in range(ncd):
        cd = mesh.GetCellData().GetArray(cdi)
        if cd.GetNumberOfComponents() == 1: # assumes scalar cell data for max and min
            cd_scalar_names.append(cd.GetName())
            cd_np = vtk_to_numpy(cd)
            cd_scalar_maxs.append(cd_np.max()) 
            cd_scalar_mins.append(cd_np.min()) 

    cd_tensor_names = []
    for cdi in range(ncd):
        cd = mesh.GetCellData().GetArray(cdi)
        if cd.GetNumberOfComponents() != 1:
            cd_tensor_names.append(cd.GetName())

    pd_scalar_names = []
    pd_scalar_maxs = []
    pd_scalar_mins = []
    npd = mesh.GetPointData().GetNumberOfArrays()
    for pdi in range(npd):
        pd = mesh.GetPointData().GetArray(pdi)
        if pd.GetNumberOfComponents() == 1: # assumes scalar point data for max and min
            pd_scalar_names.append(pd.GetName())
            pd_np = vtk_to_numpy(pd)
            pd_scalar_maxs.append(pd_np.max()) 
            pd_scalar_mins.append(pd_np.min()) 

    pd_tensor_names = []
    for pdi in range(npd):
        pd = mesh.GetPointData().GetArray(pdi)
        if pd.GetNumberOfComponents() != 1:
            pd_tensor_names.append(pd.GetName())

    point_ids = bool(mesh.GetPointData().GetGlobalIds())
    cell_ids = bool(mesh.GetCellData().GetGlobalIds())

    coords = vtk_to_numpy(mesh.GetPoints().GetData())
    center = (coords.max(axis=0) + coords.min(axis=0))/2


    return Result( num_elements=ne, num_nodes=nn, num_cell_types=nct, cell_types=cts, cell_type_counts=ct_counts, 
                   scalar_cell_data_names=cd_scalar_names, scalar_cell_data_mins=cd_scalar_mins, scalar_cell_data_maxs=cd_scalar_maxs, tensor_cell_data_names=cd_tensor_names,
                   scalar_point_data_names=pd_scalar_names, scalar_point_data_mins=pd_scalar_mins, scalar_point_data_maxs=pd_scalar_maxs, tensor_point_data_names=pd_tensor_names,
                   has_point_global_ids=point_ids, has_cell_global_ids=cell_ids, min_coords=coords.min(axis=0), max_coords=coords.max(axis=0) )

def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )
