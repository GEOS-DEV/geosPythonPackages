# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
def test_import() -> None:
    """Test GeosTrame import."""
    from geos.trame.app.core import GeosTrame  # noqa: F401
