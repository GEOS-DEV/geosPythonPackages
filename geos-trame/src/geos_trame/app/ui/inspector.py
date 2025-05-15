# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from dataclasses import dataclass
from enum import Enum

import yaml
from pydantic import BaseModel
from trame.widgets import vuetify3 as vuetify
from trame_simput import get_simput_manager
from typing import Any


class Renderable( Enum ):
    VTKMESH = "VTKMesh"
    INTERNALMESH = "InternalMesh"
    INTERNALWELL = "InternalWell"
    VTKWELL = "VTKWell"
    PERFORATION = "Perforation"


# Pure pydantic version
#
# class TreeNode(BaseModel):
#     id: str
#     name: str
#     is_drawable: bool
#     drawn: bool
#     children: list['TreeNode']
#     hidden_children: list['TreeNode']

# def get_node(obj, node_id, path):
#     children = []
#     for name, info in obj.model_fields.items():
#         if name in obj.model_fields_set:
#             print(type(info))
#             print(name, "-", info.annotation, " - ", get_origin(info.annotation), get_args(info.annotation)[0])
#             metadata = getattr(info, "xsdata_metadata", None) or {}
#             print(metadata["name"])
#             if get_origin(info.annotation) is list:
#                 attr= getattr(obj, name)
#                 print(attr)
#                 for idx, item in enumerate(attr):
#                     children.append(get_node(item, name, path + [name] + [idx]))

#     return TreeNode(
#         id = "Problem/" + "/".join(map(str, path)),
#         name = "metadata",
#         children = children,
#         hidden_children = [],
#         is_drawable = node_id in Renderable,
#         drawn = False,
#     )


@dataclass
class TreeNode:
    id: str
    title: str
    children: list
    hidden_children: list
    is_drawable: bool
    drawn: bool

    @property
    def json( self ) -> dict:
        if self.children:
            return dict(
                id=self.id,
                title=self.title,
                is_drawable=self.is_drawable,
                drawn=self.drawn,
                children=[ c.json for c in self.children ],
                hidden_children=[ c.json for c in self.hidden_children ],
            )
        return dict(
            id=self.id,
            title=self.title,
            is_drawable=self.is_drawable,
            drawn=self.drawn,
            children=None,
            hidden_children=[],
        )


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

    return TreeNode(
        id="Problem/" + "/".join( map( str, path ) ),
        title=node_name,
        children=children if len( children ) else [],
        hidden_children=[],
        is_drawable=node_id in ( k.value for k in Renderable ),
        drawn=False,
    )


def object_to_tree( obj: dict ) -> dict:
    return get_node_dict( obj, "Problem", [] ).json


def dump( item ):
    match item:
        case BaseModel() as model:
            subitems: dict[ str, Any ] = dict()
            model.model_fields

            for field, value in model:

                if isinstance( value, str ):
                    subitems[ field ] = value
                    continue

            return subitems
        case list() | tuple() | set():  # pyright: ignore
            # Pyright finds this disgusting; this passes `mypy` though. `  # type:
            # ignore` would fail `mypy` is it'd be unused (because there's nothing to
            # ignore because `mypy` is content)
            # return type(container)(  # pyright: ignore
            #     _dump(i) for i in container  # pyright: ignore
            # )
            pass
        case dict():
            # return {
            #     k: _dump(v)
            #     for k, v in item.items()  # pyright: ignore[reportUnknownVariableType]
            # }
            pass
        case _:
            return item


def iterate_nested_dict( iterable, returned="key" ):
    """Returns an iterator that returns all keys or values
    of a (nested) iterable.

    Arguments:
        - iterable: <list> or <dictionary>
        - returned: <string> "key" or "value"

    Returns:
        - <iterator>
    """

    if isinstance( iterable, dict ):
        for key, value in iterable.items():
            if key == "id":
                if not ( isinstance( value, dict ) or isinstance( value, list ) ):
                    yield value
            # else:
            #     raise ValueError("'returned' keyword only accepts 'key' or 'value'.")
            for ret in iterate_nested_dict( value, returned=returned ):
                yield ret
    elif isinstance( iterable, list ):
        for el in iterable:
            for ret in iterate_nested_dict( el, returned=returned ):
                yield ret


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
                "rounded": True,
                # "dense": True,
                # "density": "compact",
                # "active_color": "blue",
                # activation logic
                # "activatable": True,
                # "active_strategy": "single-independent",
                # "activated": ("active_ids", ),
                # "update_activated": "(active_ids) => {active_id = active_ids[0]}",
                # selection logic
                "selectable": True,
                "select_strategy": "single-independent",
                "selected": ( "active_ids", ),
                "update_selected": "(active_ids) => {active_id = active_ids[0]}",
                **kwargs,
            },
        )
        self.tree = source
        self._source = None
        self.listen_to_active = listen_to_active

        self.state.object_state = [ "", False ]

        # register used types from Problem
        self.simput_types = []

        self.simput_manager = get_simput_manager( id=self.state.sm_id )

        if source.input_file is None:
            return

        self.set_source( source.input_file.problem )

        def on_change( topic, ids=None, **kwargs ):
            if topic == "changed":
                for obj_id in ids:
                    proxy = self.simput_manager.proxymanager.get( obj_id )
                    self.tree.decode( obj_id )
                    for prop in proxy.edited_property_names:
                        self.tree.update( obj_id, prop, proxy.get_property( prop ) )

        self.simput_manager.proxymanager.on( on_change )

        with self:
            with vuetify.Template( v_slot_append="{ item }" ):
                vuetify.VCheckboxBtn(
                    v_if="item.is_drawable",
                    icon=True,
                    true_icon="mdi-eye",
                    false_icon="mdi-eye-off",
                    dense=True,
                    hide_details=True,
                    update_modelValue=( self.to_draw_change, "[ item.id, $event ] " ),
                )

    def to_draw_change( self, id, drawn ):
        self.state.object_state = [ id, drawn ]

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

    # def on_active_change(self, **_):
    #     if self.listen_to_active:
    #         print("on_active_change")
    # self.set_source_proxy(simple.GetActiveSource())

    # def on_selection_change(self, node_active, **_):
    #     print("on_selection_change", node_active)
