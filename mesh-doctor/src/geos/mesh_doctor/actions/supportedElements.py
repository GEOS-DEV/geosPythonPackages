# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
import multiprocessing
import networkx
from numpy import ones
from tqdm import tqdm
from typing import Iterable, Mapping, Optional
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, vtkUnstructuredGrid, VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON,
                                            VTK_LINE, VTK_PENTAGONAL_PRISM, VTK_POLYGON, VTK_POLYHEDRON, VTK_PYRAMID,
                                            VTK_QUAD, VTK_TETRA, VTK_TRIANGLE, VTK_VERTEX, VTK_VOXEL, VTK_WEDGE )
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
    unsupportedStdElementsTypes: list[ str ]  # list of unsupported types
    unsupportedPolyhedronElements: frozenset[
        int ]  # list of polyhedron elements that could not be converted to supported std elements


# for multiprocessing, vtkUnstructuredGrid cannot be pickled. Let's use a global variable instead.
# Global variable to be set in each worker process
MESH: Optional[ vtkUnstructuredGrid ] = None


def initWorker( meshToInit: vtkUnstructuredGrid ) -> None:
    """Initializer for each worker process to set the global mesh."""
    global MESH
    MESH = meshToInit


supportedCellTypes: set[ int ] = {
    VTK_HEXAGONAL_PRISM, VTK_HEXAHEDRON, VTK_LINE, VTK_PENTAGONAL_PRISM, VTK_POLYGON, VTK_POLYHEDRON, VTK_PYRAMID,
    VTK_QUAD, VTK_TETRA, VTK_TRIANGLE, VTK_VERTEX, VTK_VOXEL, VTK_WEDGE
}


class IsPolyhedronConvertible:

    def __init__( self ) -> None:
        """Initializer for the IsPolyhedronConvertible class."""

        def buildPrismGraph( n: int, name: str ) -> networkx.Graph:
            """Builds the face to face connectivities (through edges) for prism graphs.

            Args:
                n (int): The number of nodes of the base (e.g., pentagonal prism gets n = 5).
                name (str): A human-readable name for logging purposes.

            Returns:
                networkx.Graph: A graph instance representing the prism.
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

    def __isPolyhedronSupported( self, faceStream: FaceStream ) -> str:
        """Checks if a polyhedron can be converted into a supported cell.

        Args:
            faceStream: The polyhedron.

        Returns:
            str: The name of the supported type or an empty string.
        """
        cellGraph = buildFaceToFaceConnectivityThroughEdges( faceStream, addCompatibility=True )
        for referenceGraph in self.__referenceGraphs[ cellGraph.order() ]:
            if networkx.is_isomorphic( referenceGraph, cellGraph ):
                return str( referenceGraph.name )
        return ""

    def __call__( self, ic: int ) -> int:
        """Check if a vtk polyhedron cell can be converted into a supported GEOS element.

        Args:
            ic (int): The index of the element.

        Returns:
            int: -1 if the polyhedron vtk element can be converted into a supported element type, the index otherwise.
        """
        global MESH
        assert MESH is not None
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
            setupLogger.debug( f"Polyhedron cell {ic} cannot be converted into any supported element." )
            return ic


def findUnsupportedStdElementsTypes( mesh: vtkUnstructuredGrid ) -> list[ str ]:
    """Find unsupported standard element types in the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.

    Returns:
        list[ str ]: List of unsupported element type descriptions.
    """
    if hasattr( mesh, "GetDistinctCellTypesArray" ):  # For more recent versions of vtk.
        uniqueCellTypes = set( vtk_to_numpy( mesh.GetDistinctCellTypesArray() ) )
    else:
        _vtkCellTypes = vtkCellTypes()
        mesh.GetCellTypes( _vtkCellTypes )
        uniqueCellTypes = set( vtkIter( _vtkCellTypes ) )
    resultValues: set[ int ] = uniqueCellTypes - supportedCellTypes
    results = [ f"Type {i}: {vtkCellTypes.GetClassNameFromTypeId( i )}" for i in frozenset( resultValues ) ]
    return results


def findUnsupportedPolyhedronElements( mesh: vtkUnstructuredGrid, options: Options ) -> list[ int ]:
    """Find unsupported polyhedron elements in the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The options for processing.

    Returns:
        list[ int ]: List of element indices for unsupported polyhedrons.
    """
    # Dealing with polyhedron elements.
    numCells: int = mesh.GetNumberOfCells()
    result = ones( numCells, dtype=int ) * -1
    # Use the initializer to set up each worker process
    # Pass the mesh to the initializer
    with multiprocessing.Pool( processes=options.nproc, initializer=initWorker, initargs=( mesh, ) ) as pool:
        # Pass a mesh-free instance of the class to the workers.
        # The MESH global will already be set in each worker.
        generator = pool.imap_unordered( IsPolyhedronConvertible(), range( numCells ), chunksize=options.chunkSize )
        for i, val in enumerate( tqdm( generator, total=numCells, desc="Testing support for elements" ) ):
            result[ i ] = val

    return [ i for i in result if i > -1 ]


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the supported elements check on a vtkUnstructuredGrid.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of the supported elements check.
    """
    unsupportedStdElementsTypes: list[ str ] = findUnsupportedStdElementsTypes( mesh )
    unsupportedPolyhedronElements: list[ int ] = findUnsupportedPolyhedronElements( mesh, options )
    return Result( unsupportedStdElementsTypes=unsupportedStdElementsTypes,
                   unsupportedPolyhedronElements=frozenset( unsupportedPolyhedronElements ) )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs the supported elements check on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the supported elements check.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
