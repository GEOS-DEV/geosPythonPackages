# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: GitHub Copilot, Jacques Franc
import os
from dataclasses import dataclass
from typing import Optional

import vtk
from vtkmodules.vtkCommonCore import vtkIdTypeArray, vtkPoints, reference
from vtkmodules.vtkCommonDataModel import vtkSelection, vtkSelectionNode, vtkUnstructuredGrid, vtkMultiBlockDataSet
from vtkmodules.vtkFiltersCore import vtkAppendPolyData, vtkCleanPolyData
from vtkmodules.vtkFiltersExtraction import vtkExtractSelection
from vtkmodules.vtkFiltersGeometry import vtkGeometryFilter
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader, vtkXMLUnstructuredGridWriter

from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    attrs: tuple[ int, ... ] = ()
    skipCleanCollocated: bool = False
    skipFilterVolumeCells: bool = False
    outputFile: Optional[ str ] = None


@dataclass( frozen=True )
class Result:
    outputFile: str
    bounds: tuple[ float, float, float, float, float, float ]
    numPoints: int
    numCells: int
    attrs: tuple[ int, ... ]
    skipCleanCollocated: bool
    skipFilterVolumeCells: bool


TOLERANCE = 1e-6


def is_surface_cell_type( t: int ) -> bool:
    surface_types = {
        vtk.VTK_TRIANGLE,
        vtk.VTK_QUAD,
        vtk.VTK_POLYGON,
        vtk.VTK_TRIANGLE_STRIP,
    }
    return t in surface_types


def __process_block( block, append_filter: vtkAppendPolyData, attrs: list[ int ] ) -> None:
    if isinstance( block, vtkMultiBlockDataSet ):
        for i in range( block.GetNumberOfBlocks() ):
            child = block.GetBlock( i )
            if child is not None:
                __process_block( child, append_filter, attrs )
        return

    if not hasattr( block, "GetNumberOfCells" ):
        return
    if block.GetNumberOfCells() == 0:
        return

    cell_type = block.GetCellType( 0 )
    if is_surface_cell_type( cell_type ):
        cell_attributes = block.GetCellData().GetArray( "attribute" )
        if len( attrs ) == 0 or ( cell_attributes is not None and cell_attributes.GetTuple1( 0 ) in attrs ):
            if isinstance( block, vtk.vtkPolyData ):
                append_filter.AddInputData( block )
            else:
                gf = vtkGeometryFilter()
                gf.SetInputData( block )
                gf.Update()
                append_filter.AddInputData( gf.GetOutput() )


def __extract_vol( block ):
    if isinstance( block, vtkMultiBlockDataSet ):
        for i in range( block.GetNumberOfBlocks() ):
            child = block.GetBlock( i )
            if child is not None:
                found = __extract_vol( child )
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


def _filterVolumeCells( mesh: vtkUnstructuredGrid, attrs: list[ int ] ) -> tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid ]:
    volumeIds = vtkIdTypeArray()
    surfaceIds = vtkIdTypeArray()
    nVolume = nSurface = nOther = 0

    for i in range( mesh.GetNumberOfCells() ):
        dim = mesh.GetCell( i ).GetCellDimension()
        if dim == 3:
            volumeIds.InsertNextValue( i )
            nVolume += 1
        elif dim == 2:
            cell_attributes = mesh.GetCellData().GetArray( "attribute" )
            if cell_attributes is not None and cell_attributes.GetTuple1( 0 ) in attrs:
                surfaceIds.InsertNextValue( i )
                nSurface += 1
        else:
            nOther += 1

    setupLogger.info( f"  Cell types: {nVolume} volume (3D) | {nSurface} surface (filtered 2D) | {nOther} other" )

    if nSurface == 0 and nOther == 0:
        setupLogger.info( "No filtering needed (all cells are 3D)" )
        return mesh, mesh.NewInstance()

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
            return ext.GetOutput(), Eext.GetOutput()
        return ext.GetOutput(), mesh.NewInstance()

    return mesh.NewInstance(), mesh.NewInstance()


def __clean_collocated( main: vtkUnstructuredGrid ) -> vtkUnstructuredGrid:
    clean_point_set = {}
    reverse_map = {}

    for pid in range( main.GetNumberOfPoints() ):
        pt = main.GetPoints().GetPoint( pid )
        reverse_map[ pid ] = clean_point_set.get( pt, pid )
        clean_point_set.setdefault( pt, pid )

    old_to_new = {}
    clean_points = vtkPoints()
    for pt, new_id in clean_point_set.items():
        old_to_new[ new_id ] = clean_points.InsertNextPoint( pt )

    rewrite_mesh = vtkUnstructuredGrid()
    rewrite_mesh.SetPoints( clean_points )

    for cell_id in range( main.GetNumberOfCells() ):
        cell = main.GetCell( cell_id )
        new_ids = []
        for i in range( cell.GetNumberOfPoints() ):
            pid = cell.GetPointId( i )
            new_ids.append( old_to_new.get( reverse_map.get( pid, pid ), old_to_new[ pid ] ) )
        rewrite_mesh.InsertNextCell( cell.GetCellType(), len( new_ids ), new_ids )

    rewrite_mesh.GetCellData().ShallowCopy( main.GetCellData() )

    for array_i in range( main.GetPointData().GetNumberOfArrays() ):
        arr = main.GetPointData().GetArray( array_i )
        new_arr = vtk.vtkDataArray.CreateDataArray( arr.GetDataType() )
        new_arr.SetName( arr.GetName() )
        new_arr.SetNumberOfComponents( arr.GetNumberOfComponents() )
        new_arr.SetNumberOfTuples( clean_points.GetNumberOfPoints() )
        for old_id, new_id in old_to_new.items():
            new_arr.SetTuple( new_id, arr.GetTuple( old_id ) )
        rewrite_mesh.GetPointData().AddArray( new_arr )

    return rewrite_mesh


