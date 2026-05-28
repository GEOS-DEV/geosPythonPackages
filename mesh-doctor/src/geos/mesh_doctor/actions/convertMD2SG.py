# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: GitHub Copilot, Jacques Franc
from dataclasses import dataclass
from typing import Optional, Union

from vtkmodules.vtkCommonDataModel import VTK_TRIANGLE, VTK_TRIANGLE_STRIP, VTK_QUAD, VTK_POLYGON, vtkPolyData, vtkKdTree, vtkCell
from vtkmodules.vtkCommonCore import vtkIdTypeArray, vtkPoints, reference, vtkUnsignedIntArray, vtkDataArray, vtkIdList
from vtkmodules.vtkCommonDataModel import vtkSelection, vtkSelectionNode, vtkUnstructuredGrid, vtkMultiBlockDataSet
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, vtkCleanPolyData
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter

from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readMesh, VtkOutput, writeMesh


@dataclass( frozen=True )
class Options:
    meshVtkOutput: VtkOutput
    attrs: tuple[ int, ...] = ()
    skipCleanCollocated: bool = False
    skipFilterVolumeCells: bool = False


@dataclass( frozen=True )
class Result:
    outputMesh: Optional[ vtkUnstructuredGrid ]
    bounds: tuple[ float, float, float, float, float, float ]
    numPoints: int
    numCells: int
    attrs: tuple[ int, ...]
    skipCleanCollocated: bool
    nCleanCollocated: int
    skipFilterVolumeCells: bool
    nFilterVolumeCells: int
    nColors: int


TOLERANCE = 1e-6


def is_surface_cell_type( t: int ) -> bool:
    """Checks if the given VTK cell type is a surface cell type (2D)."""
    surface_types = {
        VTK_TRIANGLE,
        VTK_QUAD,
        VTK_POLYGON,
        VTK_TRIANGLE_STRIP,
    }
    return t in surface_types


def __process_block( block: Union[ vtkMultiBlockDataSet, vtkUnstructuredGrid, vtkPolyData ],
                     append_filter: vtkAppendPolyData, attrs: list[ int ] ) -> None:
    """Recursively processes a block of the multi-block dataset, extracting surface cells that match the given attributes and adding them to the append filter."""
    if isinstance( block, vtkMultiBlockDataSet ):
        for i in range( block.GetNumberOfBlocks() ):
            child: Union[ vtkMultiBlockDataSet, vtkUnstructuredGrid,
                          vtkPolyData ] = block.GetBlock( i )  # type: ignore[assignment]
            if child is not None:
                __process_block( child, append_filter, attrs )
        return

    if not hasattr( block, "GetNumberOfCells" ):
        return
    if block.GetNumberOfCells() == 0:
        return

    cell_types = set()
    for i in range( block.GetNumberOfCells() ):
        cell_types.add( block.GetCellType( i ) )

    if all([is_surface_cell_type( ct ) for ct in cell_types]):
        cell_attributes = block.GetCellData().GetArray( "attribute" )
        if len( attrs ) == 0 or ( cell_attributes is not None and cell_attributes.GetTuple1( 0 ) in attrs ):
            if isinstance( block, vtkPolyData ):
                append_filter.AddInputData( block )
            else:
                gf = vtkGeometryFilter()
                gf.SetInputData( block )
                gf.Update()
                append_filter.AddInputData( gf.GetOutput() )


def __extract_first_vol( block: Union[ vtkMultiBlockDataSet, vtkUnstructuredGrid ] ) -> Optional[ vtkUnstructuredGrid ]:
    """Recursively searches for the first volumetric block in the multi-block dataset."""
    if isinstance( block, vtkMultiBlockDataSet ):
        for i in range( block.GetNumberOfBlocks() ):
            child: Union[ vtkMultiBlockDataSet, vtkUnstructuredGrid ] = block.GetBlock( i )  # type: ignore[assignment]
            if child is not None:
                found = __extract_first_vol( child )
                if found is not None:
                    return found
        return None

    if not hasattr( block, "GetNumberOfCells" ):
        return None
    if block.GetNumberOfCells() == 0:
        return None

    is_vol = False
    for i in range( block.GetNumberOfCells() ):
        cell_type = block.GetCellType( i )
        is_vol = not is_surface_cell_type( cell_type )
        if is_vol:
            break
    return block if is_vol else None


