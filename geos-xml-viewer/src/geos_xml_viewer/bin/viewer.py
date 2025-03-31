# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner

import argparse
import time
from datetime import timedelta

import colorcet as cc  # type: ignore[import-untyped]
import pyvista as pv
import vtkmodules.all as vtk
from geos_xml_viewer.filters.geosDeckReader import GeosDeckReader
from geos_xml_viewer.geos.models.schema import Problem
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.parsers.config import ParserConfig


def parsing() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser( description="Extract Internal wells into VTK files" )

    parser.add_argument(
        "-xp",
        "--xmlFilepath",
        type=str,
        default="",
        help="path to xml file.",
        required=True,
    )
    parser.add_argument( "-vtpc", "--vtpcFilepath", type=str, default="", help="path to .vtpc file." )
    parser.add_argument(
        "--showmesh",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show mesh.",
    )
    parser.add_argument(
        "--showsurfaces",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show surfaces.",
    )
    parser.add_argument(
        "--showboxes",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show boxes.",
    )
    parser.add_argument(
        "--showwells",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show wells.",
    )
    parser.add_argument(
        "--showperforations",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show well perforations.",
    )
    parser.add_argument(
        "--clipToBoxes",
        default=True,
        action=argparse.BooleanOptionalAction,
        help="show only mesh elements inside boxes from xml file.",
    )
    parser.add_argument(
        "--Zamplification",
        type=float,
        default=1,
        action="store",
        help="Z amplification factor.",
    )
    parser.add_argument(
        "--attributeName",
        type=str,
        default="attribute",
        help="Attribute name.",
        required=False,
    )

    return parser


class WellViewer:

    def __init__( self, size: float, amplification: float ) -> None:
        self.input: list[ pv.PolyData ] = []
        self.tubes: list[ pv.PolyData ] = []
        self.size: float = size
        self.amplification: float = amplification
        self.STARTING_VALUE: float = 5.0

    def __call__( self, value: float ) -> None:
        self.update( value )

    def add_mesh( self, mesh: pv.PolyData ) -> None:
        self.input.append( mesh )  # type: ignore
        radius = self.size * ( self.STARTING_VALUE / 100 )
        self.tubes.append(
            mesh.tube( radius=radius, n_sides=50 )  # .scale([1.0, 1.0, self.amplification], inplace=True)
        )  # type: ignore

    def update( self, value: float ) -> None:
        radius = self.size * ( value / 100 )
        for idx, m in enumerate( self.input ):
            self.tubes[ idx ].copy_from(
                m.tube( radius=radius, n_sides=50 )  # .scale([1.0, 1.0, self.amplification], inplace=True)
            )


class PerforationViewer:

    def __init__( self, size: float ) -> None:
        self.input: list[ pv.PointSet ] = []
        self.spheres: list[ pv.Sphere ] = []
        self.size: float = size
        self.STARTING_VALUE: float = 5.0

    def __call__( self, value: float ) -> None:
        self.update( value )

    def add_mesh( self, mesh: pv.PointSet ) -> None:
        self.input.append( mesh )  # type: ignore
        radius: float = self.size * ( self.STARTING_VALUE / 100 )
        self.spheres.append( pv.Sphere( center=mesh.center, radius=radius ) )

    def update( self, value: float ) -> None:
        radius: float = self.size * ( value / 100 )
        for idx, m in enumerate( self.input ):
            self.spheres[ idx ].copy_from( pv.Sphere( center=m.center, radius=radius ) )


class RegionViewer:

    def __init__( self ) -> None:
        self.input: pv.UnstructuredGrid = pv.UnstructuredGrid()
        self.mesh: pv.UnstructuredGrid

    def __call__( self, normal: tuple[ float ], origin: tuple[ float ] ) -> None:
        self.update_clip( normal, origin )

    def add_mesh( self, mesh: pv.UnstructuredGrid ) -> None:
        self.input.merge( mesh, inplace=True )  # type: ignore
        self.mesh = self.input.copy()  # type: ignore

    def update_clip( self, normal: tuple[ float ], origin: tuple[ float ] ) -> None:
        self.mesh.copy_from( self.input.clip( normal=normal, origin=origin, crinkle=True ) )  # type: ignore


