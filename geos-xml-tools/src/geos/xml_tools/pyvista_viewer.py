import argparse
import colorcet as cc  # type: ignore[import-untyped]
from datetime import timedelta
from lxml import etree as ElementTree  # type: ignore[import-untyped]
import pyvista as pv
import time
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import vtkDataAssembly, vtkPartitionedDataSetCollection, vtkStaticCellLocator
from vtkmodules.vtkFiltersCore import vtkExtractCells
from vtkmodules.vtkIOXML import vtkXMLPartitionedDataSetCollectionReader
from vtkmodules.vtkRenderingCore import vtkActor
from geos.xml_tools.vtk_builder import create_vtk_deck
from geos.xml_tools.xml_processor import process


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
    parser.add_argument(
        "-vtpc",
        "--vtpcFilepath",
        type=str,
        default="",
        help="path to .vtpc file.",
    )
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

    def __init__( self, actor: vtkActor ) -> None:
        self.actor = actor

    def __call__( self, state: bool ) -> None:
        self.actor.SetVisibility( state )


class SetVisibilitiesCallback:
    """Helper callback to keep a reference to the actor being modified."""

    def __init__( self ) -> None:
        self.actors: list[ vtkActor ] = []

    def add_actor( self, actor: vtkActor ) -> None:
        self.actors.append( actor )

    def update_visibility( self, state: bool ) -> None:
        for actor in self.actors:
            actor.SetVisibility( state )

    def __call__( self, state: bool ) -> None:
        for actor in self.actors:
            actor.SetVisibility( state )


def find_surfaces( xmlFile: str ) -> list[ str ]:
    """Find all surfaces in xml file using lxml instead of xsdata."""
    # Process the XML file using the existing geos-xml-tools processor
    processed_xml_path = process( inputFiles=[ xmlFile ], keep_parameters=True, keep_includes=True )
    
    # Parse the processed XML with lxml
    parser = ElementTree.XMLParser( remove_comments=True, remove_blank_text=True )
    tree = ElementTree.parse( processed_xml_path, parser=parser )
    root = tree.getroot()
    
    used: list[ str ] = []
    
    # Find all FieldSpecifications
    for field_spec in root.findall( ".//FieldSpecifications/FieldSpecification" ):
        set_names_attr = field_spec.get( "setNames" )
        if set_names_attr:
            # Parse the set names (format: "{name1, name2, all}" or similar)
            names = set_names_attr.replace( "{", "[" ).replace( "}", "]" )
            elements = names.strip( "][" ).split( "," )
            elements = [ element.strip() for element in elements ]
            if "all" in elements:
                elements.remove( "all" )
            if elements:
                used.extend( elements )
    
    return used


def main( args: argparse.Namespace ) -> None:
    start_time = time.monotonic()
    pdsc: vtkPartitionedDataSetCollection

    if args.vtpcFilepath != "":
        reader = vtkXMLPartitionedDataSetCollectionReader()
        reader.SetFileName( args.vtpcFilepath )
        reader.Update()
        pdsc = reader.GetOutput()
    else:
        pdsc = create_vtk_deck( args.xmlFilepath, args.attributeName )

    read_time = time.monotonic()
    print( "time elapsed reading files: ", timedelta( seconds=read_time - start_time ) )

    assembly: vtkDataAssembly = pdsc.GetDataAssembly()
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

            my_cell_locator = vtkStaticCellLocator()
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
                        id_list = vtkIdList()
                        id_list.InsertNextId( cell_id )
                        extract = vtkExtractCells()
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
