# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

import numpy as np
import numpy.typing as npt
from typing_extensions import Self

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


class TestsGeometryFunctions( unittest.TestCase ):

    def test_getChangeOfBasisMatrixToCanonic( self: Self ) -> None:
        """Test change of basis matrix using canonic basis."""
        obtained: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisCanon )
        # matrix where the columns are the vectors
        expected: npt.NDArray[ np.float64 ] = np.transpose( np.array( basisTo0 ) )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_getChangeOfBasisMatrix( self: Self ) -> None:
        """Test change of basis matrix format from basis vectors."""
        obtained: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisTo1 )
        expected: npt.NDArray[ np.float64 ] = np.array( [ [ 2.5, 4.5, -0.5 ], [ 0.5, 0.5, 0.5 ], [ -0.5, -0.5, 0.5 ] ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_computeCoordinatesInNewBasisIdentity( self: Self ) -> None:
        """Test calculation of coordinates of a vector in the same basis."""
        vec: npt.NDArray[ np.float64 ] = np.array( [ 2.0, 3.0, 4.0 ] )

        # get change of basis matrix
        changeOfBasisMatrix: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisCanon, basisCanon )
        obtained: npt.NDArray[ np.float64 ] = fcts.computeCoordinatesInNewBasis( vec, changeOfBasisMatrix )
        expected: npt.NDArray[ np.float64 ] = vec
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_computeCoordinatesInNewBasis( self: Self ) -> None:
        """Test calculation of coordinates of a vector in another basis."""
        vec: npt.NDArray[ np.float64 ] = np.array( [ 2.0, 3.0, 4.0 ] )

        # get change of basis matrix and the inverse
        changeOfBasisMatrix: npt.NDArray[ np.float64 ] = fcts.getChangeOfBasisMatrix( basisTo0, basisTo1 )
        obtained = fcts.computeCoordinatesInNewBasis( vec, changeOfBasisMatrix )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 16.5, 4.5, -0.5 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_computePlaneFrom3Points( self: Self ) -> None:
        """Test calculation of plane coefficients from 3 points."""
        pt1: npt.NDArray[ np.float64 ] = np.array( [ 1.0, 2.0, 1.0 ] )
        pt2: npt.NDArray[ np.float64 ] = np.array( [ 1.0, 1.0, 2.0 ] )
        pt3: npt.NDArray[ np.float64 ] = np.array( [ 3.0, 2.0, 2.0 ] )
        obtained: tuple[ float, float, float, float ] = fcts.computePlaneFrom3Points( pt1, pt2, pt3 )
        expected: tuple[ float, float, float, float ] = ( -1.0, 2.0, 2.0, -5.0 )
        self.assertSequenceEqual( obtained, expected )

    def test_getPointSideAgainstPlaneAssertion( self: Self ) -> None:
        """Test get point side against a plane."""
        planePt: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 0.0 ] )

        # assertion error - Point on the plane
        planeNormal: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 1.0 ] )
        self.assertRaises( AssertionError, fcts.getPointSideAgainstPlane, planePt, planePt, planeNormal )

    def test_getPointSideAgainstPlaneHorizontal( self: Self ) -> None:
        """Test get point side against a horizontal plane."""
        # horizontal plane
        planePt: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 0.0 ] )
        listPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
            np.array( [ 0.5, 0.5, 0.5 ] ),
            np.array( [ 0.5, 0.5, -0.5 ] ),
        ]
        planeNormal: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 1.0 ] )
        obtained: list[ bool ] = []
        for ptCoords in listPtsCoords:
            side: bool = fcts.getPointSideAgainstPlane( ptCoords, planePt, planeNormal )
            obtained += [ side ]
        expected: tuple[ bool, bool ] = ( True, False )
        self.assertSequenceEqual( obtained, expected )

    def test_getPointSideAgainstPlaneVertical( self: Self ) -> None:
        """Test get point side against a vertical plane."""
        # vertical plane
        planePt: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 0.0, 0.0 ] )
        listPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
            np.array( [ 0.5, 0.5, 0.5 ] ),
            np.array( [ -0.5, 0.5, 0.5 ] ),
        ]
        planeNormal: npt.NDArray[ np.float64 ] = np.array( [ 1.0, 0.0, 0.0 ] )
        obtained: list[ bool ] = []
        for ptCoords in listPtsCoords:
            side: bool = fcts.getPointSideAgainstPlane( ptCoords, planePt, planeNormal )
            obtained += [ side ]
        expected: tuple[ bool, bool ] = ( True, False )
        self.assertSequenceEqual( obtained, expected )

    def test_getCellSideAgainstPlaneRandom( self: Self ) -> None:
        """Test get cell side against a plane."""
        # random plane
        planePt = np.array( [ 125.58337, 1386.0465, -2782.502 ] )
        listCellPtsCoords = [
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
        planeNormal = np.array( [ 0.8660075, 0.0, -0.5000311 ] )
        obtained = []
        for cellPtsCoords in listCellPtsCoords:
            side: bool = fcts.getCellSideAgainstPlane( cellPtsCoords, planePt, planeNormal )
            obtained += [ side ]
        expected = ( True, False )
        self.assertSequenceEqual( obtained, expected )