def __paintNodes( main: vtkUnstructuredGrid, frac_polys: list[ vtkUnstructuredGrid ] ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    kd = vtk.vtkKdTree()
    kd.BuildLocatorFromPoints( main )

    narray = vtk.vtkUnsignedIntArray()
    narray.SetNumberOfComponents( 1 )
    narray.SetNumberOfTuples( main.GetNumberOfPoints() )

    for i in range( main.GetNumberOfPoints() ):
        narray.SetTuple1( i, 0 )

    for poly in frac_polys:
        for i in range( poly.GetNumberOfPoints() ):
            dist = reference( 0.0 )
            id_source = kd.FindClosestPoint( poly.GetPoint( i ), dist )
            if dist > TOLERANCE:
                setupLogger.warning(
                    f"[too far point] main point ({id_source}) is too far from frac point ({i}) = ({dist} > {TOLERANCE})"
                )
            narray.SetTuple1( id_source, 1 )

    narray.SetName( "faultNodes" )
    main.GetPointData().AddArray( narray )
    return main, frac_polys


def polydata_to_ugrid( poly: vtkUnstructuredGrid ) -> vtkUnstructuredGrid:
    ugrid = vtkUnstructuredGrid()
    ugrid.SetPoints( poly.GetPoints() )
    for cid in range( poly.GetNumberOfCells() ):
        cell = poly.GetCell( cid )
        ugrid.InsertNextCell( cell.GetCellType(), cell.GetPointIds() )
    ugrid.GetPointData().ShallowCopy( poly.GetPointData() )
    ugrid.GetCellData().ShallowCopy( poly.GetCellData() )
    return ugrid


def meshDoctor_to_surfaceGen( hierachical_mesh: vtkMultiBlockDataSet, attrs: tuple[ int, ... ], skip_clean_collocated: bool ) -> vtkUnstructuredGrid:
    append_filter = vtkAppendPolyData()
    __process_block( hierachical_mesh, append_filter, list( attrs ) )

    main = __extract_vol( hierachical_mesh )
    if main is None:
        raise ValueError( "No volumetric block found in the multi-block mesh." )

    if not skip_clean_collocated:
        main = __clean_collocated( main )

    append_filter.Update()
    clean = vtkCleanPolyData()
    clean.SetInputConnection( append_filter.GetOutputPort() )
    clean.Update()

    painted_main, _ = __paintNodes( main, [ clean.GetOutput() ] )
    return polydata_to_ugrid( painted_main )


def toSurfaceGen( hierachical_mesh: vtkUnstructuredGrid, attrs: tuple[ int, ... ], skip_clean_collocated: bool,
                  skip_filter_volume_cells: bool ) -> vtkUnstructuredGrid:
    if skip_filter_volume_cells:
        main = hierachical_mesh
        surfaces: list[ vtkUnstructuredGrid ] = []
    else:
        main, surfs = _filterVolumeCells( hierachical_mesh, list( attrs ) )
        surfaces = [ surfs ]

    if not skip_clean_collocated:
        main = __clean_collocated( main )

    painted_main, _ = __paintNodes( main, surfaces )
    return polydata_to_ugrid( painted_main )


def __read_input_mesh( input_file: str ):
    reader = vtkXMLMultiBlockDataReader()
    reader.SetFileName( input_file )
    reader.Update()
    output = reader.GetOutput()
    if isinstance( output, vtkMultiBlockDataSet ) and output.GetNumberOfBlocks() > 0:
        return output
    return readUnstructuredGrid( input_file )


def __write_output_mesh( mesh: vtkUnstructuredGrid, output_file: str ) -> None:
    writer = vtkXMLUnstructuredGridWriter()
    writer.SetFileName( output_file )
    writer.SetInputData( mesh )
    writer.Write()


def meshAction( mesh, options: Options, output_file: str ) -> Result:
    if isinstance( mesh, vtkMultiBlockDataSet ):
        converted = meshDoctor_to_surfaceGen( mesh, options.attrs, options.skipCleanCollocated )
    elif isinstance( mesh, vtkUnstructuredGrid ):
        converted = toSurfaceGen( mesh, options.attrs, options.skipCleanCollocated, options.skipFilterVolumeCells )
    else:
        raise TypeError( f"Unsupported mesh type {type( mesh )}." )

    __write_output_mesh( converted, output_file )
    return Result( outputFile=output_file,
                   bounds=converted.GetBounds(),
                   numPoints=converted.GetNumberOfPoints(),
                   numCells=converted.GetNumberOfCells(),
                   attrs=options.attrs,
                   skipCleanCollocated=options.skipCleanCollocated,
                   skipFilterVolumeCells=options.skipFilterVolumeCells )


def action( vtuInputFile: str, options: Options ) -> Result:
    if vtuInputFile is None:
        raise ValueError( "An input file must be provided." )

    mesh = __read_input_mesh( vtuInputFile )
    output_file = options.outputFile if options.outputFile else f"{os.path.splitext( vtuInputFile )[0]}_converted.vtu"
    return meshAction( mesh, options, output_file )
