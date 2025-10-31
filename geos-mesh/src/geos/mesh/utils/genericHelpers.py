# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
import numpy as np
import logging
import numpy.typing as npt
from typing import Iterator, List, Sequence, Any, Union, Tuple
from vtkmodules.util.numpy_support import ( numpy_to_vtk, vtk_to_numpy )
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints, reference, vtkDataArray, vtkLogger, vtkFloatArray
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkMultiBlockDataSet,
    vtkPolyData,
    vtkDataSet,
    vtkDataObject,
    vtkPlane,
    vtkCellTypes,
    vtkIncrementalOctreePointLocator,
)
from vtkmodules.vtkFiltersCore import ( vtk3DLinearGridPlaneCutter, vtkPolyDataNormals, vtkPolyDataTangents )
from vtkmodules.vtkFiltersTexture import vtkTextureMapToPlane

from geos.mesh.utils.multiblockHelpers import ( getBlockElementIndexesFlatten, getBlockFromFlatIndex )

from geos.utils.algebraFunctions import (
    getAttributeMatrixFromVector,
    getAttributeVectorFromMatrix,
)
from geos.utils.geometryFunctions import ( getChangeOfBasisMatrix, CANONICAL_BASIS_3D )
from geos.utils.Logger import ( getLogger, Logger, VTKCaptureLog, RegexExceptionFilter )
from geos.utils.Errors import VTKError

__doc__ = """
Generic VTK utilities.

These methods include:
    - extraction of a surface from a given elevation
    - conversion from a list to vtkIdList
    - conversion of vtk container into iterable
"""


def toVtkIdList( data: List[ int ] ) -> vtkIdList:
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


def vtkIter( vtkContainer: Union[ vtkIdList, vtkCellTypes ] ) -> Iterator[ Any ]:
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


def convertAttributeFromLocalToXYZForOneCell(
    vector: npt.NDArray[ np.float64 ], localBasisVectors: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                                                                 npt.NDArray[ np.float64 ] ]
) -> npt.NDArray[ np.float64 ]:
    """Convert one cell attribute from local to XYZ basis.

    .. Warning::
        Vectors components are considered to be in GEOS output order such that \
        v = ( M00, M11, M22, M12, M02, M01, M21, M20, M10 )

    Args:
        vector (npt.NDArray[np.float64]): The attribute expressed in local basis. The size of the vector must be 3, 9 or 6 (symmetrical case)
        localBasisVectors (tuple[ npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]): The local basis vectors expressed in the XYZ basis.

    Returns:
        vectorXYZ (npt.NDArray[np.float64]): The attribute expressed in XYZ basis.
    """
    # Get components matrix from GEOS attribute vector
    matrix3x3: npt.NDArray[ np.float64 ] = getAttributeMatrixFromVector( vector )

    # Get transform matrix
    transformMatrix: npt.NDArray[ np.float64 ] = getChangeOfBasisMatrix( localBasisVectors, CANONICAL_BASIS_3D )

    # Apply transformation
    arrayXYZ: npt.NDArray[ np.float64 ] = transformMatrix @ matrix3x3 @ transformMatrix.T

    # Convert back to GEOS type attribute and return
    return getAttributeVectorFromMatrix( arrayXYZ, vector.size )


def getNormalVectors( surface: vtkPolyData ) -> npt.NDArray[ np.float64 ]:
    """Return the normal vectors of a surface mesh.

    Args:
        surface (vtkPolyData): The input surface.

    Raises:
        ValueError: No normal attribute found in the mesh. Use the computeNormals function beforehand.

    Returns:
        npt.NDArray[ np.float64 ]: The normal vectors of the input surface.
    """
    normals: Union[ npt.NDArray[ np.float64 ],
                    None ] = surface.GetCellData().GetNormals()  # type: ignore[no-untyped-call]
    if normals is None:
        raise ValueError( "No normal attribute found in the mesh. Use the computeNormals function beforehand." )

    return vtk_to_numpy( normals )


def getTangentsVectors( surface: vtkPolyData ) -> Tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:
    """Return the tangential vectors of a surface.

    Args:
        surface (vtkPolyData): The input surface.

    Raises:
        ValueError: Tangent attribute not found in the mesh. Use computeTangents beforehand.
        ValueError: Problem during the calculation of the second tangential vectors.

    Returns:
        Tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]: The tangents vectors of the input surface.
    """
    # Get first tangential component
    vtkTangents: Union[ vtkFloatArray, None ] = surface.GetCellData().GetTangents()  # type: ignore[no-untyped-call]
    tangents1: npt.NDArray[ np.float64 ]

    try:
        tangents1 = vtk_to_numpy( vtkTangents )
    except AttributeError as err:
        print( "No tangential attribute found in the mesh. Use the computeTangents function beforehand." )
        raise VTKError( err ) from err
    else:
        # Compute second tangential component
        normals: npt.NDArray[ np.float64 ] = getNormalVectors( surface )

        tangents2: npt.NDArray[ np.float64 ] = np.cross( normals, tangents1, axis=1 ).astype( np.float64 )

    return ( tangents1, tangents2 )


