# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from pathlib import Path
import pytest

from trame.app import get_server
from geos_trame.app.core import GeosTrame
from trame_client.utils.testing import enable_testing

from seleniumbase import SB
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By


# ruff: noqa
@pytest.mark.skip( "Test to fix" )
@pytest.mark.parametrize( "server_path", [ "tests/utils/start_geos_trame_for_testing.py" ] )
def test_saving_node_modification( server, capsys ):

    with SB( browser="firefox" ) as sb:
        url = f"http://127.0.0.1:{server.port}/"
        sb.open( url )
        sb.sleep( 0.5 )

        # Modify a node
        sb.driver.find_element( By.CSS_SELECTOR, "#v-list-group--id-Problem\\/Events\\/0 .mdi-menu-right" ).click()
        sb.driver.find_element( By.ID, "input-14" ).click()
        sb.driver.find_element( By.NAME, "PeriodicEvent:begin_time:undefined" ).send_keys( "19" )

        # write the edited file
        sb.driver.find_element( By.ID, "save-button" ).click()
        element = sb.driver.find_element( By.CSS_SELECTOR, "body" )
        actions = ActionChains( sb.driver )
        actions.move_to_element( element ).perform()

    # Make sure we can load the saved file
    server_trame = enable_testing( get_server( client_type="vue3" ), "message" )
    root_path = Path( __file__ ).parent.absolute().__str__()
    file_name = root_path + "tests/data/singlePhaseFlow/FieldCaseTutorial3_smoke_v0.xml"

    GeosTrame( server_trame, file_name )
    captured = capsys.readouterr()
    assert captured.err == "Cannot build ui as the input file cannot be parse.\n"
