import vtk
import time
from vtkmodules.vtkCommonDataModel import vtkBoundingBox
from enum import IntEnum   
import numpy as np

class PIECE(IntEnum):
    ONPOINT =  1
    ONCELL = 2


block2block = [[]] # map index of the source blocks itersecting the target blocks 

def clamp_interpolate(mesh_source, mesh_target, _get_points):

    #because of distributed vtm format we use distributed datastruct (e.g. list are list of list then reduced)
    kd = vtk.vtkKdTree()
    kd.BuildLocatorFromPoints( _get_points(mesh_source))

    tg_pts = _get_points( mesh_target)
    source2target = [[] for i in range(tg_pts.GetNumberOfPoints())] # map index from source to target
    for i in range(tg_pts.GetNumberOfPoints()):
        dist = vtk.reference(0.)
        id_source = kd.FindClosestPoint(tg_pts.GetPoint(i),dist)
        source2target[i].append( (dist,id_source) )
    
    return source2target

# def _within_block(i, box_target):

#     for iblock, block in mesh_source:
#         block2block[itarget].append( iblock if vtkBoundingBox( block.bounds() ).IntersectBox( box_target ) )


def reduce(listOfList):
    return [min(llist)[1] for llist in listOfList]


def _get_cellCenters(mesh):
    centers = vtk.vtkCellCenters()
    centers.SetInputData(mesh)
    centers.Update()

    return centers.GetOutput().GetPoints()

def _vectorize_fields_out(fieldnames, mesh, piece):
    from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
    #use numpy for some speedup
    if piece == PIECE.ONPOINT: 
        fp = np.zeros(shape=(mesh.GetNumberOfPoints(), len(fieldnames)), dtype=float)
    elif piece == PIECE.ONCELL:
        fp = np.zeros(shape=(mesh.GetNumberOfCells(), len(fieldnames)), dtype=float)

    for j,field in enumerate(fieldnames):
        if piece == PIECE.ONPOINT:
            data = mesh.GetPointData().GetArray(field[0])
        elif piece == PIECE.ONCELL:
            data = mesh.GetCellData().GetArray(field[0])

        fp[:,j] = vtk_to_numpy(data)
    
    return fp

def _vectorize_fields_in(fieldnames, mesh, fp,  piece):
    from vtk.util.numpy_support import vtk_to_numpy, numpy_to_vtk
    #use numpy for some speedup

    for j,field in enumerate(fieldnames):
        arr = numpy_to_vtk(fp[:,j])
        arr.SetName(field[1])
        if piece == PIECE.ONPOINT:
            mesh.GetPointData().AddArray(arr)
        elif piece == PIECE.ONCELL:
            mesh.GetCellData().AddArray(arr)

    return fp

def main():

    reader = vtk.vtkXMLUnstructuredGridReader()
    # reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/geos-data/Case2/Outputs_GNL_Coupled_Case2_Test6_585524-100/GNL/000086/MESH/Level0/Drake/rank_43.vtu')
    reader.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/data/GNL/Asmae/Mesh/GNL_update_poro.vtu')
    reader.Update()
    source_mesh = reader.GetOutput()
    
    # reader.SetFileName('')
    reader.Update()
    target_mesh = reader.GetOutput()

    section = 'mapping'
    start = time.perf_counter()
    pt_s2t = reduce( clamp_interpolate( source_mesh, target_mesh, lambda m : m.GetPoints() ) )
    c_s2t = reduce( clamp_interpolate( source_mesh, target_mesh, lambda m : _get_cellCenters(m) ) )
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

    print(pt_s2t[1:10])
    print(c_s2t[1:10])

    section = 'Vectorizing'
    start = time.perf_counter()
    # c_fieldnames = [('pressure','mapped_pressure')] # for rank43 test
    c_fieldnames = [('Porosity','mapped_POROSITY')] # for GNL test
    # pt_fieldnames = [('','')]
    c_source_vec = _vectorize_fields_out(c_fieldnames,source_mesh, PIECE.ONCELL)
    _vectorize_fields_in(c_fieldnames, target_mesh, c_source_vec[c_s2t,:],  PIECE.ONCELL)
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

    section = 'Writing'
    start = time.perf_counter()
    writer = vtk.vtkXMLUnstructuredGridWriter()
    writer.SetFileName('/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/data/GNL/Asmae/Mesh/GNL_update_poro_new.vtu')
    writer.SetInputData(target_mesh)
    writer.Update()
    writer.Write()
    end = time.perf_counter()
    print(f"[{section}] Elapsed time: {end - start:.6f} seconds")

    # later tri-linear interp on simplexes
    #neigh = vtk.vtkIdList()
    #kd.FindClosestNPoints(3,(2,0,0),neigh)
    #neigh.GetId(0)


if __name__ == "__main__":
    main()
