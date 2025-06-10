# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lucas Givord - Kitware
from typing import Any

import pyvista as pv
from pydantic import BaseModel
from pyvista.trame.ui import plotter_ui
from trame.widgets import html
from trame.widgets import vuetify3 as vuetify
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkRenderingCore import vtkActor

from geos.trame.app.deck.tree import DeckTree
from geos.trame.app.ui.viewer.perforationViewer import PerforationViewer
from geos.trame.app.ui.viewer.regionViewer import RegionViewer
from geos.trame.app.ui.viewer.wellViewer import WellViewer
from geos.trame.schema_generated.schema_mod import Vtkmesh, Vtkwell, InternalWell, Perforation

pv.OFF_SCREEN = True


class DeckViewer( vuetify.VCard ):

    def __init__(
        self,
        source: DeckTree,
        region_viewer: RegionViewer,
        well_viewer: WellViewer,
        **kwargs: Any,
    ) -> None:
        """Deck representing the 3D View using PyVista.

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
        super().__init__( **kwargs )

        self._picked_actor: vtkActor | None = None
        self._point_data_array_names: list[ str ] = []
        self._cell_data_array_names: list[ str ] = []
        self._source = source
        self._pl = pv.Plotter()
        self._pl.enable_mesh_picking( callback=self._picking_callback,
                                      show_message=False,
                                      line_width=2,
                                      use_actor=True )

        self.CUT_PLANE = "on_cut_plane_visibility_change"
        self.ZAMPLIFICATION = "_z_amplification"
        self.state[ self.CUT_PLANE ] = True
        self.state[ self.ZAMPLIFICATION ] = 1

        self.DATA_ARRAYS = "viewer_data_arrays_items"
        self.SELECTED_DATA_ARRAY = "viewer_selected_data_array"
        self.state.change( self.SELECTED_DATA_ARRAY )( self._update_actor_array )

        self.region_engine = region_viewer
        self.well_engine = well_viewer
        self._perforations: dict[ str, PerforationViewer ] = {}

        self.ctrl.update_viewer.add( self.update_viewer )

        with self:
            vuetify.VCardTitle( "3D View" )
            view = plotter_ui(
                self._pl,
                add_menu_items=self.rendering_menu_extra_items,
            )
            view.menu.style += "; height: 50px; min-width: 50px;"
            view.menu.children[ 0 ].style += "; justify-content: center;"
            self.ctrl.view_update = view.update

    @property
    def plotter( self ) -> pv.Plotter:
        """Getter for plotter."""
        return self._pl

    @property
    def source( self ) -> DeckTree:
        """Getter for source."""
        return self._source

    def rendering_menu_extra_items( self ) -> None:
        """Extend the default pyvista menu with custom button.

        For now, adding a button to show/hide all widgets.
        """
        self.state.change( self.CUT_PLANE )( self._on_clip_visibility_change )
        with vuetify.VRow(
                classes='pa-0 ma-0 align-center fill-height',
                style="flex-wrap: nowrap",
        ):
            vuetify.VDivider( vertical=True, classes="mr-1" )
            with vuetify.VTooltip( location="bottom" ):
                with (
                        vuetify.Template( v_slot_activator=( "{ props }", ) ),
                        html.Div( v_bind=( "props", ) ),
                ):
                    vuetify.VCheckbox(
                        v_model=( self.CUT_PLANE, True ),
                        icon=True,
                        true_icon="mdi-eye",
                        false_icon="mdi-eye-off",
                        dense=True,
                        hide_details=True,
                    )
                html.Span( "Show/Hide widgets" )
            vuetify.VDivider( vertical=True, classes="mr-1" )
            vuetify.VSelect(
                hide_details=True,
                label="Data Array",
                items=( self.DATA_ARRAYS, [] ),
                v_model=( self.SELECTED_DATA_ARRAY, None ),
                min_width="150px",
            )

    def _picking_callback( self, actor: vtkActor | None ) -> None:
        """Actor picking callback.

        Get the data arrays from its mesh.
        """
        if actor is None:
            self.state[ self.DATA_ARRAYS ] = []
        else:
            mesh = actor.mapper.GetInputDataObject( 0, 0 )
            self._point_data_array_names = list( mesh.point_data.keys() )
            self._cell_data_array_names = list( mesh.cell_data.keys() )
            self.state[ self.DATA_ARRAYS ] = self._point_data_array_names + self._cell_data_array_names
            self._picked_actor = actor

        self.state[ self.SELECTED_DATA_ARRAY ] = None

    def _update_actor_array( self, **_: Any ) -> None:
        """Update the picked actor scalar array."""
        array_name = self.state[ self.SELECTED_DATA_ARRAY ]
        if array_name is None or self._picked_actor is None:
            return
        mapper: pv.DataSetMapper = self._picked_actor.mapper
        mesh: vtkUnstructuredGrid = mapper.GetInputDataObject( 0, 0 )

        data = mesh.GetPointData() if array_name in self._point_data_array_names else mesh.GetCellData()
        data.SetActiveScalars( array_name )
        mapper.scalar_range = data.GetArray( array_name ).GetRange()
        mapper.scalar_map_mode = "point" if array_name in self._point_data_array_names else "cell"

        self.plotter.scalar_bar.title = array_name
        self.ctrl.view_update()

    def update_viewer( self, active_block: BaseModel, path: str, show_obj: bool ) -> None:
        """Add from path the dataset given by the user.

        Supported data type is: Vtkwell, Vtkmesh, InternalWell, Perforation.

        object_state  : array used to store path to the data and if we want to show it or not.
        """
        if isinstance( active_block, Vtkmesh ):
            self._update_vtkmesh( show_obj )

        if isinstance( active_block, Vtkwell ):
            self._update_vtkwell( path, show_obj )

        if isinstance( active_block, InternalWell ):
            self._update_internalwell( path, show_obj )

        if isinstance( active_block, Perforation ):
            self._update_perforation( active_block, show_obj, path )

    def _on_clip_visibility_change( self, **kwargs: Any ) -> None:
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
        """Create slider to control in the gui well parameters."""
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
        """Create slider to control in the gui well parameters."""
        self.plotter.clear_slider_widgets()

    def _on_change_tube_size( self, value: float ) -> None:
        self.well_engine.update( value )

    def _get_tube_size( self ) -> float:
        return self.well_engine.get_tube_size()

    def _on_change_perforation_size( self, value: float ) -> None:
        for _, perforation in self._perforations.items():
            perforation.update_perforation_radius( value )

    def _get_perforation_size( self ) -> float | None:
        if len( self._perforations ) <= 0:
            return 5.0

        for _, perforation in self._perforations.items():
            return perforation.get_perforation_size()
        return None

    def _update_internalwell( self, path: str, show: bool ) -> None:
        """Used to control the visibility of the InternalWell.

        This method will create the mesh if it doesn't exist.
        """
        if not show:
            self.plotter.remove_actor( self.well_engine.get_actor( path ) )  # type: ignore
            return

        tube_actor = self.plotter.add_mesh( self.well_engine.get_tube( self.well_engine.get_last_mesh_idx() ) )
        self.well_engine.append_actor( path, tube_actor )

        self.ctrl.view_update()

    def _update_vtkwell( self, path: str, show: bool ) -> None:
        """Used to control the visibility of the Vtkwell.

        This method will create the mesh if it doesn't exist.
        """
        if not show:
            self.plotter.remove_actor( self.well_engine.get_actor( path ) )  # type: ignore
            return

        tube_actor = self.plotter.add_mesh( self.well_engine.get_tube( self.well_engine.get_last_mesh_idx() ) )
        self.well_engine.append_actor( path, tube_actor )

        self.ctrl.view_update()

    def _update_vtkmesh( self, show: bool ) -> None:
        """Used to control the visibility of the Vtkmesh.

        This method will create the mesh if it doesn't exist.

        Additionally, a clip filter will be added.
        """
        if not show:
            self.plotter.clear_plane_widgets()
            self.plotter.remove_actor( self._clip_mesh )  # type: ignore
            return

        self._clip_mesh: vtkActor = self.plotter.add_mesh_clip_plane(
            self.region_engine.input,
            origin=self.region_engine.input.center,
            normal=[ -1, 0, 0 ],
            crinkle=True,
            show_edges=False,
        )
        self._picking_callback( self._clip_mesh )

    def _update_perforation( self, perforation: Perforation, show: bool, path: str ) -> None:
        """Generate VTK dataset from a perforation."""
        if not show:
            if path in self._perforations:
                self._remove_perforation( path )
            return

        distance_from_head = float( perforation.distance_from_head )
        self._add_perforation( distance_from_head, path )

    def _remove_perforation( self, path: str ) -> None:
        """Remove all actor related to the given path and clean the stored perforation."""
        saved_perforation: PerforationViewer = self._perforations[ path ]
        self.plotter.remove_actor( saved_perforation.extracted_cell )  # type: ignore
        self.plotter.remove_actor( saved_perforation.perforation_actor )  # type: ignore
        saved_perforation.reset()

    def _add_perforation( self, distance_from_head: float, path: str ) -> None:
        """Generate perforation dataset based on the distance from the top of a polyline."""
        polyline: pv.PolyData | None = self.well_engine.get_mesh( path )
        if polyline is None:
            return

        point = polyline.points[ 0 ]
        point_offsetted = [
            point[ 0 ],
            point[ 1 ],
            point[ 2 ] - distance_from_head,
        ]

        center = [
            float( point[ 0 ] ),
            float( point[ 1 ] ),
            point[ 2 ] - float( distance_from_head ),
        ]
        sphere = pv.Sphere( radius=5, center=center )

        perforation_actor = self.plotter.add_mesh( sphere )
        saved_perforation = PerforationViewer( sphere, center, 5, perforation_actor )

        cell_id = self.region_engine.input.find_closest_cell( point_offsetted )
        cell = self.region_engine.input.extract_cells( [ cell_id ] )
        cell_actor = self.plotter.add_mesh( cell )
        saved_perforation.add_extracted_cell( cell_actor )

        self._perforations[ path ] = saved_perforation
