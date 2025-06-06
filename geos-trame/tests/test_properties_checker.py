# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
# ruff: noqa
from pathlib import Path

from trame_server import Server
from trame_server.state import State
from trame_vuetify.ui.vuetify3 import VAppLayout

from geos.trame.app.core import GeosTrame
from geos.trame.app.data_types.field_status import FieldStatus
from tests.trame_fixtures import trame_server_layout, trame_state


def test_properties_checker( trame_server_layout: tuple[ Server, VAppLayout ], trame_state: State ) -> None:
    """Test properties checker."""
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/singlePhaseFlow/FieldCaseTutorial3_smoke.xml"

    geos_trame = GeosTrame( trame_server_layout[ 0 ], file_name )

    field = trame_state.deck_tree[ 4 ][ "children" ][ 0 ]
    assert field[ "valid" ] == FieldStatus.UNCHECKED.value

    geos_trame.simput_manager.proxymanager.get( "Problem/Mesh/0/VTKMesh/0" )[ "region_attribute" ] = "invalid"
    geos_trame.properties_checker.check_fields()
    assert field[ "valid" ] == FieldStatus.INVALID.value

    geos_trame.simput_manager.proxymanager.get( "Problem/Mesh/0/VTKMesh/0" )[ "region_attribute" ] = "attribute"
    geos_trame.properties_checker.check_fields()
    assert field[ "valid" ] == FieldStatus.VALID.value
