# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv


class RegionViewer:

    def __init__( self ) -> None:
        """Stores all related data information to represent the whole mesh.

        This mesh is represented in GEOS with a Region.
        """
        self.input = pv.UnstructuredGrid()
        self.clip = self.input

    def add_mesh( self, mesh: pv.UnstructuredGrid ) -> None:
        """Set the input to the given mesh."""
        self.input = mesh  # type: ignore
        self.clip = self.input.copy()  # type: ignore

    def update_clip( self, normal: tuple[ float ], origin: tuple[ float ] ) -> None:
        """Update the current clip with the given normal and origin."""
        self.clip = self.input.clip( normal=normal, origin=origin, crinkle=True )  # type: ignore

    def reset( self ) -> None:
        """Reset the input mesh and clip."""
        self.input = pv.UnstructuredGrid()
        self.clip = self.input
