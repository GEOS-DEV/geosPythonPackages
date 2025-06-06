# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Kitware
from typing import Type, Any

import numpy as np
from trame_client.widgets.core import AbstractElement
import pyvista as pv

from geos.trame.app.deck.tree import DeckTree
from geos.trame.app.geosTrameException import GeosTrameException
from geos.trame.app.ui.viewer.regionViewer import RegionViewer
from geos.trame.app.ui.viewer.wellViewer import WellViewer
from geos.trame.app.utils.pv_utils import read_unstructured_grid
from geos.trame.schema_generated.schema_mod import (
    Vtkmesh,
    Vtkwell,
    Perforation,
    InternalWell,
)


class DataLoader( AbstractElement ):
    """Helper class to handle IO operations for data loading."""

    def __init__(
        self,
        source: DeckTree,
        region_viewer: RegionViewer,
        well_viewer: WellViewer,
        **kwargs: Any,
    ) -> None:
        """Constructor."""
        super().__init__( "span", **kwargs )

        self.source = source
        self.region_viewer = region_viewer
        self.well_viewer = well_viewer

        self.state.change( "object_state" )( self._update_object_state )
        self.ctrl.load_vtkmesh_from_id.add( self.load_vtkmesh_from_id )

    def load_vtkmesh_from_id( self, node_id: str ) -> None:
        """Load the data at the given id if none is already loaded."""
        if self.region_viewer.input.number_of_cells == 0:
            active_block = self.source.decode( node_id )
            if isinstance( active_block, Vtkmesh ):
                self._read_mesh( active_block )

    def _update_object_state( self, object_state: tuple[ str, bool ], **_: dict ) -> None:

        path, show_obj = object_state

        if path == "":
            return

        active_block = self.source.decode( path )

        if isinstance( active_block, Vtkmesh ):
            self._update_vtkmesh( active_block, show_obj )

        if isinstance( active_block, Vtkwell ):
            if self.region_viewer.input.number_of_cells == 0 and show_obj:
                self.ctrl.on_add_warning(
                    "Can't display " + active_block.name,
                    "Please display the mesh before creating a well.",
                )
                return

            self._update_vtkwell( active_block, path, show_obj )

        if isinstance( active_block, InternalWell ):
            if self.region_viewer.input.number_of_cells == 0 and show_obj:
                self.ctrl.on_add_warning(
                    "Can't display " + active_block.name,
                    "Please display the mesh before creating a well",
                )
                return

            self._update_internalwell( active_block, path, show_obj )

        if ( isinstance( active_block, Perforation ) and self.well_viewer.get_number_of_wells() == 0 and show_obj ):
            self.ctrl.on_add_warning(
                "Can't display " + active_block.name,
                "Please display a well before creating a perforation",
            )
            return

        self.ctrl.update_viewer( active_block, path, show_obj )

    def _update_vtkmesh( self, mesh: Vtkmesh, show: bool ) -> None:
        if not show:
            self.region_viewer.reset()
            return

        self._read_mesh( mesh )

    def _read_mesh( self, mesh: Vtkmesh ) -> None:
        unstructured_grid = read_unstructured_grid( self.source.get_abs_path( mesh.file ) )
        self.region_viewer.add_mesh( unstructured_grid )

    def _update_vtkwell( self, well: Vtkwell, path: str, show: bool ) -> None:
        if not show:
            self.well_viewer.remove( path )
            return

        well_polydata = pv.read( self.source.get_abs_path( well.file ) )
        if not isinstance( well_polydata, pv.PolyData ):
            raise GeosTrameException( f"Expected PolyData, got {type(well_polydata).__name__}" )
        self.well_viewer.add_mesh( well_polydata, path )

    def _update_internalwell( self, well: InternalWell, path: str, show: bool ) -> None:
        """Used to control the visibility of the InternalWell.

        This method will create the mesh if it doesn't exist.
        """
        if not show:
            self.well_viewer.remove( path )
            return

        points = self.__parse_polyline_property( well.polyline_node_coords, dtype=float )
        connectivity = self.__parse_polyline_property( well.polyline_segment_conn, dtype=int )
        connectivity = connectivity.flatten()

        sorted_points = []
        for point_id in connectivity:
            sorted_points.append( points[ point_id ] )

        well_polydata = pv.MultipleLines( sorted_points )
        self.well_viewer.add_mesh( well_polydata, path )

    @staticmethod
    def __parse_polyline_property( polyline_property: str, dtype: Type[ Any ] ) -> np.ndarray:
        """Internal method used to parse and convert a property, such as polyline_node_coords, from an InternalWell.

        This string always follow this for :
            "{ { 800, 1450, 395.646 }, { 800, 1450, -554.354 } }"
        """
        try:
            nodes_str = polyline_property.split( "}, {" )
            points = []
            for i in range( 0, len( nodes_str ) ):

                nodes_str[ i ] = nodes_str[ i ].replace( " ", "" )
                nodes_str[ i ] = nodes_str[ i ].replace( "{", "" )
                nodes_str[ i ] = nodes_str[ i ].replace( "}", "" )

                point = np.array( nodes_str[ i ].split( "," ), dtype=dtype )

                points.append( point )

            return np.array( points, dtype=dtype )
        except ValueError as e:
            raise GeosTrameException(
                "cannot be able to convert the property into a numeric array: ",
                ValueError,
            ) from e
