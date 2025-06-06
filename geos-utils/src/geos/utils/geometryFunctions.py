# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Any

import numpy as np
import numpy.typing as npt
from geos.utils.PhysicalConstants import EPSILON

__doc__ = """Functions to permform geometry calculations."""


def getChangeOfBasisMatrix(
    basisFrom: tuple[ npt.NDArray[ np.floating[ Any ] ], npt.NDArray[ np.floating[ Any ] ],
                      npt.NDArray[ np.floating[ Any ] ] ],
    basisTo: tuple[ npt.NDArray[ np.floating[ Any ] ], npt.NDArray[ np.floating[ Any ] ],
                    npt.NDArray[ np.floating[ Any ] ] ],
) -> Any:
    """Get the change of basis matrix from basis basisFrom to basis basisTo.

    Let's define the basis (basisFrom) (b1, b2, b3) and basis (basisTo) (c1, c2, c3)
    where b1, b2, b3, and c1, c2, c3 are the vectors of the basis in the canonic form.
    This method returns the change of basis matrix P from basisFrom to basisTo.

    The coordinates of a vector Vb(vb1, vb2, vb3) from the basis B in the basis
    C is then Vc = P.Vb

    Args:
        basisFrom (tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]]): Origin basis
        basisTo (tuple[npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]], npt.NDArray[np.floating[Any]]]): Destination basis

    Returns:
        npt.NDArray[np.floating[Any]]: Change of basis matrix.
    """
    assert ( basisFrom[ 0 ].size == basisFrom[ 1 ].size ) and ( basisFrom[ 0 ].size == basisFrom[ 2 ].size ), (
        "Origin space vectors must have the same size." )

    assert ( basisTo[ 0 ].size == basisTo[ 1 ].size ) and ( basisTo[ 0 ].size == basisTo[ 2 ].size ), (
        "Destination space vectors must have the same size." )

    # build the matrices where columns are the vectors of the bases
    B = np.transpose( np.array( basisFrom ) )
    C = np.transpose( np.array( basisTo ) )
    # compute the inverse of C
    C1: npt.NDArray[ np.floating[ Any ] ] = np.linalg.inv( C )
    # get the change of basis matrix
    return np.dot( C1, B )


def computeCoordinatesInNewBasis( vec: npt.NDArray[ np.floating[ Any ] ],
                                  changeOfBasisMatrix: npt.NDArray[ np.floating[ Any ] ] ) -> Any:
    """Computes the coordinates of a matrix from a basis B in the new basis B'.

    Args:
        vec (npt.NDArray[np.floating[Any]]): Vector to compute the new coordinates
        changeOfBasisMatrix (npt.NDArray[np.floating[Any]]): Change of basis matrix

    Returns:
        npt.NDArray[np.floating[Any]]: The new coordinates of the matrix in the basis
        B'.
    """
    assert ( vec.size == changeOfBasisMatrix.shape[ 1 ] ), """The size of the vector
    must be equal to the number of columns of and change of basis matrix."""
    return np.dot( changeOfBasisMatrix, vec )


def computePlaneFrom3Points(
    pt1: npt.NDArray[ np.floating[ Any ] ],
    pt2: npt.NDArray[ np.floating[ Any ] ],
    pt3: npt.NDArray[ np.floating[ Any ] ],
) -> tuple[ float, float, float, float ]:
    """Compute the 4 coefficients of a plane equation.

    Let's defined a plane from the following equation: ax + by + cz + d = 0.
    This function determines a, b, c, d from 3 points of the plane.

    Args:
        pt1 (npt.NDArray[np.floating[Any]]): 1st point of the plane.
        pt2 (npt.NDArray[np.floating[Any]]): 2nd point of the plane.
        pt3 (npt.NDArray[np.floating[Any]]): 3rd point of the plane.

    Returns:
        tuple[float, float, float, float]: Tuple of the 4 coefficients.
    """
    # plane vectors
    v1: npt.NDArray[ np.floating[ Any ] ] = pt2 - pt1
    v2: npt.NDArray[ np.floating[ Any ] ] = pt3 - pt1
    # normal vector
    normal: npt.NDArray[ np.floating[ Any ] ] = np.cross( v1, v2 )
    assert np.linalg.norm( normal ) != 0, "Vectors of the plane must not be colinear."
    # first 3 coefficients of the plane equation
    a, b, c = normal
    # last coefficient of the plane equation
    d: float = -np.dot( normal, pt1 )
    return a, b, c, d


def getCellSideAgainstPlane(
    cellPtsCoords: npt.NDArray[ np.floating[ Any ] ],
    planePt: npt.NDArray[ np.floating[ Any ] ],
    planeNormal: npt.NDArray[ np.floating[ Any ] ],
) -> bool:
    """Get the side of input cell against input plane.

    Input plane is defined by a point on it and its normal vector.

    Args:
        cellPtsCoords (npt.NDArray[np.floating[Any]]): Coordinates of the vertices of
            the cell to get the side.
        planePt (npt.NDArray[np.floating[Any]]): Point on the plane.
        planeNormal (npt.NDArray[np.floating[Any]]): Normal vector to the plane.

    Returns:
        bool: True if the cell is in the direction of the normal vector,
        False otherwise.
    """
    assert ( len( cellPtsCoords ) > 1 ), "The list of points must contains more than one element"
    ptCenter: npt.NDArray[ np.floating[ Any ] ] = np.mean( cellPtsCoords, axis=0 )
    return getPointSideAgainstPlane( ptCenter, planePt, planeNormal )


