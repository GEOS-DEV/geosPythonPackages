# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

from trame.ui.vuetify3 import VAppLayout
from trame.decorators import TrameApp
from trame.widgets import html, simput
from trame.widgets import vuetify3 as vuetify
from trame_server import Server
from trame_server.controller import Controller
from trame_server.state import State
from trame_simput import get_simput_manager

from geos.trame import module
from geos.trame.app.deck.tree import DeckTree
from geos.trame.app.io.data_loader import DataLoader
from geos.trame.app.ui.viewer.regionViewer import RegionViewer
from geos.trame.app.ui.viewer.wellViewer import WellViewer
from geos.trame.app.components.properties_checker import PropertiesChecker
from geos.trame.app.ui.editor import DeckEditor
from geos.trame.app.ui.inspector import DeckInspector
from geos.trame.app.ui.plotting import DeckPlotting
from geos.trame.app.ui.timeline import TimelineEditor
from geos.trame.app.ui.viewer.viewer import DeckViewer
from geos.trame.app.components.alertHandler import AlertHandler

import sys


@TrameApp()
class GeosTrame:

    def __init__( self, server: Server, file_name: str ) -> None:
        """Constructor."""
        self.alertHandler: AlertHandler | None = None
        self.deckPlotting: DeckPlotting | None = None
        self.deckViewer: DeckViewer | None = None
        self.deckEditor: DeckEditor | None = None
        self.timelineEditor: TimelineEditor | None = None
        self.deckInspector: DeckInspector | None = None
        self.server = server
        server.enable_module( module )

        self.state.input_file = file_name

        # TODO handle hot_reload

        # Set state variables of the App
        self.state.trame__title = "geos-trame"
        self.state.simput_loaded = False

        # Simput configuration
        self.simput_manager = get_simput_manager()
        self.state.sm_id = self.simput_manager.id
        self.simput_widget = simput.Simput( self.simput_manager, prefix="geos", trame_server=server )
        self.simput_widget.auto_update = True

        # Controller
        self.ctrl.simput_apply = self.simput_widget.apply
        self.ctrl.simput_reset = self.simput_widget.reset
        self.ctrl.simput_reload_data = self.simput_widget.reload_data

        # Tree
        self.tree = DeckTree( self.state.sm_id )

        # Viewers
        self.region_viewer = RegionViewer()
        self.well_viewer = WellViewer( 5, 5 )

        # Data loader
        self.data_loader = DataLoader( self.tree, self.region_viewer, self.well_viewer, trame_server=server )

        # Properties checker
        self.properties_checker = PropertiesChecker( self.tree, self.region_viewer, trame_server=server )

        # TODO put as a modal window
        self.set_input_file( file_name=self.state.input_file )

        # Load components
        self.build_ui()

    @property
    def state( self ) -> State:
        """Getter for the state."""
        return self.server.state

    @property
    def ctrl( self ) -> Controller:
        """Getter for the controller."""
        return self.server.controller

    def set_input_file( self, file_name: str ) -> None:
        """Sets the input file of the InputTree object and populates simput/ui."""
        self.tree.set_input_file( file_name )

    def deck_ui( self ) -> None:
        """Generates the UI for the deck edition / visualization tab."""
        with vuetify.VRow( classes="mb-6 fill-height" ):
            with vuetify.VCol(
                    cols=2,
                    order=1,
            ):
                self.deckInspector = DeckInspector( source=self.tree, classes="fit-content" )
                vuetify.VBtn(
                    text="Check fields",
                    classes="ma-4",
                    click=( self.properties_checker.check_fields, ),
                )

            with vuetify.VCol(
                    cols=10,
                    order=2,
            ):
                self.timelineEditor = TimelineEditor( source=self.tree, classes="ma-2", style="height: 40%" )
                with vuetify.VRow( classes="mb-6 fill-height", ):

                    with vuetify.VCol(
                            cols=5,
                            order=3,
                    ):
                        self.deckEditor = DeckEditor(
                            source=self.tree,
                            classes="ma-2",
                            style="flex: 1; height: 100%;",
                        )

                    with vuetify.VCol(
                            cols=7,
                            order=4,
                    ):
                        self.deckViewer = DeckViewer(
                            source=self.tree,
                            region_viewer=self.region_viewer,
                            well_viewer=self.well_viewer,
                            classes="ma-2",
                            style="flex: 1; height: 60%; width: 100%;",
                        )

                        self.deckPlotting = DeckPlotting(
                            source=self.tree,
                            classes="ma-2",
                            style="flex: 1; height: 40%; width: 100%;",
                        )

    def build_ui( self ) -> None:
        """Generates the full UI for the GEOS Trame Application."""
        with VAppLayout( self.server ) as layout:
            self.simput_widget.register_layout( layout )

            self.alertHandler = AlertHandler()

            with html.Div( style="position: relative; display: flex; border-bottom: 1px solid gray", ):
                with vuetify.VTabs(
                        v_model=( "tab_idx", 0 ),
                        style="z-index: 1;",
                        color="grey",
                ):
                    for tab_label in [ "Input File", "Execute", "Results Viewer" ]:
                        vuetify.VTab( tab_label )

                with html.Div(
                        style=
                        "position: absolute; top: 0; left: 0; height: 100%; width: 100%; display: flex; align-items: center; justify-content: center;",
                ):
                    with (
                            html.Div(
                                v_if=( "tab_idx == 0", ),
                                style=
                                "height: 100%; width: 100%; display: flex; align-items: center; justify-content: flex-end;",
                            ),
                            vuetify.VBtn(
                                click=self.tree.write_files,
                                icon=True,
                                style="z-index: 1;",
                                id="save-button",
                            ),
                    ):
                        vuetify.VIcon( "mdi-content-save-outline" )

                    with html.Div(
                            style=
                            "height: 100%; width: 300px; display: flex; align-items: center; justify-content: space-between;",
                            v_if=( "tab_idx == 1", ),
                    ):
                        vuetify.VBtn(
                            "Run",
                            style="z-index: 1;",
                        )
                        vuetify.VBtn(
                            "Kill",
                            style="z-index: 1;",
                        )
                        vuetify.VBtn(
                            "Clear",
                            style="z-index: 1;",
                        )

            # input file editor
            with vuetify.VCol( v_show=( "tab_idx == 0", ), classes="flex-grow-1 pa-0 ma-0" ):
                if self.tree.input_file is not None:
                    self.deck_ui()
                else:
                    self.ctrl.on_add_error(
                        "Error",
                        "The file " + self.state.input_file + " cannot be parsed.",
                    )
                    print(
                        "The file " + self.state.input_file + " cannot be parsed.",
                        file=sys.stderr,
                    )