def _filterVolumeCells( mesh: vtkUnstructuredGrid,
                        attrs: list[ int ] ) -> tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid, int ]:
    """Filters out volume cells from the input mesh, keeping only surface cells that match the given attributes. Returns the filtered volume mesh, the extracted surface mesh, and the number of cells removed."""
    volumeIds = vtkIdTypeArray()
    surfaceIds = vtkIdTypeArray()
    nVolume = nSurface = nOther = 0

    cell_attributes = mesh.GetCellData().GetArray( "attribute" )
    for i in range( mesh.GetNumberOfCells() ):
        dim = mesh.GetCell( i ).GetCellDimension()
        if dim == 3:
            volumeIds.InsertNextValue( i )
            nVolume += 1
        elif dim == 2:
            assert cell_attributes is not None, "Input mesh must have a 'attribute' cell data array for filtering."
            if cell_attributes.GetTuple1( i ) in attrs or len( attrs ) == 0:
                surfaceIds.InsertNextValue( i )
                nSurface += 1
        else:
            nOther += 1

    if cell_attributes is not None:
        setupLogger.info(
            f"Mesh contains {nVolume} volume cells, {nSurface} surface cells matching attributes {attrs}, and {nOther} other cells."
        )
    else:
        setupLogger.info(
            f"Mesh contains {nVolume} volume cells, {nSurface} surface cells, and {nOther} other cells (no 'attribute' array for filtering)."
        )

    if nSurface == 0 and nOther == 0:
        setupLogger.info( "No filtering needed (all cells are 3D)" )
        return mesh, mesh.NewInstance(), nSurface + nOther

    sn = vtkSelectionNode()
    sn.SetFieldType( vtkSelectionNode.CELL )
    sn.SetContentType( vtkSelectionNode.INDICES )
    sn.SetSelectionList( volumeIds )
    Esn = vtkSelectionNode()
    Esn.SetFieldType( vtkSelectionNode.CELL )
    Esn.SetContentType( vtkSelectionNode.INDICES )
    Esn.SetSelectionList( surfaceIds )

    sel = vtkSelection()
    sel.AddNode( sn )
    Esel = vtkSelection()
    Esel.AddNode( Esn )

    ext = vtkExtractSelection()
    ext.SetInputData( 0, mesh )
    ext.SetInputData( 1, sel )
    ext.Update()
    Eext = vtkExtractSelection()
    Eext.SetInputData( 0, mesh )
    Eext.SetInputData( 1, Esel )
    Eext.Update()

    setupLogger.info( f"Filtered → {nVolume} cells (removed {nSurface + nOther})" )

    if nVolume > 0:
        if nSurface > 0:
            return ext.GetOutput(), Eext.GetOutput(), nSurface + nOther
        return ext.GetOutput(), mesh.NewInstance(), nSurface + nOther

    return mesh.NewInstance(), mesh.NewInstance(), nSurface + nOther


def __clean_collocated( main: vtkUnstructuredGrid ) -> tuple[ vtkUnstructuredGrid, int ]:
    """Cleans collocated points in the input mesh, returning a new mesh with unique points and updated cell connectivity, as well as the number of points cleaned."""
    clean_point_set: dict[ tuple[ float, float, float ], int ] = {}
    reverse_map: dict[ int, int ] = {}

    for pid in range( main.GetNumberOfPoints() ):
        pt = main.GetPoints().GetPoint( pid )
        reverse_map[ pid ] = clean_point_set.get( pt, pid )
        clean_point_set.setdefault( pt, pid )

    old_to_new: dict[ int, int ] = {}
    clean_points = vtkPoints()
    for pt, ids in clean_point_set.items():
        old_to_new[ ids ] = clean_points.InsertNextPoint( pt )

    rewrite_mesh = vtkUnstructuredGrid()
    rewrite_mesh.SetPoints( clean_points )

    for cell_id in range( main.GetNumberOfCells() ):
        cell: vtkCell = main.GetCell( cell_id )
        new_ids: list[ int ] = []
        for i in range( cell.GetNumberOfPoints() ):
            pid = cell.GetPointId( i )
            new_ids.append( old_to_new.get( reverse_map.get( pid, pid ), pid ) )
        rewrite_mesh.InsertNextCell( cell.GetCellType(), len( new_ids ), new_ids )

    rewrite_mesh.GetCellData().ShallowCopy( main.GetCellData() )

    for array_i in range( main.GetPointData().GetNumberOfArrays() ):
        arr = main.GetPointData().GetArray( array_i )
        new_arr = vtkDataArray.CreateDataArray( arr.GetDataType() )
        new_arr.SetName( arr.GetName() )
        new_arr.SetNumberOfComponents( arr.GetNumberOfComponents() )
        new_arr.SetNumberOfTuples( clean_points.GetNumberOfPoints() )
        for old_id, new_id in old_to_new.items():
            new_arr.SetTuple( new_id, arr.GetTuple( old_id ) )
        rewrite_mesh.GetPointData().AddArray( new_arr )

    nCleanCollocated = main.GetNumberOfPoints() - rewrite_mesh.GetNumberOfPoints()
    return rewrite_mesh, nCleanCollocated


