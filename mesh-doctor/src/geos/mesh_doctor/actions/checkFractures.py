from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
from tqdm import tqdm
from typing import Collection, Iterable, Sequence
from vtkmodules.vtkCommonDataModel import vtkCell, vtkMultiBlockDataSet, vtkUnstructuredGrid
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.vtkIOXML import vtkXMLMultiBlockDataReader
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh.utils.genericHelpers import vtkIter
from geos.mesh_doctor.actions.generateFractures import Coordinates3D
from geos.mesh_doctor.parsing.cliParsing import setupLogger


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


def __readMultiblock( vtuInputFile: str, matrixName: str,
                      fractureName: str ) -> tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid ]:
    """Reads a multiblock VTU file and extracts the matrix and fracture meshes.

    Args:
        vtuInputFile (str): The input VTU file path.
        matrixName (str): The name of the matrix mesh block.
        fractureName (str): The name of the fracture mesh block.

    Returns:
        tuple[ vtkUnstructuredGrid, vtkUnstructuredGrid ]: The matrix and fracture meshes.
    """
    reader = vtkXMLMultiBlockDataReader()
    reader.SetFileName( vtuInputFile )
    reader.Update()
    multiBlock: vtkMultiBlockDataSet = reader.GetOutput()
    for b in range( multiBlock.GetNumberOfBlocks() ):
        blockName: str = multiBlock.GetMetaData( b ).Get( multiBlock.NAME() )
        if blockName == matrixName:
            matrix = vtkUnstructuredGrid.SafeDownCast( multiBlock.GetBlock( b ) )
        if blockName == fractureName:
            fracture = vtkUnstructuredGrid.SafeDownCast( multiBlock.GetBlock( b ) )
    assert matrix and fracture
    return matrix, fracture


def formatCollocatedNodes( fractureMesh: vtkUnstructuredGrid ) -> Sequence[ Iterable[ int ] ]:
    """Extract the collocated nodes information from the mesh and formats it in a python way.

    Args:
        fractureMesh (vtkUnstructuredGrid): The mesh of the fracture (with 2d cells).

    Returns:
        Sequence[ Iterable[ int ] ]: An iterable over all the buckets of collocated nodes.
    """
    collocatedNodes: npt.NDArray = vtk_to_numpy( fractureMesh.GetPointData().GetArray( "collocated_nodes" ) )
    if len( collocatedNodes.shape ) == 1:
        collocatedNodes = collocatedNodes.reshape( ( collocatedNodes.shape[ 0 ], 1 ) )
    generator = ( tuple( sorted( bucket[ bucket > -1 ] ) ) for bucket in collocatedNodes )
    return tuple( generator )


def __checkCollocatedNodesPositions(
    matrixPoints: npt.NDArray, fracturePoints: npt.NDArray, g2l: npt.NDArray[ np.int64 ],
    collocatedNodes: Iterable[ Iterable[ int ] ]
) -> Collection[ tuple[ int, Iterable[ int ], Iterable[ Coordinates3D ] ] ]:
    """Check that the collocated nodes are indeed collocated in space.

    Args:
        matrixPoints (npt.NDArray): The points of the matrix mesh.
        fracturePoints (npt.NDArray): The points of the fracture mesh.
        g2l (npt.NDArray[ np.int64 ]): Mapping from global to local indices in the matrix mesh.
        collocatedNodes (Iterable[ Iterable[ int ] ]): The collocated nodes information.

    Returns:
        Collection[ tuple[ int, Iterable[ int ], Iterable[ Coordinates3D ] ] ]: A collection of issues found.
    """
    issues = []
    for li, bucket in enumerate( collocatedNodes ):
        matrix_nodes = ( fracturePoints[ li ], ) + tuple( matrixPoints[ g2l[ gi ] ] for gi in bucket )
        m = np.array( matrix_nodes )
        rank: int = np.linalg.matrix_rank( m )
        if rank > 1:
            issues.append( ( li, bucket, tuple( matrixPoints[ g2l[ gi ] ] for gi in bucket ) ) )
    return issues


def myIter( ccc: tuple ) -> Iterable[ tuple ]:
    """Recursively generates all combinations from nested sequences.

    Args:
        ccc (tuple): A tuple of sequences to generate combinations from.

    Yields:
        Iterable[ tuple ]: All possible combinations, one element from each sequence.
    """
    car, cdr = ccc[ 0 ], ccc[ 1: ]
    for i in car:
        if cdr:
            for j in myIter( cdr ):
                yield i, *j
        else:
            yield ( i, )


def __checkNeighbors( matrix: vtkUnstructuredGrid, fracture: vtkUnstructuredGrid, g2l: npt.NDArray[ np.int64 ],
                      collocatedNodes: Sequence[ Iterable[ int ] ] ) -> None:
    """Check that for each pair of collocated nodes, the corresponding fracture faces have exactly two neighbor cells.

    Args:
        matrix (vtkUnstructuredGrid): The matrix mesh.
        fracture (vtkUnstructuredGrid): The fracture mesh.
        g2l (npt.NDArray[ np.int64 ]): Mapping from global to local indices in the matrix mesh.
        collocatedNodes (Sequence[ Iterable[ int ] ]): The collocated nodes information.
    """
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


def meshAction( matrix: vtkUnstructuredGrid, fracture: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the check of the fractures and collocated nodes generated.

    Args:
        matrix (vtkUnstructuredGrid): The matrix mesh.
        fracture (vtkUnstructuredGrid): The fracture mesh.
        options (Options): The options for processing.

    Returns:
        Result: The result of the self intersecting elements check.
    """
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


def action( vtkMultiBlockInputFile: str, options: Options ) -> Result:
    """Reads a vtkMultiblock and performs the check of the fractures and collocated nodes generated.

    Args:
        vtkMultiBlockInputFile (str): The path to the input vtkMultiBlock file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the check of the fractures and collocated nodes generated.
    """
    matrix, fracture = __readMultiblock( vtkMultiBlockInputFile, options.matrixName, options.fractureName )
    return meshAction( matrix, fracture, options )
