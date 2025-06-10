# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
# ruff: noqa
import pyvista as pv
from pathlib import Path

from trame_server import Server
from trame_server.state import State
from trame_vuetify.ui.vuetify3 import VAppLayout

from geos.trame.app.core import GeosTrame
from tests.trame_fixtures import trame_server_layout, trame_state


def test_data_loader( trame_server_layout: tuple[ Server, VAppLayout ], trame_state: State ) -> None:
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    geos_trame = GeosTrame( trame_server_layout[ 0 ], file_name )

    geos_trame.data_loader.load_vtkmesh_from_id( "Problem/Mesh/0/VTKMesh/0" )
    ug: pv.UnstructuredGrid = geos_trame.data_loader.region_viewer.input
    assert ug.GetCellData().HasArray( "attribute" )
    assert ug.GetPointData().HasArray( "RandomPointScalars" )
    assert not ug.GetPointData().HasArray( "RandomPointVectors" )
    assert ug.GetPointData().HasArray( "RandomPointVectors_0" )
    assert ug.GetPointData().HasArray( "RandomPointVectors_1" )
    assert ug.GetPointData().HasArray( "RandomPointVectors_2" )
    assert not ug.GetPointData().HasArray( "RandomPointVectors_3" )