def __paintNodes(
        main: vtkUnstructuredGrid,
        frac_polys: list[ vtkUnstructuredGrid ] ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    """Paints the nodes of the main mesh that are close to the fracture polygons, returning the modified main mesh and the list of fracture polygons."""
    kd = vtkKdTree()
    kd.BuildLocatorFromPoints( main )

    narray = vtkUnsignedIntArray()
    narray.SetNumberOfComponents( 1 )
    narray.SetNumberOfTuples( main.GetNumberOfPoints() )

    for i in range( main.GetNumberOfPoints() ):
        narray.SetTuple1( i, 0 )

    count = 0
    setupLogger.info( f"Number of fracpolys: {len(frac_polys)}" )
    for poly in frac_polys:
        setupLogger.info(
            f"Processing fracpoly with {poly.GetNumberOfPoints()} points and {poly.GetNumberOfCells()} cells." )
        for i in range( poly.GetNumberOfPoints() ):
            dist = reference( 0.0 )
            id_source = kd.FindClosestPoint( poly.GetPoint( i ), dist )  # type: ignore[call-overload]
            if dist > TOLERANCE:  # type: ignore[operator]
                setupLogger.warning(
                    f"[too far point] main point ({id_source}) is too far from frac point ({i}) = ({dist} > {TOLERANCE})"
                )
            narray.SetTuple1( id_source, 1 )
            count += 1

    setupLogger.info( f"Painted {count}/{narray.GetNumberOfTuples()} nodes based on proximity to fracture polygons." )
    narray.SetName( "faultNodes" )
    main.GetPointData().AddArray( narray )
    return main, frac_polys


#TODO refactor with other coloring function to avoid code duplication
def __coloringNodes( main: vtkUnstructuredGrid ) -> tuple[ vtkUnstructuredGrid, int ]:
    """Colors the nodes of the main mesh based on their point-connectivity, one array per connected component of faultNodes==1 points. Returns the modified mesh and the number of connected components found."""
    fault_array = main.GetPointData().GetArray( "faultNodes" )
    n_pts = main.GetNumberOfPoints()

    # Collect only the fault-node ids up front
    fault_pids = { pid for pid in range( n_pts ) if fault_array.GetTuple1( pid ) == 1 }
    setupLogger.info( f"Found {len(fault_pids)} fault nodes to color based on connectivity." )

    visited: set[ int ] = set()
    color = 0

    for seed in fault_pids:
        if seed in visited:
            continue

        # One fresh, zero-filled array per connected component
        color_array = vtkUnsignedIntArray()
        color_array.SetNumberOfComponents( 1 )
        color_array.SetNumberOfTuples( n_pts )
        color_array.Fill( 0 )

        # Iterative DFS — avoids Python recursion-depth limit
        stack = [ seed ]
        count = 0
        while stack:
            pid = stack.pop()
            if pid in visited:
                continue
            visited.add( pid )
            color_array.SetTuple1( pid, 1 )  # mark this point as belonging to component
            count += 1

            cells = vtkIdList()
            main.GetPointCells( pid, cells )
            for ci in range( cells.GetNumberOfIds() ):
                cell = main.GetCell( cells.GetId( ci ) )
                for vi in range( cell.GetNumberOfPoints() ):
                    nbr = cell.GetPointId( vi )
                    if nbr not in visited and nbr in fault_pids:
                        stack.append( nbr )

        color_array.SetName( f"faultNodes_{color}" )
        setupLogger.info( f"Connected component {color}: {count} points" )

        main.GetPointData().AddArray( color_array )
        color += 1

    return main, color


def polydata_to_ugrid( poly: vtkUnstructuredGrid ) -> vtkUnstructuredGrid:
    """Converts a vtkPolyData to a vtkUnstructuredGrid by copying points, cells, and data."""
    ugrid = vtkUnstructuredGrid()
    ugrid.SetPoints( poly.GetPoints() )
    for cid in range( poly.GetNumberOfCells() ):
        cell = poly.GetCell( cid )
        ugrid.InsertNextCell( cell.GetCellType(), cell.GetPointIds() )
    ugrid.GetPointData().ShallowCopy( poly.GetPointData() )
    ugrid.GetCellData().ShallowCopy( poly.GetCellData() )
    return ugrid


def meshDoctor_to_surfaceGen( hierachical_mesh: vtkMultiBlockDataSet, attrs: tuple[ int, ...],
                              skip_clean_collocated: bool ) -> tuple[ vtkUnstructuredGrid, int, int ]:
    """Converts a mesh-doctor multi-block dataset to a surface mesh compatible with SurfaceGen by extracting surface cells that match the given attributes, optionally cleaning collocated points, and returning the resulting unstructured grid along with the number of points cleaned.

    Args:
        hierachical_mesh: The input multi-block dataset containing the mesh.
        attrs: A tuple of attribute values to filter surface cells. If empty, all surface cells are included.
        skip_clean_collocated: If True, skips the step of cleaning collocated points. If False, collocated points will be cleaned and the number of points cleaned will be returned.

    Returns:
        A tuple containing the converted surface mesh as a vtkUnstructuredGrid and the number of points cleaned from collocated points (if skip_clean_collocated is False) or 0 (if skip
    """
    append_filter = vtkAppendPolyData()
    __process_block( hierachical_mesh, append_filter, list( attrs ) )

    main = __extract_first_vol( hierachical_mesh )
    if main is None:
        raise ValueError( "No volumetric block found in the multi-block mesh." )

    nCleanCollocated, nColors = 0, 0
    if not skip_clean_collocated:
        main, nCleanCollocated = __clean_collocated( main )

    append_filter.Update()
    clean = vtkCleanPolyData()
    clean.SetInputConnection( append_filter.GetOutputPort() )
    clean.Update()

    painted_main, _ = __paintNodes( main, [ clean.GetOutput() ] )
    colored_main, nColors = __coloringNodes( painted_main )
    return polydata_to_ugrid( colored_main ), nCleanCollocated, nColors


def toSurfaceGen( hierachical_mesh: vtkUnstructuredGrid, attrs: tuple[ int, ...], skip_clean_collocated: bool,
                  skip_filter_volume_cells: bool ) -> tuple[ vtkUnstructuredGrid, int, int, int ]:
    """Converts a single unstructured grid mesh to a surface mesh compatible with SurfaceGen by optionally filtering out volume cells, extracting surface cells that match the given attributes, optionally cleaning collocated points, and returning the resulting unstructured grid along with the number of points cleaned and cells filtered.

    Args:
        hierachical_mesh: The input unstructured grid mesh.
        attrs: A tuple of attribute values to filter surface cells. If empty, all surface cells are included.
        skip_clean_collocated: If True, skips the step of cleaning collocated points. If False, collocated points will be cleaned and the number of points cleaned will be returned.
        skip_filter_volume_cells: If True, skips the step of filtering out volume cells and extracting surface cells. If False, volume cells will be filtered out and surface cells matching the attributes will be extracted, and the number of cells filtered will be returned.

    Returns:
        A tuple containing the converted surface mesh as a vtkUnstructuredGrid, the number of points cleaned from collocated points (if skip_clean_collocated is False) or 0 (if skip clean_collocated is True), and the number of cells filtered out as volume cells (if skip_filter_volume_cells is False) or 0 (if skip_filter_volume_cells is True).
    """
    nCleanCollocated, nFilteredVolumeCells, nColors = 0, 0, 0
    if skip_filter_volume_cells:
        main = hierachical_mesh
        surfaces: list[ vtkUnstructuredGrid ] = []
    else:
        main, surfs, nFilteredVolumeCells = _filterVolumeCells( hierachical_mesh, list( attrs ) )
        surfaces = [ surfs ]

    if not skip_clean_collocated:
        main, nCleanCollocated = __clean_collocated( main )

    painted_main, _ = __paintNodes( main, surfaces )
    setupLogger.info( f"Has Array faultNodes: {painted_main.GetPointData().HasArray('faultNodes')}" )
    setupLogger.info(
        f"Range of faultNodes: {painted_main.GetPointData().GetArray('faultNodes').GetRange() if painted_main.GetPointData().HasArray('faultNodes') else 'N/A'}"
    )
    colored_main, nColors = __coloringNodes( painted_main )
    return polydata_to_ugrid( colored_main ), nCleanCollocated, nFilteredVolumeCells, nColors


def meshAction( mesh: Union[ vtkMultiBlockDataSet, vtkUnstructuredGrid ], options: Options ) -> Result:
    """Performs the conversion of the input mesh to a surface mesh compatible with SurfaceGen using the specified options, and returns the result containing the output file path, bounds, number of points and cells, and details about the cleaning and filtering steps.

    Args:
        mesh: The input mesh to be converted, which can be either a vtkMultiBlockDataSet or a vtkUnstructuredGrid.
        options: The options for the conversion, including attributes to filter, whether to skip cleaning collocated points, and whether to skip filtering volume cells.

    Returns:
        A Result object containing the output file path, bounds, number of points and cells in the converted mesh, the attributes used for filtering, whether cleaning collocated points was skipped, whether filtering volume cells was skipped, and the number of points cleaned and cells filtered if those steps were performed.

    """
    if isinstance( mesh, vtkMultiBlockDataSet ):
        converted, nCleanCollocated, nColors = meshDoctor_to_surfaceGen( mesh, options.attrs,
                                                                         options.skipCleanCollocated )
        nFilteredVolumeCells = 0
    elif isinstance( mesh, vtkUnstructuredGrid ):
        converted, nCleanCollocated, nFilteredVolumeCells, nColors = toSurfaceGen( mesh, options.attrs,
                                                                                   options.skipCleanCollocated,
                                                                                   options.skipFilterVolumeCells )
    else:
        raise TypeError( f"Unsupported mesh type {type( mesh )}." )

    return Result( outputMesh=converted,
                   bounds=converted.GetBounds(),
                   numPoints=converted.GetNumberOfPoints(),
                   numCells=converted.GetNumberOfCells(),
                   attrs=options.attrs,
                   skipCleanCollocated=options.skipCleanCollocated,
                   skipFilterVolumeCells=options.skipFilterVolumeCells,
                   nCleanCollocated=nCleanCollocated,
                   nFilterVolumeCells=nFilteredVolumeCells,
                   nColors=nColors )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a mesh from the input file, converts it to a surface mesh compatible with SurfaceGen using the specified options, and returns the result containing the output file path, bounds, number of points and cells, and details about the cleaning and filtering steps.

    Args:
        vtuInputFile: The path to the input VTU file containing the mesh to be converted.
        options: The options for the conversion, including attributes to filter, whether to skip cleaning collocated points, and whether to skip filtering volume cells.

    Returns:
        A Result object containing the output file path, bounds, number of points and cells in the converted mesh, the attributes used for filtering, whether cleaning collocated points was skipped, whether filtering volume cells was skipped, and the number of points cleaned and cells filtered if those steps were performed.
    """
    if vtuInputFile is None:
        raise ValueError( "An input file must be provided." )

    mesh = readMesh( vtuInputFile )
    result = meshAction( mesh, options )

    setupLogger.info( f"Writing converted mesh to {options.meshVtkOutput.output}" )
    writeMesh( result.outputMesh, options.meshVtkOutput )

    return result
