from collections import defaultdict
from dataclasses import dataclass
import networkx
from typing import Collection, Dict, FrozenSet, Iterable, List, Sequence, Tuple
from vtkmodules.vtkCommonCore import vtkIdList
from geos.mesh.utils.genericHelpers import vtkIter


@dataclass( frozen=True )
class Options:
    dummy: float


@dataclass( frozen=True )
class Result:
    dummy: float


def parseFaceStream( ids: vtkIdList ) -> Sequence[ Sequence[ int ] ]:
    """
    Parses the face stream raw information and converts it into a tuple of tuple of integers,
    each tuple of integer being the nodes of a face.
    :param ids: The raw vtk face stream.
    :return: The tuple of tuple of integers.
    """
    result = []
    it = vtkIter( ids )
    numFaces = next( it )
    try:
        while True:
            numNodes = next( it )
            tmp = []
            for i in range( numNodes ):
                tmp.append( next( it ) )
            result.append( tuple( tmp ) )
    except StopIteration:
        pass
    assert len( result ) == numFaces
    assert sum( map( len, result ) ) + len( result ) + 1 == ids.GetNumberOfIds()

    return tuple( result )


class FaceStream:
    """
    Helper class to manipulate the vtk face streams.
    """

    def __init__( self, data: Sequence[ Sequence[ int ] ] ):
        # self.__data contains the list of faces nodes, like it appears in vtk face streams.
        # Except that the additional size information is removed
        # in favor of the __len__ of the containers.
        self.__data: Sequence[ Sequence[ int ] ] = data

    @staticmethod
    def buildFromVtkIdList( ids: vtkIdList ):
        """
        Builds a FaceStream from the raw vtk face stream.
        :param ids: The vtk face stream.
        :return: A new FaceStream instance.
        """
        return FaceStream( parseFaceStream( ids ) )

    @property
    def faceNodes( self ) -> Iterable[ Sequence[ int ] ]:
        """
        Iterate on the nodes of all the faces.
        :return: An iterator.
        """
        return iter( self.__data )

    @property
    def numFaces( self ) -> int:
        """
        Number of faces in the face stream
        :return: An integer
        """
        return len( self.__data )

    @property
    def supportPointIds( self ) -> Collection[ int ]:
        """
        The list of all (unique) support points of the face stream, in no specific order.
        :return: The set of all the point ids.
        """
        tmp: List[ int ] = []
        for nodes in self.faceNodes:
            tmp += nodes
        return frozenset( tmp )

    @property
    def numSupportPoints( self ) -> int:
        """
        The number of unique support nodes of the polyhedron.
        :return: An integer.
        """
        return len( self.supportPointIds )

    def __getitem__( self, faceIndex ) -> Sequence[ int ]:
        """
        The support point ids for the `faceIndex` face.
        :param faceIndex: The face index (within the face stream).
        :return: A tuple containing all the point ids.
        """
        return self.__data[ faceIndex ]

    def flipFaces( self, faceIndices ):
        """
        Returns a new FaceStream instance with the face indices defined in faceIndices flipped.,
        :param faceIndices: The faces (local) indices to flip.
        :return: A newly created instance.
        """
        result = []
        for faceIndex, faceNodes in enumerate( self.__data ):
            result.append( tuple( reversed( faceNodes ) ) if faceIndex in faceIndices else faceNodes )
        return FaceStream( tuple( result ) )

    def dump( self ) -> Sequence[ int ]:
        """
        Returns the face stream awaited by vtk, but in a python container.
        The content can be used, once converted to a vtkIdList, to define another polyhedron in vtk.
        :return: The face stream in a python container.
        """
        result = [ len( self.__data ) ]
        for faceNodes in self.__data:
            result.append( len( faceNodes ) )
            result += faceNodes
        return tuple( result )

    def __repr__( self ):
        result = [ str( len( self.__data ) ) ]
        for faceNodes in self.__data:
            result.append( str( len( faceNodes ) ) )
            result.append( ", ".join( map( str, faceNodes ) ) )
        return ",\n".join( result )


