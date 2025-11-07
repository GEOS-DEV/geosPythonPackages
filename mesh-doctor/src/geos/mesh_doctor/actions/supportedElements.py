from dataclasses import dataclass
import multiprocessing
import networkx
from tqdm import tqdm
from typing import Iterable, Mapping, Optional
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, vtkUnstructuredGrid, VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON,
                                            VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
                                            VTK_WEDGE )
from geos.mesh_doctor.actions.vtkPolyhedron import buildFaceToFaceConnectivityThroughEdges, FaceStream
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid
from geos.mesh.utils.genericHelpers import vtkIter


@dataclass( frozen=True )
class Options:
    nproc: int
    chunkSize: int


@dataclass( frozen=True )
class Result:
    unsupportedStdElementsTypes: frozenset[ int ]  # list of unsupported types
    unsupportedPolyhedronElements: frozenset[
        int ]  # list of polyhedron elements that could not be converted to supported std elements


# for multiprocessing, vtkUnstructuredGrid cannot be pickled. Let's use a global variable instead.
MESH: Optional[ vtkUnstructuredGrid ] = None


def initWorkerMesh( inputFileForWorker: str ):
    """Initializer for multiprocessing.Pool to set the global MESH variable in each worker process.

    Args:
        inputFileForWorker (str): Filepath to vtk grid
    """
    global MESH
    setupLogger.debug(
        f"Worker process (PID: {multiprocessing.current_process().pid}) initializing MESH from file: {inputFileForWorker}"
    )
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( inputFileForWorker )
    if MESH is None:
        setupLogger.error(
            f"Worker process (PID: {multiprocessing.current_process().pid}) failed to load mesh from {inputFileForWorker}"
        )
        # You might want to raise an error here or ensure MESH being None is handled downstream
        # For now, the assert MESH is not None in __call__ will catch this.


class IsPolyhedronConvertible:

    def __init__( self ):

        def buildPrismGraph( n: int, name: str ) -> networkx.Graph:
            """Builds the face to face connectivities (through edges) for prism graphs.

            Args:
                n (int): The number of nodes of the basis (i.e. the pentagonal prims gets n = 5)
                name (str): A human-readable name for logging purpose.

            Returns:
                networkx.Graph: A graph instance.
            """
            tmp = networkx.cycle_graph( n )
            for node in range( n ):
                tmp.add_edge( node, n )
                tmp.add_edge( node, n + 1 )
            tmp.name = name
            return tmp

        # Building the reference graphs
        tetGraph = networkx.complete_graph( 4 )
        tetGraph.name = "Tetrahedron"
        pyrGraph = buildPrismGraph( 4, "Pyramid" )
        pyrGraph.remove_node( 5 )  # Removing a node also removes its associated edges.
        self.__referenceGraphs: Mapping[ int, Iterable[ networkx.Graph ] ] = {
            4: ( tetGraph, ),
            5: ( pyrGraph, buildPrismGraph( 3, "Wedge" ) ),
            6: ( buildPrismGraph( 4, "Hexahedron" ), ),
            7: ( buildPrismGraph( 5, "Prism5" ), ),
            8: ( buildPrismGraph( 6, "Prism6" ), ),
            9: ( buildPrismGraph( 7, "Prism7" ), ),
            10: ( buildPrismGraph( 8, "Prism8" ), ),
            11: ( buildPrismGraph( 9, "Prism9" ), ),
            12: ( buildPrismGraph( 10, "Prism10" ), ),
            13: ( buildPrismGraph( 11, "Prism11" ), ),
        }

    def __isPolyhedronSupported( self, faceStream ) -> str:
        """Checks if a polyhedron can be converted into a supported cell.
        If so, returns the name of the type. If not, the returned name will be empty.

        Args:
            faceStream (_type_): The polyhedron.

        Returns:
            str: The name of the supported type or an empty string.
        """
        cellGraph = buildFaceToFaceConnectivityThroughEdges( faceStream, add_compatibility=True )
        if cellGraph.order() not in self.__referenceGraphs:
            return ""
        for referenceGraph in self.__referenceGraphs[ cellGraph.order() ]:
            if networkx.is_isomorphic( referenceGraph, cellGraph ):
                return str( referenceGraph.name )
        return ""

    def __call__( self, ic: int ) -> int:
        """Checks if a vtk polyhedron cell can be converted into a supported GEOS element.

        Args:
            ic (int): The index element.

        Returns:
            int: -1 if the polyhedron vtk element can be converted into a supported element type. The index otherwise.
        """
        global MESH
        assert MESH is not None, f"MESH global variable not initialized in worker process (PID: {multiprocessing.current_process().pid}). This should have been set by initWorkerMesh."
        if MESH.GetCellType( ic ) != VTK_POLYHEDRON:
            return -1
        ptIds = vtkIdList()
        MESH.GetFaceStream( ic, ptIds )
        faceStream = FaceStream.buildFromVtkIdList( ptIds )
        convertedTypeName = self.__isPolyhedronSupported( faceStream )
        if convertedTypeName:
            setupLogger.debug( f"Polyhedron cell {ic} can be converted into \"{convertedTypeName}\"" )
            return -1
        else:
            setupLogger.debug(
                f"Polyhedron cell {ic} (in PID {multiprocessing.current_process().pid}) cannot be converted into any supported element."
            )
            return ic


def __action( vtkInputFile: str, options: Options ) -> Result:
    # Main process loads the mesh for its own use
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtkInputFile )
    if mesh is None:
        setupLogger.error( f"Main process failed to load mesh from {vtkInputFile}. Aborting." )
        # Return an empty/error result or raise an exception
        return Result( unsupportedStdElementsTypes=frozenset(), unsupportedPolyhedronElements=frozenset() )

    if hasattr( mesh, "GetDistinctCellTypesArray" ):
        cellTypesNumpy = vtk_to_numpy( mesh.GetDistinctCellTypesArray() )
        cellTypes = set( cellTypesNumpy.tolist() )
    else:
        vtkCellTypesObj = vtkCellTypes()
        mesh.GetCellTypes( vtkCellTypesObj )
        cellTypes = set( vtkIter( vtkCellTypesObj ) )

    supportedCellTypes = {
        VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON, VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
        VTK_WEDGE
    }
    unsupportedStdElementsTypes = cellTypes - supportedCellTypes

    # Dealing with polyhedron elements.
    numCells = mesh.GetNumberOfCells()
    polyhedronConverter = IsPolyhedronConvertible()

    unsupportedPolyhedronIndices = []
    # Pass the vtkInputFile to the initializer
    with multiprocessing.Pool( processes=options.nproc, initializer=initWorkerMesh,
                               initargs=( vtkInputFile, ) ) as pool:  # Comma makes it a tuple
        generator = pool.imap_unordered( polyhedronConverter, range( numCells ), chunksize=options.chunkSize )
        for cellIndexOrNegOne in tqdm( generator, total=numCells, desc="Testing support for elements" ):
            if cellIndexOrNegOne != -1:
                unsupportedPolyhedronIndices.append( cellIndexOrNegOne )

    return Result( unsupportedStdElementsTypes=frozenset( unsupportedStdElementsTypes ),
                   unsupportedPolyhedronElements=frozenset( unsupportedPolyhedronIndices ) )


def action( vtkInputFile: str, options: Options ) -> Result:
    return __action( vtkInputFile, options )
