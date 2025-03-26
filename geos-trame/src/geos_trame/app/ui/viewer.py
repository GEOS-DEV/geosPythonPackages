# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
import pyvista as pv
from pyvista.trame.ui import plotter_ui
from trame.widgets import html, vtk
from trame.widgets import vuetify3 as vuetify

from geos_trame.schema_generated.schema_mod import InternalWell, Vtkmesh

# def setup_viewer():
#     pl = pv.Plotter()

#     p.reset_camera()

#     return p.ren_vin

# prevents launching an external window with rendering
pv.OFF_SCREEN = True


class RegionViewer:
    def __init__(self) -> None:
        self.input: pv.UnstructuredGrid = pv.UnstructuredGrid()
        self.mesh: pv.UnstructuredGrid

    def __call__(self, normal: tuple[float], origin: tuple[float]) -> None:
        self.update_clip(normal, origin)

    def add_mesh(self, mesh: pv.UnstructuredGrid) -> None:
        self.input = mesh  # type: ignore
        self.mesh = self.input.copy()  # type: ignore

    def update_clip(self, normal: tuple[float], origin: tuple[float]) -> None:
        self.mesh.copy_from(self.input.clip(normal=normal, origin=origin, crinkle=True))  # type: ignore


# class WellViewer:
#     def __init__(self, size: float, amplification: float) -> None:
#         self.input: list[pv.PolyData] = []
#         self.tubes: list[pv.PolyData] = []
#         self.size: float = size
#         self.amplification: float = amplification
#         self.STARTING_VALUE: float = 5.0

#     def __call__(self, value: float) -> None:
#         self.update(value)

#     def add_mesh(self, mesh: pv.PolyData) -> None:
#         self.input.append(mesh)  # type: ignore
#         radius = self.size * (self.STARTING_VALUE / 100)
#         self.tubes.append(
#             mesh.tube(
#                 radius=radius, n_sides=50
#             )  # .scale([1.0, 1.0, self.amplification], inplace=True)
#         )  # type: ignore

#     def update(self, value: float) -> None:
#         radius = self.size * (value / 100)
#         for idx, m in enumerate(self.input):
#             self.tubes[idx].copy_from(
#                 m.tube(
#                     radius=radius, n_sides=50
#                 )  # .scale([1.0, 1.0, self.amplification], inplace=True)
#             )


# class GeosPlotterBase:
#     def add_region(self, mesh: pv.UnstructuredGrid, name: str, zscale: int = 1) -> None:
#         super().add_mesh(mesh, name=name, **kwargs)

#     def add_well(self, mesh: pv.PolyData, name: str, zscale: int = 1) -> None:
#         # build tube
#         super().add_mesh()

#     def update_clip(self, normal: tuple[float], origin: tuple[float]) -> None:
#         pass
#         # for m in super().meshes:
#         #     m.


# class GeosPlotter(GeosPlotterBase, pv.Plotter):
#     pass


### VIEWER


def button(click, icon, tooltip):  # numpydoc ignore=PR01
    """Create a vuetify button."""
    with vuetify.VTooltip(bottom=True):
        with vuetify.Template(v_slot_activator="{ on, attrs }"):
            with vuetify.VBtn(icon=True, v_bind="attrs", v_on="on", click=click):
                vuetify.VIcon(icon)
        html.Span(tooltip)


def checkbox(model, icons, tooltip):  # numpydoc ignore=PR01
    """Create a vuetify checkbox."""
    with vuetify.VTooltip(bottom=True):
        with vuetify.Template(v_slot_activator="{ on, attrs }"):
            with html.Div(v_on="on", v_bind="attrs"):
                vuetify.VCheckbox(
                    v_model=model,
                    on_icon=icons[0],
                    off_icon=icons[1],
                    dense=True,
                    hide_details=True,
                    classes="my-0 py-0 ml-1",
                )
        html.Span(tooltip)


def spin_edit(model, tooltip):  # numpydoc ignore=PR01
    """Create a vuetify slider."""
    with vuetify.VTooltip(bottom=True):
        with vuetify.Template(v_slot_activator="{ on, attrs }"):
            with html.Div(v_on="on", v_bind="attrs"):
                vuetify.VTextField(
                    v_model=model,
                    dense=True,
                    hide_details=True,
                    classes="my-0 py-0 ml-1",
                    type="number",
                    counter="3",
                    # counter_value=
                )
        html.Span(tooltip)


