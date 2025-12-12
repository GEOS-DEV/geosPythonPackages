# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from geos.mesh_doctor.actions.generateCube import Options, FieldInfo, buildCube


def test_generateCube() -> None:
    """Tests the generation of a cube mesh with specific options."""
    options = Options( vtkOutput=None,
                       generateCellsGlobalIds=True,
                       generatePointsGlobalIds=False,
                       xs=( 0, 5, 10 ),
                       ys=( 0, 4, 8 ),
                       zs=( 0, 1 ),
                       nxs=( 5, 2 ),
                       nys=( 1, 1 ),
                       nzs=( 1, ),
                       fields=( FieldInfo( name="test", dimension=2, support="CELLS" ), ) )
    output = buildCube( options )
    assert output.GetNumberOfCells() == 14
    assert output.GetNumberOfPoints() == 48
    assert output.GetCellData().GetArray( "test" ).GetNumberOfComponents() == 2
    assert output.GetCellData().GetGlobalIds()
    assert not output.GetPointData().GetGlobalIds()
