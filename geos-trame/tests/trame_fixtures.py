# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware

import pytest
from trame_server import Server
from trame_server.state import State
from trame_vuetify.ui.vuetify3 import VAppLayout
from typing import Generator


@pytest.fixture
def trame_server_layout() -> Generator[ tuple[ Server, VAppLayout ], None, None ]:
    """Yield a test server and layout."""
    server = Server()
    server.debug = True

    with VAppLayout( server ) as layout:
        yield server, layout


@pytest.fixture
def trame_state( trame_server_layout: tuple[ Server, VAppLayout ] ) -> Generator[ State, None, None ]:
    """Yield a test state."""
    trame_server_layout[ 0 ].state.ready()
    yield trame_server_layout[ 0 ].state
