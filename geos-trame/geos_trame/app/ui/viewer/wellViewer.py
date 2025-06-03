# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv

from dataclasses import dataclass


@dataclass
class Well:
    """A Well is represented by a polyline and a tube.

    This class stores also the related actor and his given path
    to simplify data management.
    """

    well_path: str
    polyline: pv.PolyData
    tube: pv.PolyData
    actor: pv.Actor


class WellViewer:

    def __init__( self, size: float, amplification: float ) -> None:
        """WellViewer stores all Well used in the pv.Plotter().

        A Well in GEOS could a InternalWell or a Vtkwell.
        """
        self._wells: list[ Well ] = []

        self.size: float = size
        self.amplification: float = amplification
        self.STARTING_VALUE: float = 5.0

    def __call__( self, value: float ) -> None:
        """Call update."""
        self.update( value )

    def get_last_mesh_idx( self ) -> int:
        """Returns the index of the last mesh."""
        return len( self._wells ) - 1

    def add_mesh( self, mesh: pv.PolyData, mesh_path: str ) -> int:
        """Store a given mesh representing a polyline.

        This polyline will be used then to create a tube to represent this line.

        return the indexed position of the stored well.
        """
        radius = self.size * ( self.STARTING_VALUE / 100 )
        tube = mesh.tube( radius=radius, n_sides=50 )

        self._wells.append( Well( mesh_path, mesh, tube, pv.Actor() ) )

        return len( self._wells ) - 1

    def get_mesh( self, perforation_path: str ) -> pv.PolyData | None:
        """Retrieve the polyline linked to a given perforation path."""
        index = self._get_index_from_perforation( perforation_path )
        if index == -1:
            print( "Cannot found the well to remove from path: ", perforation_path )
            return None

        return self._wells[ index ].polyline

    def get_tube( self, index: int ) -> pv.PolyData | None:
        """Retrieve the polyline linked to a given perforation path."""
        if index < 0 or index > len( self._wells ):
            print( "Cannot get the tube at index: ", index )
            return None

        return self._wells[ index ].tube

    def get_tube_size( self ) -> float:
        """Get the size used for the tube."""
        return self.size

    def append_actor( self, perforation_path: str, tube_actor: pv.Actor ) -> None:
        """Append a given actor, typically the Actor returned by the pv.Plotter() when a given mes is added."""
        index = self._get_index_from_perforation( perforation_path )
        if index == -1:
            print( "Cannot found the well to remove from path: ", perforation_path )
            return

        self._wells[ index ].actor = tube_actor

    def get_actor( self, perforation_path: str ) -> pv.Actor | None:
        """Retrieve the polyline linked to a given perforation path."""
        index = self._get_index_from_perforation( perforation_path )
        if index == -1:
            print( "Cannot found the well to remove from path: ", perforation_path )
            return None

        return self._wells[ index ].actor

    def update( self, value: float ) -> None:
        """Update the radius of the tubes."""
        self.size = value
        for idx, m in enumerate( self._wells ):
            self._wells[ idx ].tube.copy_from( m.polyline.tube( radius=self.size, n_sides=50 ) )

    def remove( self, perforation_path: str ) -> None:
        """Clear all data stored in this class."""
        index = self._get_index_from_perforation( perforation_path )
        if index == -1:
            print( "Cannot found the well to remove from path: ", perforation_path )

        self._wells.remove( self._wells[ index ] )

    def _get_index_from_perforation( self, perforation_path: str ) -> int:
        """Retrieve the well associated to a given perforation, otherwise return -1."""
        index = -1
        if len( self._wells ) == 0:
            return index

        for i in range( 0, len( self._wells ) ):
            if self._wells[ i ].well_path in perforation_path:
                index = i
                break

        return index

    def get_number_of_wells( self ) -> int:
        """Get the number of wells in the viewer."""
        return len( self._wells )
