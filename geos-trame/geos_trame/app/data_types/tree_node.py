# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from dataclasses import dataclass


@dataclass
class TreeNode:
    """Single element of the tree, used by `DeckTree`.

    `valid` has to be an int for serialization purposes, but is actually a FieldStatus so only possibles values are:
        - 0 (UNCHECKED): Validity check has not been performed.
        - 1 (VALID): TreeNode is checked and valid.
        - 2 (INVALID): TreeNode is checked and invalid.
    """

    id: str
    title: str
    children: list
    hidden_children: list
    is_drawable: bool
    drawn: bool
    valid: int

    @property
    def json( self ) -> dict:
        """Get the tree node as json."""
        return {
            "id": self.id,
            "title": self.title,
            "is_drawable": self.is_drawable,
            "drawn": self.drawn,
            "valid": self.valid,
            "children": [ c.json for c in self.children ] if self.children else None,
            "hidden_children": ( [ c.json for c in self.hidden_children ] if self.hidden_children else [] ),
        }
