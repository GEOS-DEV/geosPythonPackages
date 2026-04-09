# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Any

import numpy as np
import numpy.typing as npt

__doc__ = """Functions to permform geometry calculations."""

CANONICAL_BASIS_3D: npt.NDArray[ np.float64 ] = np.array( [ [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ], [ 0.0, 0.0, 1.0 ] ] )

# for batch cross product
EPS = np.zeros( ( 3, 3, 3 ), dtype=int )
EPS[ 0, 1, 2 ] = EPS[ 1, 2, 0 ] = EPS[ 2, 0, 1 ] = 1
EPS[ 0, 2, 1 ] = EPS[ 2, 1, 0 ] = EPS[ 1, 0, 2 ] = -1


# (n,x,x) opertors
def _normalize( arr : npt.NDArray[ np.float64 ]) -> npt.NDArray[ np.float64 ]:
    """N generatlization of normalization."""
    return np.einsum( 'ni,n->ni', arr, 1 / np.linalg.norm( arr, axis=1 ) )

def _transposeProd( basisTo: npt.NDArray[ np.float64 ], basisFrom : npt.NDArray[ np.float64 ])-> npt.NDArray[ np.float64 ]:
    """N generalization of transpose product."""
    return np.einsum( 'nlj,nkj->nlk', basisTo, basisFrom )

def _cross( vec1 : npt.NDArray[ np.float64 ],  vec2 : npt.NDArray[ np.float64 ]) -> npt.NDArray[ np.float64 ]:
    """N generatlization of cross product."""
    return np.einsum( 'ijk,nj,nk->ni', EPS, vec1, vec2 )

def _normBasis( basis: npt.NDArray[ np.float64 ] ) -> npt.NDArray[ np.float64 ]:
    """Norm and orthonormalize basis vector wise."""
    Q, _ = np.linalg.qr( basis )
    det = np.linalg.det( Q )
    Q[ det < 0 ] *= -1

    return Q

def getChangeOfBasisMatrix(
    basisFrom: npt.NDArray[ np.float64 ],
    basisTo: npt.NDArray[ np.float64 ],
) -> Any:
    """Get the change of basis matrix from basis basisFrom to basis basisTo.

    Let's define the basis (basisFrom) (b1, b2, b3) and basis (basisTo) (c1, c2, c3)
    where b1, b2, b3, and c1, c2, c3 are the vectors of the basis in the canonic form.
    This method returns the change of basis matrix P from basisFrom to basisTo.

    The coordinates of a vector Vb(vb1, vb2, vb3) from the basis B in the basis
    C is then Vc = P.Vb

    Args:
        basisFrom (tuple[npt.NDArray[np.float64 npt.NDArray[np.float64 npt.NDArray[np.float64): Origin basis
        basisTo (tuple[npt.NDArray[np.float64 npt.NDArray[np.float64 npt.NDArray[np.float64): Destination basis

    Returns:
        npt.NDArray[np.float64 Change of basis matrix.
    """
    basisFrom = _normBasis( basisFrom )
    basisTo = _normBasis( basisTo )

    assert ( basisFrom.shape[ 1 ] == basisFrom.shape[ 2 ] ), (
        f"Origin space vectors must have the same size. shape: {basisFrom.shape}" )

    if len( basisTo.shape ) < len( basisFrom.shape ):
        basisTo = np.repeat( basisTo[ None, : ], basisFrom.shape[ 0 ], axis=0 )
    assert ( basisTo.shape[ 1 ] == basisTo.shape[ 2 ] ), ( "Destination space vectors must have the same size." )

    # build the matrices where columns are the vectors of the bases
    # B = np.transpose( np.array( basisFrom ) )
    # C = np.transpose( np.array( basisTo ) )
    # no need to compute the inverse of C as it is orthonormal checked - transpose is enough
    assert np.linalg.norm(
        _transposeProd(basisTo,basisTo)
        np.repeat( np.eye( 3 )[ None, : ], basisFrom.shape[ 0 ], axis=0 ) ) < 1e-6
    # get the change of basis matrix
    return _transposeProd(basisTo,basisFrom)


# def computeCoordinatesInNewBasis( vec: npt.NDArray[ np.float64 ],
#                                   changeOfBasisMatrix: npt.NDArray[ np.float64 ] ) -> Any:
#     """Computes the coordinates of a matrix from a basis B in the new basis B'.

