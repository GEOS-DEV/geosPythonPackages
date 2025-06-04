# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv

from geos.trame.schema_generated.schema_mod import Box

import re


class BoxViewer:
    """A BoxViewer represents a Box and its intersected cell in a mesh.

    This mesh is represented in GEOS with a Box.
    """

    def __init__( self, mesh: pv.UnstructuredGrid, box: Box ) -> None:
        """Initialize the BoxViewer with a mesh and a box."""
        self._mesh: pv.UnstructuredGrid = mesh

        self._box: Box = box
        self._box_polydata: pv.PolyData = None
        self._box_polydata_actor: pv.Actor = None

        self._extracted_cell: pv.UnstructuredGrid = None
        self._extracted_cell_actor: pv.Actor = None

        self._compute_box_as_polydata()
        self._compute_intersected_cell()

    def append_to_plotter( self, plotter: pv.Plotter ) -> None:
        """Append the box and the intersected cell to the plotter.

        The box is represented as a polydata with a low opacity.
        """
        self._box_polydata_actor = plotter.add_mesh( self._box_polydata, opacity=0.2 )

        if self._extracted_cell is not None:
            self._extracted_cell_actor = plotter.add_mesh( self._extracted_cell, show_edges=True )

    def reset( self, plotter: pv.Plotter ) -> None:
        """Reset the box viewer by removing the box and the intersected cell from the plotter."""
        if self._box_polydata_actor is not None:
            plotter.remove_actor( self._box_polydata_actor )

        if self._extracted_cell_actor is not None:
            plotter.remove_actor( self._extracted_cell_actor )

        self._box_polydata = None
        self._extracted_cell = None

    def _compute_box_as_polydata( self ) -> None:
        """Create a polydata reresenting a BBox using pyvista and coordinates from the Geos Box."""
        bounding_box: list[ float ] = self._retrieve_bounding_box()
        self._box_polydata = pv.Box( bounds=bounding_box )

    def _retrieve_bounding_box( self ) -> list[ float ]:
        """This method converts bounding box information from Box into a list of coordinates readable by pyvista.

        e.g., this Box:

        <Box name="box_1"
             xMin="{ 1150, 700, 62 }"
             xMax="{ 1250, 800, 137 }"/>

        will return [1150, 1250, 700, 800, 62, 137].
        """
        # split str and remove brackets
        min_point_str = re.findall( r"-?\d+\.\d+|-?\d+", self._box.x_min )
        max_point_str = re.findall( r"-?\d+\.\d+|-?\d+", self._box.x_max )

        min_point = list( map( float, min_point_str ) )
        max_point = list( map( float, max_point_str ) )

        return [
            min_point[ 0 ],
            max_point[ 0 ],
            min_point[ 1 ],
            max_point[ 1 ],
            min_point[ 2 ],
            max_point[ 2 ],
        ]

    def _compute_intersected_cell( self ) -> None:
        """Extract the cells from the mesh that are inside the box."""
        ids = self._mesh.find_cells_within_bounds( self._box_polydata.bounds )

        saved_ids: list[ int ] = []

        for id in ids:
            cell: pv.vtkCell = self._mesh.GetCell( id )

            is_inside = self._check_cell_inside_box( cell, self._box_polydata.bounds )
            if is_inside:
                saved_ids.append( id )

        if len( saved_ids ) > 0:
            self._extracted_cell = self._mesh.extract_cells( saved_ids )

    def _check_cell_inside_box( self, cell: pv.Cell, box_bounds: list[ float ] ) -> bool:
        """Check if the cell is inside the box bounds.

        A cell is considered inside the box if his bounds are completely
        inside the box bounds.
        """
        cell_bounds = cell.GetBounds()
        is_inside_in_x = cell_bounds[ 0 ] >= box_bounds[ 0 ] and cell_bounds[ 1 ] <= box_bounds[ 1 ]
        is_inside_in_y = cell_bounds[ 2 ] >= box_bounds[ 2 ] and cell_bounds[ 3 ] <= box_bounds[ 3 ]
        is_inside_in_z = cell_bounds[ 4 ] >= box_bounds[ 4 ] and cell_bounds[ 5 ] <= box_bounds[ 5 ]

        return is_inside_in_x and is_inside_in_y and is_inside_in_z
