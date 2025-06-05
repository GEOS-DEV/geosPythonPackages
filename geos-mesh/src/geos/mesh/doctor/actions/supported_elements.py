from dataclasses import dataclass
import multiprocessing
import networkx
from tqdm import tqdm
from typing import FrozenSet, Iterable, Mapping, Optional
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, vtkUnstructuredGrid, VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON,
                                            VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
                                            VTK_WEDGE )
from geos.mesh.doctor.actions.vtk_polyhedron import build_face_to_face_connectivity_through_edges, FaceStream
from geos.mesh.utils.genericHelpers import vtk_iter
from geos.mesh.io.vtkIO import read_mesh
from geos.utils.Logger import getLogger

logger = getLogger( "supported_elements" )


@dataclass( frozen=True )
class Options:
    nproc: int
    chunk_size: int


@dataclass( frozen=True )
class Result:
    unsupported_std_elements_types: FrozenSet[ int ]  # list of unsupported types
    unsupported_polyhedron_elements: FrozenSet[
        int ]  # list of polyhedron elements that could not be converted to supported std elements


# for multiprocessing, vtkUnstructuredGrid cannot be pickled. Let's use a global variable instead.
MESH: Optional[ vtkUnstructuredGrid ] = None


def init_worker_mesh( input_file_for_worker: str ):
    """Initializer for multiprocessing.Pool to set the global MESH variable in each worker process.

    Args:
        input_file_for_worker (str): Filepath to vtk grid
    """
    global MESH
    logger.debug(
        f"Worker process (PID: {multiprocessing.current_process().pid}) initializing MESH from file: {input_file_for_worker}"
    )
    MESH = read_mesh( input_file_for_worker )
    if MESH is None:
        logger.error(
            f"Worker process (PID: {multiprocessing.current_process().pid}) failed to load mesh from {input_file_for_worker}"
        )
        # You might want to raise an error here or ensure MESH being None is handled downstream
        # For now, the assert MESH is not None in __call__ will catch this.


class IsPolyhedronConvertible:

    def __init__( self ):

        def build_prism_graph( n: int, name: str ) -> networkx.Graph:
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
        tet_graph = networkx.complete_graph( 4 )
        tet_graph.name = "Tetrahedron"
        pyr_graph = build_prism_graph( 4, "Pyramid" )
        pyr_graph.remove_node( 5 )  # Removing a node also removes its associated edges.
        self.__reference_graphs: Mapping[ int, Iterable[ networkx.Graph ] ] = {
            4: ( tet_graph, ),
            5: ( pyr_graph, build_prism_graph( 3, "Wedge" ) ),
            6: ( build_prism_graph( 4, "Hexahedron" ), ),
            7: ( build_prism_graph( 5, "Prism5" ), ),
            8: ( build_prism_graph( 6, "Prism6" ), ),
            9: ( build_prism_graph( 7, "Prism7" ), ),
            10: ( build_prism_graph( 8, "Prism8" ), ),
            11: ( build_prism_graph( 9, "Prism9" ), ),
            12: ( build_prism_graph( 10, "Prism10" ), ),
            13: ( build_prism_graph( 11, "Prism11" ), ),
        }

    def __is_polyhedron_supported( self, face_stream ) -> str:
        """Checks if a polyhedron can be converted into a supported cell.
        If so, returns the name of the type. If not, the returned name will be empty.

        Args:
            face_stream (_type_): The polyhedron.

        Returns:
            str: The name of the supported type or an empty string.
        """
        cell_graph = build_face_to_face_connectivity_through_edges( face_stream, add_compatibility=True )
        if cell_graph.order() not in self.__reference_graphs:
            return ""
        for reference_graph in self.__reference_graphs[ cell_graph.order() ]:
            if networkx.is_isomorphic( reference_graph, cell_graph ):
                return str( reference_graph.name )
        return ""

    def __call__( self, ic: int ) -> int:
        """Checks if a vtk polyhedron cell can be converted into a supported GEOSX element.

        Args:
            ic (int): The index element.

        Returns:
            int: -1 if the polyhedron vtk element can be converted into a supported element type. The index otherwise.
        """
        global MESH
        assert MESH is not None, f"MESH global variable not initialized in worker process (PID: {multiprocessing.current_process().pid}). This should have been set by init_worker_mesh."
        if MESH.GetCellType( ic ) != VTK_POLYHEDRON:
            return -1
        pt_ids = vtkIdList()
        MESH.GetFaceStream( ic, pt_ids )
        face_stream = FaceStream.build_from_vtk_id_list( pt_ids )
        converted_type_name = self.__is_polyhedron_supported( face_stream )
        if converted_type_name:
            logger.debug( f"Polyhedron cell {ic} can be converted into \"{converted_type_name}\"" )
            return -1
        else:
            logger.debug(
                f"Polyhedron cell {ic} (in PID {multiprocessing.current_process().pid}) cannot be converted into any supported element."
            )
            return ic


def __action( vtk_input_file: str, options: Options ) -> Result:
    # Main process loads the mesh for its own use
    mesh = read_mesh( vtk_input_file )
    if mesh is None:
        logger.error( f"Main process failed to load mesh from {vtk_input_file}. Aborting." )
        # Return an empty/error result or raise an exception
        return Result( unsupported_std_elements_types=frozenset(), unsupported_polyhedron_elements=frozenset() )

    if hasattr( mesh, "GetDistinctCellTypesArray" ):
        cell_types_numpy = vtk_to_numpy( mesh.GetDistinctCellTypesArray() )
        cell_types = set( cell_types_numpy.tolist() )
    else:
        vtk_cell_types_obj = vtkCellTypes()
        mesh.GetCellTypes( vtk_cell_types_obj )
        cell_types = set( vtk_iter( vtk_cell_types_obj ) )

    supported_cell_types = {
        VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON, VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
        VTK_WEDGE
    }
    unsupported_std_elements_types = cell_types - supported_cell_types

    # Dealing with polyhedron elements.
    num_cells = mesh.GetNumberOfCells()
    polyhedron_converter = IsPolyhedronConvertible()

    unsupported_polyhedron_indices = []
    # Pass the vtk_input_file to the initializer
    with multiprocessing.Pool( processes=options.nproc, initializer=init_worker_mesh,
                               initargs=( vtk_input_file, ) ) as pool:  # Comma makes it a tuple
        generator = pool.imap_unordered( polyhedron_converter, range( num_cells ), chunksize=options.chunk_size )
        for cell_index_or_neg_one in tqdm( generator, total=num_cells, desc="Testing support for elements" ):
            if cell_index_or_neg_one != -1:
                unsupported_polyhedron_indices.append( cell_index_or_neg_one )

    return Result( unsupported_std_elements_types=frozenset( unsupported_std_elements_types ),
                   unsupported_polyhedron_elements=frozenset( unsupported_polyhedron_indices ) )


def action( vtk_input_file: str, options: Options ) -> Result:
    return __action( vtk_input_file, options )
