# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
import numpy as np
import numpy.typing as npt

from geos.utils.PhysicalConstants import EPSILON

__doc__ = """Functions to permform geometry calculations."""


def getChangeOfBasisMatrix(
    basisFrom: tuple[
        npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]
    ],
    basisTo: tuple[
        npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]
    ],
) -> npt.NDArray[np.float64]:
    """Get the change of basis matrix from basis basisFrom to basis basisTo.

    Let's define the basis (basisFrom) (b1, b2, b3) and basis (basisTo) (c1, c2, c3)
    where b1, b2, b3, and c1, c2, c3 are the vectors of the basis in the canonic form.
    This method returns the change of basis matrix P from basisFrom to basisTo.

    The coordinates of a vector Vb(vb1, vb2, vb3) from the basis B in the basis
    C is then Vc = P.Vb

    Args:
        basisFrom (tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]): origin basis
        basisTo (tuple[npt.NDArray[np.float64], npt.NDArray[np.float64], npt.NDArray[np.float64]]): destination basis

    Returns:
        npt.NDArray[np.float64]: change of basis matrix.
    """
    assert (basisFrom[0].size == basisFrom[1].size) and (
        basisFrom[0].size == basisFrom[2].size
    ), ("Origin " + "space vectors must have the same size.")

    assert (basisTo[0].size == basisTo[1].size) and (
        basisTo[0].size == basisTo[2].size
    ), ("Destination " + "space vectors must have the same size.")

    # build the matrices where columns are the vectors of the bases
    B = np.transpose(np.array(basisFrom))
    C = np.transpose(np.array(basisTo))
    # compute the inverse of C
    C1: npt.NDArray[np.float64] = np.linalg.inv(C)
    # get the change of basis matrix
    return np.dot(C1, B)


def computeCoordinatesInNewBasis(
    vec: npt.NDArray[np.float64], changeOfBasisMatrix: npt.NDArray[np.float64]
) -> npt.NDArray[np.float64]:
    """Computes the coordinates of a matrix from a basis B in the new basis B'.

    Args:
        vec (npt.NDArray[np.float64]): vector to compute the new coordinates
        changeOfBasisMatrix (npt.NDArray[np.float64]): Change of basis matrix

    Returns:
        npt.NDArray[np.float64]: the new coordinates of the matrix in the basis
        B'.
    """
    assert (
        vec.size == changeOfBasisMatrix.shape[1]
    ), """The size of the vector
    must be equal to the number of columns of and change of basis matrix."""
    return np.dot(changeOfBasisMatrix, vec)


def computePlaneFrom3Points(
    pt1: npt.NDArray[np.float64],
    pt2: npt.NDArray[np.float64],
    pt3: npt.NDArray[np.float64],
) -> tuple[float, float, float, float]:
    """Compute the 4 coefficients of a plane equation.

    Let's defined a plane from the following equation: ax + by + cz + d = 0.
    This function determines a, b, c, d from 3 points of the plane.

    Args:
        pt1 (npt.NDArray[np.float64]): 1st point of the plane.
        pt2 (npt.NDArray[np.float64]): 2nd point of the plane.
        pt3 (npt.NDArray[np.float64]): 3rd point of the plane.

    Returns:
        tuple[float, float, float, float]: tuple of the 4 coefficients.
    """
    # plane vectors
    v1: npt.NDArray[np.float64] = pt2 - pt1
    v2: npt.NDArray[np.float64] = pt3 - pt1
    # normal vector
    normal: npt.NDArray[np.float64] = np.cross(v1, v2)
    assert np.linalg.norm(normal) != 0, "Vectors of the plane must not be colinear."
    # first 3 coefficients of the plane equation
    a, b, c = normal
    # last coefficient of the plane equation
    d: float = -np.dot(normal, pt1)
    return a, b, c, d


def getCellSideAgainstPlane(
    cellPtsCoords: npt.NDArray[np.float64],
    planePt: npt.NDArray[np.float64],
    planeNormal: npt.NDArray[np.float64],
) -> bool:
    """Get the side of input cell against input plane.

    Input plane is defined by a point on it and its normal vector.

    Args:
        cellPtsCoords (npt.NDArray[np.float64]): Coordinates of the vertices of
            the cell to get the side.
        planePt (npt.NDArray[np.float64]): Point on the plane.
        planeNormal (npt.NDArray[np.float64]): Normal vector to the plane.

    Returns:
        bool: True if the cell is in the direction of the normal vector,
        False otherwise.
    """
    assert (
        len(cellPtsCoords) > 1
    ), "The list of points must contains more than one element"
    ptCenter: npt.NDArray[np.float64] = np.mean(cellPtsCoords, axis=0)
    return getPointSideAgainstPlane(ptCenter, planePt, planeNormal)


def getPointSideAgainstPlane(
    ptCoords: npt.NDArray[np.float64],
    planePt: npt.NDArray[np.float64],
    planeNormal: npt.NDArray[np.float64],
) -> bool:
    """Get the side of input point against input plane.

    Input plane is defined by a point on it and its normal vector.

    Args:
        ptCoords (npt.NDArray[np.float64]): Coordinates of the point to get
            the side.
        planePt (npt.NDArray[np.float64]): Point on the plane.
        planeNormal (npt.NDArray[np.float64]): Normal vector to the plane.

    Returns:
        bool: True if the point is in the direction of the normal vector,
        False otherwise.
    """
    assert ptCoords.size == 3, "Point coordinates must have 3 components"
    assert planeNormal.size == 3, "Plane normal vector must have 3 components"
    assert planePt.size == 3, "Plane point must have 3 components"
    vec: npt.NDArray[np.float64] = ptCoords - planePt
    dot: float = np.dot(planeNormal, vec)
    assert abs(dot) > EPSILON, "The point is on the plane."
    return dot > 0
