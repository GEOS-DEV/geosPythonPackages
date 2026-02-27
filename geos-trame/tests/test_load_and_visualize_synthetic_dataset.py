# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
import pytest
import os

from trame.app import get_server
from geos.trame.app.core import GeosTrame

from seleniumbase import SB
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By

# ruff: noqa


@pytest.mark.skip( "Test to fix" )
@pytest.mark.parametrize( "server_path", [ "tests/utils/start_geos_trame_for_testing.py" ] )
def test_server_state( server ):

    # Start geos-trame with a specific xml data
    with pytest.raises( Exception ):
        app = GeosTrame()

    server = get_server()
    server.client_type = "vue3"

    file_name = "tests/data/singlePhaseFlow/FieldCaseTutorial3_smoke.xml"
    app = GeosTrame( server, file_name )

    # Check that Tree is correctly generated
    tree_generated = app.tree.get_tree()

    first_item_is_about_field_specification = "FieldSpecifications"
    assert ( tree_generated[ "children" ][ 1 ][ "title" ] == first_item_is_about_field_specification )

    numerical_methods_node = tree_generated[ "children" ][ 5 ]
    assert numerical_methods_node[ "title" ] == "NumericalMethods"
    finite_volume_node = numerical_methods_node[ "children" ][ 0 ]
    assert finite_volume_node[ "title" ] == "FiniteVolume"
    single_phase_node = finite_volume_node[ "children" ][ 0 ]
    assert single_phase_node[ "title" ] == "singlePhaseTPFA"

    absolute_mesh_path = app.tree.get_mesh()
    parsed_mesh_file_name = os.path.basename( absolute_mesh_path )
    expected_mesh_file_name = "synthetic.vtu"
    assert parsed_mesh_file_name == expected_mesh_file_name


@pytest.mark.skip( "Test to fix" )
@pytest.mark.parametrize( "server_path", [ "tests/utils/start_geos_trame_for_testing.py" ] )
def test_client_interaction( server, baseline_image ):

    with SB( browser="firefox" ) as sb:
        url = f"http://127.0.0.1:{server.port}/"
        sb.driver.set_window_size( 1848, 1200 )
        sb.open( url )
        sb.sleep( 1 )

        # Select in the DeckTree the synthetic mesh
        sb.driver.find_element( By.ID, "input-76" ).click()
        element = sb.driver.find_element( By.CSS_SELECTOR, "#v-list-group--id-Problem\\/Mesh\\/0 .mdi-menu-right" )
        actions = ActionChains( sb.driver )
        actions.move_to_element( element ).perform()
        sb.driver.find_element( By.CSS_SELECTOR, "#v-list-group--id-Problem\\/Mesh\\/0 .mdi-menu-right" ).click()
        element = sb.driver.find_element( By.CSS_SELECTOR, "body" )
        actions = ActionChains( sb.driver )
        actions.move_to_element( element ).perform()

        # Verify that the dataset used is the synthetic.vtu
        sb.driver.find_element( By.ID, "input-79" ).click()
        assert sb.get_text( "name=VtkmeshType:file:undefined" ) == "synthetic.vtu"

        # Visualize it in the 3D View: show it and reset the camera
        sb.driver.find_element( By.CSS_SELECTOR, ".mdi-eye-off" ).click()
        sb.driver.find_element( By.CSS_SELECTOR, ".mdi-arrow-expand-all" ).click()
        sb.sleep( 2 )

        # Generate a screenshot
        sb.driver.find_element( By.CSS_SELECTOR, ".mdi-file-png-box" ).click()
