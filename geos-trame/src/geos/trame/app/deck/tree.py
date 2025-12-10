# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import os
from collections import defaultdict
from typing import Any
from datetime import timedelta, datetime

import dpath
import funcy
from pydantic import BaseModel

from trame_simput.core.proxy import ProxyManager, Proxy
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.utils import text
from xsdata_pydantic.bindings import DictDecoder, XmlContext, XmlSerializer, DictEncoder

from trame_server.controller import Controller
from trame_simput import get_simput_manager

from geos.trame.app.deck.file import DeckFile
from geos.trame.app.geosTrameException import GeosTrameException
from geos.trame.schema_generated.schema_mod import Problem, Included, File, Functions
from geos.trame.app.utils.file_utils import normalize_path, format_xml

import logging
date_fmt = "%Y-%m-%d"
logger = logging.getLogger("tree")
logger.setLevel(logging.ERROR)         
class DeckTree( object ):
    """A tree that represents a deck file along with all the available blocks and parameters."""

    def __init__( self, sm_id: str | None = None, ctrl: Controller = None, **kwargs: Any ) -> None:
        """Constructor."""
        super( DeckTree, self ).__init__( **kwargs )

        self.input_file: DeckFile | None = None
        self.input_filename: str | None = None
        self.input_folder: str | None = None
        self.root = None
        self.input_has_errors = False
        self._sm_id = sm_id
        self._ctrl = ctrl
        self.world_origin_time = datetime(1924,3,28).strftime(date_fmt)# Total start date !!
        self.registered_targets : dict = {}

    def set_input_file( self, input_filename: str ) -> None:
        """Set a new input file.

        Input:
            input_filename[str]: The name of the input file
        Return:
            bool: If it was a valid input file
        """
        try:
            self.input_filename = input_filename
            self.input_file = DeckFile( self.input_filename )
            self.input_folder = os.path.dirname( self.input_file.filename )
        except GeosTrameException:
            return

    def get_mesh( self ) -> str:
        """Get the path of the mesh."""
        assert self.input_file is not None and self.input_file.problem is not None
        return normalize_path( self.input_file.path + "/" + self.input_file.problem.mesh[ 0 ].vtkmesh[ 0 ].file )

    def get_abs_path( self, file: str ) -> str:
        """Get the absolute path from a path."""
        assert self.input_file is not None and self.input_file.path is not None
        return normalize_path( self.input_file.path + "/" + file )

    def to_str( self ) -> str:
        """Get the input file as a string."""
        assert self.input_file is not None
        return self.input_file.to_str()

    def get_tree( self ) -> dict:
        """Get the tree from the input file."""
        assert self.input_file is not None and self.input_file.inspect_tree is not None
        return self.input_file.inspect_tree

    def update( self, path: str, key: str, value: Any ) -> None:
        """Update the tree."""
        new_path = [ int( x ) if x.isdigit() else x for x in path.split( "/" ) ]
        new_path.append( key )
        assert self.input_file is not None and self.input_file.pb_dict is not None
        self.input_file.pb_dict = funcy.set_in( self.input_file.pb_dict, new_path, value )

    def drop(self, path:str ) -> None:
        """Remove in the tree."""
        new_path = [ int( x ) if x.isdigit() else x for x in path.split( "/" ) ]
        assert self.input_file is not None and self.input_file.pb_dict is not None
        self.input_file.pb_dict = funcy.del_in( self.input_file.pb_dict, new_path )

    def _search( self, path: str ) -> list | None:
        new_path = path.split( "/" )
        if self.input_file is None:
            return None
        assert self.input_file.pb_dict is not None
        return dpath.values( self.input_file.pb_dict, new_path )

    def decode( self, path: str ) -> BaseModel | None:
        """Decode the given file to a BaseModel."""
        data = self._search( path )
        if data is None:
            return None

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        decoder = DictDecoder( context=context, config=ParserConfig() )
        return decoder.decode( data[ 0 ] )

    @staticmethod
    def encode_data( data: BaseModel ) -> dict:
        """Convert a data to a xml serializable file."""
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        encoder = DictEncoder( context=context, config=SerializerConfig(indent="  ") )
        nodeDict : dict = encoder.encode( data )
        return nodeDict 

    @staticmethod
    def decode_data( data: dict ) -> Problem:
        """Convert a data to a xml serializable file."""
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        decoder = DictDecoder( context=context, config=ParserConfig() )
        node: Problem = decoder.decode( data )
        return node

    @staticmethod
    def to_xml( obj: BaseModel ) -> str:
        """Convert the given obj to xml."""
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )

        config = SerializerConfig( indent="  ", xml_declaration=False, ignore_default_attributes=True )
        serializer = XmlSerializer( context=context, config=config )

        return format_xml( serializer.render( obj ) )

    def timeline( self ) -> list[ dict ] | None:
        """Get the timeline."""
        if self.input_file is None:
            return None
        if self.input_file.problem is None:
            return None

        timeline = []
        # list root events
        global_id = 0
        # solver_events = filter(lambda ev : 'Solver' in ev.target, self.input_file.problem.events[0].periodic_event)
        solver_events = self.input_file.problem.events[0].periodic_event
        max_time = self.input_file.problem.events[0].max_time
        for e in solver_events:
            self.registered_targets[e.target.split('/')[-1]] = e.target            
            e.end_time = max_time if float(e.end_time) > float(max_time) else e.end_time
            #note here float conversion is used to correctly interpret scientific format
            item: dict[ str, str | int ] = {
                "id": global_id,
                "name": e.name,
                "start": (datetime.strptime(self.world_origin_time,date_fmt) + timedelta(seconds=float(e.begin_time))).strftime(date_fmt),
                "end": (datetime.strptime(self.world_origin_time,date_fmt) + timedelta(seconds=float(e.end_time))).strftime(date_fmt),
                "duration" : str( timedelta(seconds=(float(e.end_time) - float(e.begin_time))).days ),
                "category" : e.target.split('/')[-1],
            }
            if(int(float(e.time_frequency))>0): 
                item["freq"] = timedelta(seconds=float(e.time_frequency)).days #TODO deal with Days-Hours-Seconds
            timeline.append( item )
            global_id = global_id + 1

        return timeline

    def plots( self ) -> list[ Functions ]:
        """Get the functions in the current problem."""
        assert self.input_file is not None and self.input_file.problem is not None
        return self.input_file.problem.functions

    def write_files( self ) -> None:
        """Write geos files with all changes made by the user."""
        pb = self._search( "Problem" )
        if pb is None:
            return
        files = self._split( pb )

        for filepath, content in files.items():
            model_loaded: Problem = DeckTree.decode_data( content )
            model_with_changes: Problem = self._apply_changed_properties( model_loaded )

            assert ( self.input_file is not None and self.input_file.xml_parser is not None )
            if self.input_file.xml_parser.contains_include_files():
                includeName: str = self.input_file.xml_parser.get_relative_path_of_file( filepath )
                DeckTree._append_include_file( model_with_changes, includeName )

            model_as_xml: str = DeckTree.to_xml( model_with_changes )

            basename = os.path.basename( filepath )
            assert self.input_folder is not None
            edited_folder_path = self.input_folder
            location = edited_folder_path + "/" + DeckTree._append_id( basename )
            with open( location, "w" ) as file:
                file.write( model_as_xml )
                file.close()

            self._ctrl.on_add_success( title="File saved", message=f"File {basename} has been saved." )

            self._ctrl.on_add_success( title="File saved", message=f"File {basename} has been saved." )

    @staticmethod
    def _append_include_file( model: Problem, included_file_path: str ) -> None:
        """Append an Included object which follows this structure according to the documentation.

        <Included>
            <File name="./included_file.xml" />
        </Included>

        Only Problem can contain an included tag:
        https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/CompleteXMLSchema.html

        """
        if len( included_file_path ) == 0:
            return

        includedTag = Included()
        includedTag.file.append( File( name=DeckTree._append_id( included_file_path ) ) )

        model.included.append( includedTag )

    @staticmethod
    def _append_id( filename: str ) -> str:
        """Return the new filename with the correct suffix and his extension.

        The suffix added will be '_vX' where X is the incremented value of the current version.
        '_v0' if any suffix is present.
        """
        name, ext = os.path.splitext( filename )
        name_length = len( name )

        suffix = "_v"
        version = 0
        suffix_pos = name_length - 3
        if name_length > 3 and name.endswith( suffix, suffix_pos, name_length - 1 ):
            version_str = name[ name_length - 1: ]
            version = int( version_str ) + 1
            name = name[ :name_length - 3 ]

        suffix += str( version )
        return f"{name}{suffix}{ext}"

    @staticmethod
    def _convert_to_camel_case( content: str ) -> str:
        """Convert any given string in CamelCase.

        Useful to transform trame_simput convention in geos schema names convention.
        """
        camel_case_str: str = content.title()
        return camel_case_str.replace( "_", "" )

    @staticmethod
    def _convert_to_snake_case( content: str ) -> str:
        """Convert any given string in snake case.

        Useful to transform geos schema names convention in trame_simput convention.
        """
        return "".join( [ "_" + char.lower() if char.isupper() else char for char in content ] ).lstrip( "_" )

    def _apply_changed_properties( self, model: Problem ) -> Problem:
        """Retrieves all edited 'properties' from the simput_manager and apply it to a given model."""
        manager = get_simput_manager( self._sm_id )
        modified_proxy_ids: set[ str ] = manager.proxymanager.dirty_proxy_data

        if len( modified_proxy_ids ) == 0:
            return model

        model_as_dict = dict( model )

        for proxy_id in modified_proxy_ids:
            properties = manager.data( proxy_id )[ "properties" ]
            events = DeckTree._get_base_model_from_path( model_as_dict, proxy_id )
            events_as_dict = dict( events )
            for property_name, value in properties.items():
                events_as_dict[ property_name ] = value

            DeckTree._set_base_model_properties( model_as_dict, proxy_id, events_as_dict )

        model = model.model_validate( model_as_dict )
        return model

    @staticmethod
    def _convert_proxy_path_into_proxy_names( proxy_path: str ) -> list[ str ]:
        """Split a given proxy path into a list of proxy names.

        note: each proxy name will be converted in snake case to fit with the
        pydantic model naming convention.
        """
        split_path = proxy_path.split( "/" )
        split_path_without_root = split_path[ 1: ]

        return [ DeckTree._convert_to_snake_case( proxy ) for proxy in split_path_without_root ]

    @staticmethod
    def _set_base_model_properties( model: dict, proxy_path: str, properties: dict ) -> None:
        """Apply all changed property to the model for a specific proxy."""
        # retrieve the whole BaseModel list to the modified proxy
        proxy_names = DeckTree._convert_proxy_path_into_proxy_names( proxy_path )
        model_copy = model
        models: list[ tuple[ str, dict ] ] = []
        for proxy_name in proxy_names:
            is_dict = type( model_copy ) is dict
            is_list = type( model_copy ) is list
            is_class = not is_dict and not is_list

            if is_class:
                model_copy = dict( model_copy )

            if proxy_name.isnumeric() and int( proxy_name ) < len( model_copy ):
                models.append( ( proxy_name, model_copy ) )
                model_copy = model_copy[ int( proxy_name ) if is_list else proxy_name ]
                continue

            if proxy_name in model_copy:
                models.append( ( proxy_name, model_copy ) )
                model_copy = model_copy[ proxy_name ]
            else:
                return

        models.reverse()

        # propagate the modification to the parent node
        index = -1
        for model_inverted in models:
            prop_identifier: str = model_inverted[ 0 ]

            if prop_identifier.isnumeric():
                index = int( prop_identifier )
                continue

            if index == -1:
                continue

            current_node = model_inverted[ 1 ]
            current_base_model = current_node[ prop_identifier ][ index ]
            current_base_model = current_base_model.model_validate( properties )

            current_node[ prop_identifier ][ index ] = current_base_model

            break

        models.reverse()

    @staticmethod
    def _get_base_model_from_path( model: dict, proxy_id: str ) -> dict:
        """Retrieve the BaseModel changed from the proxy id. The proxy_id is a unique path from the simput manager."""
        proxy_names = DeckTree._convert_proxy_path_into_proxy_names( proxy_id )

        model_found: dict = model

        for proxy_name in proxy_names:

            is_dict = type( model_found ) is dict
            is_list = type( model_found ) is list
            is_class = not is_dict and not is_list

            if is_class:
                model_found = dict( model_found )

            # path can contain a numerical index, useful to be sure that each
            # proxy is unique, typically used for a list of proxy located at the same level
            if proxy_name.isnumeric() and int( proxy_name ) < len( model_found ):
                model_found = model_found[ int( proxy_name ) ]
                continue

            if proxy_name in model_found:
                model_found = model_found[ proxy_name ]

        return model_found

    def _split( self, xml: list ) -> defaultdict[ str, dict[ str, str ] ]:
        assert self.input_file is not None and self.input_file.xml_parser is not None
        data = self.input_file.xml_parser.file_to_tags
        restructured_files: defaultdict[ str, dict ] = defaultdict( dict )
        for file_path, associated_tags in data.items():
            restructured_files[ file_path ] = {}
            for tag, contents in xml[ 0 ].items():
                if len( contents ) == 0:
                    continue
                tag_formatted = tag
                if tag_formatted in associated_tags:
                    restructured_files[ file_path ][ tag ] = contents

        return restructured_files
