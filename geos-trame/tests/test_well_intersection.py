# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
from pathlib import Path

from geos_trame.app.core import GeosTrame
from tests.trame_fixtures import trame_state, trame_server_layout


def test_internal_well_intersection( trame_server_layout, trame_state ):
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    app = GeosTrame( trame_server_layout[ 0 ], file_name )

    trame_state.object_state = ( "Problem/Mesh/0/VTKMesh/0", True )
    trame_state.flush()

    trame_state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0",
        True,
    )
    trame_state.flush()

    trame_state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0/Perforation/0",
        True,
    )
    trame_state.flush()

    trame_state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/InternalWell/0/Perforation/1",
        True,
    )
    trame_state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 1
    assert len( app.deckViewer._perforations ) == 2


def test_vtk_well_intersection( trame_server_layout, trame_state ):
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/geosDeck/geosDeck.xml"

    app = GeosTrame( trame_server_layout[ 0 ], file_name )

    trame_state.object_state = ( "Problem/Mesh/0/VTKMesh/0", True )
    trame_state.flush()

    trame_state.object_state = ( "Problem/Mesh/0/VTKMesh/0/VTKWell/0", True )
    trame_state.flush()

    trame_state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/VTKWell/0/Perforation/0",
        True,
    )
    trame_state.flush()

    trame_state.object_state = (
        "Problem/Mesh/0/VTKMesh/0/VTKWell/0/Perforation/1",
        True,
    )
    trame_state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 1
    assert len( app.deckViewer._perforations ) == 2

    trame_state.object_state = ( "Problem/Mesh/0/VTKMesh/0/VTKWell/0", False )
    trame_state.flush()

    assert app.deckViewer.well_engine.get_number_of_wells() == 0
