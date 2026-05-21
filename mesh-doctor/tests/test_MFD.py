from geos.mesh_doctor.actions.mapMFD import create_hex_grid, add_cell_volumes, meshAction, Options
from geos.mesh.io.vtkIO import VtkOutput


def test_mfd_indicators_hex_grid(tmp_path):
    mesh = create_hex_grid(1, 1, 1)
    mesh = add_cell_volumes(mesh)

    for ip in ["QTPFA", "BdLVM"]:
        out = tmp_path / f"mfd_{ip}.vtu"
        options = Options(vtkOutput=VtkOutput(output=str(out), isDataModeBinary=True), ip=ip)
        meshAction(mesh, options)

        arr = mesh.GetCellData().GetArray(f"{ip}_Results")
        assert arr is not None
        assert arr.GetNumberOfTuples() == mesh.GetNumberOfCells()
        assert out.exists()
