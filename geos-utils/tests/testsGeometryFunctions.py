# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
import numpy as np
import numpy.typing as npt
from typing import Iterator
from dataclasses import dataclass
from itertools import combinations
import geos.utils.geometryFunctions as fcts

basisCanon: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                   npt.NDArray[ np.float64 ] ] = ( np.array( [ 1.0, 0.0, 0.0 ] ), np.array( [ 0.0, 1.0, 0.0 ] ),
                                                   np.array( [ 0.0, 0.0, 1.0 ] ) )
# destination basis according to canonic coordinates
basisTo0: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                 npt.NDArray[ np.float64 ] ] = ( np.array( [ 2.0, 3.0, 0.0 ] ), np.array( [ 4.0, 5.0, 0.0 ] ),
                                                 np.array( [ 0.0, 0.0, 1.0 ] ) )
basisTo1: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                 npt.NDArray[ np.float64 ] ] = ( np.array( [ 1.0, 1.0, 0.0 ] ), np.array( [ 0.0, 1.0, 1.0 ] ),
                                                 np.array( [ 1.0, 0.0, 1.0 ] ) )
basisTo2: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ],
                 npt.NDArray[ np.float64 ] ] = ( np.array( [ 0.0, 2.0, 0.0 ] ), np.array( [ -2.0, 0.0, 0.0 ] ),
                                                 np.array( [ 0.0, 0.0, 2.0 ] ) )


def test_getChangeOfBasisMatrixToCanonic() -> None:
    """Test change of basis matrix using canonic basis."""
    obtained: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisCanon )
    # matrix where the columns are the vectors
    expected: npt.NDArray[ np.float64 ] = np.transpose( np.array( basisTo0 ) )
    assert np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ),
                           equal_nan=True ), f"Expected array is {np.round( expected, 2 ).tolist()}"


def test_getChangeOfBasisMatrix() -> None:
    """Test change of basis matrix format from basis vectors."""
    obtained: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisTo1 )
    expected: npt.NDArray[ np.float64 ] = np.array( [ [ 2.5, 4.5, -0.5 ], [ 0.5, 0.5, 0.5 ], [ -0.5, -0.5, 0.5 ] ] )
    assert np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ),
                           equal_nan=True ), f"Expected array is {np.round( expected, 2 ).tolist()}"


def test_computeCoordinatesInNewBasisIdentity() -> None:
    """Test calculation of coordinates of a vector in the same basis."""
    vec: npt.NDArray[ np.float64 ] = np.array( [ 2.0, 3.0, 4.0 ] )

    # get change of basis matrix
    changeOfBasisMatrix: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisCanon, basisCanon )
    obtained: npt.NDArray[ np.float64 ] = fcts.computeCoordinatesInNewBasis( vec, changeOfBasisMatrix )
    expected: npt.NDArray[ np.float64 ] = vec
    assert np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ),
                           equal_nan=True ), f"Expected array is {np.round( expected, 2 ).tolist()}"


def test_computeCoordinatesInNewBasis() -> None:
    """Test calculation of coordinates of a vector in another basis."""
    vec: npt.NDArray[ np.float64 ] = np.array( [ 2.0, 3.0, 4.0 ] )

    # get change of basis matrix and the inverse
    changeOfBasisMatrix: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisTo1 )
    obtained = fcts.computeCoordinatesInNewBasis( vec, changeOfBasisMatrix )
    expected: npt.NDArray[ np.float64 ] = np.array( [ 16.5, 4.5, -0.5 ] )
    assert np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ),
                           equal_nan=True ), f"Expected array is {np.round( expected, 2 ).tolist()}"


def test_computePlaneFrom3Points() -> None:
    """Test calculation of plane coefficients from 3 points."""
    pt1: npt.NDArray[ np.float64 ] = np.array( [ 1.0, 2.0, 1.0 ] )
    pt2: npt.NDArray[ np.float64 ] = np.array( [ 1.0, 1.0, 2.0 ] )
    pt3: npt.NDArray[ np.float64 ] = np.array( [ 3.0, 2.0, 2.0 ] )
    obtained: tuple[ float, float, float, float ] = fcts.computePlaneFrom3Points( pt1, pt2, pt3 )
    expected: tuple[ float, float, float, float ] = ( -1.0, 2.0, 2.0, -5.0 )
    assert obtained == expected, f"Expected tuple is {expected}"


def test_getPointSideAgainstPlaneAssertion() -> None:
    """Test get point side against a plane."""
    planePt: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 0.0 ] )

    # assertion error - Point on the plane
    planeNormal: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 1.0 ] )
    with pytest.raises( AssertionError ):
        fcts.getPointSideAgainstPlane( planePt, planePt, planeNormal )


listPtsCoords_all = (
    [
        np.array( [ 0.5, 0.5, 0.5 ] ),
        np.array( [ 0.5, 0.5, -0.5 ] ),
    ],
    [
        np.array( [ 0.5, 0.5, 0.5 ] ),
        np.array( [ -0.5, 0.5, 0.5 ] ),
    ],
)
planePt_all = (
    np.array( [ 0.0, 0.0, 0.0 ] ),
    np.array( [ 0.0, 0.0, 0.0 ] ),
)
planeNormal_all = (
    np.array( [ 0.0, 0.0, 1.0 ] ),
    np.array( [ 1.0, 0.0, 0.0 ] ),
)
expected_all = (
    ( True, False ),
    ( True, False ),
)


