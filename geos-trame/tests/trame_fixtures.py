# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import pytest
from trame_server import Server
from trame_vuetify.ui.vuetify3 import VAppLayout


@pytest.fixture
def trame_server_layout():
    server = Server()
    server.debug = True

    with VAppLayout( server ) as layout:
        yield server, layout


@pytest.fixture
def trame_state( trame_server_layout ):
    trame_server_layout[ 0 ].state.ready()
    yield trame_server_layout[ 0 ].state
