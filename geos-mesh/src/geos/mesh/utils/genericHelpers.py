# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
import numpy as np
import numpy.typing as npt
from typing import Iterator, List, Sequence, Any, Union
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints, reference
import vtkmodules.vtkCommonDataModel as vtk_dm
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkMultiBlockDataSet, vtkPolyData, vtkDataSet, vtkDataObject, vtkPlane, vtkCellTypes, vtkIncrementalOctreePointLocator
from vtkmodules.vtkFiltersCore import vtk3DLinearGridPlaneCutter
from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockFromFlatIndex )

__doc__ = """
Generic VTK utilities.

These methods include:
    - extraction of a surface from a given elevation
    - conversion from a list to vtkIdList
    - conversion of vtk container into iterable
"""


def get_vtk_constant_str( vtk_int_value: int ) -> str:
    """
    Finds the string name of a VTK constant from its integer value.

    Args:
        vtk_int_value: The integer value of the constant (e.g., 12).

    Returns:
        A string like "12: VTK_HEXAHEDRON" or "12: <UNKNOWN_VTK_CONSTANT>".
    """
    # Search through the vtkCommonDataModel module
    for name in dir( vtk_dm ):
        # We only want variables that start with "VTK_"
        if name.startswith( "VTK_" ):
            if getattr( vtk_dm, name ) == vtk_int_value:
                return f"{vtk_int_value}: {name}"
    return f"{vtk_int_value}: <UNKNOWN_VTK_CONSTANT>"


def to_vtk_id_list( data: List[ int ] ) -> vtkIdList:
    """Utility function transforming a list of ids into a vtkIdList.

    Args:
        data (list[int]): Id list

    Returns:
        result (vtkIdList):  Vtk Id List corresponding to input data
    """
    result = vtkIdList()
    result.Allocate( len( data ) )
    for d in data:
        result.InsertNextId( d )
    return result


def vtk_iter( vtkContainer: vtkIdList | vtkCellTypes ) -> Iterator[ Any ]:
    """Utility function transforming a vtk "container" into an iterable.

    Args:
        vtkContainer (vtkIdList | vtkCellTypes): A vtk container

    Returns:
        Iterator[ Any ]: The iterator
    """
    if isinstance( vtkContainer, vtkIdList ):
        for i in range( vtkContainer.GetNumberOfIds() ):
            yield vtkContainer.GetId( i )
    elif isinstance( vtkContainer, vtkCellTypes ):
        for i in range( vtkContainer.GetNumberOfTypes() ):
            yield vtkContainer.GetCellType( i )


def extractSurfaceFromElevation( mesh: vtkUnstructuredGrid, elevation: float ) -> vtkPolyData:
    """Extract surface at a constant elevation from a mesh.

    Args:
        mesh (vtkUnstructuredGrid): input mesh
        elevation (float): elevation at which to extract the surface

    Returns:
        vtkPolyData: output surface
    """
    assert mesh is not None, "Input mesh is undefined."
    assert isinstance( mesh, vtkUnstructuredGrid ), "Wrong object type"

    bounds: tuple[ float, float, float, float, float, float ] = mesh.GetBounds()
    ooX: float = ( bounds[ 0 ] + bounds[ 1 ] ) / 2.0
    ooY: float = ( bounds[ 2 ] + bounds[ 3 ] ) / 2.0

    # check plane z coordinates against mesh bounds
    assert ( elevation <= bounds[ 5 ] ) and ( elevation >= bounds[ 4 ] ), "Plane is out of input mesh bounds."

    plane: vtkPlane = vtkPlane()
    plane.SetNormal( 0.0, 0.0, 1.0 )
    plane.SetOrigin( ooX, ooY, elevation )

    cutter = vtk3DLinearGridPlaneCutter()
    cutter.SetInputDataObject( mesh )
    cutter.SetPlane( plane )
    cutter.SetInterpolateAttributes( True )
    cutter.Update()
    return cutter.GetOutputDataObject( 0 )


