# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Any

import yaml
from pydantic import BaseModel
from trame.widgets import vuetify3 as vuetify, html
from trame_simput import get_simput_manager

from geos_trame.app.data_types.field_status import FieldStatus
from geos_trame.app.data_types.renderable import Renderable
from geos_trame.app.data_types.tree_node import TreeNode
from geos_trame.app.utils.dict_utils import iterate_nested_dict

vuetify.enable_lab()


class DeckInspector( vuetify.VTreeview ):

    def __init__( self, listen_to_active=True, source=None, **kwargs ):
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
        self._source = None
        self.listen_to_active = listen_to_active

        self.state.object_state = ( "", False )

        # register used types from Problem
        self.simput_types = []

        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        if source.input_file is None:
            return

        self.set_source( source.input_file.problem )

        def on_change( topic, ids=None, **_ ):
            if topic == "changed":
                for obj_id in ids:
                    proxy = self.simput_manager.proxymanager.get( obj_id )
                    self.tree.decode( obj_id )
                    for prop in proxy.edited_property_names:
                        self.tree.update( obj_id, prop, proxy.get_property( prop ) )

        self.simput_manager.proxymanager.on( on_change )

        with self:
            with vuetify.Template( v_slot_append="{ item }" ):
                with vuetify.VTooltip( v_if=( "item.valid == 2", ) ):
                    with vuetify.Template(
                            v_slot_activator=( "{ props }", ),
                            __properties__=[ ( "v_slot_activator", "v-slot:activator" ) ],
                    ):
                        vuetify.VIcon( v_bind=( "props", ), classes="mr-2", icon="mdi-close", color="red" )
                    html.Div( v_if=( "item.invalid_properties", ),
                              v_text=( "'Invalid properties: ' + item.invalid_properties", ) )
                    html.Div( v_if=( "item.invalid_children", ),
                              v_text=( "'Invalid children: ' + item.invalid_children", ) )

                vuetify.VIcon( v_if=( "item.valid < 2", ),
                               classes="mr-2",
                               icon='mdi-check',
                               color=( "['gray', 'green'][item.valid]", ) )
                vuetify.VCheckboxBtn( v_if="item.is_drawable",
                                      focused=True,
                                      dense=True,
                                      hide_details=True,
                                      icon=True,
                                      false_icon="mdi-eye-off",
                                      true_icon="mdi-eye",
                                      update_modelValue=( self.to_draw_change, "[ item.id, $event ] " ) )

    def to_draw_change( self, item_id, drawn ):
        self.state.object_state = ( item_id, drawn )

    @property
    def source( self ):
        return self._source

    # TODO
    # v should be a proxy like the one in paraview simple
    # maybe it can be Any of schema_mod (e.g. Problem)
    def set_source( self, v ):

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
        # with this one by passing v as Problem
        # self._source = v

        if v is None:
            self.state.deck_tree = []
        else:
            self.state.deck_tree = object_to_tree( self._source ).get( "children", [] )

        for v in iterate_nested_dict( self.state.deck_tree ):

            active_block = self.tree.decode( v )
            # active_name = None

            # if hasattr(active_block, "name"):
            #     active_name = active_block.name

            simput_type = type( active_block ).__name__

            test = dump( active_block )

            if test:
                params_dict = {}
                for key, value in test.items():
                    params_dict[ key ] = {
                        # "initial": str(v),
                        "type": "string",
                    }

                self.simput_types.append( simput_type )
                yaml_str = yaml.dump( { simput_type: params_dict }, sort_keys=False )

                self.simput_manager.load_model( yaml_content=yaml_str )

                debug = self.simput_manager.proxymanager.create( simput_type, proxy_id=v )

                for key, value in test.items():
                    debug.set_property( key, getattr( active_block, key ) )
                debug.commit()

    def change_current_id( self, item_id=None ):
        """
        Change the current id of the tree.
        This function is called when the user click on the tree.
        """
        if item_id is None:
            # Silently ignore, it could occur if the user click on the tree
            # and this item is already selected
            return

        self.state.active_id = item_id


def get_node_dict( obj, node_id, path ):
    children = []
    for key, value in obj.items():
        # todo look isinstance(value, dict):
        if isinstance( value, list ):
            for idx, item in enumerate( value ):
                if isinstance( item, dict ):
                    children.append( get_node_dict( item, key, path + [ key ] + [ idx ] ) )

    node_name = node_id
    if "name" in obj:
        node_name = obj[ "name" ]

    return TreeNode( id="Problem/" + "/".join( map( str, path ) ),
                     title=node_name,
                     children=children if len( children ) else [],
                     hidden_children=[],
                     is_drawable=node_id in ( k.value for k in Renderable ),
                     drawn=False,
                     valid=FieldStatus.UNCHECKED.value )


def object_to_tree( obj: dict ) -> dict:
    return get_node_dict( obj, "Problem", [] ).json


def dump( item ) -> dict[ str, Any ] | None:
    if isinstance( item, BaseModel ):
        subitems: dict[ str, Any ] = dict()

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
