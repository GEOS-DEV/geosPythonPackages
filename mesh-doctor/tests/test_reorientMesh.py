from dataclasses import dataclass
import numpy
import pytest
from typing import Generator
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_POLYHEDRON
from geos.mesh_doctor.actions.reorientMesh import reorientMesh
from geos.mesh_doctor.actions.vtkPolyhedron import FaceStream
from geos.mesh.utils.genericHelpers import toVtkIdList, vtkIter


@dataclass( frozen=True )
class Expected:
    mesh: vtkUnstructuredGrid
    faceStream: FaceStream


def __buildTestMeshes() -> Generator[ Expected, None, None ]:
    """Builds test meshes for reorientMesh testing."""
    # Creating the support nodes for the polyhedron.
    # It has a C shape and is actually non-convex, non star-shaped.
    frontNodes = numpy.array( (
        ( 0, 0, 0 ),
        ( 3, 0, 0 ),
        ( 3, 1, 0 ),
        ( 1, 1, 0 ),
        ( 1, 2, 0 ),
        ( 3, 2, 0 ),
        ( 3, 3, 0 ),
        ( 0, 3, 0 ),
    ),
                              dtype=float )
    frontNodes = numpy.array( frontNodes, dtype=float )
    backNodes = frontNodes - ( 0., 0., 1. )

    n = len( frontNodes )

    points = vtkPoints()
    points.Allocate( 2 * n )
    for coords in frontNodes:
        points.InsertNextPoint( coords )
    for coords in backNodes:
        points.InsertNextPoint( coords )

    # Creating the polyhedron with faces all directed outward.
    faces: list[ tuple[ int, ... ] ] = []
    # Creating the side faces
    for i in range( n ):
        faces.append( ( i % n + n, ( i + 1 ) % n + n, ( i + 1 ) % n, i % n ) )
    # Creating the front faces
    faces.append( tuple( range( n ) ) )
    faces.append( tuple( reversed( range( n, 2 * n ) ) ) )
    faceStream = FaceStream( faces )

    # Creating multiple meshes, each time with one unique polyhedron,
    # but with different "face flip status".
    # First case, no face is flipped.
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( 1 )
    mesh.SetPoints( points )
    mesh.InsertNextCell( VTK_POLYHEDRON, toVtkIdList( faceStream.dump() ) )
    yield Expected( mesh=mesh, faceStream=faceStream )

    # Here, two faces are flipped.
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( 1 )
    mesh.SetPoints( points )
    mesh.InsertNextCell( VTK_POLYHEDRON, toVtkIdList( faceStream.flipFaces( ( 1, 2 ) ).dump() ) )
    yield Expected( mesh=mesh, faceStream=faceStream )

    # Last, all faces are flipped.
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( 1 )
    mesh.SetPoints( points )
    mesh.InsertNextCell( VTK_POLYHEDRON, toVtkIdList( faceStream.flipFaces( range( len( faces ) ) ).dump() ) )
    yield Expected( mesh=mesh, faceStream=faceStream )


@pytest.mark.parametrize( "expected", __buildTestMeshes() )
def test_reorientPolyhedron( expected: Expected ) -> None:
    """Tests reorientMesh on polyhedron elements."""
    outputMesh = reorientMesh( expected.mesh, range( expected.mesh.GetNumberOfCells() ) )
    assert outputMesh.GetNumberOfCells() == 1
    assert outputMesh.GetCell( 0 ).GetCellType() == VTK_POLYHEDRON
    faceStreamIds = vtkIdList()
    outputMesh.GetFaceStream( 0, faceStreamIds )
    # Note that the following makes a raw (but simple) check.
    # But one may need to be more precise some day,
    # since triangular faces (0, 1, 2) and (1, 2, 0) should be considered as equivalent.
    # And the current simpler check does not consider this case.
    assert tuple( vtkIter( faceStreamIds ) ) == expected.faceStream.dump()