def getBounds(
        input: Union[ vtkUnstructuredGrid,
                      vtkMultiBlockDataSet ] ) -> tuple[ float, float, float, float, float, float ]:
    """Get bounds of either single of composite data set.

    Args:
        input (Union[vtkUnstructuredGrid, vtkMultiBlockDataSet]): input mesh

    Returns:
        tuple[float, float, float, float, float, float]: tuple containing
            bounds (xmin, xmax, ymin, ymax, zmin, zmax)

    """
    if isinstance( input, vtkMultiBlockDataSet ):
        return getMultiBlockBounds( input )
    else:
        return getMonoBlockBounds( input )


def getMonoBlockBounds( input: vtkUnstructuredGrid, ) -> tuple[ float, float, float, float, float, float ]:
    """Get boundary box extrema coordinates for a vtkUnstructuredGrid.

    Args:
        input (vtkMultiBlockDataSet): input single block mesh

    Returns:
        tuple[float, float, float, float, float, float]: tuple containing
            bounds (xmin, xmax, ymin, ymax, zmin, zmax)

    """
    return input.GetBounds()


def getMultiBlockBounds( input: vtkMultiBlockDataSet, ) -> tuple[ float, float, float, float, float, float ]:
    """Get boundary box extrema coordinates for a vtkMultiBlockDataSet.

    Args:
        input (vtkMultiBlockDataSet): input multiblock mesh

    Returns:
        tuple[float, float, float, float, float, float]: bounds.

    """
    xmin, ymin, zmin = 3 * [ np.inf ]
    xmax, ymax, zmax = 3 * [ -1.0 * np.inf ]
    blockIndexes: list[ int ] = getBlockElementIndexesFlatten( input )
    for blockIndex in blockIndexes:
        block0: vtkDataObject = getBlockFromFlatIndex( input, blockIndex )
        assert block0 is not None, "Mesh is undefined."
        block: vtkDataSet = vtkDataSet.SafeDownCast( block0 )
        bounds: tuple[ float, float, float, float, float, float ] = block.GetBounds()
        xmin = bounds[ 0 ] if bounds[ 0 ] < xmin else xmin
        xmax = bounds[ 1 ] if bounds[ 1 ] > xmax else xmax
        ymin = bounds[ 2 ] if bounds[ 2 ] < ymin else ymin
        ymax = bounds[ 3 ] if bounds[ 3 ] > ymax else ymax
        zmin = bounds[ 4 ] if bounds[ 4 ] < zmin else zmin
        zmax = bounds[ 5 ] if bounds[ 5 ] > zmax else zmax
    return xmin, xmax, ymin, ymax, zmin, zmax


def getBoundsFromPointCoords( cellPtsCoord: list[ npt.NDArray[ np.float64 ] ] ) -> Sequence[ float ]:
    """Compute bounding box coordinates of the list of points.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of points

    Returns:
        Sequence[float]: bounding box coordinates (xmin, xmax, ymin, ymax, zmin, zmax)
    """
    bounds: list[ float ] = [
        np.inf,
        -np.inf,
        np.inf,
        -np.inf,
        np.inf,
        -np.inf,
    ]
    for ptsCoords in cellPtsCoord:
        mins: npt.NDArray[ np.float64 ] = np.min( ptsCoords, axis=0 )
        maxs: npt.NDArray[ np.float64 ] = np.max( ptsCoords, axis=0 )
        for i in range( 3 ):
            bounds[ 2 * i ] = float( min( bounds[ 2 * i ], mins[ i ] ) )
            bounds[ 2 * i + 1 ] = float( max( bounds[ 2 * i + 1 ], maxs[ i ] ) )
    return bounds


