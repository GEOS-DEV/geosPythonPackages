# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any

import yaml
from pydantic import BaseModel
from trame.widgets import vuetify3 as vuetify, html
from trame_simput import get_simput_manager

from xsdata.utils import text

from geos.trame.app.data_types.field_status import FieldStatus
from geos.trame.app.data_types.renderable import Renderable
from geos.trame.app.data_types.tree_node import TreeNode
from geos.trame.app.deck.tree import DeckTree
from geos.trame.app.utils.dict_utils import iterate_nested_dict
from geos.trame.schema_generated.schema_mod import Problem

vuetify.enable_lab()


class DeckInspector( vuetify.VTreeview ):

    def __init__( self, source: DeckTree, listen_to_active: bool = True, **kwargs: Any ) -> None:
        """Constructor."""
        super().__init__(
            # data
            items=( "deck_tree", ),
            item_value="id",
            **{
                # style
                "hoverable": True,
                "max_width": 500,
                "rounded": True,
                # activation logic
                "activatable": True,
                "activated": ( "active_ids", ),
                "active_strategy": "single-independent",
                "update_activated": ( self.change_current_id, "$event" ),
                # selection logic
                "selectable": False,
                **kwargs,
            },
        )
        self.tree = source
        self._source: dict | None = None
        self.listen_to_active = listen_to_active

        self.state.object_state = ( "", False )

        # register used types from Problem
        self.simput_types: list = []

        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        if source.input_file is None:
            return

        self._set_source( source.input_file.problem )

        def _on_change( topic: str, ids: list | None = None ) -> None:
            if ids is not None and topic == "changed":
                for obj_id in ids:
                    proxy = self.simput_manager.proxymanager.get( obj_id )
                    #self.tree.decode( obj_id ) # if const function and return not used why ?? to decode context ??
                    for prop in proxy.edited_property_names:
                        self.tree.update( obj_id, text.camel_case( prop ), proxy.get_property( prop ) )

        self.simput_manager.proxymanager.on( _on_change )

        with self, vuetify.Template( v_slot_append="{ item }" ):
            with vuetify.VTooltip( v_if=( "item.valid == 2", ) ):
                with vuetify.Template(
                        v_slot_activator=( "{ props }", ),
                        __properties__=[ ( "v_slot_activator", "v-slot:activator" ) ],
                ):
                    vuetify.VIcon( v_bind=( "props", ), classes="mr-2", icon="mdi-close", color="red" )
                html.Div(
                    v_if=( "item.invalid_properties", ),
                    v_text=( "'Invalid properties: ' + item.invalid_properties", ),
                )
                html.Div(
                    v_if=( "item.invalid_children", ),
                    v_text=( "'Invalid children: ' + item.invalid_children", ),
                )

            vuetify.VIcon(
                v_if=( "item.valid < 2", ),
                classes="mr-2",
                icon="mdi-check",
                color=( "['gray', 'green'][item.valid]", ),
            )
            vuetify.VCheckboxBtn(
                v_if="item.is_drawable",
                focused=True,
                dense=True,
                hide_details=True,
                icon=True,
                false_icon="mdi-eye-off",
                true_icon="mdi-eye",
                update_modelValue=( self._to_draw_change, "[ item.id, $event ] " ),
            )

    def _to_draw_change( self, item_id: str, drawn: bool ) -> None:
        self.state.object_state = ( item_id, drawn )

    @property
    def source( self ) -> dict | None:
        """Getter for source."""
        return self._source

    # TODO
    # v should be a proxy like the one in paraview simple
    # maybe it can be Any of schema_mod (e.g. Problem)
    def _set_source( self, v: Problem | None ) -> None:

        # TODO replace this snippet
        from xsdata.formats.dataclass.serializers.config import SerializerConfig
        from xsdata.utils import text
        from xsdata_pydantic.bindings import DictEncoder, XmlContext

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )

        encoder = DictEncoder( context=context, config=SerializerConfig( indent="  " ) )
        self._source = encoder.encode( v )
        assert self._source is not None
        # with this one by passing v as Problem
        # self._source = v

        if v is None:
            self.state.deck_tree = []
        else:
            self.state.deck_tree = _object_to_tree( self._source ).get( "children", [] )

        for path in iterate_nested_dict( self.state.deck_tree ):

            active_block = self.tree.decode( path )
            # active_name = None

            # if hasattr(active_block, "name"):
            #     active_name = active_block.name

            simput_type = type( active_block ).__name__

            test = _dump( active_block )

            if test:
                params_dict = {}
                for key, _ in test.items():
                    params_dict[ key ] = {
                        "type": "string",
                    }

                self.simput_types.append( simput_type )
                yaml_str = yaml.dump( { simput_type: params_dict }, sort_keys=False )

                self.simput_manager.load_model( yaml_content=yaml_str )

                debug = self.simput_manager.proxymanager.create( simput_type, proxy_id=path )

                for key, _ in test.items():
                    debug.set_property( key, getattr( active_block, key ) )
                debug.commit()

    def change_current_id( self, item_id: str | None = None ) -> None:
        """Change the current id of the tree.

        This function is called when the user click on the tree.
        """
        if item_id is None:
            # Silently ignore, it could occur if the user click on the tree
            # and this item is already selected
            return

        self.state.active_id = item_id


def _get_node_dict( obj: dict, node_id: str, path: list ) -> TreeNode:
    children = []
    for key, value in obj.items():
        # todo look isinstance(value, dict):
        if isinstance( value, list ):
            for idx, item in enumerate( value ):
                if isinstance( item, dict ):
                    children.append( _get_node_dict( item, key, path + [ key ] + [ idx ] ) )

    node_name = node_id
    if "name" in obj:
        node_name = obj[ "name" ]

    return TreeNode(
        id="Problem/" + "/".join( map( str, path ) ),
        title=node_name,
        children=children if len( children ) else [],
        hidden_children=[],
        is_drawable=node_id in ( k.value for k in Renderable ),
        drawn=False,
        valid=FieldStatus.UNCHECKED.value,
    )


def _object_to_tree( obj: dict ) -> dict:
    return _get_node_dict( obj, "Problem", [] ).json


def _dump( item: Any ) -> dict[ str, Any ] | None:
    if isinstance( item, BaseModel ):
        subitems: dict[ str, Any ] = {}

        for field, value in item:

            if isinstance( value, str ):
                subitems[ field ] = value
                continue
        return subitems
    elif isinstance( item, ( list, tuple, set ) ):  # pyright: ignore
        # Pyright finds this disgusting; this passes `mypy` though. `  # type:
        # ignore` would fail `mypy` is it'd be unused (because there's nothing to
        # ignore because `mypy` is content)
        # return type(container)(  # pyright: ignore
        #     _dump(i) for i in container  # pyright: ignore
        # )
        return None
    elif isinstance( item, dict ):
        # return {
        #     k: _dump(v)
        #     for k, v in item.items()  # pyright: ignore[reportUnknownVariableType]
        # }
        return None
    else:
        return item
