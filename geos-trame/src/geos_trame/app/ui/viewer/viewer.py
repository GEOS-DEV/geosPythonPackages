# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
import pyvista as pv
from pyvista.trame.ui import plotter_ui
from trame.widgets import vuetify3 as vuetify
from trame.widgets import html

from geos_trame.schema_generated.schema_mod import (
    Vtkmesh,
    Vtkwell,
    Perforation,
    InternalWell,
)

import geos_trame.app.ui.viewer.regionViewer as RegionViewer
import geos_trame.app.ui.viewer.wellViewer as WellViewer
import geos_trame.app.ui.viewer.perforationViewer as PerforationViewer
from geos_trame.app.geosTrameException import GeosTrameException

import numpy as np
from typing import Type, Any

pv.OFF_SCREEN = True


class DeckViewer( vuetify.VCard ):
    """
    Deck representing the 3D View using PyVista.

    This view can show:
     - Vtkmesh,
     - Vtkwell,
     - Perforation,
     - InternalWell

    Everything is handle in the method 'update_viewer()' which is trigger when the
    'state.object_state' changed (see DeckTree).

    This View handle widgets, such as clip widget or slider to control Wells or
    Perforation settings.
    """

    def __init__( self, source, **kwargs ):
        super().__init__( **kwargs )

        self._source = source
        self._pl = pv.Plotter()

        self.CUT_PLANE = "on_cut_plane_visibility_change"
        self.ZAMPLIFICATION = "_z_amplification"
        self.server.state[ self.CUT_PLANE ] = True
        self.server.state[ self.ZAMPLIFICATION ] = 1

        self.region_engine = RegionViewer.RegionViewer()
        self.well_engine = WellViewer.WellViewer( 5, 5 )
        self._perforations: dict[ str, PerforationViewer.PerforationViewer ] = dict()

        self.state.change( "object_state" )( self.update_viewer )

        with self:
            vuetify.VCardTitle( "3D View" )
            view = plotter_ui(
                self._pl,
                add_menu_items=self.rendering_menu_extra_items,
                style="position: absolute;",
            )
            self.ctrl.view_update = view.update

    @property
    def plotter( self ):
        return self._pl

    @property
    def source( self ):
        return self._source

    def rendering_menu_extra_items( self ):
        """
        Extend the default pyvista menu with custom button.

        For now, adding a button to show/hide all widgets.
        """
        self.state.change( self.CUT_PLANE )( self._on_clip_visibility_change )
        vuetify.VDivider( vertical=True, classes="mr-1" )
        with vuetify.VTooltip( location="bottom" ):
            with vuetify.Template( v_slot_activator=( "{ props }", ) ):
                with html.Div( v_bind=( "props", ) ):
                    vuetify.VCheckbox(
                        v_model=( self.CUT_PLANE, True ),
                        icon=True,
                        true_icon="mdi-eye",
                        false_icon="mdi-eye-off",
                        dense=True,
                        hide_details=True,
                    )
            html.Span( "Show/Hide widgets" )

    def update_viewer( self, object_state: list[ str, bool ], **kwargs ) -> None:
        """
        Add from path the dataset given by the user.
        Supported data type is: Vtkwell, Vtkmesh, InternalWell, Perforation.

        object_state  : array used to store path to the data and if we want to show it or not.
        """
        path = object_state[ 0 ]
        show_obj = object_state[ 1 ]

        if path == "":
            return
        active_block = self.source.decode( path )

        if isinstance( active_block, Vtkmesh ):
            self._update_vtkmesh( active_block, show_obj )

        if isinstance( active_block, Vtkwell ):
            if self.region_engine.input.number_of_cells == 0 and show_obj:

                self.ctrl.on_add_warning(
                    "Can't display " + active_block.name,
                    "Please display the mesh before creating a well.",
                )
                return

            self._update_vtkwell( active_block, path, show_obj )

        if isinstance( active_block, InternalWell ):
            if self.region_engine.input.number_of_cells == 0 and show_obj:
                self.ctrl.on_add_warning(
                    "Can't display " + active_block.name,
                    "Please display the mesh before creating a well",
                )
                return

            self._update_internalwell( active_block, path, show_obj )

        if isinstance( active_block, Perforation ):
            if self.well_engine.get_number_of_wells() == 0 and show_obj:
                self.ctrl.on_add_warning(
                    "Can't display " + active_block.name,
                    "Please display a well before creating a perforation",
                )
                return
            self._update_perforation( active_block, show_obj, path )

    def _on_clip_visibility_change( self, **kwargs ):
        """Toggle cut plane visibility for all actors.

        Parameters
        ----------
        **kwargs : dict, optional
            Unused keyword arguments.

        """
        show_widgets = kwargs[ self.CUT_PLANE ]
        if show_widgets:
            self._setup_slider()
        else:
            self._remove_slider()

        if self.plotter.plane_widgets:
            widgets = self.plotter.plane_widgets
            widgets[ 0 ].SetEnabled( show_widgets )
        self.plotter.render()

    def _setup_slider( self ) -> None:
        """
        Create slider to control in the gui well parameters.
        """

        wells_radius = self._get_tube_size()
        self.plotter.add_slider_widget(
            self._on_change_tube_size,
            [ 1, 20 ],
            title="Wells radius",
            pointa=( 0.02, 0.12 ),
            pointb=( 0.30, 0.12 ),
            title_opacity=0.5,
            title_color="black",
            title_height=0.02,
            value=wells_radius,
        )

        perforation_radius = self._get_perforation_size()
        self.plotter.add_slider_widget(
            self._on_change_perforation_size,
            [ 1, 50 ],
            title="Perforation radius",
            title_opacity=0.5,
            pointa=( 0.02, 0.25 ),
            pointb=( 0.30, 0.25 ),
            title_color="black",
            title_height=0.02,
            value=perforation_radius,
        )

    def _remove_slider( self ) -> None:
        """
        Create slider to control in the gui well parameters.
        """
        self.plotter.clear_slider_widgets()

    def _on_change_tube_size( self, value ) -> None:
        self.well_engine.update( value )

    def _get_tube_size( self ) -> float:
        return self.well_engine.get_tube_size()

    def _on_change_perforation_size( self, value ) -> None:
        for key, perforation in self._perforations.items():
            perforation.update_perforation_radius( value )

    def _get_perforation_size( self ) -> float:
        if len( self._perforations ) <= 0:
            return 5

        for key, perforation in self._perforations.items():
            return perforation.get_perforation_size()

    def _update_internalwell( self, well: InternalWell, path: str, show: bool ) -> None:
        """
        Used to control the visibility of the InternalWell.
        This method will create the mesh if it doesn't exist.
        """
        if not show:
            self.plotter.remove_actor( self.well_engine.get_actor( path ) )
            self.well_engine.remove( path )
            return

        points = self.__parse_polyline_property( well.polyline_node_coords, dtype=float )
        connectivity = self.__parse_polyline_property( well.polyline_segment_conn, dtype=int )
        connectivity = connectivity.flatten()

        sorted_points = []
        for id in connectivity:
            sorted_points.append( points[ id ] )

        well_polydata = pv.MultipleLines( sorted_points )
        index = self.well_engine.add_mesh( well_polydata, path )

        tube_actor = self.plotter.add_mesh( self.well_engine.get_tube( index ) )
        self.well_engine.append_actor( path, tube_actor )

        self.server.controller.view_update()

    def _update_vtkwell( self, well: Vtkwell, path: str, show: bool ) -> None:
        """
        Used to control the visibility of the Vtkwell.
        This method will create the mesh if it doesn't exist.
        """
        if not show:
            self.plotter.remove_actor( self.well_engine.get_actor( path ) )
            self.well_engine.remove( path )
            return

        well_polydata = pv.PolyData.SafeDownCast( pv.read( self.source.get_abs_path( well.file ) ) )
        index = self.well_engine.add_mesh( well_polydata, path )

        tube_actor = self.plotter.add_mesh( self.well_engine.get_tube( index ) )
        self.well_engine.append_actor( path, tube_actor )

        self.server.controller.view_update()

    def _update_vtkmesh( self, mesh: Vtkmesh, show: bool ) -> None:
        """
        Used to control the visibility of the Vtkmesh.
        This method will create the mesh if it doesn't exist.

        Additionally, a clip filter will be added.
        """

        if not show:
            self.region_engine.reset()
            self.plotter.clear_plane_widgets()
            self.plotter.remove_actor( self._clip_mesh )
            return

        unsctructured_grid = pv.UnstructuredGrid.SafeDownCast( pv.read( self.source.get_abs_path( mesh.file ) ) )
        self.region_engine.add_mesh( unsctructured_grid )
        active_scalar = self.region_engine.input.active_scalars_name
        self._clip_mesh = self.plotter.add_mesh_clip_plane(
            self.region_engine.input,
            origin=self.region_engine.input.center,
            normal=[ -1, 0, 0 ],
            crinkle=True,
            show_edges=False,
            cmap="glasbey_bw",
            scalars=active_scalar,
        )

        self.server.controller.view_update()

    def _update_perforation( self, perforation: Perforation, show: bool, path: str ) -> None:
        """
        Generate VTK dataset from a perforation.
        """

        if not show:
            if path in self._perforations:
                self._remove_perforation( path )
            return

        distance_from_head = float( perforation.distance_from_head )
        self._add_perforation( distance_from_head, path )

    def _remove_perforation( self, path: str ) -> None:
        """
        Remove all actor related to the given path and clean the stored perforation
        """
        saved_perforation: PerforationViewer.PerforationViewer = self._perforations[ path ]
        self.plotter.remove_actor( saved_perforation.extracted_cell )
        self.plotter.remove_actor( saved_perforation.perforation_actor )
        saved_perforation.reset()

    def _add_perforation( self, distance_from_head: float, path: str ) -> None:
        """
        Generate perforation dataset based on the distance from the top of a polyline
        """

        polyline: pv.PolyData = self.well_engine.get_mesh( path )
        if polyline is None:
            return

        point = polyline.points[ 0 ]
        point_offsetted = [
            point[ 0 ],
            point[ 1 ],
            point[ 2 ] - distance_from_head,
        ]

        center = [ point[ 0 ], point[ 1 ], point[ 2 ] - float( distance_from_head ) ]
        sphere = pv.Sphere( radius=5, center=center )

        perforation_actor = self.plotter.add_mesh( sphere )
        saved_perforation = PerforationViewer.PerforationViewer( sphere, center, 5, perforation_actor )

        id = self.region_engine.input.find_closest_cell( point_offsetted )
        cell = self.region_engine.input.extract_cells( [ id ] )
        cell_actor = self.plotter.add_mesh( cell )
        saved_perforation.add_extracted_cell( cell_actor )

        self._perforations[ path ] = saved_perforation

    def __parse_polyline_property( self, property: str, dtype: Type[ Any ] ) -> np.ndarray[ Any ]:
        """
        Internal method used to parse and convert a property, such as polyline_node_coords, from an InternalWell.
        This string always follow this for :
            "{ { 800, 1450, 395.646 }, { 800, 1450, -554.354 } }"
        """
        try:
            nodes_str = property.split( "}, {" )
            points = []
            for i in range( 0, len( nodes_str ) ):

                nodes_str[ i ] = nodes_str[ i ].replace( " ", "" )
                nodes_str[ i ] = nodes_str[ i ].replace( "{", "" )
                nodes_str[ i ] = nodes_str[ i ].replace( "}", "" )

                point = np.array( nodes_str[ i ].split( "," ), dtype=dtype )

                points.append( point )

            return np.array( points, dtype=dtype )
        except ValueError:
            raise GeosTrameException(
                "cannot be able to convert the property into a numeric array: ",
                ValueError,
            )
