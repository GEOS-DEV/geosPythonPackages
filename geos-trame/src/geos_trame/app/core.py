# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from trame.ui.vuetify3 import VAppLayout
from trame.decorators import TrameApp
from trame.widgets import html, simput
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager

from geos_trame import module
from geos_trame.app.deck.tree import DeckTree
from geos_trame.app.ui.editor import DeckEditor
from geos_trame.app.ui.inspector import DeckInspector
from geos_trame.app.ui.plotting import DeckPlotting
from geos_trame.app.ui.timeline import TimelineEditor
from geos_trame.app.ui.viewer import DeckViewer

import sys


@TrameApp()
class GeosTrame:
    def __init__(self, server, file_name: str):

        self.server = server
        server.enable_module(module)

        self.state.input_file = file_name

        # TODO handle hot_reload

        # Set state variables of the App
        self.state.trame__title = "geos-trame"
        self.state.simput_loaded = False

        # Simput configuration
        self.simput_manager = get_simput_manager()
        self.state.sm_id = self.simput_manager.id
        self.simput_widget = simput.Simput(
            self.simput_manager, prefix="geos", trame_server=server
        )
        self.simput_widget.auto_update = True

        # Controller
        self.ctrl.simput_apply = self.simput_widget.apply
        self.ctrl.simput_reset = self.simput_widget.reset
        self.ctrl.simput_reload_data = self.simput_widget.reload_data

        # Tree
        self.tree = DeckTree(self.state.sm_id)

        # TODO put as a modal window
        self.set_input_file(file_name=self.state.input_file)

        # Load components
        self.ui = self.build_ui()

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    def set_input_file(self, file_name, file_str=None):
        """sets the input file of the InputTree object and populates simput/ui"""
        self.tree.set_input_file(file_name)

    def deck_ui(self):
        """Generates the UI for the deck edition / visualization tab"""
        with vuetify.VRow(classes="mb-6 fill-height"):
            with vuetify.VCol(
                cols=2,
                order=1,
            ):
                self.deckInspector = DeckInspector(
                    source=self.tree, classes="fill-height"
                )

            with vuetify.VCol(
                cols=10,
                order=2,
            ):
                self.timelineEditor = TimelineEditor(
                    source=self.tree, classes="ma-2", style="height: 40%"
                )
                with vuetify.VRow(
                    classes="mb-6 fill-height",
                ):

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
                            classes="ma-2",
                            style="flex: 1; height: 60%; width: 100%;",
                        )

                        self.deckPlotting = DeckPlotting(
                            source=self.tree,
                            classes="ma-2",
                            style="flex: 1; height: 40%; width: 100%;",
                        )

    def build_ui(self, *args, **kwargs):
        """Generates the full UI for the GEOS Trame Application"""

        with VAppLayout(self.server) as layout:
            self.simput_widget.register_layout(layout)

            def on_tab_change(tab_idx):
                pass

            with html.Div(
                style="position: relative; display: flex; border-bottom: 1px solid gray",
            ):
                with vuetify.VTabs(
                    v_model=("tab_idx", 0),
                    style="z-index: 1;",
                    color="grey",
                    change=(on_tab_change, "[$event]"),
                ):
                    for tab_label in ["Input File", "Execute", "Results Viewer"]:
                        vuetify.VTab(tab_label)

                with html.Div(
                    style="position: absolute; top: 0; left: 0; height: 100%; width: 100%; display: flex; align-items: center; justify-content: center;",
                ):
                    with html.Div(
                        v_if=("tab_idx == 0",),
                        style="height: 100%; width: 100%; display: flex; align-items: center; justify-content: flex-end;",
                    ):
                        with vuetify.VBtn(
                            click=self.tree.write_files,
                            icon=True,
                            style="z-index: 1;",
                            id="save-button",
                        ):
                            vuetify.VIcon("mdi-content-save-outline")

                    with html.Div(
                        style="height: 100%; width: 300px; display: flex; align-items: center; justify-content: space-between;",
                        v_if=("tab_idx == 1",),
                    ):
                        vuetify.VBtn(
                            "Run",
                            # click=self.executor.run,
                            # disabled=(
                            #     "exe_running || exe_use_threading && exe_threads < 2 || exe_use_mpi && exe_processes < 2",
                            # ),
                            style="z-index: 1;",
                        )
                        vuetify.VBtn(
                            "Kill",
                            # click=self.executor.kill,
                            # disabled=("!exe_running",),
                            style="z-index: 1;",
                        )
                        vuetify.VBtn(
                            "Clear",
                            # click=self.ctrl.terminal_clear,
                            style="z-index: 1;",
                        )

            # input file editor
            with vuetify.VCol(
                v_show=("tab_idx == 0",), classes="flex-grow-1 pa-0 ma-0"
            ):
                if self.tree.input_file is not None:
                    self.deck_ui()
                else:

                    print(
                        "Cannot build ui as the input file cannot be parse.",
                        file=sys.stderr,
                    )
