# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
# ruff: noqa
from pathlib import Path

from trame_server import Server
from trame_server.state import State
from trame_vuetify.ui.vuetify3 import VAppLayout

from geos.trame.app.core import GeosTrame
from tests.trame_fixtures import trame_state, trame_server_layout


def test_box_intersection( trame_server_layout: tuple[ Server, VAppLayout ] ) -> None:
    """Test box intersection."""
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    app = GeosTrame( trame_server_layout[ 0 ], file_name )
    app.state.ready()

    app.deckInspector.state.object_state = [ "Problem/Mesh/0/VTKMesh/0", True ]
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = [ "Problem/Geometry/0/Box/0", True ]
    app.deckInspector.state.flush()

    box = app.deckViewer.box_engine._box
    cells = app.deckViewer.box_engine._extracted_cells

    assert box is not None
    assert box.x_min == '{ 3509, 4117, -596 }'
    assert box.x_max == '{ 4482, 5041, -500 }'
    assert cells is not None
    assert cells.number_of_cells == 1