@dataclass( frozen=True )
class TestCasePointSideAgainstPlane:
    """Test case."""
    __test__ = False
    #: list of points
    listPtsCoords: list[ npt.NDArray[ np.float64 ] ]
    #: plane point
    planePt: npt.NDArray[ np.float64 ]
    #: plane normal
    planeNormal: npt.NDArray[ np.float64 ]
    #: expected result
    expected: list[ bool ]


def __generate_PointSideAgainstPlane_test_data() -> Iterator[ TestCasePointSideAgainstPlane ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases
    """
    for listPtsCoords, planePt, planeNormal, expected in zip( listPtsCoords_all,
                                                              planePt_all,
                                                              planeNormal_all,
                                                              expected_all,
                                                              strict=True ):
        yield TestCasePointSideAgainstPlane( listPtsCoords, planePt, planeNormal, list( expected ) )


ids: tuple[ str, str ] = ( "Horizontal plane", "Vertical plane" )


@pytest.mark.parametrize( "test_case", __generate_PointSideAgainstPlane_test_data(), ids=ids )
def test_getPointSideAgainstPlane( test_case: TestCasePointSideAgainstPlane ) -> None:
    """Test get point side against a plane."""
    obtained: list[ bool ] = []
    for ptCoords in test_case.listPtsCoords:
        side: bool = fcts.getPointSideAgainstPlane( ptCoords, test_case.planePt, test_case.planeNormal )
        obtained += [ side ]
    assert obtained == test_case.expected, f"Expected tuple is {test_case.expected}"


def test_getCellSideAgainstPlaneRandom() -> None:
    """Test get cell side against a plane."""
    # random plane
    planePt: npt.NDArray[ np.float64 ] = np.array( [ 125.58337, 1386.0465, -2782.502 ] )
    listCellPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
        np.array( [
            [ 135.49551, 1374.7644, -2786.884 ],
            [ 125.58337, 1376.7441, -2782.502 ],
            [ 132.19525, 1382.2516, -2771.0508 ],
            [ 125.58337, 1386.0465, -2782.502 ],
        ] ),
        np.array( [
            [ 111.9148, 1377.0265, -2764.875 ],
            [ 132.19525, 1382.2516, -2771.0508 ],
            [ 125.58337, 1376.7441, -2782.502 ],
            [ 125.58337, 1386.0465, -2782.502 ],
        ] ),
    ]
    planeNormal: npt.NDArray[ np.float64 ] = np.array( [ 0.8660075, 0.0, -0.5000311 ] )
    obtained: list[ bool ] = []
    for cellPtsCoords in listCellPtsCoords:
        side: bool = fcts.getCellSideAgainstPlane( cellPtsCoords, planePt, planeNormal )
        obtained += [ side ]
    expected: list[ bool ] = [ True, False ]
    assert obtained == expected, f"Expected tuple is {expected}"


pts_all: tuple[ npt.NDArray[ np.float64 ], ...] = (
    np.array( [ 0.0, 0.0, 0.0 ] ),
    np.array( [ 1.0, 0.0, 0.0 ] ),
    np.array( [ 0.5, 0.5, 0.0 ] ),
    np.array( [ -0.5, 0.5, 0.0 ] ),
    np.array( [ -0.5, -0.5, 0.0 ] ),
    np.array( [ 0.5, -0.5, -1.0 ] ),
)
angleExp_all: tuple[ float, ...] = (
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
    0.,
)


@dataclass( frozen=True )
class TestCaseAngle:
    """Test case."""
    __test__ = False
    pt1: npt.NDArray[ np.float64 ]
    pt2: npt.NDArray[ np.float64 ]
    pt3: npt.NDArray[ np.float64 ]
    angleExp: float


def __generate_Angle_test_data() -> Iterator[ TestCaseAngle ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: Iterator on test cases
    """
    print( len( list( combinations( pts_all, 3 ) ) ) )
    for pts, angle in zip( list( combinations( pts_all, 3 ) ), angleExp_all, strict=True ):
        yield TestCaseAngle( pts[ 0 ], pts[ 1 ], pts[ 2 ], angle )


@pytest.mark.skip( "Test to fix" )
@pytest.mark.parametrize( "test_case", __generate_Angle_test_data() )
def test_computeAngleFromPoints( test_case: TestCaseAngle ) -> None:
    """Test computeAngleFromPoints method."""
    obs: float = fcts.computeAngleFromPoints( test_case.pt1, test_case.pt2, test_case.pt3 )
    assert obs == test_case.angleExp
    pass


@pytest.mark.skip( "Test to fix" )
@pytest.mark.parametrize( "test_case", __generate_Angle_test_data() )
def test_computeAngleFromVectors( test_case: TestCaseAngle ) -> None:
    """Test computeAngleFromVectors method."""
    vec1: npt.NDArray[ np.float64 ] = test_case.pt1 - test_case.pt2
    vec2: npt.NDArray[ np.float64 ] = test_case.pt3 - test_case.pt2
    obs: float = fcts.computeAngleFromVectors( vec1, vec2 )
    print( f"{test_case.__str__}: {obs}" )
    assert obs == test_case.angleExp


@pytest.mark.skip( "Test to fix" )
def test_computeNormalFromPoints() -> None:
    """Test computeNormalFromPoints method."""
    pass


@pytest.mark.skip( "Test to fix" )
def test_computeNormalFromVectors() -> None:
    """Test computeNormalFromVectors method."""
    pass
