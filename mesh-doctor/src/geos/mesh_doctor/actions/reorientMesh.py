import networkx
import numpy
from tqdm import tqdm
from typing import Iterator
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import ( VTK_POLYHEDRON, VTK_TRIANGLE, vtkCellArray, vtkPolyData, vtkPolygon,
                                            vtkUnstructuredGrid, vtkTetra )
from vtkmodules.vtkFiltersCore import vtkTriangleFilter
from geos.mesh_doctor.actions.vtkPolyhedron import FaceStream, buildFaceToFaceConnectivityThroughEdges
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.utils.genericHelpers import toVtkIdList


def __computeVolume( meshPoints: vtkPoints, faceStream: FaceStream ) -> float:
    """Computes the volume of a polyhedron element (defined by its faceStream).

    .. Note::
        The faces of the polyhedron are triangulated and the volumes of the tetrahedra
        from the barycenter to the triangular bases are summed.
        The normal of each face plays critical role,
        since the volume of each tetrahedron can be positive or negative.

    Args:
        meshPoints (vtkPoints): The mesh points, needed to compute the volume.
        faceStream (FaceStream): The vtk face stream.

    Returns:
        float: The volume of the element.
    """
    # Triangulating the envelope of the polyhedron for further volume computation.
    polygons = vtkCellArray()
    for faceNodes in faceStream.faceNodes:
        polygon = vtkPolygon()
        polygon.GetPointIds().SetNumberOfIds( len( faceNodes ) )
        # We use the same global points numbering for the polygons than for the input mesh.
        # There will be a lot of points in the poly data that won't be used as a support for the polygons.
        # But the algorithm deals with it, and it's actually faster (and easier) to do this
        # than to renumber and allocate a new fit-for-purpose set of points just for the polygons.
        for i, pointId in enumerate( faceNodes ):
            polygon.GetPointIds().SetId( i, pointId )
        polygons.InsertNextCell( polygon )
    polygonPolyData = vtkPolyData()
    polygonPolyData.SetPoints( meshPoints )
    polygonPolyData.SetPolys( polygons )

    f = vtkTriangleFilter()
    f.SetInputData( polygonPolyData )
    f.Update()
    triangles = f.GetOutput()
    # Computing the barycenter that will be used as the tip of all the tetra which mesh the polyhedron.
    # (The basis of all the tetra being the triangles of the envelope).
    # We could take any point, not only the barycenter.
    # But in order to work with figure of the same magnitude, let's compute the barycenter.
    tmpBarycenter = numpy.empty( ( faceStream.numSupportPoints, 3 ), dtype=float )
    for i, pointId in enumerate( faceStream.supportPointIds ):
        tmpBarycenter[ i, : ] = meshPoints.GetPoint( pointId )
    barycenter = [ tmpBarycenter[ :, 0 ].mean(), tmpBarycenter[ :, 1 ].mean(), tmpBarycenter[ :, 2 ].mean() ]
    # Looping on all the triangles of the envelope of the polyhedron, creating the matching tetra.
    # Then the volume of all the tetra are added to get the final polyhedron volume.
    cellVolume = 0.
    for i in range( triangles.GetNumberOfCells() ):
        triangle = triangles.GetCell( i )
        assert triangle.GetCellType() == VTK_TRIANGLE
        p = triangle.GetPoints()
        cellVolume += vtkTetra.ComputeVolume( barycenter, p.GetPoint( 0 ), p.GetPoint( 1 ), p.GetPoint( 2 ) )
    return cellVolume


def __selectAndFlipFaces( meshPoints: vtkPoints, colors: dict[ frozenset[ int ], int ],
                          faceStream: FaceStream ) -> FaceStream:
    """Given a polyhedra, given that we were able to paint the faces in two colors,
    we now need to select which faces/color to flip such that the volume of the element is positive.

    Args:
        meshPoints (vtkPoints): The mesh points, needed to compute the volume.
        colors (dict[ frozenset[ int ], int ]): Maps the nodes of each connected component (defined as a frozenset)
                                                to its color.
        faceStream (FaceStream): The face stream representing the polyhedron.

    Returns:
        FaceStream: The face stream that leads to a positive volume.
    """
    # Flipping either color 0 or 1.
    colorToNodes: dict[ int, list[ int ] ] = { 0: [], 1: [] }
    for connectedComponentsIndices, color in colors.items():
        colorToNodes[ color ] += connectedComponentsIndices
    # This implementation works even if there is one unique color.
    # Admittedly, there will be one face stream that won't be flipped.
    fs: tuple[ FaceStream,
               FaceStream ] = ( faceStream.flipFaces( colorToNodes[ 0 ] ), faceStream.flipFaces( colorToNodes[ 1 ] ) )
    volumes = __computeVolume( meshPoints, fs[ 0 ] ), __computeVolume( meshPoints, fs[ 1 ] )
    # We keep the flipped element for which the volume is largest
    # (i.e. positive, since they should be the opposite of each other).
    return fs[ numpy.argmax( volumes ) ]


