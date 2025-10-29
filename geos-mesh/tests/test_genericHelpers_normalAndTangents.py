# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from enum import IntEnum
from typing_extensions import Self, Iterator
import numpy.typing as npt
import numpy as np
from dataclasses import dataclass, field

from vtkmodules.vtkCommonDataModel import ( vtkPolyData, vtkTriangle, vtkCellArray )
from vtkmodules.vtkCommonCore import vtkPoints
from vtkmodules.util.numpy_support import vtk_to_numpy

from geos.mesh.utils.genericHelpers import ( computeSurfaceTextureCoordinates, computeTangents, computeNormals,
                                             getLocalBasisVectors, getTangentsVectors, getNormalVectors,
                                             convertAttributeFromLocalToXYZForOneCell )

from geos.utils.Errors import VTKError

# yapf: disable
pointsCoordsAll: list[ list[ list[ float ] ] ] = [
    [ [ 0., 0., 0. ], [ 0., 1., 0. ], [ 0., 2., 0. ], [ 0., 2., 1. ], [ 0., 1., 1. ], [ 0., 0., 1. ], ],
    [ [ 0., 0., 0. ], [ 0., 1., 0. ], [ 0., 2., 0. ], [ 0., 2., 1. ], [ 1., 1., 1.5 ], [ 0., 0., 1. ], ],
]
trianglesAll: list[ list[ tuple[ int, int, int ] ] ] = [
    [ ( 0, 1, 5 ), ( 1, 4, 5 ), ( 1, 2, 3 ), ( 1, 4, 3 ) ],
    [ ( 0, 1, 5 ), ( 1, 4, 5 ), ( 1, 2, 3 ), ( 1, 4, 3 ) ],
]
expectedNormalsAll: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ [ 1., 0., 0. ], [ 1., 0., 0. ], [ 1., 0., 0. ], [ 1., 0., 0. ], ] ),
    np.array( [ [ 1., 0., 0. ], [ 0.7276069, -0.48507124, -0.48507124 ], [ 1., 0., 0. ],
                [ 0.7276069, 0.48507124, -0.48507124 ] ] ),
]
expectedTangentsAll: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ [ [ 0., 2., 0. ], [ -0., 2., 0. ], [ 0., 2., 0. ], [ 0., 2., 0. ] ],
                [ [ 0., 0., 2. ], [ 0., -0., 2. ], [ 0., 0., 2. ], [ 0., 0., 2. ],
                ] ] ),
    np.array( [ [ [ 0., 2., 0. ], [ 0.8301887, 2., -0.754717 ], [ 0., 2., 0. ], [ -0.8301887, 2., 0.754717 ] ],
                [ [ 0., 0., 2. ], [ 1.33623397, 0.14643663, 1.85791445 ], [ 0., 0., 2. ],
                  [ 1.33623397, -0.14643663, 1.85791445 ] ] ] ),
]
expectedTexturedCoordsAll: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ [ 0., 0. ], [ 0.5, 0. ], [ 1., 0. ], [ 1., 1. ], [ 0.5, 1. ], [ 0., 1. ],
    ] ),
    np.array( [ [ [ 0., 0. ], [ 0.5, 0. ], [ 1., 0. ], [ 1., 0.41509435 ], [ 0.5, 1. ], [ 0., 0.41509435 ] ],
    ] ),
]
# Same attribute for all cells, test for vector size 3, 6, 9
attributes: list[ npt.NDArray[ np.float64 ] ] = [ np.arange( 1., 4., dtype=np.float64 ), np.arange( 1., 7., dtype=np.float64 ), np.arange( 1., 10., dtype=np.float64 )
]
expectedAttributesXYZ: list[ list[ npt.NDArray[ np.float64 ] ] ] = [
    [
        np.array( [ [ 1., 8., 12. ], [ 1., 8., 12. ], [ 1., 8., 12. ], [ 1., 8., 12. ],
        ] ),
        np.array( [ [ 1., 8., 12., 16., 10., 12. ], [ 1., 8., 12., 16., 10., 12. ], [ 1., 8., 12., 16., 10., 12. ],
                    [ 1., 8., 12., 16., 10., 12. ] ] ),
        np.array( [ [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ], [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ],
                    [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ], [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ],
                    [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ], [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ] ] )
    ],  # case 1
    [
        np.array( [ [ 1., 8., 12. ], [ 7.26440201, 8.29962517, 11.73002787 ], [ 1., 8., 12. ],
                    [ 7.26440201, 8.29962517, 11.73002787 ] ] ),
        np.array( [ [ 1., 8., 12., 16., 10., 12. ],
                    [ 33.11015535, -1.70942051, -4.10667954, 3.96829788, 5.78481908, 18.33796323 ],
                    [ 1., 8., 12., 16., 10., 12. ],
                    [ 0.86370966, 16.88802688, 9.54231792, 17.62557587, 12.93534579, 16.64449814 ] ] ),
        np.array( [ [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ],
                    [ 41.16704654, -3.95432477, -9.91866643, 0.51321919, -0.39322437, 23.20275907, 13.51039649,
                        12.82015999, 23.3879596
                    ], [ 1., 8., 12., 16., 10., 12., 28., 16., 18. ],
                    [ -1.35966323, 18.70673795, 9.9469796, 14.59669037, 15.22437721, 25.39830602, 32.57499969,
                        14.01099303, 21.0552047
                    ] ] )
    ],  # case 2
]
# yapf: enable


