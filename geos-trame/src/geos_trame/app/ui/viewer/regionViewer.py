# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv


class RegionViewer:
    """
    Stores all related data information to represent the whole mesh.

    This mesh is represented in GEOS with a Region.
    """

    def __init__( self ) -> None:
        self.input: pv.UnstructuredGrid
        self.clip: pv.UnstructuredGrid
        self.reset()

    def __call__( self, normal: tuple[ float ], origin: tuple[ float ] ) -> None:
        self.update_clip( normal, origin )

    def add_mesh( self, mesh: pv.UnstructuredGrid ) -> None:
        self.input = mesh  # type: ignore
        self.clip = self.input.copy()  # type: ignore

    def update_clip( self, normal: tuple[ float ], origin: tuple[ float ] ) -> None:
        self.clip.copy_from( self.input.clip( normal=normal, origin=origin, crinkle=True ) )  # type: ignore

    def reset( self ) -> None:
        self.input = pv.UnstructuredGrid()
        self.clip = self.input
