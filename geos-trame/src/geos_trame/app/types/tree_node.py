# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from dataclasses import dataclass


@dataclass
class TreeNode:
    id: str
    title: str
    children: list
    hidden_children: list
    is_drawable: bool
    drawn: bool
    valid: int

    @property
    def json( self ) -> dict:
        if self.children:
            return dict(
                id=self.id,
                title=self.title,
                is_drawable=self.is_drawable,
                drawn=self.drawn,
                valid=self.valid,
                children=[ c.json for c in self.children ],
                hidden_children=[ c.json for c in self.hidden_children ],
            )
        return dict(
            id=self.id,
            title=self.title,
            is_drawable=self.is_drawable,
            drawn=self.drawn,
            valid=self.valid,
            children=None,
            hidden_children=[],
        )