class Options( IntEnum ):
    """Enum corresponding to data required for tests.

    - RAW : bare mesh
    - NORMALS : only normals are calculated
    - NORMALS_TEXTURED : normals and textured coordinates are computed
    - TANGENTS : normals and tangents are present in the mesh
    """
    RAW = 0
    NORMALS = 1
    NORMALS_TEXTURED = 2
    TANGENTS = 3


@dataclass
class TriangulatedSurfaceTestCase:
    """Test case."""
    pointsCoords: list[ list[ float ] ]
    triangles: list[ tuple[ int, int, int ] ]
    attribute: list[ npt.NDArray ]
    expectedNormals: npt.NDArray
    expectedTangents: npt.NDArray
    expectedTexturedCoords: npt.NDArray
    expectedAttributeInXYZ: list[ npt.NDArray ]
    options: Options
    mesh: vtkPolyData = field( init=False )

    def __post_init__( self: Self ) -> None:
        """Generate the mesh."""
        points: vtkPoints = vtkPoints()
        for coord in self.pointsCoords:
            points.InsertNextPoint( coord )

        triangles: vtkCellArray = vtkCellArray()
        for t in self.triangles:
            triangle = vtkTriangle()
            triangle.GetPointIds().SetId( 0, t[ 0 ] )
            triangle.GetPointIds().SetId( 1, t[ 1 ] )
            triangle.GetPointIds().SetId( 2, t[ 2 ] )
            triangles.InsertNextCell( triangle )

        polydata: vtkPolyData = vtkPolyData()
        polydata.SetPoints( points )
        polydata.SetPolys( triangles )

        # Compute additional properties depending on the tests options
        if self.options == Options.NORMALS:
            self.mesh = computeNormals( polydata )

        elif self.options == Options.NORMALS_TEXTURED:
            mesh: vtkPolyData = computeSurfaceTextureCoordinates( polydata )
            mesh2: vtkPolyData = computeNormals( mesh )
            self.mesh = mesh2

        elif self.options == Options.TANGENTS:
            mesh = computeSurfaceTextureCoordinates( polydata )
            mesh2 = computeNormals( mesh )
            mesh3: vtkPolyData = computeTangents( mesh2 )
            self.mesh = mesh3

        else:
            # Unknown cases and case 0
            self.mesh = polydata


def __generateSurfacicTestCase( options: tuple[ Options, ...] ) -> Iterator[ TriangulatedSurfaceTestCase ]:
    """Generate test cases with different options.

    Args:
        options (tuple[Options]): Requested additional feature.

    Yields:
        Iterator[ TriangulatedSurfaceTestCase ]: Test case containing mesh with requested optional features and expected values.
    """
    for opt in options:
        for i in range( len( pointsCoordsAll ) ):
            yield TriangulatedSurfaceTestCase( pointsCoordsAll[ i ], trianglesAll[ i ], attributes,
                                               expectedNormalsAll[ i ], expectedTangentsAll[ i ],
                                               expectedTexturedCoordsAll[ i ], expectedAttributesXYZ[ i ], opt )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.RAW, ) ) )
def test_computeTextureCoords( case: TriangulatedSurfaceTestCase ) -> None:
    """Test the computation of texture coordinates."""
    stc: vtkPolyData = computeSurfaceTextureCoordinates( case.mesh )
    texturedMap: npt.NDArray[ np.float64 ] = vtk_to_numpy( stc.GetPointData().GetArray( "Texture Coordinates" ) )
    assert np.allclose( texturedMap, case.expectedTexturedCoords )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.NORMALS_TEXTURED, ) ) )
def test_computeTangents( case: TriangulatedSurfaceTestCase ) -> None:
    """Test the computation of tangents."""
    surfaceWithTangents: vtkPolyData = computeTangents( case.mesh )
    tangents: npt.NDArray[ np.float64 ] = vtk_to_numpy( surfaceWithTangents.GetCellData().GetTangents() )

    assert np.allclose( tangents, case.expectedTangents[ 0 ] )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.TANGENTS, ) ) )
def test_getTangents( case: TriangulatedSurfaceTestCase ) -> None:
    """Test tangents getter."""
    tangents1: npt.NDArray[ np.float64 ]
    tangents2: npt.NDArray[ np.float64 ]

    tangents1, tangents2 = getTangentsVectors( case.mesh )

    assert np.allclose( tangents1, case.expectedTangents[ 0 ], rtol=1e-3 )
    assert np.allclose( tangents2, case.expectedTangents[ 1 ], rtol=1e-3 )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.RAW, ) ) )