def getPointSideAgainstPlane(
    ptCoords: npt.NDArray[ np.floating[ Any ] ],
    planePt: npt.NDArray[ np.floating[ Any ] ],
    planeNormal: npt.NDArray[ np.floating[ Any ] ],
) -> bool:
    """Get the side of input point against input plane.

    Input plane is defined by a point on it and its normal vector.

    Args:
        ptCoords (npt.NDArray[np.floating[Any]]): Coordinates of the point to get
            the side.
        planePt (npt.NDArray[np.floating[Any]]): Point on the plane.
        planeNormal (npt.NDArray[np.floating[Any]]): Normal vector to the plane.

    Returns:
        bool: True if the point is in the direction of the normal vector,
        False otherwise.
    """
    assert ptCoords.size == 3, "Point coordinates must have 3 components"
    assert planeNormal.size == 3, "Plane normal vector must have 3 components"
    assert planePt.size == 3, "Plane point must have 3 components"
    vec: npt.NDArray[ np.floating[ Any ] ] = ptCoords - planePt
    dot: float = np.dot( planeNormal, vec )
    assert abs( dot ) > EPSILON, "The point is on the plane."
    return dot > 0


def computeAngleFromPoints( pt1: npt.NDArray[ np.float64 ], pt2: npt.NDArray[ np.float64 ],
                            pt3: npt.NDArray[ np.float64 ] ) -> float:
    """Compute angle from 3 points.

    Args:
        pt1 (npt.NDArray[np.float64]): First point
        pt2 (npt.NDArray[np.float64]): Second point
        pt3 (npt.NDArray[np.float64]): Third point

    Returns:
        float: Angle
    """
    # compute vectors
    vec1: npt.NDArray[ np.float64 ] = pt1 - pt2
    vec2: npt.NDArray[ np.float64 ] = pt3 - pt2
    return computeAngleFromVectors( vec1, vec2 )


def computeAngleFromVectors(
    vec1: npt.NDArray[ np.float64 ],
    vec2: npt.NDArray[ np.float64 ],
) -> float:
    """Compute angle from 2 vectors.

    Args:
        vec1 (npt.NDArray[np.float64]): First vector
        vec2 (npt.NDArray[np.float64]): Second vector

    Returns:
        float: angle
    """
    assert abs( np.linalg.norm( vec1 ) ) > 0., "First vector cannot be null"
    assert abs( np.linalg.norm( vec2 ) ) > 0., "Second vector cannot be null"
    # normalization
    vec1_norm: npt.NDArray[ np.float64 ] = vec1 / np.linalg.norm( vec1 )
    vec2_norm: npt.NDArray[ np.float64 ] = vec2 / np.linalg.norm( vec2 )
    dot: float = np.dot( vec1, vec2 )
    det: float = np.linalg.det( ( vec1_norm, vec2_norm ) )
    # truncation due to numerical approximations
    if dot > 1.:
        dot = 1.
    if dot < -1.:
        dot = -1.
    teta: float = np.arccos( dot )
    if det < 0:
        teta = 2.0 * np.pi - teta
    return teta


def computeCosineFromVectors(
    vec1: npt.NDArray[ np.float64 ],
    vec2: npt.NDArray[ np.float64 ],
) -> float:
    """Compute cosine from 2 vectors.

    Args:
        vec1 (npt.NDArray[np.float64]): First vector
        vec2 (npt.NDArray[np.float64]): Second vector

    Returns:
        float: Cosine
    """
    assert abs( np.linalg.norm( vec1 ) ) > 0., "First vector cannot be null"
    assert abs( np.linalg.norm( vec2 ) ) > 0., "Second vector cannot be null"
    # normalization
    vec1_norm: npt.NDArray[ np.float64 ] = vec1 / np.linalg.norm( vec1 )
    vec2_norm: npt.NDArray[ np.float64 ] = vec2 / np.linalg.norm( vec2 )
    return np.dot( vec1_norm, vec2_norm )


def computeNormalFromPoints( pt1: npt.NDArray[ np.float64 ], pt2: npt.NDArray[ np.float64 ],
                             pt3: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    """Compute the normal of a plane defined from 3 points.

    Args:
        pt1 (npt.NDArray[np.float64]): First point
        pt2 (npt.NDArray[np.float64]): Second point
        pt3 (npt.NDArray[np.float64]): Third point

    Returns:
        npt.NDArray[np.float64]: Normal vector coordinates
    """
    # compute vectors
    vec1: npt.NDArray[ np.float64 ] = pt1 - pt2
    vec2: npt.NDArray[ np.float64 ] = pt3 - pt2
    return computeNormalFromVectors( vec1, vec2 )


def computeNormalFromVectors(
    vec1: npt.NDArray[ np.float64 ],
    vec2: npt.NDArray[ np.float64 ],
) -> npt.NDArray[ np.float64 ]:
    """Compute the normal of a plane defined from 2 vectors.

    Args:
        vec1 (npt.NDArray[np.float64]): First vector
        vec2 (npt.NDArray[np.float64]): Second vector

    Returns:
        npt.NDArray[np.float64]: Normal vector coordinates
    """
    assert abs( np.linalg.norm( vec1 ) ) > 0., "First and second points must be different"
    assert abs( np.linalg.norm( vec2 ) ) > 0., "Second and third points must be different"
    # normalization
    vec1_norm = vec1 / np.linalg.norm( vec1 )
    vec2_norm = vec2 / np.linalg.norm( vec2 )
    return np.cross( vec1_norm, vec2_norm )
