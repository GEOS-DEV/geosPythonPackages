# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
import numpy as np
import numpy.typing as npt

__doc__ = """
GeosUtils module defines usefull methods to process GEOS outputs according to
GEOS conventions.
"""


def getAttributeMatrixFromVector( attrArray: npt.NDArray[ np.float64 ], ) -> npt.NDArray[ np.float64 ]:
    """Get the matrix of attribute values from the vector.
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

    Returns:
        npt.NDArray[np.float64]: matrix of attribute values

    Raises:
        ValueError: The input vector must be of size 3, 9 or 6 (symmetrical case).

    """
    if attrArray.size not in ( 3, 6, 9 ):
        raise ValueError( "Vectorial attribute must contain 3, 6 or 9 components." )

    # diagonal terms
    matrix: npt.NDArray[ np.float64 ] = np.diagflat( attrArray[ :3 ] )

    # shear stress components
    if attrArray.size == 6:
        matrix[ 0, 1 ] = attrArray[ 5 ] # v1
        matrix[ 1, 0 ] = attrArray[ 5 ]

        matrix[ 0, 2 ] = attrArray[ 4 ] # v5
        matrix[ 2, 0 ] = attrArray[ 4 ]

        matrix[ 1, 2 ] = attrArray[ 3 ] # v4
        matrix[ 2, 1 ] = attrArray[ 3 ]

    elif attrArray.size == 9:
        matrix[ 0, 1 ] = attrArray[ 5 ] # v1
        matrix[ 1, 0 ] = attrArray[ 8 ] # v9

        matrix[ 0, 2 ] = attrArray[ 4 ] # v5
        matrix[ 2, 0 ] = attrArray[ 7 ] # v8

        matrix[ 1, 2 ] = attrArray[ 3 ] # v4
        matrix[ 2, 1 ] = attrArray[ 6 ] # v7

    return matrix


def getAttributeVectorFromMatrix( attrMatrix: npt.NDArray[ np.float64 ], size: int ) -> npt.NDArray[ np.float64 ]:
    """Get the vector of attribute values from the matrix.

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
            \end{matrix}
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

    Returns:
        npt.NDArray[np.float64]: vector of attribute values

    Raises:
        ValueError: The output vector size requested can only be 3, 9 or 6.

    """
    attrArray: npt.NDArray[ np.float64 ] = np.full( size, np.nan )
    if size not in ( 3, 6, 9 ):
        raise ValueError( "Requested output size can only be 3, 9 or 6 (symmetrical case)." )

    # Diagonal terms
    attrArray[ :3 ] = np.diag( attrMatrix )

    # shear stress components
    if attrArray.size == 6:
        attrArray[ 3 ] = attrMatrix[ 1, 2 ]
        attrArray[ 4 ] = attrMatrix[ 0, 2 ]
        attrArray[ 5 ] = attrMatrix[ 0, 1 ]

    elif attrArray.size == 9:
        attrArray[ 3 ] = attrMatrix[ 1, 2 ]
        attrArray[ 4 ] = attrMatrix[ 0, 2 ]
        attrArray[ 5 ] = attrMatrix[ 0, 1 ]
        attrArray[ 6 ] = attrMatrix[ 2, 1 ]
        attrArray[ 7 ] = attrMatrix[ 2, 0 ]
        attrArray[ 8 ] = attrMatrix[ 1, 0 ]

    return attrArray


def getLocalToXYZTransformMatrix( localBasis ) -> npt.NDArray[ np.float64 ]:
    """Compute and return the transformation matrix to convert from local basis to XYZ basis.

    Args:
        localBasis (npt.NDArray[np.float64]): Local basis coordinates vectors in fonction of XYZ basis.

    Returns:
        npt.NDArray[ np.float64 ]: Local to XYZ transformation matrix.
    """
    if localBasis.shape != ( 3, 3 ):
        raise ValueError( "Expected a 3x3 matrix." )

    P: npt.NDArray[ np.float64 ] = np.transpose( localBasis )

    return P