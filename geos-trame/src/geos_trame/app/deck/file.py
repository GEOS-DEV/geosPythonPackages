# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import os
import re
import typing
from dataclasses import fields, is_dataclass
from io import StringIO
from typing import Any, Iterator, List, TextIO

import typing_extensions
import typing_inspect
from lxml import etree as ElementTree  # type: ignore[import-untyped]
from pydantic import BaseModel

# from xsdata.formats.dataclass.context import XmlContext
# from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig

# from xsdata.formats.dataclass.serializers import DictEncoder
# from xsdata.formats.dataclass.serializers import XmlSerializer
from xsdata.formats.dataclass.serializers.config import SerializerConfig
from xsdata.utils import text
from xsdata_pydantic.bindings import DictEncoder, XmlContext, XmlParser, XmlSerializer

# from geos_trame.app.deck.inspector import object_to_tree
from geos_trame.app.geosTrameException import GeosTrameException
from geos_trame.schema_generated.schema_mod import Problem

from geos_trame.app.io.xml_parser import XMLParser


def get_origin(v: typing.Any) -> typing.Any:
    pydantic_generic_metadata = getattr(
        v, "__pydantic_generic_metadata__", None
    )  #: PydanticGenericMetadata | None
    if pydantic_generic_metadata:
        return pydantic_generic_metadata.get("origin")
    return typing_extensions.get_origin(v)


def all_fields(c: type, already_checked) -> list[str]:
    resolved_hints = typing.get_type_hints(c)
    field_names = [field.name for field in fields(c)]
    resolved_field_types = {name: resolved_hints[name] for name in field_names}

    field_list = []
    for key in resolved_field_types:
        current_type = resolved_field_types[key]
        if typing_inspect.get_origin(current_type) in (list, typing.List):
            inner_type = typing_inspect.get_args(current_type)[0]
            if inner_type not in already_checked:
                already_checked.append(inner_type)
                field_list.extend(all_fields(inner_type, already_checked))
        if is_dataclass(current_type) and current_type not in already_checked:
            already_checked.append(current_type)
            field_list.extend(all_fields(current_type, already_checked))

        # {"id": i, "name": f, "children": [], "hidden_children": []}

    return field_list


def required_fields(model: type[BaseModel], recursive: bool = False) -> Iterator[str]:
    for name, field in model.model_fields.items():
        print(name)
        if not field.is_required():
            continue
        t = field.annotation
        print(t)
        if recursive and isinstance(t, type) and issubclass(t, BaseModel):
            yield from required_fields(t, recursive=True)
        else:
            yield name


def is_pydantic_model(obj):
    try:
        return issubclass(obj, BaseModel)
    except TypeError:
        return False


def show_hierarchy(Model: BaseModel, processed_types: set, indent: int = 0):
    print(type(Model).__name__)
    if type(Model).__name__ not in processed_types:
        processed_types.add(type(Model).__name__)
        print(processed_types)
        for k, v in Model.model_fields.items():
            print(
                f'{" "*indent}{k}: '
                f"type={v.annotation}, "
                f"required={v.is_required()}"
            )
            if is_pydantic_model(typing.get_args(v.annotation)[0]):
                # print("plop")
                show_hierarchy(
                    typing.get_args(v.annotation)[0], processed_types, indent + 2
                )


def normalize_path(x):
    tmp = os.path.expanduser(x)
    tmp = os.path.abspath(tmp)
    if os.path.isfile(tmp):
        x = tmp
    return x


