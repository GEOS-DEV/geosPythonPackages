# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import dpath
import funcy

import os

from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.utils import text
from xsdata_pydantic.bindings import DictDecoder, XmlContext, XmlSerializer

from geos_trame.app.deck.file import DeckFile
from geos_trame.app.geosTrameException import GeosTrameException
from geos_trame.app.utils.file_utils import normalize_path, format_xml
from geos_trame.schema_generated.schema_mod import BaseModel, Problem, Included, File

from collections import defaultdict
from trame_simput import get_simput_manager


class DeckTree( object ):
    """
    A tree that represents a deck file along with all the available blocks and parameters.
    """

    def __init__( self, sm_id=None, **kwds ):
        """
        Constructor.
        """
        super( DeckTree, self ).__init__( **kwds )

        self.input_file = None
        self.input_filename = None
        self.input_folder = None
        self.input_real_filename = None
        # self._copyDefaultTree()
        self.root = None
        self.path_map = {}
        self.input_has_errors = False
        self._sm_id = sm_id

    def set_input_file( self, input_filename ):
        """
        Set a new input file
        Input:
            input_filename[str]: The name of the input file
        Return:
            bool: If it was a valid input file
        """
        try:
            self.input_filename = input_filename
            self.input_file = DeckFile( self.input_filename )
            self.input_folder = os.path.dirname( self.input_file.filename )
            self.input_real_filename = os.path.basename( self.input_file.filename )
        except Exception as e:
            msg = "set_input_file exception: %s" % e
            return GeosTrameException( msg )

    def root_fields( self ) -> list[ str ]:
        return self.input_file.root_fields

    def get_mesh( self ) -> str:
        return normalize_path( self.input_file.path + "/" + self.input_file.problem.mesh[ 0 ].vtkmesh[ 0 ].file )

    def get_abs_path( self, file ) -> str:
        return normalize_path( self.input_file.path + "/" + file )

    def to_str( self ) -> str:
        return self.input_file.to_str()

    def get_tree( self ) -> dict:
        return self.input_file.inspect_tree

    def update( self, path, key, value ) -> None:
        new_path = [ int( x ) if x.isdigit() else x for x in path.split( "/" ) ]
        new_path.append( key )
        funcy.set_in( self.input_file.pb_dict, new_path, value )

    def search( self, path ) -> list | None:
        new_path = path.split( "/" )
        if self.input_file is None:
            return None
        return dpath.values( self.input_file.pb_dict, new_path )

    def decode( self, path ):
        data = self.search( path )
        if data is None:
            return None

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        decoder = DictDecoder( context=context, config=ParserConfig() )
        node = decoder.decode( data[ 0 ] )
        return node

    def decode_data( self, data: BaseModel | None ) -> str:
        """
        Convert a data to a xml serializable file
        """
        if data is None:
            return

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        decoder = DictDecoder( context=context, config=ParserConfig() )
        node = decoder.decode( data )
        return node

    def to_xml( self, obj ) -> str:
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )

        config = SerializerConfig( indent="  ", xml_declaration=False )
        serializer = XmlSerializer( context=context, config=config )

        return format_xml( serializer.render( obj ) )

    def timeline( self ) -> dict:
        if self.input_file is None:
            return
        if self.input_file.problem is None:
            return
        if self.input_file.problem.events is None:
            return

        timeline = list()
        # list root events
        global_id = 0
        for e in self.input_file.problem.events[ 0 ].periodic_event:
            item = dict()
            item[ "id" ] = global_id
            item[ "summary" ] = e.name
            item[ "start_date" ] = e.begin_time
            timeline.append( item )
            global_id = global_id + 1

        return timeline

    def plots( self ):
        return self.input_file.problem.functions

    def write_files( self ):
        """
        Write geos files with all changes made by the user.
        """

        pb = self.search( "Problem" )
        files = self._split( pb )

        for filepath, content in files.items():
            model_loaded: BaseModel = self.decode_data( content )
            model_with_changes: BaseModel = self._apply_changed_properties( model_loaded )

            if self.input_file.xml_parser.contains_include_files():
                includeName: str = self.input_file.xml_parser.get_relative_path_of_file( filepath )
                self._append_include_file( model_with_changes, includeName )

            model_as_xml: str = self.to_xml( model_with_changes )

            basename = os.path.basename( filepath )
            edited_folder_path = self.input_folder
            location = edited_folder_path + "/" + self._append_id( basename )
            with open( location, "w" ) as file:
                file.write( model_as_xml )
                file.close()

    def _setInputFile( self, input_file ):
        """
        Copies the nodes of an input file into the tree
        Input:
            input_file[InputFile]: Input file to copy
        Return:
            bool: True if successful
        """
        self.input_has_errors = False
        if input_file.root_node is None:
            return False
        self.input_file = input_file
        self.input_filename = input_file.filename

        return False

    def _append_include_file( self, model: Problem, includedFilePath: str ) -> None:
        """
        Append an Included object which follows this structure according to the documentation:
        <Included>
            <File name="./included_file.xml" />
        </Included>

        Only Problem can contains an included tag:
        https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/CompleteXMLSchema.html

        """
        if len( includedFilePath ) == 0:
            return None

        includedTag = Included()
        includedTag.file.append( File( name=self._append_id( includedFilePath ) ) )

        model.included.append( includedTag )

    def _append_id( self, filename: str ) -> str:
        """
        Return the new filename with the correct suffix and his extension. The suffix
        added will be '_vX' where X is the incremented value of the current version.
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

    def _convert_to_camel_case( self, content: str ) -> str:
        """
        Convert any given string in CamelCase.

        Useful to transform trame_simput convention in geos schema names convention.
        """
        camel_case_str: str = content.title()
        return camel_case_str.replace( "_", "" )

    def _convert_to_snake_case( self, content: str ) -> str:
        """
        Convert any given string in snake case.

        Useful to transform geos schema names convention in trame_simput convention.
        """
        return "".join( [ "_" + char.lower() if char.isupper() else char for char in content ] ).lstrip( "_" )

    def _apply_changed_properties( self, model: Problem ) -> Problem:
        """
        Retrieves all edited 'properties' from the simput_manager and apply it to a
        given model.

        """

        manager = get_simput_manager( self._sm_id )
        modified_proxy_ids: set[ str ] = manager.proxymanager.dirty_proxy_data

        if len( modified_proxy_ids ) == 0:
            return model

        model_as_dict = dict( model )

        for proxy_id in modified_proxy_ids:
            properties = manager.data( proxy_id )[ "properties" ]
            events = self._get_base_model_from_path( model_as_dict, proxy_id )
            if events is None:
                continue
            events_as_dict = dict( events )
            for property_name, value in properties.items():
                events_as_dict[ property_name ] = value

            self._set_base_model_properties( model_as_dict, proxy_id, events_as_dict )

        model = getattr( model, "model_validate" )( model_as_dict )
        return model

    def _convert_proxy_path_into_proxy_names( self, proxy_path: str ) -> list[ str ]:
        """
        Split a given proxy path into a list of proxy names.

        note: each proxy name will be converted in snake case to fit with the
        pydantic model naming convention.
        """
        splitted_path = proxy_path.split( "/" )
        splitted_path_without_root = splitted_path[ 1: ]

        return [ self._convert_to_snake_case( proxy ) for proxy in splitted_path_without_root ]

    def _set_base_model_properties( self, model: dict, proxy_path: str, properties: dict ) -> None:
        """
        Apply all changed property to the model for a specific proxy.
        """

        # retrieve the whole BaseModel list to the modified proxy
        proxy_names = self._convert_proxy_path_into_proxy_names( proxy_path )
        model_copy = model
        models = []
        for proxy_name in proxy_names:
            is_dict = type( model_copy ) is dict
            is_list = type( model_copy ) is list
            is_class = not is_dict and not is_list

            if is_class:
                model_copy = dict( model_copy )

            if proxy_name.isnumeric() and int( proxy_name ) < len( model_copy ):
                models.append( [ proxy_name, model_copy ] )
                model_copy = model_copy[ int( proxy_name ) ]
                continue

            if proxy_name in model_copy:
                models.append( [ proxy_name, model_copy ] )
                model_copy = model_copy[ proxy_name ]
            else:
                return None

        models.reverse()

        # propagate the modification to the parent node
        index = -1
        for model_inverted in models:
            prop_identifier = model_inverted[ 0 ]

            if prop_identifier.isnumeric():
                index = int( prop_identifier )
                continue

            if index == -1:
                continue

            current_node = model_inverted[ 1 ]
            current_base_model = current_node[ prop_identifier ][ index ]
            current_base_model = getattr( current_base_model, "model_validate" )( properties )

            current_node[ prop_identifier ][ index ] = current_base_model

            properties = dict( current_base_model )
            break

        models.reverse()
        model = models[ 0 ]

    def _get_base_model_from_path( self, model: dict, proxy_id: str ) -> BaseModel:
        """
        Retrieve the BaseModel changed from the proxy id. The proxy_id is a unique path
        from the simput manager.
        """
        proxy_names = self._convert_proxy_path_into_proxy_names( proxy_id )

        model_found: dict = model

        for proxy_name in proxy_names:

            is_dict = type( model_found ) is dict
            is_list = type( model_found ) is list
            is_class = not is_dict and not is_list

            if is_class:
                model_found = dict( model_found )

            # path can contains a numerical index, useful to be sure that each
            # proxy is unique, typically used for a list of proxy located at the same level
            if proxy_name.isnumeric() and int( proxy_name ) < len( model_found ):
                model_found = model_found[ int( proxy_name ) ]
                continue

            if proxy_name in model_found:
                model_found = model_found[ proxy_name ]

        return model_found

    def _split( self, xml: str ) -> dict[ str, str ]:
        data = self.input_file.xml_parser.file_to_tags
        restructured_files = defaultdict( dict )
        for file_path, associated_tags in data.items():
            restructured_files[ file_path ] = dict()
            for tag, contents in xml[ 0 ].items():
                if len( contents ) == 0:
                    continue
                tag_formatted = tag
                if tag_formatted in associated_tags:
                    restructured_files[ file_path ][ tag ] = contents

        return restructured_files
