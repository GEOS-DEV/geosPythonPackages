# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt

__doc__ = """
The algebraFunctions module of `geos-utils` package defines methods to switch from vector <> matrix and conversely, following GEOS outputs conventions.
"""


def getAttributeMatrixFromVector( attrArray: npt.NDArray[ np.float64 ], ) -> npt.NDArray[ np.float64 ]:
    r"""Get the matrix of attribute values from the vector.

    Matrix to vector conversion is the following:

    * if input vector size is 3:
        .. math::

            (v1, v2, v3)   =>   \begin{bmatrix}
                                    v0 &  0 &  0 \\
                                    0 & v1 &  0 \\
                                    0 &  0 & v2
                                \end{bmatrix}

    * if input vector size is 9:
        .. math::

            (v1, v2, v3, v4, v5, v6, v7, v8, v9)   =>   \begin{bmatrix}
                                                            v1 & v6 & v5 \\
                                                            v9 & v2 & v4 \\
                                                            v8 & v7 & v3
                                                        \end{bmatrix}

    * if input vector size is 6 (symmetrical tensor):
        .. math::

            (v1, v2, v3, v4, v5, v6)   =>   \begin{bmatrix}
                                                v1 & v6 & v5 \\
                                                v6 & v2 & v4 \\
                                                v5 & v4 & v3
                                            \end{bmatrix}

    .. Note::
        In the case of 3 x 3 tensors, GEOS is currently only implemented for symmetrical cases.

    Args:
        attrArray (npt.NDArray[np.float64]): Vector of attribute values.

    Raises:
        ValueError: The input vector must be of size 3, 9 or 6 (symmetrical case).

    Returns:
        npt.NDArray[np.float64]: The matrix of attribute values.
    """
    if attrArray.shape[ 1 ] not in ( 3, 6, 9 ):
        raise ValueError( "Vectorial attribute must contain 3, 6 or 9 components." )

    # diagonal terms
    matrices: npt.NDArray[ np.float64 ] = np.empty( shape=( attrArray.shape[ 0 ], 3, 3 ) )

    #diag
    matrices[ :, 0, 0 ] = attrArray[ :, 0 ]  #
    matrices[ :, 1, 1 ] = attrArray[ :, 1 ]  #
    matrices[ :, 2, 2 ] = attrArray[ :, 2 ]  #

    # shear stress components
    if attrArray.shape[ 1 ] == 6:
        matrices[ :, 0, 1 ] = attrArray[ :, 5 ]  # v1
        matrices[ :, 1, 0 ] = attrArray[ :, 5 ]

        matrices[ :, 0, 2 ] = attrArray[ :, 4 ]  # v5
        matrices[ :, 2, 0 ] = attrArray[ :, 4 ]

        matrices[ :, 1, 2 ] = attrArray[ :, 3 ]  # v4
        matrices[ :, 2, 1 ] = attrArray[ :, 3 ]

    elif attrArray.shape[ 1 ] == 9:
        matrices[ :, 0, 1 ] = attrArray[ :, 5 ]  # v1
        matrices[ :, 1, 0 ] = attrArray[ :, 8 ]  # v9

        matrices[ :, 0, 2 ] = attrArray[ :, 4 ]  # v5
        matrices[ :, 2, 0 ] = attrArray[ :, 7 ]  # v8

        matrices[ :, 1, 2 ] = attrArray[ :, 3 ]  # v4
        matrices[ :, 2, 1 ] = attrArray[ :, 6 ]  # v7

    return matrices


def getAttributeVectorFromMatrix( attrMatrix: npt.NDArray[ np.float64 ], shape: tuple[int,int,int] ) -> npt.NDArray[ np.float64 ]:
    r"""Get the vector of attribute values from the matrix.

    Matrix to vector conversion is the following:

    * 3x3 diagonal matrix:
        .. math::

            \begin{bmatrix}
                M00 &   0 &   0 \\
                  0 & M11 &   0 \\
                  0 &   0 & M22
            \end{bmatrix}
               =>   (M00, M11, M22)

    * 3x3 Generic matrix:
        .. math::

            \begin{bmatrix}
                M00 & M01 & M02 \\
                M10 & M11 & M12 \\
                M20 & M21 & M22
            \end{bmatrix}
               =>   (M00, M11, M22, M12, M02, M01, M21, M20, M10)

    * Symmetric case
        .. math::

            \begin{bmatrix}
                M00 & M01 & M02 \\
                M01 & M11 & M12 \\
                M02 & M12 & M22
            \end{bmatrix}
               =>   (M00, M11, M22, M12, M02, M01)

    .. Note::
        In the case of 3 x 3 tensors, GEOS is currently only implemented for symmetrical cases.

    Args:
        attrMatrix (npt.NDArray[np.float64]): Matrix of attribute values.
        size (int): Size of the final vector. Values accepted are 3, 9 or 6.

    Raises:
        ValueError: The output vector size requested can only be 3, 9 or 6.
        ValueError: Input matrix shape must be (3,3).

    Returns:
        npt.NDArray[np.float64]: Vector of attribute values.
    """
    attrArray: npt.NDArray[ np.float64 ] = np.zeros( shape )
    if shape[1] not in ( 3, 6, 9 ):
        raise ValueError( "Requested output size can only be 3, 9 or 6 (symmetrical case)." )
    if attrMatrix.shape[1:] != ( 3, 3 ):
        raise ValueError( "Input matrix shape must be (3,3)." )

    # Diagonal terms
    attrArray[:, 0 ] = attrMatrix[:,0,0]
    attrArray[:, 1 ] = attrMatrix[:,1,1]
    attrArray[:, 2 ] = attrMatrix[:,2,2]

    # shear stress components
    if attrArray.size == 6:
        attrArray[:, 3 ] = attrMatrix[:, 1, 2 ]
        attrArray[:, 4 ] = attrMatrix[:, 0, 2 ]
        attrArray[:, 5 ] = attrMatrix[:, 0, 1 ]

    elif attrArray.size == 9:
        attrArray[:, 3 ] = attrMatrix[:, 1, 2 ]
        attrArray[:, 4 ] = attrMatrix[:, 0, 2 ]
        attrArray[:, 5 ] = attrMatrix[:, 0, 1 ]
        attrArray[:, 6 ] = attrMatrix[:, 2, 1 ]
        attrArray[:, 7 ] = attrMatrix[:, 2, 0 ]
        attrArray[:, 8 ] = attrMatrix[:, 1, 0 ]

    return attrArray
