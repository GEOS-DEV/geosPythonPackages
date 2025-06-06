# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from _pytest.capture import CaptureFixture
from trame.app import get_server
from trame_client.utils.testing import enable_testing
from geos.trame.app.core import GeosTrame


def test_unsupported_file( capsys: CaptureFixture[ str ] ) -> None:
    """Test unsupported file."""
    server = enable_testing( get_server( client_type="vue3" ), "message" )
    file_name = "tests/data/acous3D/acous3D_vtu.xml"

    GeosTrame( server, file_name )

    captured = capsys.readouterr()
    assert ( captured.err == "The file tests/data/acous3D/acous3D_vtu.xml cannot be parsed.\n" )
