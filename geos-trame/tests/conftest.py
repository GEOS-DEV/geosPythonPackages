# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import pytest
from pathlib import Path
from trame_client.utils.testing import FixtureHelper

ROOT_PATH = Path( __file__ ).parent.parent.absolute()
print( ROOT_PATH )
HELPER = FixtureHelper( ROOT_PATH )


@pytest.fixture()
def baseline_image():
    HELPER.remove_page_urls()
    yield
    HELPER.remove_page_urls()


@pytest.fixture
def server( xprocess, server_path ):
    name, Starter, Monitor = HELPER.get_xprocess_args( server_path )
    Starter.timeout = 10

    # ensure process is running and return its logfile
    logfile = xprocess.ensure( name, Starter )
    yield Monitor( logfile[ 1 ] )

    # clean up whole process tree afterwards
    xprocess.getinfo( name ).terminate()