class SetVisibilityCallback:
    """Helper callback to keep a reference to the actor being modified."""

    def __init__( self, actor: vtk.vtkActor ) -> None:
        self.actor = actor

    def __call__( self, state: bool ) -> None:
        self.actor.SetVisibility( state )


class SetVisibilitiesCallback:
    """Helper callback to keep a reference to the actor being modified."""

    def __init__( self ) -> None:
        self.actors: list[ vtk.vtkActor ] = []

    def add_actor( self, actor: vtk.vtkActor ) -> None:
        self.actors.append( actor )

    def update_visibility( self, state: bool ) -> None:
        for actor in self.actors:
            actor.SetVisibility( state )

    def __call__( self, state: bool ) -> None:
        for actor in self.actors:
            actor.SetVisibility( state )


def find_surfaces( xmlFile: str ) -> list[ str ]:
    """Find all surfaces in xml file."""
    config = ParserConfig(
        base_url=None,
        load_dtd=False,
        process_xinclude=False,
        fail_on_unknown_properties=True,
        fail_on_unknown_attributes=True,
        fail_on_converter_warnings=True,
    )

    parser = XmlParser( context=XmlContext() )  # , config=config)
    problem = parser.parse( xmlFile, Problem )

    used: list[ str ] = []
    for f in problem.field_specifications:
        for f2 in f.field_specification:
            names = f2.set_names
            names = names.replace( "{", "[" ).replace( "}", "]" )
            e = names.strip( "][" ).split( "," )
            e = [ element.strip() for element in e ]
            if "all" in e:
                e.remove( "all" )
            if e:
                used += e

    return used