def buildFaceToFaceConnectivityThroughEdges( faceStream: FaceStream, addCompatibility=False ) -> networkx.Graph:
    """
    Given a face stream/polyhedron, builds the connections between the faces.
    Those connections happen when two faces share an edge.
    :param faceStream: The face stream description of the polyhedron.
    :param addCompatibility: Two faces are considered compatible if their normals point in the same direction (inwards or outwards).
        If `addCompatibility=True`, we add a `compatible={"-", "+"}` flag on the edges
        to indicate that the two connected faces are compatible or not.
        If `addCompatibility=False`, non-compatible faces are simply not connected by any edge.
    :return: A graph which nodes are actually the faces of the polyhedron.
        Two nodes of the graph are connected if they share an edge.
    """
    edgesToFaceIndices: Dict[ FrozenSet[ int ], List[ int ] ] = defaultdict( list )
    for faceIndex, faceNodes in enumerate( faceStream.faceNodes ):
        # Each edge is defined by two nodes. We do a small trick to loop on consecutive points.
        faceIndices: Tuple[ int, int ]
        for faceIndices in zip( faceNodes, faceNodes[ 1: ] + ( faceNodes[ 0 ], ) ):
            edgesToFaceIndices[ frozenset( faceIndices ) ].append( faceIndex )
    # We are doing here some small validations w.r.t. the connections of the faces
    # which may only make sense in the context of numerical simulations.
    # As such, an error will be thrown in case the polyhedron is not closed.
    # So there may be a lack of absolute genericity, and the code may evolve if needed.
    for faceIndices in edgesToFaceIndices.values():
        assert len( faceIndices ) == 2
    # Computing the graph degree for validation
    degrees: Dict[ int, int ] = defaultdict( int )
    for faceIndices in edgesToFaceIndices.values():
        for faceIndex in faceIndices:
            degrees[ faceIndex ] += 1
    for faceIndex, degree in degrees.items():
        assert len( faceStream[ faceIndex ] ) == degree
    # Validation that there is one unique edge connecting two faces.
    faceIndicesToEdgeIndex = defaultdict( list )
    for edgeIndex, faceIndices in edgesToFaceIndices.items():
        faceIndicesToEdgeIndex[ frozenset( faceIndices ) ].append( edgeIndex )
    for edgeIndices in faceIndicesToEdgeIndex.values():
        assert len( edgeIndices ) == 1
    # Connecting the faces. Neighbor faces with consistent normals (i.e. facing both inward or outward)
    # will be connected. This will allow us to extract connected components with consistent orientations.
    # Another step will then reconcile all the components such that all the normals of the cell
    # will consistently point outward.
    graph = networkx.Graph()
    graph.add_nodes_from( range( faceStream.numFaces ) )
    for edge, faceIndices in edgesToFaceIndices.items():
        faceIndex0, faceIndex1 = faceIndices
        faceNodes0 = faceStream[ faceIndex0 ] + ( faceStream[ faceIndex0 ][ 0 ], )
        faceNodes1 = faceStream[ faceIndex1 ] + ( faceStream[ faceIndex1 ][ 0 ], )
        node0, node1 = edge
        order0 = 1 if faceNodes0[ faceNodes0.index( node0 ) + 1 ] == node1 else -1
        order1 = 1 if faceNodes1[ faceNodes1.index( node0 ) + 1 ] == node1 else -1
        # Same order of nodes means that the normals of the faces
        # are _not_ both in the same "direction" (inward or outward).
        if order0 * order1 == 1:
            if addCompatibility:
                graph.add_edge( faceIndex0, faceIndex1, compatible="-" )
        else:
            if addCompatibility:
                graph.add_edge( faceIndex0, faceIndex1, compatible="+" )
            else:
                graph.add_edge( faceIndex0, faceIndex1 )
    return graph
