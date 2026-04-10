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

from geos.mesh.utils.genericHelpers import ( computeTangents, computeNormals, getLocalBasisVectors, getTangentsVectors,
                                             getNormalVectors, convertAttributeFromLocalToXYZ )

from geos.utils.Errors import VTKError

# yapf: disable
pointsCoordsAll: list[ list[ list[ float ] ] ] = [
    [ [ 0., 0., 0. ], [ 0., 1., 0. ], [ 0., 2., 0. ], [ 0., 2., 1. ], [ 0., 1., 1. ], [ 0., 0., 1. ], ],
    [ [ 0., 0., 0. ], [ 0., 1., 0. ], [ 0., 2., 0. ], [ 0., 2., 1. ], [ 1., 1., 1. ], [ 0., 0., 1. ], ],
]
trianglesAll: list[ list[ tuple[ int, int, int ] ] ] = [
    [ ( 0, 1, 5 ), ( 1, 4, 5 ), ( 1, 2, 3 ), ( 3, 4, 1 ) ],
    [ ( 0, 1, 5 ), ( 1, 4, 5 ), ( 1, 2, 3 ), ( 3, 4, 1 ) ],
]

B_015: npt.NDArray[ np.float64 ] = np.array([
    [1.0, 0.0, 0.0],   # n
    [0.0, 1.0, 0.0],   # t1
    [0.0, 0.0, 1.0],   # t2
])

B_145: list[ npt.NDArray[ np.float64 ] ] = [
np.array([
    [1.0, 0.0, 0.0],   # n
    [0.0, 0.0, 1.0],   # t1
    [0.0, -1.0, 0.0],  # t2
]),
np.array([
    [ 0.577350, -0.577350, -0.577350],  # n
    [ 0.707107,  0.000000,  0.707107],  # t1
    [-0.408248, -0.816497,  0.408248],  # t2
])
]

B_123: npt.NDArray[ np.float64 ]  = np.array([
    [1.0, 0.0, 0.0],   # n
    [0.0, 1.0, 0.0],   # t1
    [0.0, 0.0, 1.0],   # t2
])

B_341: list[ npt.NDArray[ np.float64 ] ] = [
np.array([
    [1.0, 0.0, 0.0],   # n
    [0.0, -1.0, 0.0],   # t1
    [0.0, 0.0, -1.0],   # t2
]),
np.array([
    [ 0.577350,  0.577350, -0.577350],  # n
    [ 0.707107, -0.707107,  0.000000],  # t1
    [-0.408248, -0.408248, -0.816497],  # t2
])
]

expectedBasisAll: list[ npt.NDArray[ np.float64 ] ] = [
   np.array([B_015.T, B_145[0].T, B_123.T, B_341[0].T]),
   np.array([B_015.T, B_145[1].T, B_123.T, B_341[1].T]),
]

# Same attribute for all cells, test for vector size 3, 6, 9
attributes: list[ npt.NDArray[ np.float64 ] ] = [ np.arange( 1., 4., dtype=np.float64 ).reshape(1,3),
np.arange( 1., 7., dtype=np.float64 ).reshape(1,6), np.arange( 1., 10., dtype=np.float64 ).reshape(1,9)
]

# -2.309401, 2.828427,-0.816497
expectedAttributesXYZ: list[ list[ list[ npt.NDArray[ np.float64 ] ] ] ] = [[
        [
        np.array(  [ 1., 2., 3. ]),
        np.array( [ 1., 3., 2. ]),
        np.array( [ 1., 2., 3. ]),
        np.array( [ 1., 2., 3. ]), ],
        [
           np.array( [ 1., 2., 3., 4., 5., 6.]),
           np.array( [ 1., 3., 2., -4., 6. , -5.]),
           np.array( [ 1., 2., 3., 4., 5., 6.]),
           np.array( [ 1., 2., 3., 4., -5., -6.]) ],
        [

          np.array(       [1.,2.,3.,4.,5.,6.,7.,8.,9.]),
          np.array(  [1., 3., 2., -7., 6., -5., -4., 9., -8. ] ),
          np.array(   [1.,2.,3.,4.,5.,6.,7.,8.,9.] ),
          np.array(   [1.,2.,3., 4., -5., -6., 7., -8., -9.] )
        ]
    ],  # case 1
    [
        [
        np.array( [ 1., 2., 3. ] ),
         np.array( [1.99999814e+00, 2.00000124e+00, 2.00000042e+00, 5.77350037e-01, 1.15470000e-06,-8.16496453e-01] ),
           np.array( [ 1., 2. , 3. ] ),
           np.array([ 1.99999814, 1.50000093,2.50000134, 0.28867502, 0.70710768,-0.40824823 ])
           ],
           [
        np.array( [1.,2.,3.,4.,5.,6.] ),
        np.array(     [-2.66666418,7.00000433,1.66666919,-5.1961574,1.88561586,-4.89897872]),
        np.array(     [1.,2.,3.,4.,5.,6.]),
        np.array(     [2.54962629e-17,-4.50000279e+00,1.04999973e+01,-2.88675726e-01,-4.24263915e+00,-8.16496453e-01])
            ],
            [
        np.array([1.,2.,3.,4.,5.,6.,7.,8.,9.]),
        np.array([-3.66666325,8.50000526,1.16666991,-7.79423469,4.71404139,-7.34846808,-6.06218458,0.47140223,-4.89897872]),
        np.array([1.,2.,3.,4.,5.,6.,7.,8.,9.]),
        np.array([-0.99999907,-6.00000371,12.9999962,0.57734933,-3.53553321,0.40824823,-1.15470078,-7.77817236,-2.04124113])
    ],# case 2
]
]
# yapf: enable


