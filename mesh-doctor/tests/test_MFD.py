import numpy as np
import vtk
from vtkmodules.util.numpy_support import vtk_to_numpy, numpy_to_vtk

from geos.mesh.io.vtkIO import VtkOutput
from geos.mesh_doctor.actions.mapMFD import add_cell_volumes, meshAction, Options

def __create_hex_grid(nx=2, ny=2, nz=2) -> vtk.vtkUnstructuredGrid:
    """Creates a simple hexagonal grid with the specified number of cells in each direction."""
    mesh = vtk.vtkUnstructuredGrid()
    points = vtk.vtkPoints()
    for k in range(nz + 1):
        for j in range(ny + 1):
            for i in range(nx + 1):
                points.InsertNextPoint(i / nx, j / ny, k / nz)
    mesh.SetPoints(points)

    def pid(i, j, k):
        return k * (ny + 1) * (nx + 1) + j * (nx + 1) + i

    for k in range(nz):
        for j in range(ny):
            for i in range(nx):
                ids = vtk.vtkIdList()
                for node in [
                    pid(i, j, k),
                    pid(i + 1, j, k),
                    pid(i + 1, j + 1, k),
                    pid(i, j + 1, k),
                    pid(i, j, k + 1),
                    pid(i + 1, j, k + 1),
                    pid(i + 1, j + 1, k + 1),
                    pid(i, j + 1, k + 1),
                ]:
                    ids.InsertNextId(node)
                mesh.InsertNextCell(vtk.VTK_HEXAHEDRON, ids)
    return __add_permeability(mesh)


def __add_permeability(mesh, permeability_value=1.0) -> vtk.vtkUnstructuredGrid:
    """Adds a simple permeability field to the mesh."""
    perm = np.ones((mesh.GetNumberOfCells(), 3)) * permeability_value
    vtk_perm = numpy_to_vtk(perm, array_type=vtk.VTK_DOUBLE)
    vtk_perm.SetName("Permeability")
    mesh.GetCellData().AddArray(vtk_perm)
    return mesh

def test_mfd_indicators_hex_grid(tmp_path):
    mesh = __create_hex_grid(1, 1, 1)
    mesh = add_cell_volumes(mesh)
    mesh = __add_permeability(mesh)

    for ip in ["QTPFA", "BdLVM"]:
        out = tmp_path / f"mfd_{ip}.vtu"
        options = Options(vtkOutput=VtkOutput(output=str(out), isDataModeBinary=True), ip=ip, permeability="Permeability")
        meshAction(mesh, options)

        arr = mesh.GetCellData().GetArray(f"{ip}_Results")
        assert arr is not None
        assert arr.GetNumberOfTuples() == mesh.GetNumberOfCells()
        assert out.exists()

        if ip == "QTPFA":
            varr = vtk_to_numpy(arr)[0]
            assert np.isclose(varr[0], 1) #conditioning
            assert np.isclose(varr[2:3], 0.5) #spectrum
            assert np.isclose(varr[4], 0, atol=1e-15) #orthogonality
            assert np.isclose(varr[5], 0, atol=1e-15) #consistency
        elif ip == "BdLVM":
            varr = vtk_to_numpy(arr)[0]
            assert np.isclose(varr[0], 3) #conditioning
            assert np.allclose(varr[2:4], np.array([1/6, 1/2]), atol=1e-15) #spectrum
            assert np.isclose(varr[4], 0, atol=1e-15) #orthogonality
            assert np.isclose(varr[5], 0, atol=1e-15) #consistency