class DeckViewer(vuetify.VCard):
    def __init__(self, source, **kwargs):
        super().__init__(**kwargs)

        self._source = source
        self._pl = pv.Plotter()

        self.CUT_PLANE = f"_cut_plane_visibility"
        self.ZAMPLIFICATION = f"_z_amplification"
        self.server.state[self.CUT_PLANE] = False
        self.server.state[self.ZAMPLIFICATION] = 1

        self.state.change("obj_path")(self.add_to_3dviewer)

        self.region_engine = RegionViewer()

        # self.well_engine = WellViewer()

        with self:
            vuetify.VCardTitle("3D View")
            view = plotter_ui(
                self._pl,
                add_menu_items=self.rendering_menu_extra_items,
                style="position: absolute;",
            )
            self.ctrl.view_update = view.update

    @property
    def plotter(self):
        return self._pl

    @property
    def source(self):
        return self._source

    def rendering_menu_extra_items(self):
        self.state.change(self.CUT_PLANE)(self.on_cut_plane_visiblity_change)
        vuetify.VDivider(vertical=True, classes="mr-3")
        # html.Span('foo', classes="mr-3")
        # spin_edit(
        #     model=(self.ZAMPLIFICATION, 3),
        #     tooltip=f"Z Amplification",
        # )

        # tooltip=f"Toggle cut plane visibility ({{{{ {self.CUT_PLANE} ? 'on' : 'off' }}}})",
        # with vuetify.VBtn(
        #     icon=True,
        #                         # v_on="on",
        #                         # v_bind="attrs",
        #                         # click="(event) => {event.stopPropagation(); event.preventDefault();}",
        # ):
        #     vuetify.VIcon(
        #                 "mdi-plus-circle",
        #                     )

    def on_cut_plane_visiblity_change(self, **kwargs):
        pass
        """Toggle cut plane visibility for all actors.

        Parameters
        ----------
        **kwargs : dict, optional
            Unused keyword arguments.

        """
        # value = kwargs[self.CUT_PLANE]
        # for renderer in self.plotter.renderers:
        #     for actor in renderer.actors.values():
        #         if isinstance(actor, pyvista.Actor):
        #             actor.prop.show_edges = value
        # self.update()

    def add_to_3dviewer(self, obj_path, **kwargs):
        path = obj_path

        if path == "":
            return

        active_block = self.source.decode(path)

        # def update_tree(entry, search_id):

        #     print("entry :", entry)
        #     print("search_id : ", search_id)

        #     print(entry["id"])
        #     if entry["id"] == search_id:
        #         entry["drawn"] = True
        #         return

        #     for child in entry["children"]:
        #         update_tree(child, search_id)
        #     for child in entry["hidden_children"]:
        #         update_tree(child, search_id)

        # print(self.server.state.deck_tree[0])
        # update_tree(self.server.state.deck_tree, path)
        # self.server.state.dirty("deck_tree")

        if isinstance(active_block, Vtkmesh):
            self.region_engine.add_mesh(
                pv.read(self.source.get_abs_path(active_block.file))
            )
            self.plotter.add_mesh_clip_plane(
                self.region_engine.mesh,
                origin=self.region_engine.mesh.center,
                normal=[-1, 0, 0],
                crinkle=True,
                show_edges=False,
                cmap="glasbey_bw",
                # cmap=cmap,
                # clim=clim,
                # categories=True,
                scalars="attribute",
                # n_colors=n,
            )

            self.server.controller.view_update()

        if isinstance(active_block, InternalWell):
            s = active_block.polyline_node_coords
            points = np.array(literal_eval(s.translate(tr)), dtype=np.float64)
            tip = points[0]

            s = active_block.polyline_segment_conn
            lines = np.array(literal_eval(s.translate(tr)), dtype=np.int64)
            v_indices = np.unique(lines.flatten())

            r = literal_eval(active_block.radius.translate(tr))
            radius = np.repeat(r, points.shape[0])

            vpoints = vtk.vtkPoints()
            vpoints.SetNumberOfPoints(points.shape[0])
            vpoints.SetData(numpy_to_vtk(points))

            polyLine = vtk.vtkPolyLine()
            polyLine.GetPointIds().SetNumberOfIds(len(v_indices))

            for iline, vidx in enumerate(v_indices):
                polyLine.GetPointIds().SetId(iline, vidx)

            cells = vtk.vtkCellArray()
            cells.InsertNextCell(polyLine)

            vradius = vtk.vtkDoubleArray()
            vradius.SetName("radius")
            vradius.SetNumberOfComponents(1)
            vradius.SetNumberOfTuples(points.shape[0])
            vradius.SetVoidArray(numpy_to_vtk(radius), points.shape[0], 1)

            polyData = vtk.vtkPolyData()
            polyData.SetPoints(vpoints)
            polyData.SetLines(cells)
            polyData.GetPointData().AddArray(vradius)
            polyData.GetPointData().SetActiveScalars("radius")

            bounds = self.region_engine.mesh.bounds

            xsize = bounds[1] - bounds[0]
            ysize = bounds[3] - bounds[2]

            maxsize = max(xsize, ysize)
            self.well_engine = WellViewer(maxsize, 1)

            self.well_engine.add_mesh(pv.wrap(polyData))

            for m in self.well_engine.tubes:
                actor = self.plotter.add_mesh(m, color=True, show_edges=False)

            self.server.controller.view_update()

        # if isinstance(active_block, Perforation):