def __reorientElement( meshPoints: vtkPoints, faceStreamIds: vtkIdList ) -> vtkIdList:
    """Considers a vtk face stream and flips the appropriate faces to get an element with normals directed outwards.

    Args:
        meshPoints (vtkPoints): The mesh points, needed to compute the volume.
        faceStreamIds (vtkIdList): The raw vtk face stream, not converted into a more practical python class.

    Returns:
        vtkIdList: The raw vtk face stream with faces properly flipped.
    """
    faceStream = FaceStream.buildFromVtkIdList( faceStreamIds )
    faceGraph = buildFaceToFaceConnectivityThroughEdges( faceStream, addCompatibility=True )
    # Removing the non-compatible connections to build the non-connected components.
    g = networkx.Graph()
    g.add_nodes_from( faceGraph.nodes )
    g.add_edges_from( filter( lambda uvd: uvd[ 2 ][ "compatible" ] == "+", faceGraph.edges( data=True ) ) )
    connectedComponents = tuple( networkx.connected_components( g ) )
    # Squashing all the connected nodes that need to receive the normal direction flip (or not) together.
    quotientGraph = networkx.algorithms.quotient_graph( faceGraph, connectedComponents )
    # Coloring the new graph lets us know how which cluster of faces need to eventually receive the same flip.
    # W.r.t. the nature of our problem (a normal can be directed inwards or outwards),
    # two colors should be enough to color the face graph.
    # `colors` maps the nodes of each connected component to its color.
    colors: dict[ frozenset[ int ], int ] = networkx.algorithms.greedy_color( quotientGraph )
    assert len( colors ) in ( 1, 2 )
    # We now compute the face stream which generates outwards normal vectors.
    flippedFaceStream = __selectAndFlipFaces( meshPoints, colors, faceStream )
    return toVtkIdList( flippedFaceStream.dump() )


def reorientMesh( mesh: vtkUnstructuredGrid, cellIndices: Iterator[ int ] ) -> vtkUnstructuredGrid:
    """Reorient the polyhedron elements such that they all have their normals directed outwards.

    Args:
        mesh (vtkUnstructuredGrid): The input vtk mesh.
        cellIndices (Iterator[ int ]): The indices of the cells to reorient.

    Returns:
        vtkUnstructuredGrid: The vtk mesh with the desired polyhedron cells directed outwards.
    """
    numCells = mesh.GetNumberOfCells()
    # Building an indicator/predicate from the list
    needsToBeReoriented = numpy.zeros( numCells, dtype=bool )
    for ic in cellIndices:
        needsToBeReoriented[ ic ] = True

    outputMesh = mesh.NewInstance()
    # I did not manage to call `outputMesh.CopyStructure(mesh)` because I could not modify the polyhedron in place.
    # Therefore, I insert the cells one by one...
    outputMesh.SetPoints( mesh.GetPoints() )
    setupLogger.info( "Reorienting the polyhedron cells to enforce normals directed outward." )
    with tqdm( total=needsToBeReoriented.sum(), desc="Reorienting polyhedra"
              ) as progressBar:  # For smoother progress, we only update on reoriented elements.
        for ic in range( numCells ):
            cell = mesh.GetCell( ic )
            cellType = cell.GetCellType()
            if cellType == VTK_POLYHEDRON:
                faceStreamIds = vtkIdList()
                mesh.GetFaceStream( ic, faceStreamIds )
                if needsToBeReoriented[ ic ]:
                    newFaceStreamIds = __reorientElement( mesh.GetPoints(), faceStreamIds )
                else:
                    newFaceStreamIds = faceStreamIds
                outputMesh.InsertNextCell( VTK_POLYHEDRON, newFaceStreamIds )
            else:
                outputMesh.InsertNextCell( cellType, cell.GetPointIds() )
            if needsToBeReoriented[ ic ]:
                progressBar.update( 1 )
    assert outputMesh.GetNumberOfCells() == mesh.GetNumberOfCells()
    return outputMesh