def main( args: argparse.Namespace ) -> None:
    start_time = time.monotonic()
    pdsc: vtk.vtkPartitionedDataSetCollection

    if args.vtpcFilepath != "":
        reader = vtk.vtkXMLPartitionedDataSetCollectionReader()
        reader.SetFileName( args.vtpcFilepath )
        reader.Update()
        pdsc = reader.GetOutput()
    else:
        reader = GeosDeckReader()
        reader.SetFileName( args.xmlFilepath )
        reader.SetAttributeName( args.attributeName )
        reader.Update()
        pdsc = reader.GetOutputDataObject( 0 )

    read_time = time.monotonic()
    print( "time elapsed reading files: ", timedelta( seconds=read_time - start_time ) )

    assembly: vtk.vtkDataAssembly = pdsc.GetDataAssembly()
    root_name: str = assembly.GetNodeName( assembly.GetRootNode() )
    surfaces_used = find_surfaces( args.xmlFilepath )

    print( "surfaces used as boundary conditionsp", surfaces_used )

    global_bounds = [ 0, 0, 0, 0, 0, 0 ]

    plotter = pv.Plotter( shape=( 2, 2 ), border=True )
    ## 1. Region subview
    region_engine = RegionViewer()
    if args.showmesh:
        start = time.monotonic()
        plotter.subplot( 0, 0 )

        mesh = assembly.GetFirstNodeByPath( "//" + root_name + "/Mesh" )

        for sub_node in assembly.GetChildNodes( mesh, False ):
            datasets = assembly.GetDataSetIndices( sub_node, False )
            for d in datasets:
                dataset = pdsc.GetPartitionedDataSet( d )
                grid = pv.wrap( dataset.GetPartition( 0 ) )
                # grid.scale([1.0, 1.0, args.Zamplification], inplace=True)
                region_engine.add_mesh( grid )

        plotter.add_mesh_clip_plane(
            region_engine.mesh,
            origin=region_engine.mesh.center,
            normal=[ -1, 0, 0 ],
            crinkle=True,
            show_edges=True,
            cmap="glasbey_bw",
            # cmap=cmap,
            # clim=clim,
            # categories=True,
            scalars=args.attributeName,
            # n_colors=n,
        )
        stop = time.monotonic()
        global_bounds = region_engine.mesh.bounds
        plotter.add_text( "Mesh", font_size=24 )
        plotter.background_color = "white"
        plotter.show_bounds(
            grid="back",
            location="outer",
            ticks="both",
            n_xlabels=2,
            n_ylabels=2,
            n_zlabels=2,
            ztitle="Elevation",
            use_3d_text=True,
            minor_ticks=True,
        )
        print( "region subplot preparation time: ", timedelta( seconds=stop - start ) )

    # 2. Surfaces subview
    if args.showsurfaces:
        start = time.monotonic()
        plotter.subplot( 0, 1 )

        surfaces = assembly.GetFirstNodeByPath( "//" + root_name + "/Surfaces" )

        if surfaces > 0:
            Startpos = 12
            size = 35
            for i, sub_node in enumerate( assembly.GetChildNodes( surfaces, False ) ):
                datasets = assembly.GetDataSetIndices( sub_node, False )
                for d in datasets:
                    dataset = pdsc.GetPartitionedDataSet( d )
                    label = assembly.GetAttributeOrDefault( sub_node, "label", "no label" )
                    matches = [ "Surface" + s for s in surfaces_used ]
                    if any( x in label for x in matches ):
                        actor = plotter.add_mesh(
                            pv.wrap(
                                dataset.GetPartition( 0 ) ),  # .scale([1.0, 1.0, args.Zamplification], inplace=True),
                            show_edges=True,
                            color=cc.cm.glasbey_bw( i ),  # type: ignore
                        )
                        callback = SetVisibilityCallback( actor )
                        plotter.add_checkbox_button_widget(
                            callback,
                            value=True,
                            position=( Startpos, 10.0 ),
                            size=size,
                            border_size=1,
                            color_on=cc.cm.glasbey_bw( i ),
                            color_off=cc.cm.glasbey_bw( i ),
                            background_color="grey",
                        )
                        Startpos = Startpos + size + ( size // 10 )
                    else:
                        actor = plotter.add_mesh(
                            pv.wrap(
                                dataset.GetPartition( 0 ) ),  # .scale([1.0, 1.0, args.Zamplification], inplace=True),
                            show_edges=True,
                            color=cc.cm.glasbey_bw( i ),  # type: ignore
                            opacity=0.2,
                        )
                        callback = SetVisibilityCallback( actor )
                        plotter.add_checkbox_button_widget(
                            callback,
                            value=True,
                            position=( Startpos, 10.0 ),
                            size=size,
                            border_size=1,
                            color_on=cc.cm.glasbey_bw( i ),
                            color_off=cc.cm.glasbey_bw( i ),
                            background_color="grey",
                        )
                        Startpos = Startpos + size + ( size // 10 )

        plotter.add_text( "Surfaces", font_size=24 )
        plotter.show_bounds(
            bounds=global_bounds,
            grid="back",
            location="outer",
            ticks="both",
            n_xlabels=2,
            n_ylabels=2,
            n_zlabels=2,
            ztitle="Elevation",
            minor_ticks=True,
        )

        stop = time.monotonic()

        print( "surfaces subplot preparation time: ", timedelta( seconds=stop - start ) )

    # 3. Well subview
    if args.showwells:
        start = time.monotonic()
        plotter.subplot( 1, 0 )

        bounds = global_bounds
        xsize = bounds[ 1 ] - bounds[ 0 ]
        ysize = bounds[ 3 ] - bounds[ 2 ]

        maxsize = max( xsize, ysize )

        well_engine = WellViewer( maxsize, args.Zamplification )
        perfo_engine = PerforationViewer( maxsize )

        wells = assembly.GetFirstNodeByPath( "//" + root_name + "/Wells" )
        if wells > 0:
            for well in assembly.GetChildNodes( wells, False ):
                sub_nodes = assembly.GetChildNodes( well, False )
                for sub_node in sub_nodes:
                    if assembly.GetNodeName( sub_node ) == "Mesh":
                        datasets = assembly.GetDataSetIndices( sub_node, False )
                        for d in datasets:
                            dataset = pdsc.GetPartitionedDataSet( d )
                            if dataset.GetPartition( 0 ) is not None:
                                well_engine.add_mesh( pv.wrap( dataset.GetPartition(
                                    0 ) ) )  # .scale([1.0, 1.0, args.Zamplification], inplace=True)) #
                    elif assembly.GetNodeName( sub_node ) == "Perforations":
                        for i, perfos in enumerate( assembly.GetChildNodes( sub_node, False ) ):
                            datasets = assembly.GetDataSetIndices( perfos, False )
                            for d in datasets:
                                dataset = pdsc.GetPartitionedDataSet( d )
                                if dataset.GetPartition( 0 ) is not None:
                                    pointset = pv.wrap(
                                        dataset.GetPartition( 0 )
                                    )  # .cast_to_pointset().scale([1.0, 1.0, args.Zamplification], inplace=True) #
                                    perfo_engine.add_mesh( pointset )

            plotter.add_slider_widget( callback=well_engine.update, rng=[ 0.1, 10 ], title="Wells Radius" )

            well_visibilty: SetVisibilitiesCallback = SetVisibilitiesCallback()
            for m in well_engine.tubes:
                actor = plotter.add_mesh( m, color=True, show_edges=False )
                well_visibilty.add_actor( actor )

            size = 35
            plotter.add_checkbox_button_widget(
                callback=well_visibilty.update_visibility,
                value=True,
                position=( 50, 10.0 ),
                size=size,
                border_size=1,
            )

            my_cell_locator = vtk.vtkStaticCellLocator()
            my_cell_locator.SetDataSet( region_engine.input )
            my_cell_locator.AutomaticOn()
            my_cell_locator.SetNumberOfCellsPerNode( 20 )

            my_cell_locator.BuildLocator()

            if len( perfo_engine.spheres ) > 0:
                Startpos = 12
                callback: SetVisibilitiesCallback = SetVisibilitiesCallback()
                for m in perfo_engine.spheres:
                    actor = plotter.add_mesh( m, color=True, show_edges=False )
                    callback.add_actor( actor )
                    # render cell containing perforation
                    cell_id = my_cell_locator.FindCell( m.center )
                    if cell_id != -1:
                        id_list = vtk.vtkIdList()
                        id_list.InsertNextId( cell_id )
                        extract = vtk.vtkExtractCells()
                        extract.SetInputDataObject( region_engine.input )
                        extract.SetCellList( id_list )
                        extract.Update()
                        cell = extract.GetOutputDataObject( 0 )

                        # cell = region_engine.input.extract_cells(cell_id)  # type: ignore
                        plotter.add_mesh(
                            pv.wrap( cell ).scale( [ 1.0, 1.0, args.Zamplification ], inplace=True ),
                            opacity=0.5,
                            color="red",
                            smooth_shading=True,
                            show_edges=True,
                        )

                plotter.add_checkbox_button_widget(
                    callback=callback.update_visibility,
                    value=True,
                    position=( Startpos, 10.0 ),
                    size=size,
                    border_size=1,
                )

                plotter.add_slider_widget(
                    callback=perfo_engine.update,
                    starting_value=perfo_engine.STARTING_VALUE,
                    rng=[ 0.1, 10 ],
                    title=" Perforations\n Radius",
                    pointb=( 0.08, 0.9 ),
                    pointa=( 0.08, 0.03 ),
                    # title_height=0.03
                )

        plotter.add_text( "Wells", font_size=24 )
        plotter.show_bounds(
            bounds=global_bounds,
            grid="back",
            location="outer",
            ticks="both",
            n_xlabels=2,
            n_ylabels=2,
            n_zlabels=2,
            ztitle="Elevation",
            minor_ticks=True,
        )
        stop = time.monotonic()
        print( "wells subplot preparation time: ", timedelta( seconds=stop - start ) )

    ## 5. Box subview
    if args.showboxes:
        start = time.monotonic()
        plotter.subplot( 1, 1 )

        boxes = assembly.GetFirstNodeByPath( "//" + root_name + "/Boxes" )

        if boxes > 0:
            for i, sub_node in enumerate( assembly.GetChildNodes( boxes, False ) ):
                datasets = assembly.GetDataSetIndices( sub_node, False )
                for d in datasets:
                    dataset = pdsc.GetPartitionedDataSet( d )
                    plotter.add_mesh(
                        pv.wrap( dataset.GetPartition( 0 ) ),  # .scale([1.0, 1.0, args.Zamplification], inplace=True),
                        color="red",
                        show_edges=True,  # type: ignore
                    )

        plotter.add_text( "Boxes", font_size=24 )
        plotter.show_bounds(
            bounds=global_bounds,
            grid="back",
            location="outer",
            ticks="both",
            n_xlabels=2,
            n_ylabels=2,
            n_zlabels=2,
            ztitle="Elevation",
            minor_ticks=True,
        )

        stop = time.monotonic()
        print( "boxes subplot preparation time: ", timedelta( seconds=stop - start ) )

    show_time = time.monotonic()
    print( "time elapsed showing data: ", timedelta( seconds=show_time - read_time ) )

    plotter.link_views( 0 )  # link all the views
    plotter.show()


def run() -> None:
    parser = parsing()
    args, unknown_args = parser.parse_known_args()
    main( args )


if __name__ == "__main__":
    run()

# def get_data_element_index(
#     assembly: vtk.vtkDataAssembly, name: str
# ) -> list[vtk.vtkIdType] | None :
#     node_id = assembly.FindFirstNodeWithName(name)
#     if node_id == -1:
#         return None
#     ds_indices = assembly.GetDataSetIndices(node_id)

#     return ds_indices

# class MyCustomRoutine:
#     def __init__(self, mesh):
#         self.input = mesh
#         self.mesh = mesh.copy()  # Expected PyVista mesh type

#         # default parameters
#         self.kwargs = {}

#         self._last_normal = "z"
#         self._last_origin = self.mesh.center

#     def __call__(self, param, value):
#         self.kwargs[param] = value
#         self.update()

#     def update(self) -> None:
#         self.update_clip(self._last_normal, self._last_origin)
#         return

#     def update_clip(self, normal, origin):
#         self.mesh.copy_from(self.input.clip(normal=normal, origin=origin, crinkle=True))
#         self._last_normal = normal
#         self._last_origin = origin

# def distinct_colors(
#     start: int = 0, stop: int = 20, sat_values=[8 / 10]
# ):  # -> np.NDArray[np.float64]
#     """Returns an array of distinct RGB colors, from an infinite sequence of colors"""
#     if stop <= start:  # empty interval; return empty array
#         return np.array([], dtype=np.float64)
#     # sat_values =         # other tones could be added
#     val_values = [8 / 10, 5 / 10]  # other tones could be added
#     colors_per_hue_value = len(sat_values) * len(val_values)
#     # Get the start and stop indices within the hue value stream that are needed
#     # to achieve the requested range
#     hstart = start // colors_per_hue_value
#     hstop = (stop + colors_per_hue_value - 1) // colors_per_hue_value
#     # Zero will cause a singularity in the caluculation, so we will add the zero
#     # afterwards
#     prepend_zero = hstart == 0

#     # Sequence (if hstart=1): 1,2,...,hstop-1
#     i = np.arange(1 if prepend_zero else hstart, hstop)
#     # The following yields (if hstart is 1): 1/2,  1/4, 3/4,  1/8, 3/8, 5/8, 7/8,
#     # 1/16, 3/16, ...
#     hue_values = (2 * i + 1) / np.power(2, np.floor(np.log2(i * 2))) - 1

#     if prepend_zero:
#         hue_values = np.concatenate(([0], hue_values))

#     # Make all combinations of h, s and v values, as if done by a nested loop
#     # in that order
#     hsv = (
#         np.array(np.meshgrid(hue_values, sat_values, val_values, indexing="ij"))
#         .reshape((3, -1))
#         .transpose()
#     )

#     # Select the requested range (only the necessary values were computed but we
#     # need to adjust the indices since start & stop are not necessarily multiples
#     # of colors_per_hue_value)
#     hsv = hsv[
#         start % colors_per_hue_value : start % colors_per_hue_value + stop - start
#     ]
#     # Use the matplotlib vectorized function to convert hsv to rgb
#     return mplt.colors.hsv_to_rgb(hsv)

# def mainOLD(args: argparse.Namespace) -> None:

# start_time = time.monotonic()
# pdsc: vtk.vtkPartitionedDataSetCollection

# if(args.vtpcFilepath != ""):
#     reader = vtk.vtkXMLPartitionedDataSetCollectionReader()
#     reader.SetFileName(args.vtpcFilepath)
#     reader.Update()
#     pdsc: vtk.vtkPartitionedDataSetCollection = reader.GetOutput()

# else:
#     reader = GeosDeckReader()
#     reader.SetFileName(args.xmlFilepath)
#     reader.SetAttributeName(args.attributeName)
#     reader.Update()
#     pdsc: vtk.vtkPartitionedDataSetCollection = reader.GetOutputDataObject(0)

# config = ParserConfig(
#     base_url=None,
#     load_dtd=False,
#     process_xinclude=False,
#     fail_on_unknown_properties=True,
#     fail_on_unknown_attributes=True,
#     fail_on_converter_warnings=True,
# )

# parser = XmlParser(context=XmlContext()) #, config=config)
# problem = parser.parse(args.xmlFilepath, Problem)

# for e in problem.events:
#     # for pe in e.periodic_event:
#     print(type(e.max_time), e.max_time)

# used = []
# for f in problem.field_specifications:
#     for f2 in f.field_specification:
#         names = f2.set_names
#         names = names.replace('{','[').replace('}',']')
#         # print(names)
#         # print(ast.literal_eval(names))
#         # json.loads(names)
#         e = [i.split('}')[0].strip() for i in f2.set_names.split('{')[1:]]
#         if 'all' in e: e.remove('all')
#         if e:
#             print(e)
#             used += e

# print(used)

# read_time = time.monotonic()
# print("time elapsed reading files: ", timedelta(seconds=read_time - start_time))

# plotter = pv.Plotter(shape=(2, 2), border=True)
# plotter.background_color = "white"

# engine = RegionViewer()

# n = pdsc.GetNumberOfPartitionedDataSets()
# dark_color_map = ListedColormap(distinct_colors(stop=n))
# light_color_map = ListedColormap(distinct_colors(stop=n, sat_values=[3/10]))

# c = 0.3
# test = [
#     mplt.colors.rgb_to_hsv(mplt.colors.to_rgb(x))
#     for x in cc.cm.glasbey_bw(np.linspace(0.0, 1.0, n))
# ]
# pastel_glasbey = colors = (1.0 - c) * cc.cm.glasbey_bw(
#     np.linspace(0.0, 1.0, n)
# ) + c * np.ones((n, 4))
# colors = np.stack(test)
# print(colors)
# pastel_glasbey = mplt.colors.rgb_to_hsv(test)
# colors[:,1]+=0.1
# colors[:,1]-=0.1
# print(colors)
# pastel_glasbey = mplt.colors.hsv_to_rgb(colors)
# pastel_glasbey = [mplt.colors.to_rgba(mplt.colors.hsv_to_rgb(x)) for x in colors]
# print(pastel_glasbey)
# print(type(cc.cm.glasbey_bw))

# print(n)
# color_map = pv.LookupTable('glasbey_bw', n_values=n)

# data_assembly = pdsc.GetDataAssembly()
# regions = assembly.SelectNodes("//box_hybrid_fault_0-01/Region4")
# print(regions)
# regions = assembly.SelectNodes('//Mesh/Region4')
# print(regions)

# perfos = []

# Startpos = 12
# size = 35
# for i in range(pdsc.GetNumberOfPartitionedDataSets()):
#     psm = pdsc.GetPartitionedDataSet(i)
#     name = pdsc.GetMetaData(i).Get(vtk.vtkCompositeDataSet.NAME())
#     if name.startswith("Region") and args.showmesh:
#         stime = time.monotonic()
#         engine.add_mesh(pv.wrap(psm.GetPartition(0)))  # type: ignore
#         etime = time.monotonic()
#         print("time building region view: ", timedelta(seconds=etime - stime))
#     elif name.startswith("Surface") and args.showsurfaces:
#         stime = time.monotonic()
#         # "Surface"+used[0] in name:
#         # matches = ["Surface" + s for s in used]
#         # if any(x in name for x in matches):
#         plotter.subplot(0, 1)
#         actor = plotter.add_mesh(
#             pv.wrap(psm.GetPartition(0)),
#             show_edges=True,
#             color=cc.cm.glasbey_bw(i),  # type: ignore
#         )
#         callback = SetVisibilityCallback(actor)
#         plotter.add_checkbox_button_widget(
#             callback,
#             value=True,
#             position=(Startpos, 10.0),
#             size=size,
#             border_size=1,
#             color_on=cc.cm.glasbey_bw(i),
#             color_off=cc.cm.glasbey_bw(i),
#             background_color="grey",
#         )
#         Startpos = Startpos + size + (size // 10)
# else:
#     plotter.subplot(0, 1)
#     actor = plotter.add_mesh(
#         pv.wrap(psm.GetPartition(0)),
#         show_edges=True,
#         color=cc.cm.glasbey_bw(i),  # type: ignore
#         opacity=0.2
#     )
#     callback = SetVisibilityCallback(actor)
#     plotter.add_checkbox_button_widget(
#         callback,
#         value=True,
#         position=(Startpos, 10.0),
#         size=size,
#         border_size=1,
#         color_on=cc.cm.glasbey_bw(i),
#         color_off=cc.cm.glasbey_bw(i),
#         background_color="grey",
#     )
#     Startpos = Startpos + size + (size // 10)
#     etime = time.monotonic()
#     print("time building region view: ", timedelta(seconds=etime - stime))
# elif name.startswith("Well") and args.showwells:
#     plotter.subplot(1, 0)
#     plotter.add_mesh(
#         pv.wrap(psm.GetPartition(0)).tube(radius=0.025, n_sides=50),  # type: ignore
#         color=True,
#         show_edges=False,
#     )
# elif name.startswith("Perforation") and args.showperforations:
#     plotter.subplot(1, 0)
#     plotter.add_mesh(pv.wrap(psm.GetPartition(0)), color=True, show_edges=False)  # type: ignore
#     perfos.append(pv.wrap(psm.GetPartition(0)))  # type: ignore
# elif name.startswith("Box") and args.showboxes:
#     plotter.subplot(1, 1)
#     plotter.add_mesh(
#         pv.wrap(psm.GetPartition(0)),
#         color="red",
#         show_edges=True,  # type: ignore
# )  # , style="wireframe")

# extracted = engine.input.clip_box(  # type: ignore
#     bounds=pv.wrap(psm.GetPartition(0)).bounds,
#     invert=False,
#     crinkle=True,  # type: ignore
# )

# recuperer le tableau extracted['cell_ids']
# dans le maillage d'entree faire +10 a l'attribut de ces cellules

# exploded = extracted.explode(0.1)
# # plotter.add_mesh(b.mesh, opacity=0.5, color="red")
# plotter.add_mesh(
#     exploded,
#     show_edges=True,
#     smooth_shading=True,
#     # color="green",
#     cmap="glasbey_bw",
#     opacity=1.00,
# )

# plotter.subplot(0, 0)
# plotter.add_text("Mesh", font_size=24)
# # plotter.set_scale(zscale=args.Zamplification)
# plotter.show_axes()

# plotter.add_mesh_clip_plane(
#     engine.mesh,
#     origin=engine.mesh.center,
#     normal=[-1, 0, 0],
#     crinkle=True,
#     show_edges=True,
#     cmap="glasbey_bw",
#     # cmap=cmap,
#     # clim=clim,
#     # categories=True,
#     scalars=args.attributeName,
#     # n_colors=n,
# )

# plotter.subplot(1, 0)
# plotter.add_text("Wells", font_size=24)
# # plotter.set_scale(zscale=args.Zamplification)
# plotter.add_mesh(engine.input, opacity=0.1)
# plotter.show_bounds(
#     grid="back",
#     location="outer",
#     ticks="both",
#     n_xlabels=2,
#     n_ylabels=2,
#     n_zlabels=2,
#     ztitle="Elevation",
# )
# plotter.show_axes()

# my_cell_locator = vtk.vtkCellLocator()
# my_cell_locator.SetDataSet(engine.input)

# for p in perfos:
#     cell_id = my_cell_locator.FindCell(p.points[0])
#     cell = engine.input.extract_cells(cell_id)  # type: ignore
#     plotter.add_mesh(
#         cell, opacity=0.5, color="red", smooth_shading=True, show_edges=True
#     )

# plotter.subplot(1, 1)
# plotter.add_text("Boxes", font_size=24)
# # plotter.set_scale(zscale=args.Zamplification)
# plotter.add_mesh(engine.input, opacity=0.1)
# plotter.show_axes()

# plotter.link_views()  # link all the views

# plotter.show_grid()

# show_time = time.monotonic()
# print("time elapsed showing data: ", timedelta(seconds=show_time - read_time))

# plotter.show(auto_close=False)
# image = plotter.screenshot('test.png', return_img=True)
# plotter.close()
