# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
import os
from vtkmodules.vtkCommonCore import vtkIdList, vtkPoints
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_POLYHEDRON
from geos.mesh.utils.genericHelpers import toVtkIdList
from geos.mesh_doctor.actions.supportedElements import Options, action, meshAction
from geos.mesh_doctor.actions.vtkPolyhedron import FaceStream, parseFaceStream


dataRoot: str = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )
supportElementsFile: str = os.path.join( dataRoot, "supportedElements.vtu" )


def test_supportedElements() -> None:
    """Testing that the supported elements are properly detected as supported!

    Args:
        baseName (str): Supported elements are provided as standard elements or polyhedron elements.
    """
    options = Options( chunkSize=1, nproc=4 )
    result = action( supportElementsFile, options )
    assert not result.unsupportedStdElementsTypes
    assert not result.unsupportedPolyhedronElements


def makeDodecahedron() -> tuple[ vtkPoints, vtkIdList ]:
    """Returns the points and faces for a dodecahedron.

    This code was adapted from an official vtk example.

    Returns:
        The tuple of points and faces (as vtk instances).
    """
    # yapf: disable
    points = (
        (1.21412, 0, 1.58931),
        (0.375185, 1.1547, 1.58931),
        (-0.982247, 0.713644, 1.58931),
        (-0.982247, -0.713644, 1.58931),
        (0.375185, -1.1547, 1.58931),
        (1.96449, 0, 0.375185),
        (0.607062, 1.86835, 0.375185),
        (-1.58931, 1.1547, 0.375185),
        (-1.58931, -1.1547, 0.375185),
        (0.607062, -1.86835, 0.375185),
        (1.58931, 1.1547, -0.375185),
        (-0.607062, 1.86835, -0.375185),
        (-1.96449, 0, -0.375185),
        (-0.607062, -1.86835, -0.375185),
        (1.58931, -1.1547, -0.375185),
        (0.982247, 0.713644, -1.58931),
        (-0.375185, 1.1547, -1.58931),
        (-1.21412, 0, -1.58931),
        (-0.375185, -1.1547, -1.58931),
        (0.982247, -0.713644, -1.58931)
    )

    faces = (12,  # number of faces
             5, 0, 1, 2, 3, 4,  # number of ids on face, ids
             5, 0, 5, 10, 6, 1,
             5, 1, 6, 11, 7, 2,
             5, 2, 7, 12, 8, 3,
             5, 3, 8, 13, 9, 4,
             5, 4, 9, 14, 5, 0,
             5, 15, 10, 5, 14, 19,
             5, 16, 11, 6, 10, 15,
             5, 17, 12, 7, 11, 16,
             5, 18, 13, 8, 12, 17,
             5, 19, 14, 9, 13, 18,
             5, 19, 18, 17, 16, 15)
    # yapf: enable

    p = vtkPoints()
    p.Allocate( len( points ) )
    for coords in points:
        p.InsertNextPoint( coords )

    f = toVtkIdList( faces )

    return p, f


def test_dodecahedron() -> None:
    """Tests whether a dodecahedron is supported by GEOS or not.

    A dodecahedron has 12 pentagonal faces and is not supported by GEOS,
    which only supports hexahedra, tetrahedra, pyramids, wedges, and polygons.
    """
    points, faces = makeDodecahedron()
    mesh = vtkUnstructuredGrid()
    mesh.Allocate( 1 )
    mesh.SetPoints( points )
    mesh.InsertNextCell( VTK_POLYHEDRON, faces )

    # Test using meshAction directly instead of the internal __check function
    options = Options( nproc=1, chunkSize=1 )
    result = meshAction( mesh, options )
    # Dodecahedron (12 pentagonal faces) is not supported by GEOS
    assert set( result.unsupportedPolyhedronElements ) == { 0 }
    assert not result.unsupportedStdElementsTypes


def test_parseFaceStream() -> None:
    """Tests the parsing of a face stream for a dodecahedron."""
    _, faces = makeDodecahedron()
    result = parseFaceStream( faces )
    # yapf: disable
    expected = (
        (0, 1, 2, 3, 4),
        (0, 5, 10, 6, 1),
        (1, 6, 11, 7, 2),
        (2, 7, 12, 8, 3),
        (3, 8, 13, 9, 4),
        (4, 9, 14, 5, 0),
        (15, 10, 5, 14, 19),
        (16, 11, 6, 10, 15),
        (17, 12, 7, 11, 16),
        (18, 13, 8, 12, 17),
        (19, 14, 9, 13, 18),
        (19, 18, 17, 16, 15)
    )
    # yapf: enable
    assert result == expected
    faceStream = FaceStream.buildFromVtkIdList( faces )
    assert faceStream.numFaces == 12
    assert faceStream.numSupportPoints == 20
