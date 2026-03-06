# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2026 TotalEnergies.
# SPDX-FileContributor: Nicolas Pillardou, Paloma Martinez

import numpy as np
import numpy.typing as npt
from typing_extensions import Any


# ============================================================================
# STRESS TENSOR OPERATIONS
# ============================================================================
class StressTensor:
    """Utility class for stress tensor operations."""

    @staticmethod
    def buildFromArray( arr: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
        """Convert stress array to 3x3 tensor format.

        Args:
            arr ( npt.NDArray[np.float64]): Array to convert.

        Returns:
            npt.NDArray[np.float64]: 3x3 converted stress tensor.
        """
        n = arr.shape[ 0 ]
        tensors: npt.NDArray[ np.float64 ] = np.zeros( ( n, 3, 3 ), dtype=np.float64 )

        if arr.shape[ 1 ] == 6:  # Voigt notation
            tensors[ :, 0, 0 ] = arr[ :, 0 ]  # Sxx
            tensors[ :, 1, 1 ] = arr[ :, 1 ]  # Syy
            tensors[ :, 2, 2 ] = arr[ :, 2 ]  # Szz
            tensors[ :, 1, 2 ] = tensors[ :, 2, 1 ] = arr[ :, 3 ]  # Syz
            tensors[ :, 0, 2 ] = tensors[ :, 2, 0 ] = arr[ :, 4 ]  # Sxz
            tensors[ :, 0, 1 ] = tensors[ :, 1, 0 ] = arr[ :, 5 ]  # Sxy
        elif arr.shape[ 1 ] == 9:
            tensors = arr.reshape( ( -1, 3, 3 ) )
        else:
            raise ValueError( f"Unsupported stress shape: {arr.shape}" )

        return tensors

    @staticmethod
    def rotateToFaultFrame( stressTensorArr: npt.NDArray[ np.float64 ], normal: npt.NDArray[ np.float64 ],
                            tangent1: npt.NDArray[ np.float64 ],
                            tangent2: npt.NDArray[ np.float64 ] ) -> dict[ str, Any ]:
        """Rotate stress tensor to fault local coordinate system.

        Args:
            stressTensorArr (npt.NDArray[np.float64]): Stress tensor to rotate.
            normal (npt.NDArray[np.float64]): Surface normal vectors.
            tangent1 (npt.NDArray[np.float64]): Surface tangents vectors 1.
            tangent2 (npt.NDArray[np.float64])): Surface tangents vectors 2.

        Returns:
            dict[str, Any]: Dictionary containing local stress, normal stress, shear stress and strike and shear dip.
        """
        # Verify orthonormality
        if np.abs( np.linalg.norm( tangent1 ) - 1.0 ) >= 1e-10 or np.abs( np.linalg.norm( tangent2 ) - 1.0 ) >= 1e-10:
            raise ValueError( "Tangents expected to be normalized." )
        if np.abs( np.dot( normal, tangent1 ) ) >= 1e-10 or np.abs( np.dot( normal, tangent2 ) ) >= 1e-10:
            raise ValueError( "Tangents and Normals expected to be orthogonal." )

        # Rotation matrix: columns = local directions (n, t1, t2)
        R = np.column_stack( ( normal, tangent1, tangent2 ) )

        # Rotate tensor
        stressLocal = R.T @ stressTensorArr @ R

        # Traction on fault plane (normal = [1,0,0] in local frame)
        tractionLocal = stressLocal @ np.array( [ 1.0, 0.0, 0.0 ] )

        return {
            'stressLocal': stressLocal,
            'normalStress': tractionLocal[ 0 ],
            'shearStress': np.sqrt( tractionLocal[ 1 ]**2 + tractionLocal[ 2 ]**2 ),
            'shearStrike': tractionLocal[ 1 ],
            'shearDip': tractionLocal[ 2 ]
        }