def getLocalBasisVectors( surface: vtkPolyData ) -> npt.NDArray[ np.float64 ]:
    """Return the local basis vectors for all cells of the input surface.

    Args:
        surface(vtkPolydata): The input surface.

    Returns:
        npt.NDArray[np.float64]: Array with normal, tangential 1 and tangential 2 vectors.
    """
    try:
        normals: npt.NDArray[ np.float64 ] = getNormalVectors( surface )
        surfaceWithNormals: vtkPolyData = surface
    # ValueError raised if no normals found in the mesh
    except ValueError:
        # In that case, the normals are computed.
        surfaceWithNormals = computeNormals( surface )
        normals = getNormalVectors( surfaceWithNormals )

    # Tangents require normals to be present in the mesh
    try:
        tangents: Tuple[ npt.NDArray[ np.float64 ],
                         npt.NDArray[ np.float64 ] ] = getTangentsVectors( surfaceWithNormals )
    # If no tangents is present in the mesh, they are computed on that surface
    except VTKError:
        surfaceWithTangents: vtkPolyData = computeTangents( surfaceWithNormals )
        tangents = getTangentsVectors( surfaceWithTangents )

    return np.array( ( normals, *tangents ) )


def computeNormals(
    surface: vtkPolyData,
    logger: Union[ Logger, None ] = None,
) -> vtkPolyData:
    """Compute and set the normals of a given surface.

    Args:
        surface (vtkPolyData): The input surface.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        vtkPolyData: The surface with normal attribute.
    """
    if logger is None:
        logger = getLogger( "computeSurfaceNormals" )
    # Creation of a child logger to deal with VTKErrors without polluting parent logger
    vtkErrorLogger: Logger = getLogger( f"{logger.name}.vtkErrorLogger" )
    vtkErrorLogger.propagate = False

    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )

    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
    vtkErrorLogger.setLevel( logging.DEBUG )

    with VTKCaptureLog() as capturedLog:
        normalFilter: vtkPolyDataNormals = vtkPolyDataNormals()
        normalFilter.SetInputData( surface )
        normalFilter.ComputeCellNormalsOn()
        normalFilter.ComputePointNormalsOff()
        normalFilter.Update()

        capturedLog.seek( 0 )
        captured = capturedLog.read().decode()

        vtkErrorLogger.debug( captured.strip() )

    outputSurface = normalFilter.GetOutput()

    if outputSurface.GetCellData().GetNormals() is None:
        raise VTKError( "Something went wrong with VTK calculation of the normals." )

    return outputSurface


def computeTangents(
    triangulatedSurface: vtkPolyData,
    logger: Union[ Logger, None ] = None,
) -> vtkPolyData:
    """Compute and set the tangents of a given surface.

    .. Warning:: The computation of tangents requires a triangulated surface.

    Args:
        triangulatedSurface (vtkPolyData): The input surface. It should be triangulated beforehand.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        vtkPolyData: The surface with tangent attribute
    """
    # need to compute texture coordinates required for tangent calculation
    surface1: vtkPolyData = computeSurfaceTextureCoordinates( triangulatedSurface )

    # TODO: triangulate the surface before computation of the tangents if needed.

    # compute tangents
    if logger is None:
        logger = getLogger( "computeSurfaceTangents" )
    # Creation of a child logger to deal with VTKErrors without polluting parent logger
    vtkErrorLogger: Logger = getLogger( f"{logger.name}.vtkErrorLogger" )
    vtkErrorLogger.propagate = False

    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )

    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
    vtkErrorLogger.setLevel( logging.DEBUG )

    with VTKCaptureLog() as capturedLog:

        tangentFilter: vtkPolyDataTangents = vtkPolyDataTangents()
        tangentFilter.SetInputData( surface1 )
        tangentFilter.ComputeCellTangentsOn()
        tangentFilter.ComputePointTangentsOff()
        tangentFilter.Update()
        surfaceOut: vtkPolyData = tangentFilter.GetOutput()

        capturedLog.seek( 0 )
        captured = capturedLog.read().decode()

        vtkErrorLogger.debug( captured.strip() )

    if surfaceOut is None:
        raise VTKError( "Something went wrong in VTK calculation." )

    # copy tangents attributes into filter input surface because surface attributes
    # are not transferred to the output (bug that should be corrected by Kitware)
    array: vtkDataArray = surfaceOut.GetCellData().GetTangents()
    if array is None:
        raise VTKError( "Attribute Tangents is not in the mesh." )

    surface1.GetCellData().SetTangents( array )
    surface1.GetCellData().Modified()
    surface1.Modified()
    return surface1


def computeSurfaceTextureCoordinates(
    surface: vtkPolyData,
    logger: Union[ Logger, None ] = None,
) -> vtkPolyData:
    """Generate the 2D texture coordinates required for tangent computation. The dataset points are mapped onto a plane generated automatically.

    Args:
        surface (vtkPolyData): The input surface.
        logger (Union[Logger, None], optional): A logger to manage the output messages.
            Defaults to None, an internal logger is used.

    Returns:
        vtkPolyData: The input surface with generated texture map.
    """
    # Need to compute texture coordinates required for tangent calculation
    if logger is None:
        logger = getLogger( "computeSurfaceTextureCoordinates" )
    # Creation of a child logger to deal with VTKErrors without polluting parent logger
    vtkErrorLogger: Logger = getLogger( f"{logger.name}.vtkErrorLogger" )
    vtkErrorLogger.propagate = False

    vtkLogger.SetStderrVerbosity( vtkLogger.VERBOSITY_ERROR )

    vtkErrorLogger.addFilter( RegexExceptionFilter() )  # will raise VTKError if captured VTK Error
    vtkErrorLogger.setLevel( logging.DEBUG )

    with VTKCaptureLog() as capturedLog:

        textureFilter: vtkTextureMapToPlane = vtkTextureMapToPlane()
        textureFilter.SetInputData( surface )
        textureFilter.AutomaticPlaneGenerationOn()
        textureFilter.Update()

        capturedLog.seek( 0 )
        captured = capturedLog.read().decode()

        vtkErrorLogger.debug( captured.strip() )

    return textureFilter.GetOutput()