def createSingleCellMesh( cellType: int, ptsCoord: npt.NDArray[ np.float64 ] ) -> vtkUnstructuredGrid:
    """Create a mesh that consists of a single cell.

    Args:
        cellType (int): cell type
        ptsCoord (1DArray[np.float64]): cell point coordinates

    Returns:
        vtkUnstructuredGrid: output mesh
    """
    nbPoints: int = ptsCoord.shape[ 0 ]
    points: npt.NDArray[ np.float64 ] = np.vstack( ( ptsCoord, ) )
    # Convert points to vtkPoints object
    vtkpts: vtkPoints = vtkPoints()
    vtkpts.SetData( numpy_to_vtk( points ) )

    # create cells from point ids
    cellsID: vtkIdList = vtkIdList()
    for j in range( nbPoints ):
        cellsID.InsertNextId( j )

    # add cell to mesh
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    mesh.SetPoints( vtkpts )
    mesh.Allocate( 1 )
    mesh.InsertNextCell( cellType, cellsID )
    return mesh


def createMultiCellMesh( cellTypes: list[ int ],
                         cellPtsCoord: list[ npt.NDArray[ np.float64 ] ],
                         sharePoints: bool = True ) -> vtkUnstructuredGrid:
    """Create a mesh that consists of multiple cells.

    .. WARNING:: The mesh is not checked for conformity.

    Args:
        cellTypes (list[int]): Cell type
        cellPtsCoord (list[1DArray[np.float64]]): List of cell point coordinates
        sharePoints (bool): If True, cells share points, else a new point is created for each cell vertex

    Returns:
        vtkUnstructuredGrid: Output mesh
    """
    assert len( cellPtsCoord ) == len( cellTypes ), "The lists of cell types of point coordinates must be of same size."
    nbCells: int = len( cellPtsCoord )
    mesh: vtkUnstructuredGrid = vtkUnstructuredGrid()
    points: vtkPoints
    cellVertexMapAll: list[ tuple[ int, ...] ]
    points, cellVertexMapAll = createVertices( cellPtsCoord, sharePoints )
    assert len( cellVertexMapAll ) == len(
        cellTypes ), "The lists of cell types of cell point ids must be of same size."
    mesh.SetPoints( points )
    mesh.Allocate( nbCells )
    # create mesh cells
    for cellType, ptsId in zip( cellTypes, cellVertexMapAll, strict=True ):
        # create cells from point ids
        cellsID: vtkIdList = vtkIdList()
        for ptId in ptsId:
            cellsID.InsertNextId( ptId )
        mesh.InsertNextCell( cellType, cellsID )
    return mesh


def createVertices( cellPtsCoord: list[ npt.NDArray[ np.float64 ] ],
                    shared: bool = True ) -> tuple[ vtkPoints, list[ tuple[ int, ...] ] ]:
    """Create vertices from cell point coordinates list.

    Args:
        cellPtsCoord (list[npt.NDArray[np.float64]]): list of cell point coordinates
        shared (bool, optional): If True, collocated points are merged. Defaults to True.

    Returns:
        tuple[vtkPoints, list[tuple[int, ...]]]: tuple containing points and the
            map of cell point ids
    """
    # get point bounds
    bounds: Sequence[ float ] = getBoundsFromPointCoords( cellPtsCoord )
    points: vtkPoints = vtkPoints()
    # use point locator to check for colocated points
    pointsLocator = vtkIncrementalOctreePointLocator()
    pointsLocator.InitPointInsertion( points, bounds )
    cellVertexMapAll: list[ tuple[ int, ...] ] = []
    ptId: reference = reference( 0 )
    ptsCoords: npt.NDArray[ np.float64 ]
    for ptsCoords in cellPtsCoord:
        cellVertexMap: list[ int ] = []
        pt: npt.NDArray[ np.float64 ]  # 1DArray
        for pt in ptsCoords:
            if shared:
                pointsLocator.InsertUniquePoint( pt.tolist(), ptId )  # type: ignore[arg-type]
            else:
                pointsLocator.InsertPointWithoutChecking( pt.tolist(), ptId, 1 )  # type: ignore[arg-type]
            cellVertexMap += [ ptId.get() ]  # type: ignore
        cellVertexMapAll += [ tuple( cellVertexMap ) ]
    return points, cellVertexMapAll
