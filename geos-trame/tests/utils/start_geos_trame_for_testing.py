# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from trame_client.utils.testing import enable_testing
from geos.trame.app.core import GeosTrame
from trame.app import get_server
from pathlib import Path

root_path = Path( __file__ ).parent.parent.absolute().__str__()
file_name = root_path + "/data/singlePhaseFlow/FieldCaseTutorial3_smoke.xml"

server = enable_testing( get_server( client_type="vue3" ), "message" )
app = GeosTrame( server, file_name )

app.server.start()
