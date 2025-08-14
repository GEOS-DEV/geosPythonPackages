from dataclasses import dataclass
import multiprocessing
import networkx
from numpy import ones
from tqdm import tqdm
from typing import Iterable, Mapping, Optional
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, vtkUnstructuredGrid, VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON,
                                            VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
                                            VTK_WEDGE )
from geos.mesh.doctor.actions.vtk_polyhedron import build_face_to_face_connectivity_through_edges, FaceStream
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import read_unstructured_grid
from geos.mesh.utils.genericHelpers import vtk_iter


@dataclass( frozen=True )
class Options:
    nproc: int
    chunk_size: int


@dataclass( frozen=True )
class Result:
    unsupported_std_elements_types: list[ str ]  # list of unsupported types
    unsupported_polyhedron_elements: frozenset[
        int ]  # list of polyhedron elements that could not be converted to supported std elements


# for multiprocessing, vtkUnstructuredGrid cannot be pickled. Let's use a global variable instead.
# Global variable to be set in each worker process
MESH: Optional[ vtkUnstructuredGrid ] = None


def init_worker( mesh_to_init: vtkUnstructuredGrid ) -> None:
    """Initializer for each worker process to set the global mesh."""
    global MESH
    MESH = mesh_to_init


supported_cell_types: set[ int ] = {
    VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON, VTK_PENTAGONAL_PRISM, VTK_POLYHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_VOXEL,
    VTK_WEDGE
}


class IsPolyhedronConvertible:

    def __init__( self ):

        def build_prism_graph( n: int, name: str ) -> networkx.Graph:
            """
            Builds the face to face connectivities (through edges) for prism graphs.
            :param n: The number of nodes of the basis (i.e. the pentagonal prims gets n = 5)
            :param name: A human-readable name for logging purpose.
            :return: A graph instance.
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
        """
        Checks if a polyhedron can be converted into a supported cell.
        If so, returns the name of the type. If not, the returned name will be empty.
        :param face_stream: The polyhedron.
        :return: The name of the supported type or an empty string.
        """
        cell_graph = build_face_to_face_connectivity_through_edges( face_stream, add_compatibility=True )
        for reference_graph in self.__reference_graphs[ cell_graph.order() ]:
            if networkx.is_isomorphic( reference_graph, cell_graph ):
                return str( reference_graph.name )
        return ""

    def __call__( self, ic: int ) -> int:
        """
        Checks if a vtk polyhedron cell can be converted into a supported GEOSX element.
        :param ic: The index element.
        :return: -1 if the polyhedron vtk element can be converted into a supported element type. The index otherwise.
        """
        global MESH
        assert MESH is not None
        if MESH.GetCellType( ic ) != VTK_POLYHEDRON:
            return -1
        pt_ids = vtkIdList()
        MESH.GetFaceStream( ic, pt_ids )
        face_stream = FaceStream.build_from_vtk_id_list( pt_ids )
        converted_type_name = self.__is_polyhedron_supported( face_stream )
        if converted_type_name:
            setup_logger.debug( f"Polyhedron cell {ic} can be converted into \"{converted_type_name}\"" )
            return -1
        else:
            setup_logger.debug( f"Polyhedron cell {ic} cannot be converted into any supported element." )
            return ic


def find_unsupported_std_elements_types( mesh: vtkUnstructuredGrid ) -> list[ str ]:
    if hasattr( mesh, "GetDistinctCellTypesArray" ):  # For more recent versions of vtk.
        unique_cell_types = set( vtk_to_numpy( mesh.GetDistinctCellTypesArray() ) )
    else:
        vtk_cell_types = vtkCellTypes()
        mesh.GetCellTypes( vtk_cell_types )
        unique_cell_types = set( vtk_iter( vtk_cell_types ) )
    result_values: set[ int ] = unique_cell_types - supported_cell_types
    results = [ f"Type {i}: {vtkCellTypes.GetClassNameFromTypeId( i )}" for i in frozenset( result_values ) ]
    return results


def find_unsupported_polyhedron_elements( mesh: vtkUnstructuredGrid, options: Options ) -> list[ int ]:
    # Dealing with polyhedron elements.
    num_cells: int = mesh.GetNumberOfCells()
    result = ones( num_cells, dtype=int ) * -1
    # Use the initializer to set up each worker process
    # Pass the mesh to the initializer
    with multiprocessing.Pool( processes=options.nproc, initializer=init_worker, initargs=( mesh, ) ) as pool:
        # Pass a mesh-free instance of the class to the workers.
        # The MESH global will already be set in each worker.
        generator = pool.imap_unordered( IsPolyhedronConvertible(), range( num_cells ), chunksize=options.chunk_size )
        for i, val in enumerate( tqdm( generator, total=num_cells, desc="Testing support for elements" ) ):
            result[ i ] = val

    return [ i for i in result if i > -1 ]


def mesh_action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    unsupported_std_elements_types: list[ str ] = find_unsupported_std_elements_types( mesh )
    unsupported_polyhedron_elements: list[ int ] = find_unsupported_polyhedron_elements( mesh, options )
    return Result( unsupported_std_elements_types=unsupported_std_elements_types,
                   unsupported_polyhedron_elements=frozenset( unsupported_polyhedron_elements ) )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = read_unstructured_grid( vtk_input_file )
    return mesh_action( mesh, options )