class Options( IntEnum ):
    """Enum corresponding to data required for tests.

    - RAW : bare mesh
    - NORMALS : only normals are calculated
    - TANGENTS : normals and tangents are present in the mesh
    """
    RAW = 0
    NORMALS = 1
    TANGENTS = 2


@dataclass
class TriangulatedSurfaceTestCase:
    """Test case."""
    pointsCoords: list[ list[ float ] ]
    triangles: list[ tuple[ int, int, int ] ]
    attribute: list[ npt.NDArray ]
    # expectedNormals: npt.NDArray
    # expectedTangents: npt.NDArray
    expectedBasis: npt.NDArray
    expectedAttributeInXYZ: list[ list[ npt.NDArray ] ]
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

        elif self.options == Options.TANGENTS:
            mesh2 = computeNormals( polydata )
            self.mesh = computeTangents( mesh2 )

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
                                               expectedBasisAll[ i ], expectedAttributesXYZ[ i ], opt )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.TANGENTS, ) ) )
def test_getTangents( case: TriangulatedSurfaceTestCase ) -> None:
    """Test tangents getter."""
    tangents1: npt.NDArray[ np.float64 ]
    tangents2: npt.NDArray[ np.float64 ]

    tangents1, tangents2 = getTangentsVectors( case.mesh )

    assert np.allclose( tangents1, case.expectedBasis[ :, :, 1 ], rtol=1e-3 )
    assert np.allclose( tangents2, case.expectedBasis[ :, :, 2 ], rtol=1e-3 )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.RAW, ) ) )
def test_computeNormals( case: TriangulatedSurfaceTestCase ) -> None:
    """Test the computation of normals."""
    surfaceWithNormals = computeNormals( case.mesh )

    normals = vtk_to_numpy( surfaceWithNormals.GetCellData().GetNormals() )

    assert np.allclose( normals, case.expectedBasis[ :, :, 0 ], rtol=1e-3 )


@pytest.mark.parametrize( "case", __generateSurfacicTestCase( options=( Options.NORMALS, ) ) )
def test_getNormals( case: TriangulatedSurfaceTestCase ) -> None:
    """Test normals getter."""
    normals = getNormalVectors( case.mesh )

    assert np.allclose( normals, case.expectedBasis[ :, :, 0 ], rtol=1e-3 )


@pytest.mark.parametrize( "case",
                          __generateSurfacicTestCase( options=(
                              Options.RAW,
                              Options.NORMALS,
                              Options.TANGENTS,
                          ) ) )
def test_getLocalBasis( case: TriangulatedSurfaceTestCase ) -> None:
    """Test local basis getter."""
    basis = getLocalBasisVectors( case.mesh )

    assert np.linalg.norm( basis - case.expectedBasis ) < 1e-3


#########################################################################################


@pytest.fixture( scope="function" )
def emptySurface() -> vtkPolyData:
    """Generate and return an empty vtkPolyData for tests.

    Returns:
        vtkPolyData: empty vtkPolyData
    """
    return vtkPolyData()


def test_failingComputeNormals( emptySurface: vtkPolyData ) -> None:
    """Test VTK error raising of normals calculation."""
    with pytest.raises( VTKError ):
        computeNormals( emptySurface )


def test_failingGetTangents( emptySurface: vtkPolyData ) -> None:
    """Test error raising when getting the surface tangents."""
    with pytest.raises( VTKError ):
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
    basis: npt.NDArray[ np.float64 ]
    expectedVectorXYZ: npt.NDArray[ np.float64 ]


def __generateAttributeConversionTestCase() -> Iterator[ AttributeConversionTestCase ]:
    """Generator of test cases for the conversion of attributes from local to XYZ attributes."""
    cases: Iterator[ TriangulatedSurfaceTestCase ] = __generateSurfacicTestCase( options=( Options.RAW, ) )
    for nc, testcase in enumerate( cases ):
        if nc == 0:
            # Try vector size 3, 6 and 9
            for nvec, localAttribute in enumerate( attributes ):
                for ncell in range( testcase.mesh.GetNumberOfCells() ):

                    yield AttributeConversionTestCase(
                        localAttribute, testcase.expectedBasis[ ncell, :, : ].reshape( 1, 3, 3 ),
                        testcase.expectedAttributeInXYZ[ nvec ][ ncell ].reshape( 1, -1 ) )


@pytest.mark.parametrize( "testcase", __generateAttributeConversionTestCase() )
def test_convertAttributesToXYZ( testcase: AttributeConversionTestCase ) -> None:
    """Test the conversion of one cell attribute from local to canonic basis."""
    localAttr: npt.NDArray[ np.float64 ] = testcase.vector

    attrXYZ: npt.NDArray[ np.float64 ] = convertAttributeFromLocalToXYZ( localAttr, testcase.basis )
    assert np.allclose( attrXYZ, testcase.expectedVectorXYZ, rtol=1e-6 )
