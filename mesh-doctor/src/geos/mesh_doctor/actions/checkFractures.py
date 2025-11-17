from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from tqdm import tqdm
from typing import Collection, Iterable, Sequence
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, vtkCell
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh_doctor.actions.generateFractures import Coordinates3D
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.utils.genericHelpers import vtkIter


@dataclass( frozen=True )
class Options:
    tolerance: float
    matrixName: str
    fractureName: str
    collocatedNodesFieldName: str


@dataclass( frozen=True )
class Result:
    # First index is the local index of the fracture mesh.
    # Second is the local index of the matrix mesh.
    # Third is the global index in the matrix mesh.
    errors: Sequence[ tuple[ int, int, int ] ]


def __readMultiblock( vtkInputFile: str, matrixName: str,
                      fractureName: str ) -> tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid ]:
    reader = vtkXMLMultiBlockDataReader()
    reader.SetFileName( vtkInputFile )
    reader.Update()
    multiBlock = reader.GetOutput()
    for b in range( multiBlock.GetNumberOfBlocks() ):
        blockName: str = multiBlock.GetMetaData( b ).Get( multiBlock.NAME() )
        if blockName == matrixName:
            matrix: vtkUnstructuredGrid = multiBlock.GetBlock( b )
        if blockName == fractureName:
            fracture: vtkUnstructuredGrid = multiBlock.GetBlock( b )
    assert matrix and fracture
    return matrix, fracture


def formatCollocatedNodes( fractureMesh: vtkUnstructuredGrid ) -> Sequence[ Iterable[ int ] ]:
    """Extract the collocated nodes information from the mesh and formats it in a python way.

    Args:
        fractureMesh (vtkUnstructuredGrid): The mesh of the fracture (with 2d cells).

    Returns:
        Sequence[ Iterable[ int ] ]: An iterable over all the buckets of collocated nodes.
    """
    collocatedNodes: npt.NDArray = vtk_to_numpy( fractureMesh.GetPointData().GetArray( "collocatedNodes" ) )
    if len( collocatedNodes.shape ) == 1:
        collocatedNodes = collocatedNodes.reshape( ( collocatedNodes.shape[ 0 ], 1 ) )
    generator = ( tuple( sorted( bucket[ bucket > -1 ] ) ) for bucket in collocatedNodes )
    return tuple( generator )


def __checkCollocatedNodesPositions(
    matrixPoints: npt.NDArray, fracturePoints: npt.NDArray, g2l: npt.NDArray[ np.int64 ],
    collocatedNodes: Iterable[ Iterable[ int ] ]
) -> Collection[ tuple[ int, Iterable[ int ], Iterable[ Coordinates3D ] ] ]:
    issues = []
    for li, bucket in enumerate( collocatedNodes ):
        matrix_nodes = ( fracturePoints[ li ], ) + tuple( map( lambda gi: matrixPoints[ g2l[ gi ] ], bucket ) )
        m = np.array( matrix_nodes )
        rank: int = np.linalg.matrix_rank( m )
        if rank > 1:
            issues.append( ( li, bucket, tuple( map( lambda gi: matrixPoints[ g2l[ gi ] ], bucket ) ) ) )
    return issues


def myIter( ccc ):
    car, cdr = ccc[ 0 ], ccc[ 1: ]
    for i in car:
        if cdr:
            for j in myIter( cdr ):
                yield i, *j
        else:
            yield ( i, )


def __checkNeighbors( matrix: vtkUnstructuredGrid, fracture: vtkUnstructuredGrid, g2l: npt.NDArray[ np.int64 ],
                      collocatedNodes: Sequence[ Iterable[ int ] ] ):
    fractureNodes: set[ int ] = set()
    for bucket in collocatedNodes:
        for gi in bucket:
            fractureNodes.add( g2l[ gi ] )
    # For each face of each cell,
    # if all the points of the face are "made" of collocated nodes,
    # then this is a fracture face.
    fractureFaces: set[ frozenset[ int ] ] = set()
    for c in range( matrix.GetNumberOfCells() ):
        cell: vtkCell = matrix.GetCell( c )
        for f in range( cell.GetNumberOfFaces() ):
            face: vtkCell = cell.GetFace( f )
            pointIds = frozenset( vtkIter( face.GetPointIds() ) )
            if pointIds <= fractureNodes:
                fractureFaces.add( pointIds )
    # Finding the cells
    for c in tqdm( range( fracture.GetNumberOfCells() ), desc="Finding neighbor cell pairs" ):
        cell = fracture.GetCell( c )
        cns: set[ frozenset[ npt.NDArray[ np.int64 ] ] ] = set()  # subset of collocatedNodes
        pointIds = frozenset( vtkIter( cell.GetPointIds() ) )
        for pointId in pointIds:
            bucket = collocatedNodes[ pointId ]
            localBucket = frozenset( map( g2l.__getitem__, bucket ) )
            cns.add( localBucket )
        found = 0
        tmp = tuple( map( tuple, cns ) )
        for nodeCombinations in myIter( tmp ):
            faceCombination = frozenset( nodeCombinations )
            if faceCombination in fractureFaces:
                found += 1
        if found != 2:
            setupLogger.warning( "Something went wrong since we should have found 2 fractures faces (we found" +
                                 f" {found}) for collocated nodes {cns}." )


def __action( vtkInputFile: str, options: Options ) -> Result:
    matrix, fracture = __readMultiblock( vtkInputFile, options.matrixName, options.fractureName )
    matrixPoints: vtkPoints = matrix.GetPoints()
    fracturePoints: vtkPoints = fracture.GetPoints()

    collocatedNodes: Sequence[ Iterable[ int ] ] = formatCollocatedNodes( fracture )
    assert matrix.GetPointData().GetGlobalIds() and matrix.GetCellData().GetGlobalIds() and \
           fracture.GetPointData().GetGlobalIds() and fracture.GetCellData().GetGlobalIds()

    pointIds = vtk_to_numpy( matrix.GetPointData().GetGlobalIds() )
    g2l: npt.NDArray[ np.int64 ] = np.ones( len( pointIds ), dtype=np.int64 ) * -1
    for loc, glo in enumerate( pointIds ):
        g2l[ glo ] = loc
    g2l.flags.writeable = False

    issues = __checkCollocatedNodesPositions( vtk_to_numpy( matrix.GetPoints().GetData() ),
                                              vtk_to_numpy( fracture.GetPoints().GetData() ), g2l, collocatedNodes )
    assert len( issues ) == 0

    __checkNeighbors( matrix, fracture, g2l, collocatedNodes )

    errors = []
    for i, duplicates in enumerate( collocatedNodes ):
        for duplicate in filter( lambda i: i > -1, duplicates ):
            p0 = matrixPoints.GetPoint( g2l[ duplicate ] )
            p1 = fracturePoints.GetPoint( i )
            if np.linalg.norm( np.array( p1 ) - np.array( p0 ) ) > options.tolerance:
                errors.append( ( i, g2l[ duplicate ], duplicate ) )
    return Result( errors=errors )


def action( vtkInputFile: str, options: Options ) -> Result:
    try:
        return __action( vtkInputFile, options )
    except BaseException as e:
        setupLogger.error( e )
        return Result( errors=() )
