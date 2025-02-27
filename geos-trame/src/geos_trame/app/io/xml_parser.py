# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import os
import re
from os.path import expandvars
from pathlib import Path

from lxml import etree as ElementTree
from lxml.etree import XMLSyntaxError

from collections import defaultdict

from geos_trame.app.geosTrameException import GeosTrameException


class XMLParser(object):
    """
    Class used to parse a valid XML geos file and construct a link between
    each file when they are included.

    Useful to be able to able to save it later.
    """

    def __init__(self, filename: str) -> None:
        """
        Constructor which takes in input the xml file used to generate pedantic file.
        """

        self.filename = filename
        self.file_to_tags = defaultdict(list)
        self.file_to_relative_path = {}

        expanded_file = Path(expandvars(self.filename)).expanduser().resolve()
        self.file_path = expanded_file.parent
        self._is_valid = True

        try:
            parser = ElementTree.XMLParser(remove_comments=True, remove_blank_text=True)
            tree = ElementTree.parse(expanded_file, parser=parser)
            self.root = tree.getroot()
        except XMLSyntaxError as err:
            error_msg = "Invalid XML file. Cannot load " + expanded_file
            error_msg += ". Outputted error:\n" + err.msg
            print(error_msg, file=os.sys.stderr)
            self._is_valid = False

    def is_valid(self) -> bool:
        if not self._is_valid:
            print("XMLParser isn't valid", file=os.sys.stderr)
        return self._is_valid

    def build(self) -> None:
        if not self.is_valid():
            raise GeosTrameException("Cannot parse this file.")
        self._read()

    def get_simulation_deck(self) -> ElementTree.Element:
        if not self.is_valid():
            raise GeosTrameException("Not valid file, cannot return the deck.")
            return
        return self.simulation_deck

    def _read(self) -> ElementTree.Element:
        """Reads an xml file (and recursively its included files) into memory

        Args:
            xmlFilepath (str): The path the file to read.

        Returns:
            SimulationDeck: The simulation deck
        """
        for include_node in self.root:
            tags = self.file_to_tags[self.filename]
            tags.append(include_node.tag)

        includeCount = 0
        for include_node in self.root:
            if include_node.tag == "Included":
                for f in include_node.findall("File"):
                    self.file_to_relative_path[self.filename] = f.get("name")
                    self._merge_included_xml_files(
                        self.root, self.file_path, f.get("name"), includeCount
                    )

        # Remove 'Included' nodes
        for include_node in self.root.findall("Included"):
            self.root.remove(include_node)

        for neighbor in self.root.iter():
            for key in neighbor.attrib.keys():
                # remove unnecessary whitespaces for indentation
                s = re.sub(r"\s{2,}", " ", neighbor.get(key))
                neighbor.set(key, s)

        self.simulation_deck = self.root

    def _merge_xml_nodes(
        self,
        existingNode: ElementTree.Element,
        targetNode: ElementTree.Element,
        fname: str,
        level: int,
    ) -> None:
        """Merge nodes in an included file into the current structure level by level.

        Args:
            existingNode (lxml.etree.Element): The current node in the base xml structure.
            targetNode (lxml.etree.Element): The node to insert.
            level (int): The xml file depth.
        """
        if not self.is_valid():
            raise GeosTrameException("Not valid file, cannot merge nodes")
            return
        # Copy attributes on the current level
        for tk in targetNode.attrib.keys():
            existingNode.set(tk, targetNode.get(tk))

        # Copy target children into the xml structure
        currentTag = ""
        matchingSubNodes = []

        for target in targetNode.getchildren():
            tags = self.file_to_tags[fname]
            tags.append(target.tag)
            insertCurrentLevel = True

            # Check to see if a node with the appropriate type
            # exists at this level
            if currentTag != target.tag:
                currentTag = target.tag
                matchingSubNodes = existingNode.findall(target.tag)

            if matchingSubNodes:
                targetName = target.get("name")

                # Special case for the root Problem node (which may be unnamed)
                if level == 0:
                    insertCurrentLevel = False
                    self._merge_xml_nodes(matchingSubNodes[0], target, fname, level + 1)

                # Handle named xml nodes
                elif targetName and (currentTag not in ["Nodeset"]):
                    for match in matchingSubNodes:
                        if match.get("name") == targetName:
                            insertCurrentLevel = False
                            self._merge_xml_nodes(match, target, fname, level + 1)

            # Insert any unnamed nodes or named nodes that aren't present
            # in the current xml structure
            if insertCurrentLevel:
                existingNode.insert(-1, target)

    def _merge_included_xml_files(
        self,
        root: ElementTree.Element,
        file_path: str,
        fname: str,
        includeCount: int,
        maxInclude: int = 100,
    ) -> None:
        """Recursively merge included files into the current structure.

        Args:
            root (lxml.etree.Element): The root node of the base xml structure.
            fname (str): The name of the target xml file to merge.
            includeCount (int): The current recursion depth.
            maxInclude (int): The maximum number of xml files to include (default = 100)
        """
        if not self.is_valid():
            raise GeosTrameException("Not valid file, cannot merge nodes")
            return
        included_file_path = Path(expandvars(file_path), fname)
        expanded_file = included_file_path.expanduser().resolve()

        self.file_to_relative_path[fname] = ""

        # Check to see if the code has fallen into a loop
        includeCount += 1
        if includeCount > maxInclude:
            raise Exception(
                "Reached maximum recursive includes...  Is there an include loop?"
            )

        # Check to make sure the file exists
        if not included_file_path.is_file():
            print(
                "Included file does not exist: %s" % (included_file_path),
                file=os.sys.stderr,
            )
            raise Exception("Check included file path!")

        # Load target xml
        try:
            parser = ElementTree.XMLParser(remove_comments=True, remove_blank_text=True)
            includeTree = ElementTree.parse(included_file_path, parser)
            includeRoot = includeTree.getroot()
        except XMLSyntaxError as err:
            print("\nCould not load included file: %s" % (included_file_path))
            print(err.msg)
            raise Exception("\nCheck included file!") from err

        # Recursively add the includes:
        for include_node in includeRoot.findall("Included"):
            for f in include_node.findall("File"):
                self.file_to_relative_path[fname] = f.get("name")
                self._merge_included_xml_files(
                    root, expanded_file.parent, f.get("name"), includeCount
                )

        # Merge the results into the xml tree
        self._merge_xml_nodes(root, includeRoot, fname, 0)
