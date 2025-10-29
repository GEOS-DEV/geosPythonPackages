# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez

import numpy as np
import numpy.typing as npt
from unittest import TestCase
from typing.extensions import Self

from geos.utils.algebraFunctions import (
    getAttributeMatrixFromVector,
    getAttributeVectorFromMatrix,
)


class TestAttributeMatrixFromVector( TestCase ):
    """Tests for conversion from matrix to vector with GEOS convention."""

    def test_wrongInputVectorSize( self: Self ) -> None:
        """Test failure on incorrect input vector size."""
        emptyVector: npt.NDArray[ np.float64 ] = np.array( [] )
        with self.assertRaises( ValueError ):
            getAttributeMatrixFromVector( emptyVector )

    def test_vector3size( self: Self ) -> None:
        """Test for an input vector size of 3."""
        vector3 = np.arange( 1, 4 )
        expectedMatrix: npt.NDArray[ np.float64 ] = np.array( [ [ 1, 0, 0 ], [ 0, 2, 0 ], [ 0, 0, 3 ] ] )

        self.assertTrue( np.array_equal( expectedMatrix, getAttributeMatrixFromVector( vector3 ) ) )

    def test_vector6( self: Self ) -> None:
        """Test for an input vector size of 6."""
        vector6 = np.arange( 1, 7 )
        expectedMatrix = np.array( [ [ 1, 6, 5 ], [ 6, 2, 4 ], [ 5, 4, 3 ] ] )

        self.assertTrue( np.array_equal( expectedMatrix, getAttributeMatrixFromVector( vector6 ) ) )

    def test_vector9( self: Self ) -> None:
        """Test for an input vector size of 9."""
        vector9 = np.arange( 1, 10 )
        expectedMatrix = np.array( [ [ 1, 6, 5 ], [ 9, 2, 4 ], [ 8, 7, 3 ] ] )

        self.assertTrue( np.array_equal( expectedMatrix, getAttributeMatrixFromVector( vector9 ) ) )


class TestAttributeVectorFromMatrix( TestCase ):
    """Tests for conversion from vector to matrix with GEOS convention."""

    def setUp( self: Self ) -> None:
        """Set up parameters."""
        self.rdMatrix = np.arange( 1, 10 ).reshape( 3, 3 )
        self.expected: npt.NDArray[ np.float64 ] = np.array( [ 1, 5, 9, 6, 3, 2, 8, 7, 4 ] )

    def test_wrongInputMatrixShape( self ) -> None:
        """Test failure on empty input matrix."""
        emptyMatrix = np.array( [] )
        with self.assertRaises( ValueError ):
            getAttributeVectorFromMatrix( emptyMatrix, 3 )

    def test_wrongOutputSize( self: Self ) -> None:
        """Test failure on incorrect output size requested."""
        size = 4
        with self.assertRaises( ValueError ):
            getAttributeVectorFromMatrix( self.rdMatrix, size )

    def test_vecOutput( self: Self ) -> None:
        """Test correct output for requested size."""
        listSize = ( 3, 6, 9 )
        for size in listSize:
            with self.subTest( size ):
                expectedVector = np.array( self.expected[ :size ] )
                self.assertTrue( np.array_equal( expectedVector, getAttributeVectorFromMatrix( self.rdMatrix, size ) ) )
