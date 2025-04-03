# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
import numpy as np
import numpy.typing as npt

__doc__ = """
GeosUtils module defines usefull methods to process GEOS outputs according to
GEOS conventions.
"""


def getAttributeMatrixFromVector(
    attrArray: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    r"""Get the matrix of attribute values from the vector.

    Matrix to vector conversion is the following:

    * if input vector size is 3:
        .. math::

            (v1, v2, v3)   =>   \begin{bmatrix}
                                    v0 &  0 &  0 \\
                                    0 & v1 &  0 \\
                                    0 &  0 & v2
                                \end{bmatrix}

    * if input vector size is 6:
        .. math::

            (v1, v2, v3, v4, v5, v6)   =>   \begin{bmatrix}
                                                v1 & v6 & v5 \\
                                                v6 & v2 & v4 \\
                                                v5 & v4 & v3
                                            \end{bmatrix}


    .. WARNING:: Input vector must be of size 3 or 6.

    Args:
        attrArray (npt.NDArray[np.float64]): Vector of attribute values.

    Returns:
        npt.NDArray[np.float64]: matrix of attribute values

    """
    assert attrArray.size > 2, (
        "Vectorial attribute must contains at least " + "3 components."
    )
    # diagonal terms
    matrix: npt.NDArray[np.float64] = np.diagflat(attrArray[:3])
    # shear stress components
    if attrArray.size == 6:
        matrix[0, 1] = attrArray[5]
        matrix[1, 0] = attrArray[5]

        matrix[0, 2] = attrArray[4]
        matrix[2, 0] = attrArray[4]

        matrix[1, 2] = attrArray[3]
        matrix[2, 1] = attrArray[3]
    return matrix


def getAttributeVectorFromMatrix(
    attrMatrix: npt.NDArray[np.float64], size: int
) -> npt.NDArray[np.float64]:
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

    * otherwise:
        .. math::

            \begin{bmatrix}
                M00 & M01 & M02 \\
                M01 & M11 & M12 \\
                M02 & M12 & M22
            \end{bmatrix}
               =>   (M00, M11, M22, M12, M02, M01)

    Args:
        attrMatrix (npt.NDArray[np.float64]): Matrix of attribute values.
        size (int): Size of the final vector.

    Returns:
        npt.NDArray[np.float64]: vector of attribute values

    """
    attrArray: npt.NDArray[np.float64] = np.full(size, np.nan)
    # diagonal terms
    attrArray[:3] = np.diag(attrMatrix)
    # shear stress components
    if attrArray.size == 6:
        attrArray[3] = attrMatrix[1, 2]
        attrArray[4] = attrMatrix[0, 2]
        attrArray[5] = attrMatrix[0, 1]
    return attrArray
