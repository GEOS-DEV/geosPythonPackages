import pytest
from dataclasses import dataclass
from typing import Generator
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkHexahedron, VTK_HEXAHEDRON
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter # for writing the output tmp
import logging # for debug
from vtkmodules.numpy_interface import dataset_adapter as dsa
import numpy as np
from vtkmodules.util.vtkConstants import VTK_HEXAHEDRON

from geos.mesh.processing.rotateAndTranslate import transform_mesh

@dataclass( frozen=True )
class Expected:
    mesh: vtkUnstructuredGrid

def __gen_box(Lx:int, Ly:int, Lz:int, nx:int, ny:int, nz:int)-> tuple[np.ndarray, np.ndarray]:
    # np.random.seed(1) # for reproducibility
    np.random.default_rng()
    off = np.random.randn(1, 3)
    pts = []
    x,y,z = np.meshgrid(np.linspace(0,Lx,nx),np.linspace(0,Ly,ny),np.linspace(0,Lz,ny))
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            for k in range(x.shape[2]):
                pts.append(np.asarray([x[i,j,k], y[i,j,k], z[i,j,k]]))

    return (np.asarray(pts), off)

def __rotate_box(angles : np.ndarray, pts:np.ndarray) -> np.ndarray:
    a = angles[0]
    RX = np.asarray([[1., 0, 0], [0, np.cos(a), -np.sin(a)], [0, np.sin(a), np.cos(a)]])
    a = angles[1]
    RY = np.asarray([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])
    a = angles[2]
    RZ = np.asarray([[np.cos(a), -np.sin(a), 0], [np.sin(a), np.cos(a), 0], [0, 0, 1]])

    return np.asarray((RZ @ RY @ RX @ pts.transpose()).transpose())

def __build_test_mesh() -> Generator[ Expected, None, None ]:
    # generate random points in a box Lx, Ly, Lz
    # np.random.seed(1) # for reproducibility
    np.random.default_rng()
    Lx, Ly, Lz = (2, 5, 8) # box size
    nx, ny, nz = (10, 10, 10) # number of points in each direction
    pts, off = __gen_box(Lx, Ly, Lz, nx, ny, nz)

    logging.warning(f"Offseting of {off}")
    logging.warning(f"Original pts : {pts}")
    angles = -2*np.pi + np.random.randn(1, 3)*np.pi # random angles in rad
    logging.warning(f"angles {angles[0]}")
    pts = __rotate_box(angles[0], pts)
    logging.info(f"Rotated pts : {pts}")
    pts[:, 0] += off[0][0]
    pts[:, 1] += off[0][1]
    pts[:, 2] += off[0][2]
    logging.info(f"Translated pts : {pts}")

    # Creating multiple meshes, each time with a different angles
    mesh = vtkUnstructuredGrid()
    (vtps:=vtkPoints()).SetData( dsa.numpy_support.numpy_to_vtk(pts) )
    mesh.SetPoints( vtps )

    ids = vtkIdList()
    for i in range(nx-1):
        for j in range(ny-1):
            for k in range(nz-1):
                hex = vtkHexahedron()
                ids = hex.GetPointIds()
                ids.SetId(0,i+j*nx+k*nx*ny)
                ids.SetId(1,i+j*nx+k*nx*ny + 1)
                ids.SetId(2,i+j*nx+k*nx*ny + nx*ny+1)
                ids.SetId(3,i+j*nx+k*nx*ny + nx*ny)
                ids.SetId(4,i+j*nx+k*nx*ny + nx)
                ids.SetId(5,i+j*nx+k*nx*ny + nx+1)
                ids.SetId(6,i+j*nx+k*nx*ny + nx*ny+nx+1)
                ids.SetId(7,i+j*nx+k*nx*ny + nx*ny+nx)
                mesh.InsertNextCell(VTK_HEXAHEDRON,ids)

    yield Expected( mesh=mesh ) 

@pytest.mark.parametrize( "expected", __build_test_mesh() )
def test_rotateAndTranslate_polyhedron( expected: Expected ) -> None:
    output_mesh = transform_mesh( expected.mesh )
    assert output_mesh.GetNumberOfPoints() == expected.mesh.GetNumberOfPoints()
    assert output_mesh.GetNumberOfCells() == expected.mesh.GetNumberOfCells()
    assert output_mesh.GetBounds()[0] == pytest.approx(0., abs=1e-10) and output_mesh.GetBounds()[2] == pytest.approx(0., abs=1e-10) and output_mesh.GetBounds()[4] == pytest.approx(0., abs=1e-10)
    #TODO more assert but need more assumptions then
    # temp
#     w = vtkXMLUnstructuredGridWriter()
#     w.SetFileName("./test_rotateAndTranslate.vtu")
#     w.SetInputData(output_mesh)
#     w.Write()
#     w.SetFileName("./test_rotateAndTranslate_input.vtu")
#     w.SetInputData(expected.mesh)
#     w.Write()

# if __name__ == "__main__":
#     pytest.main([__file__, '-s', '-v','--log-cli-level=WARNING'])