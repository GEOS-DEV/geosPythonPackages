# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

import numpy as np
import numpy.typing as npt
from typing_extensions import Self

import geos.utils.algebraFunctions as fcts

matrix: npt.NDArray[ np.float64 ] = np.array( [ [ 11, 21, 31 ], [ 21, 22, 23 ], [ 31, 23, 33 ] ] )
vector: npt.NDArray[ np.float64 ] = np.array( [ 11, 22, 33, 23, 31, 21 ] )


class TestsFunctionsalgebraFunctions( unittest.TestCase ):

    def test_getAttributeMatrixFromVector( self: Self ) -> None:
        """Test conversion from Matrix to Vector for Geos stress."""
        obtained: npt.NDArray[ np.float64 ] = fcts.getAttributeMatrixFromVector( vector )
        self.assertTrue( np.all( np.equal( obtained, matrix ) ) )

    def test_getAttributeVectorFromMatrix( self: Self ) -> None:
        """Test conversion from Vector to Matrix for Geos stress."""
        obtained: npt.NDArray[ np.float64 ] = fcts.getAttributeVectorFromMatrix( matrix, 6 )
        self.assertTrue( np.all( np.equal( obtained, vector ) ) )