def test_computeNormals( case: TriangulatedSurfaceTestCase ) -> None:
    """Test the computation of normals."""
    surfaceWithNormals = computeNormals( case.mesh )

    normals = vtk_to_numpy( surfaceWithNormals.GetCellData().GetNormals() )

    assert np.allclose( normals, case.expectedNormals, rtol=1e-3 )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.NORMALS, ) ) )
def test_getNormals( case: TriangulatedSurfaceTestCase ) -> None:
    """Test normals getter."""
    normals = getNormalVectors( case.mesh )

    assert np.allclose( normals, case.expectedNormals, rtol=1e-3 )


@pytest.mark.parametrize( "case",
                          __generateSurfacicTestCase( options=(
                              Options.RAW,
                              Options.NORMALS,
                              Options.TANGENTS,
                          ) ) )
def test_getLocalBasis( case: TriangulatedSurfaceTestCase ) -> None:
    """Test local basis getter."""
    normals, tangents1, tangents2 = getLocalBasisVectors( case.mesh )

    assert np.allclose( normals, case.expectedNormals, rtol=1e-3 )
    assert np.allclose( tangents1, case.expectedTangents[ 0 ], rtol=1e-3 )
    assert np.allclose( tangents2, case.expectedTangents[ 1 ], rtol=1e-3 )


#########################################################################################


@pytest.fixture( scope="function" )
def emptySurface() -> vtkPolyData:
    """Generate and return an empty vtkPolyData for tests.

    Returns:
        vtkPolyData: empty vtkPolyData
    """
    return vtkPolyData()


def test_failingComputeSurfaceTextureCoords( emptySurface: vtkPolyData ) -> None:
    """Test VTK error raising of texture coordinate calculation."""
    with pytest.raises( VTKError ):
        computeSurfaceTextureCoordinates( emptySurface )


def test_failingComputeTangents( emptySurface: vtkPolyData ) -> None:
    """Test VTK error raising during tangent calculation."""
    with pytest.raises( VTKError ):
        computeTangents( emptySurface )


def test_failingComputeNormals( emptySurface: vtkPolyData ) -> None:
    """Test VTK error raising of normals calculation."""
    with pytest.raises( VTKError ):
        computeNormals( emptySurface )


def test_failingGetTangents( emptySurface: vtkPolyData ) -> None:
    """Test error raising when getting the surface tangents."""
    with pytest.raises( ValueError ):
        getTangentsVectors( emptySurface )


def test_failingGetNormals( emptySurface: vtkPolyData ) -> None:
    """Test error raising when getting the surface normals."""
    with pytest.raises( ValueError ):
        getNormalVectors( emptySurface )


###############################################################


@dataclass( frozen=True )
class AttributeConversionTestCase:
    """Test case for attribute conversion from local basis to XYZ basis for one cell."""
    vector: npt.NDArray[ np.float64 ]
    normal: npt.NDArray[ np.float64 ]
    tangent1: npt.NDArray[ np.float64 ]
    tangent2: npt.NDArray[ np.float64 ]
    expectedVectorXYZ: npt.NDArray[ np.float64 ]


def __generateAttributeConversionTestCase() -> Iterator[ AttributeConversionTestCase ]:
    """Generator of test cases for the conversion of attributes from local to XYZ attributes."""
    cases: Iterator[ TriangulatedSurfaceTestCase ] = __generateSurfacicTestCase( options=( Options.RAW, ) )
    for nc, testcase in enumerate( cases ):
        if nc == 0:
            # Try vector size 3, 6 and 9
            for nvec, localAttribute in enumerate( attributes ):
                for ncell in range( testcase.mesh.GetNumberOfCells() ):

                    yield AttributeConversionTestCase( localAttribute, testcase.expectedNormals[ ncell ],
                                                       testcase.expectedTangents[ 0 ][ ncell ],
                                                       testcase.expectedTangents[ 1 ][ ncell ],
                                                       testcase.expectedAttributeInXYZ[ nvec ][ ncell ] )


@pytest.mark.parametrize( "testcase", __generateAttributeConversionTestCase() )
def test_convertAttributesToXYZ( testcase: AttributeConversionTestCase ) -> None:
    """Test the conversion of one cell attribute from local to canonic basis."""
    localAttr: npt.NDArray[ np.float64 ] = testcase.vector

    attrXYZ: npt.NDArray[ np.float64 ] = convertAttributeFromLocalToXYZForOneCell(
        localAttr, ( testcase.normal, testcase.tangent1, testcase.tangent2 ) )
    assert np.allclose( attrXYZ, testcase.expectedVectorXYZ, rtol=1e-6 )
