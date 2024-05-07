import logging
from dataclasses import dataclass
from math import sqrt
from numpy import empty
from numpy.random import rand

from vtkmodules.util.numpy_support import (
    numpy_to_vtk,
    vtk_to_numpy, )

from vtkmodules.vtkCommonCore import (
    vtkDoubleArray, )

from . import vtk_utils

@dataclass( frozen=True )
class Options:
    support: str
    field_name: str
    source: str
    out_vtk: vtk_utils.VtkOutput


@dataclass( frozen=True )
class Result:
    info: bool

def __analytic_field(mesh, support, name) -> bool:
    if support == 'node':
        # example function: distance from mesh center
        nn = mesh.GetNumberOfPoints()
        coords = vtk_to_numpy(mesh.GetPoints().GetData())
        center = (coords.max(axis=0) + coords.min(axis=0))/2
        data_arr = vtkDoubleArray()
        data_np = empty(nn)

        for i in range(nn):
            val = 0
            pt = mesh.GetPoint(i)
            for j in range(len(pt)):
                val += (pt[j] - center[j])*(pt[j]-center[j])
            val = sqrt(val)
            data_np[i] = val
        
        data_arr = numpy_to_vtk(data_np)
        data_arr.SetName(name)
        mesh.GetPointData().AddArray(data_arr)
        return True

    elif support == 'cell':
        # example function: random field
        ne = mesh.GetNumberOfCells()
        data_arr = vtkDoubleArray()
        data_np = rand(ne, 1)

        data_arr = numpy_to_vtk(data_np)
        data_arr.SetName(name)
        mesh.GetCellData().AddArray(data_arr)
        return True
    else:
        logging.error('incorrect support option. Options are node, cell')
        return False

def __compatible_meshes(dest_mesh, source_mesh) -> bool:
    # for now, just check that meshes have same number of elements and same number of nodes
    # and require that each cell has same nodes, each node has same coordinate
    dest_ne = dest_mesh.GetNumberOfCells()
    dest_nn = dest_mesh.GetNumberOfPoints()
    source_ne = source_mesh.GetNumberOfCells()
    source_nn = source_mesh.GetNumberOfPoints()

    if dest_ne != source_ne:
        logging.error('meshes have different number of cells')
        return False
    if dest_nn != source_nn:
        logging.error('meshes have different number of nodes')
        return False
    
    for i in range(dest_nn):
        if not ((dest_mesh.GetPoint(i)) == (source_mesh.GetPoint(i))):
            logging.error('at least one node is in a different location')
            return False
    
    for i in range(dest_ne):
        if not (vtk_to_numpy(dest_mesh.GetCell(i).GetPoints().GetData()) == vtk_to_numpy(source_mesh.GetCell(i).GetPoints().GetData())).all():
            logging.error('at least one cell has different nodes')
            return False
        
    return True
        
    




def __transfer_field(mesh, support, field_name, source) -> bool:
    from_mesh = vtk_utils.read_mesh( source )
    same_mesh = __compatible_meshes(mesh, from_mesh)
    if not same_mesh:
        logging.error('meshes are not the same')
        return False
        
    if support == 'cell':
        data = from_mesh.GetCellData().GetArray(field_name)
        if data == None:
            logging.error('Requested field does not exist on source mesh')
            return False
        else:
            mesh.GetCellData().AddArray(data)
    elif support == 'node':
        data = from_mesh.GetPointData().GetArray(field_name)
        if data == None:
            logging.error('Requested field does not exist on source mesh')
            return False
        else:
            mesh.GetPointData().AddArray(data)
            return False
    else:
        logging.error('incorrect support option. Options are node, cell')
        return False
    return True


def __check( mesh, options: Options ) -> Result:
    if options.source == 'function':
        succ =__analytic_field(mesh, options.support, options.field_name)
        if succ:
            vtk_utils.write_mesh( mesh, options.out_vtk )
    elif (options.source[-4:] == '.vtu' or options.source[-4:] == '.vtk'):
        succ = __transfer_field(mesh, options.support, options.field_name, options.source)
        if succ:
            vtk_utils.write_mesh( mesh, options.out_vtk )
    else: 
        logging.error('incorrect source option. Options are function, *.vtu, *.vtk.')
        succ = False
    return Result(info=succ)
    #TODO: Better exception handle



def check( vtk_input_file: str, options: Options ) -> Result:
    mesh = vtk_utils.read_mesh( vtk_input_file )
    return __check( mesh, options )