#     Args:
#         vec (npt.NDArray[np.float64: Vector to compute the new coordinates
#         changeOfBasisMatrix (npt.NDArray[np.float64: Change of basis matrix

#     Returns:
#         npt.NDArray[np.float64 The new coordinates of the matrix in the basis
#         B'.
#     """
#     assert ( vec.shape[ 1 ] == changeOfBasisMatrix.shape[ 1 ] ), """The size of the vector
#     must be equal to the number of columns of and change of basis matrix."""
#     return np.einsum('nij,ni->ni' ,changeOfBasisMatrix, vec )

# def computePlaneFrom3Points(
#     pt1: npt.NDArray[ np.float64 ],
#     pt2: npt.NDArray[ np.float64 ],
#     pt3: npt.NDArray[ np.float64 ],
# ) -> tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ]:
#     """Compute the 4 coefficients of a plane equation.

#     Let's defined a plane from the following equation: ax + by + cz + d = 0.
#     This function determines a, b, c, d from 3 points of the plane.

#     Args:
#         pt1 (npt.NDArray[np.float64: 1st point of the plane.
#         pt2 (npt.NDArray[np.float64: 2nd point of the plane.
#         pt3 (npt.NDArray[np.float64: 3rd point of the plane.

#     Returns:
#         tuple[float, float, float, float]: Tuple of the 4 coefficients.
#     """
#     assert pt1.shape[0] == pt2.shape[0] and pt2.shape[0] == pt3.shape[0]

#     # plane vectors
#     v1: npt.NDArray[ np.float64 ] = pt2 - pt1
#     v2: npt.NDArray[ np.float64 ] = pt3 - pt1
#     # normal vector
#     normal: npt.NDArray[ np.float64 ] = np.einsum('ijk,nj,nk->ni', EPS, v1, v2)
#     assert np.linalg.norm( normal ) != 0, "Vectors of the plane must not be colinear."
#     # first 3 coefficients of the plane equation
#     a, b, c = np.unstack( normal, axis=1 )
#     # last coefficient of the plane equation
#     d: float = -np.einsum('ni,ni->n', normal, pt1 )
#     return a, b, c, d

# def getCellSideAgainstPlane(
#     cellPtsCoords: npt.NDArray[ np.float64 ],
#     planePt: npt.NDArray[ np.float64 ],
#     planeNormal: npt.NDArray[ np.float64 ],
# ) -> bool:
#     """Get the side of input cell against input plane.

#     Input plane is defined by a point on it and its normal vector.

#     Args:
#         cellPtsCoords (npt.NDArray[np.float64: Coordinates of the vertices of
#             the cell to get the side.
#         planePt (npt.NDArray[np.float64: Point on the plane.
#         planeNormal (npt.NDArray[np.float64: Normal vector to the plane.

#     Returns:
#         bool: True if the cell is in the direction of the normal vector,
#         False otherwise.
#     """
#     assert ( len( cellPtsCoords.shape[0] ) > 1 ), "The list of points must contains more than one element"
#     ptCenter: npt.NDArray[ np.float64 ] = np.mean( cellPtsCoords, axis=0 )
#     return getPointSideAgainstPlane( ptCenter, planePt, planeNormal )

# def getPointSideAgainstPlane(
#     ptCoords: npt.NDArray[ np.float64 ],
#     planePt: npt.NDArray[ np.float64 ],
#     planeNormal: npt.NDArray[ np.float64 ],
# ) -> bool:
#     """Get the side of input point against input plane.

#     Input plane is defined by a point on it and its normal vector.

#     Args:
#         ptCoords (npt.NDArray[np.float64: Coordinates of the point to get
#             the side.
#         planePt (npt.NDArray[np.float64: Point on the plane.
#         planeNormal (npt.NDArray[np.float64: Normal vector to the plane.

#     Returns:
#         bool: True if the point is in the direction of the normal vector,
#         False otherwise.
#     """
#     assert ptCoords.shape[1] == 3, "Point coordinates must have 3 components"
#     assert planeNormal.shape[1] == 3, "Plane normal vector must have 3 components"
#     assert planePt.shape[1] == 3, "Plane point must have 3 components"
#     vec: npt.NDArray[ np.float64 ] = ptCoords - planePt
#     dot: float = np.einsum('ni,ni->n', planeNormal, vec )
#     assert np.linalg.norm( dot ) > EPSILON, "The point is on the plane."
#     return dot > 0

