# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from pathlib import Path

from geos_trame.app.core import GeosTrame
from geos_trame.app.data_types.field_status import FieldStatus
from tests.trame_fixtures import trame_state, trame_server_layout


def test_properties_checker( trame_server_layout, trame_state ):
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "/data/singlePhaseFlow/FieldCaseTutorial3_smoke.xml"

    geos_trame = GeosTrame( trame_server_layout[ 0 ], file_name )

    field = trame_state.deck_tree[ 4 ][ "children" ][ 0 ]
    assert field[ "valid" ] == FieldStatus.UNCHECKED.value
    geos_trame.properties_checker.check_fields()
    assert field[ "valid" ] == FieldStatus.INVALID.value
