# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any

from trame.widgets import code, simput
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager

from geos.trame.app.deck.tree import DeckTree


class DeckEditor( vuetify.VCard ):

    def __init__( self, source: DeckTree, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__( **kwargs )

        self.tree = source
        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        self.state.active_ids = []
        self.state.active_id = "Problem"
        self.state.active_name = "Problem"

        self.state.active_snippet = ""
        self.state.change( "active_id" )( self._on_active_id )

        with self:
            with vuetify.VCardTitle( "Components editor" ):
                vuetify.VTextField(
                    v_model=( "active_name" ),
                    v_if=( "active_name != null", ),
                    label="Name",
                    dense=True,
                    hide_details=True,
                )
                vuetify.VSpacer()
                vuetify.VTextField(
                    v_model=( "active_type" ),
                    v_if=( "active_type != null", ),
                    readonly=True,
                    label="Type",
                    dense=True,
                    hide_details=True,
                )
                vuetify.VSpacer()
                vuetify.VSwitch( v_model=( "code", False ), label="view XML snippet" )
            vuetify.VDivider()

            with vuetify.VCardText( v_if="!code", ):
                simput.SimputItem( item_id=( "active_id", None ), )

            code.Editor(
                v_if="code",
                style="height: 100vh",
                value=( "active_snippet", "" ),
                options=(
                    "editor_options",
                    {
                        "automaticLayout": True,
                        "scrollbar": {
                            "vertical": True,
                            "horizontal": True
                        },
                        "layoutInfo": {
                            "width": 80
                        },
                    },
                ),
                language=( "editor_lang", "xml" ),
                theme=( "editor_theme", "vs-dark" ),
                textmate=( "editor_textmate", None ),
            )

    def _on_active_id( self, active_id: str | None, **_: Any ) -> None:
        # this function triggers when a block is selected from the tree in the ui

        if active_id is None:
            self.state.active_name = "Mesh"
            self.state.active_type = None
            self.state.active_types = []
            return

        active_block = self.tree.decode( active_id )

        simput_type = type( active_block ).__name__

        self.simput_manager.proxymanager.get_instances_of_type( simput_type )

        self.state.active_id = active_id
        self.state.active_ids = [ active_id ]

        if active_block is not None and hasattr( active_block, "name" ):
            self.state.active_name = active_block.name
        else:
            self.state.active_name = None

        if active_block is None:
            return

        self.state.active_type = simput_type
        self.state.active_types = [ simput_type ]

        self.state.active_snippet = DeckTree.to_xml( active_block )
