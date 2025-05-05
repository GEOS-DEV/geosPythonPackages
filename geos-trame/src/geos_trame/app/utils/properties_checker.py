# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware

from trame_client.widgets.core import AbstractElement

from geos_trame.app.deck.tree import DeckTree

expected_properties = [
    ("region_attribute", ["attribute", "{}"]),
    ("fields_to_import", ["attribute", "{}"]),
]

class PropertiesChecker(AbstractElement):
    """
    Class to check the validity of properties within a deck tree.
    """
    def __init__( self, tree: DeckTree, **kwargs ):
        super().__init__("div", **kwargs)

        self.tree = tree

    def check_fields(self):
        for field in self.state.deck_tree:
            self.check_field( field )
        self.state.dirty("deck_tree")
        self.state.flush()

    def check_attr_value(self, obj, attr, expected, field):
        if hasattr(obj, attr) and getattr(obj, attr) not in expected:
            field["invalid_properties"].append(attr)

    def check_field(self, field):
        field["valid"] = 1
        block = self.tree.decode(field["id"])
        field["invalid_properties"] = []

        for attr, expected in expected_properties:
            self.check_attr_value(block, attr, expected, field)

        if len(field["invalid_properties"]) != 0:
            field["valid"] = 2
        else:
            field.pop("invalid_properties", None)

        if field["children"] is not None:
            # Parents are only valid if all children are valid
            field["invalid_children"] = []
            for child in field["children"]:
                self.check_field(child)
                if child["valid"] == 2:
                    field["valid"] = 2
                    field["invalid_children"].append(child["title"])
            if len(field["invalid_children"]) == 0:
                field.pop("invalid_children", None)
