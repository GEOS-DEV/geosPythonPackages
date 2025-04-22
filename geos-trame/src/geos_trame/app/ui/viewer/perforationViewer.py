# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv


class PerforationViewer:
    """
    Class representing how storing a GEOS Perforation.

    A perforation is represented by 2 meshes:
        _perforation_mesh : which is a sphere located where the perforation is
        _extracted_cell : the extracted cell at the perforation location
    """

    def __init__( self, mesh: pv.PolyData, center: list[ float ], radius: float, actor: pv.Actor ) -> None:
        self.perforation_mesh: pv.PolyData = mesh
        self.center: list[ float ] = center
        self.radius: float = radius
        self.perforation_actor: pv.Actor = actor
        self.extracted_cell: pv.Actor

    def add_extracted_cell( self, cell_actor: pv.Actor ) -> None:
        self.extracted_cell = cell_actor

    def update_perforation_radius( self, value: float ) -> None:
        self.radius = value
        self.perforation_mesh = pv.Sphere( radius=self.radius, center=self.center )
        self.perforation_actor.GetMapper().SetInputDataObject( self.perforation_mesh )
        self.perforation_actor.GetMapper().Update()

    def get_perforation_size( self ) -> float:
        return self.radius

    def reset( self ) -> None:
        self.perforation_actor = pv.Actor()
        self.perforation_mesh = pv.PolyData()
        self.extracted_cell = pv.Actor()