class DeckFile(object):
    """
    Holds the information of a deck file.
    Can be empty.
    """

    def __init__(self, filename: str, **kwargs) -> None:
        """
        Constructor.
        Input:
            filename: file name of the deck file
        """
        super(DeckFile, self).__init__(**kwargs)

        self.root_node = None
        self.filename = normalize_path(filename)
        if self.filename:
            self.open_deck_file(self.filename)
        self.original_text = ""
        self.changed = False

        self.path = os.path.dirname(self.filename)

    def open_deck_file(self, filename: str) -> None:
        """
        Opens a file and parses it.
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
        if not os.path.exists(filename):
            msg = "Input file %s does not exist" % filename
            raise GeosTrameException(msg)

        if not os.path.isfile(filename):
            msg = "Input file %s is not a file" % filename
            raise GeosTrameException(msg)

        if not filename.endswith(".xml"):
            msg = "Input file %s does not have the proper extension" % filename
            raise GeosTrameException(msg)

        self.xml_parser = XMLParser(filename=filename)
        self.xml_parser.build()
        simulation_deck = self.xml_parser.get_simulation_deck()

        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        parser = XmlParser(
            context=context, config=ParserConfig()
        )  # fail_on_unknown_properties=True, fail_on_unknown_attributes=True, fail_on_converter_warnings=True))
        try:
            self.problem = parser.parse(simulation_deck, Problem)
        except ElementTree.XMLSyntaxError as e:
            msg = "Failed to parse input file %s:\n%s\n" % (filename, e)
            raise GeosTrameException(msg)

        encoder = DictEncoder(context=context, config=SerializerConfig(indent="  "))
        self.pb_dict = {"Problem": encoder.encode(self.problem)}
        self.inspect_tree = build_inspect_tree(encoder.encode(self.problem))

    def to_str(self) -> str:
        config = SerializerConfig(indent="  ", xml_declaration=False)
        context = XmlContext(
            element_name_generator=text.pascal_case,
            attribute_name_generator=text.camel_case,
        )
        serializer = XmlSerializer(context=context, config=config)
        return serializer.render(self.problem)


def build_inspect_tree(obj, *, dict_factory=dict) -> dict:
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

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
    # if not _is_dataclass_instance(obj):
    #     raise TypeError("asdict() should be called on dataclass instances")

    return _build_inspect_tree_inner("Problem", obj, [])


def _build_inspect_tree_inner(key, obj, path) -> dict:
    sub_node = dict()
    if "name" in obj:
        sub_node["title"] = obj["name"]
    else:
        sub_node["title"] = key
    # sub_node["id"] = randrange(150)
    sub_node["children"] = list()
    # sub_node["hidden_children"] = list()
    sub_node["is_drawable"] = key in [
        "VTKMesh",
        "InternalMesh",
        "InternalWell",
        "Perforation",
    ]
    sub_node["drawn"] = False

    for key, value in obj.items():

        if isinstance(value, list):
            for idx, item in enumerate(value):
                if isinstance(item, dict):
                    more_results = _build_inspect_tree_inner(
                        key, item, path + [key] + [idx]
                    )
                    # for another_result in more_results:
                    sub_node["children"].append(more_results)

    # sub_node["path"] = path + [sub_node["name"]]
    sub_node["id"] = "Problem/" + "/".join(map(str, path))

    return sub_node


def format_attribute(attribute_indent: str, ka: str, attribute_value: str) -> str:
    """Format xml attribute strings

    Args:
        attribute_indent (str): Attribute indent string
        ka (str): Attribute name
        attribute_value (str): Attribute value

    Returns:
        str: Formatted attribute value
    """
    # Make sure that a space follows commas
    attribute_value = re.sub(r",\s*", ", ", attribute_value)

    # Handle external brackets
    attribute_value = re.sub(r"{\s*", "{ ", attribute_value)
    attribute_value = re.sub(r"\s*}", " }", attribute_value)

    # Consolidate whitespace
    attribute_value = re.sub(r"\s+", " ", attribute_value)

    # Identify and split multi-line attributes
    if re.match(r"\s*{\s*({[-+.,0-9a-zA-Z\s]*},?\s*)*\s*}", attribute_value):
        split_positions: List[Any] = [
            match.end() for match in re.finditer(r"}\s*,", attribute_value)
        ]
        newline_indent = "\n%s" % (" " * (len(attribute_indent) + len(ka) + 4))
        new_values = []
        for a, b in zip([None] + split_positions, split_positions + [None]):
            new_values.append(attribute_value[a:b].strip())
        if new_values:
            attribute_value = newline_indent.join(new_values)

    return attribute_value


def format_xml_level(
    output: TextIO,
    node: ElementTree.Element,
    level: int,
    indent: str = " " * 2,
    block_separation_max_depth: int = 2,
    modify_attribute_indent: bool = False,
    sort_attributes: bool = False,
    close_tag_newline: bool = False,
    include_namespace: bool = False,
) -> None:
    """Iteratively format the xml file

    Args:
        output (file): the output text file handle
        node (lxml.etree.Element): the current xml element
        level (int): the xml depth
        indent (str): the xml indent style
        block_separation_max_depth (int): the maximum depth to separate adjacent elements
        modify_attribute_indent (bool): option to have flexible attribute indentation
        sort_attributes (bool): option to sort attributes alphabetically
        close_tag_newline (bool): option to place close tag on a separate line
        include_namespace (bool): option to include the xml namespace in the output
    """

    # Handle comments
    if node.tag is ElementTree.Comment:
        output.write("\n%s<!--%s-->" % (indent * level, node.text))

    else:
        # Write opening line
        opening_line = "\n%s<%s" % (indent * level, node.tag)
        output.write(opening_line)

        # Write attributes
        if len(node.attrib) > 0:
            # Choose indentation
            attribute_indent = "%s" % (indent * (level + 1))
            if modify_attribute_indent:
                attribute_indent = " " * (len(opening_line))

            # Get a copy of the attributes
            attribute_dict = {}
            attribute_dict = node.attrib

            # Sort attribute names
            akeys = list(attribute_dict.keys())
            if sort_attributes:
                akeys = sorted(akeys)

            # Format attributes
            for ka in akeys:
                # Avoid formatting mathpresso expressions
                if not (
                    node.tag in ["SymbolicFunction", "CompositeFunction"]
                    and ka == "expression"
                ):
                    attribute_dict[ka] = format_attribute(
                        attribute_indent, ka, attribute_dict[ka]
                    )

            for ii in range(0, len(akeys)):
                k = akeys[ii]
                if (ii == 0) & modify_attribute_indent:
                    # TODO: attrib_ute_dict isn't define here which leads to an error
                    # output.write(' %s="%s"' % (k, attrib_ute_dict[k]))
                    pass
                else:
                    output.write(
                        '\n%s%s="%s"' % (attribute_indent, k, attribute_dict[k])
                    )

        # Write children
        if len(node):
            output.write(">")
            Nc = len(node)
            for ii, child in zip(range(Nc), node):
                format_xml_level(
                    output,
                    child,
                    level + 1,
                    indent,
                    block_separation_max_depth,
                    modify_attribute_indent,
                    sort_attributes,
                    close_tag_newline,
                    include_namespace,
                )

                # Add space between blocks
                if (
                    (level < block_separation_max_depth)
                    & (ii < Nc - 1)
                    & (child.tag is not ElementTree.Comment)
                ):
                    output.write("\n")

            # Write the end tag
            output.write("\n%s</%s>" % (indent * level, node.tag))
        else:
            if close_tag_newline:
                output.write("\n%s/>" % (indent * level))
            else:
                output.write("/>")


def format_xml(
    input: str,
    indent_size: int = 2,
    indent_style: bool = False,
    block_separation_max_depth: int = 2,
    alphebitize_attributes: bool = False,
    close_style: bool = False,
    namespace: bool = False,
) -> None:
    """Script to format xml files

    Args:
        input (str): Input str
        indent_size (int): Indent size
        indent_style (bool): Style of indentation (0=fixed, 1=hanging)
        block_separation_max_depth (int): Max depth to separate xml blocks
        alphebitize_attributes (bool): Alphebitize attributes
        close_style (bool): Style of close tag (0=same line, 1=new line)
        namespace (bool): Insert this namespace in the xml description
    """
    try:
        root = ElementTree.fromstring(input)
        # root = tree.getroot()
        prologue_comments = [tmp.text for tmp in root.itersiblings(preceding=True)]
        epilog_comments = [tmp.text for tmp in root.itersiblings()]

        f = StringIO()
        f.write('<?xml version="1.0" ?>\n')

        for comment in reversed(prologue_comments):
            f.write("\n<!--%s-->" % (comment))

        format_xml_level(
            f,
            root,
            0,
            indent=" " * indent_size,
            block_separation_max_depth=block_separation_max_depth,
            modify_attribute_indent=indent_style,
            sort_attributes=alphebitize_attributes,
            close_tag_newline=close_style,
            include_namespace=namespace,
        )

        for comment in epilog_comments:
            f.write("\n<!--%s-->" % (comment))
        f.write("\n")

        return f.getvalue()

    except ElementTree.ParseError as err:
        print("\nCould not load file: %s" % (f))
        print(err.msg)
        raise Exception("\nCheck input file!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Need an input file as argument")
        exit(1)
    filename = sys.argv[1]
    deck_file = DeckFile(filename)
    print(deck_file.root_fields)
