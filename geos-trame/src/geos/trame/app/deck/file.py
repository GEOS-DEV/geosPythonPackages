# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import os
from typing import Any

from lxml import etree as ElementTree  # type: ignore[import-untyped]
from xsdata.formats.dataclass.parsers.config import ParserConfig
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.utils import text
from xsdata_pydantic.bindings import DictEncoder, XmlContext, XmlParser, XmlSerializer

from geos.trame.app.data_types.renderable import Renderable
from geos.trame.app.geosTrameException import GeosTrameException
from geos.trame.app.io.xml_parser import XMLParser
from geos.trame.app.utils.file_utils import normalize_path
from geos.trame.schema_generated.schema_mod import Problem


class DeckFile( object ):
    """Holds the information of a deck file. Can be empty."""

    def __init__( self, filename: str, **kwargs: Any ) -> None:
        """Constructor.

        Input:
            filename: file name of the deck file
        """
        super( DeckFile, self ).__init__( **kwargs )

        self.inspect_tree: dict[ Any, Any ] | None = None
        self.pb_dict: dict[ str, Any ] | None = None
        self.problem: Problem | None = None
        self.xml_parser: XMLParser | None = None
        self.root_node = None
        self.filename = normalize_path( filename )
        if self.filename:
            self.open_deck_file( self.filename )
        self.original_text = ""
        self.changed = False

        self.path = os.path.dirname( self.filename )

    def open_deck_file( self, filename: str ) -> None:
        """Opens a file and parses it.

        Input:
            filename: file name of the input file
        Signals:
            input_file_changed: On success
        Raises:
            GeosTrameException: On invalid input file
        """
        self.changed = False
        self.root_node = None

        # Do some basic checks on the filename to make sure
        # it is probably a real input file since the GetPot
        # parser doesn't do any checks.
        if not os.path.exists( filename ):
            msg = "Input file %s does not exist" % filename
            raise GeosTrameException( msg )

        if not os.path.isfile( filename ):
            msg = "Input file %s is not a file" % filename
            raise GeosTrameException( msg )

        if not filename.endswith( ".xml" ):
            msg = "Input file %s does not have the proper extension" % filename
            raise GeosTrameException( msg )

        self.xml_parser = XMLParser( filename=filename )
        self.xml_parser.build()
        simulation_deck = self.xml_parser.get_simulation_deck()

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        parser = XmlParser( context=context, config=ParserConfig() )
        try:
            self.problem = parser.parse( simulation_deck, Problem )
        except ElementTree.XMLSyntaxError as e:
            msg = "Failed to parse input file %s:\n%s\n" % ( filename, e )
            raise GeosTrameException( msg ) from e

        encoder = DictEncoder( context=context, config=SerializerConfig( indent="  " ) )
        self.pb_dict = { "Problem": encoder.encode( self.problem ) }
        self.inspect_tree = build_inspect_tree( encoder.encode( self.problem ) )

    def to_str( self ) -> str:
        """Get the problem as a string."""
        config = SerializerConfig( indent="  ", xml_declaration=False )
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        serializer = XmlSerializer( context=context, config=config )
        return serializer.render( self.problem )


def build_inspect_tree( obj: dict ) -> dict:
    """Return the fields of a dataclass instance as a new dictionary mapping field names to field values.

    Example usage::

      @dataclass
      class C:
          x: int
          y: int

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts. Other objects are copied with 'copy.deepcopy()'.
    """
    return _build_inspect_tree_inner( "Problem", obj, [] )


def _build_inspect_tree_inner( key: str, obj: dict, path: list ) -> dict:
    sub_node = {
        "title": obj.get( "name", key ),
        "children": [],
        "is_drawable": key in ( item.value for item in Renderable ),
        "drawn": False,
    }

    for key, value in obj.items():

        if isinstance( value, list ):
            for idx, item in enumerate( value ):
                if isinstance( item, dict ):
                    more_results = _build_inspect_tree_inner( key, item, path + [ key ] + [ idx ] )
                    # for another_result in more_results:
                    sub_node[ "children" ].append( more_results )

    sub_node[ "id" ] = "Problem/" + "/".join( map( str, path ) )

    return sub_node
