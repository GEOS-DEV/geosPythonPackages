# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
from pathlib import Path

from trame.app import get_server
from trame_client.utils.testing import enable_testing
from geos_trame.app.core import GeosTrame


def test_internal_well_intersection():

    server = enable_testing( get_server( client_type="vue3" ), "message" )

    root_path = Path(__file__).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    app = GeosTrame( server, file_name )
    app.state.ready()

    app.deckInspector.state.object_state = ( "Problem/Mesh/0/VTKMesh/0", True )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0",
        True,
    )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0/Perforation/0",
        True,
    )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0/Perforation/1",
        True,
    )
    app.deckInspector.state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 1
    assert len( app.deckViewer._perforations ) == 2


def test_vtk_well_intersection():

    server = enable_testing( get_server( client_type="vue3" ), "message" )

    root_path = Path(__file__).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    app = GeosTrame( server, file_name )
    app.state.ready()

    app.deckInspector.state.object_state = ( "Problem/Mesh/0/VTKMesh/0", True )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = ( "Problem/Mesh/0/VTKMesh/0/VTKWell/0", True )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/VTKWell/0/Perforation/0",
        True,
    )
    app.deckInspector.state.flush()

    app.deckInspector.state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/VTKWell/0/Perforation/1",
        True,
    )
    app.deckInspector.state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 1
    assert len( app.deckViewer._perforations ) == 2

    app.deckInspector.state.object_state = ( "Problem/Mesh/0/VTKMesh/0/VTKWell/0", False )
    app.deckInspector.state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 0