# def computeAngleFromPoints( pt1: npt.NDArray[ np.float64 ], pt2: npt.NDArray[ np.float64 ],
#                             pt3: npt.NDArray[ np.float64 ] ) -> float:
#     """Compute angle from 3 points.

#     Args:
#         pt1 (npt.NDArray[np.float64]): First point
#         pt2 (npt.NDArray[np.float64]): Second point
#         pt3 (npt.NDArray[np.float64]): Third point

#     Returns:
#         float: Angle
#     """
#     # compute vectors
#     vec1: npt.NDArray[ np.float64 ] = pt1 - pt2
#     vec2: npt.NDArray[ np.float64 ] = pt3 - pt2
#     return computeAngleFromVectors( vec1, vec2 )

# def computeAngleFromVectors(
#     vec1: npt.NDArray[ np.float64 ],
#     vec2: npt.NDArray[ np.float64 ],
# ) -> float:
#     """Compute angle from 2 vectors.

#     Args:
#         vec1 (npt.NDArray[np.float64]): First vector
#         vec2 (npt.NDArray[np.float64]): Second vector

#     Returns:
#         float: angle
#     """
#     assert np.where( np.abs( np.linalg.norm( vec1, axis=0 ) ) ) == 0., "First vector cannot be null"
#     assert np.where( np.abs( np.linalg.norm( vec2, axis=0 ) ) ) == 0., "Second vector cannot be null"
#     # normalization
#     vec1_norm: npt.NDArray[ np.float64 ] = np.einsum( 'ni,nj->ni', vec1, 1. / np.linalg.norm( vec1, axis=1, keepdims=True ) )
#     vec2_norm: npt.NDArray[ np.float64 ] = np.einsum( 'ni,nj->ni' , vec2, 1. / np.linalg.norm( vec2, axis=1, keepdims=True ) )

#     # Use normalized vectors for dot product
#     dot: float = np.einsum('ni,nj->n', vec1_norm, vec2_norm)

#     # Clamp to valid range for arccos
#     dot = np.clip( dot, -1.0, 1.0 )

#     # Handle 2D vs 3D cases
#     if vec1.shape[1] == 2 and vec2.shape[1] == 2:
#         # For 2D, use cross product to determine orientation
#         cross: float = np.einsum('ijk,nj,nk->ni', EPS, vec1_norm, vec2_norm)
#         angle: float = np.arccos( dot )
#         return angle if cross >= 0 else 2.0 * np.pi - angle
#     else:
#         # For 3D, return angle in [0, π]
#         return np.arccos( dot )

# def computeCosineFromVectors(
#     vec1: npt.NDArray[ np.float64 ],
#     vec2: npt.NDArray[ np.float64 ],
# ) -> float:
#     """Compute cosine from 2 vectors.

#     Args:
#         vec1 (npt.NDArray[np.float64]): First vector
#         vec2 (npt.NDArray[np.float64]): Second vector

#     Returns:
#         float: Cosine
#     """
#     assert abs( np.linalg.norm( vec1 ) ) > 0., "First vector cannot be null"
#     assert abs( np.linalg.norm( vec2 ) ) > 0., "Second vector cannot be null"
#     # normalization
#     vec1_norm: npt.NDArray[ np.float64 ] = vec1 / np.linalg.norm( vec1 )
#     vec2_norm: npt.NDArray[ np.float64 ] = vec2 / np.linalg.norm( vec2 )
#     return np.dot( vec1_norm, vec2_norm )


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
    assert pt1.shape[ 0 ] == pt2.shape[ 0 ] and pt2.shape[ 0 ] == pt3.shape[ 0 ]
    # compute vectors
    vec1: npt.NDArray[ np.float64 ] = pt1 - pt2
    vec2: npt.NDArray[ np.float64 ] = pt3 - pt2
    assert np.all( np.abs( np.linalg.norm( vec1, axis=1 ) ) > 0. ), "First and second points must be different"
    assert np.all( np.abs( np.linalg.norm( vec2, axis=1 ) ) > 0. ), "First and second points must be different"
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
    # normalization
    vec1_norm = _normalize( vec1 )
    vec2_norm = _normalize( vec2 ) 
    return _cross( vec1_norm, vec2_norm) 
