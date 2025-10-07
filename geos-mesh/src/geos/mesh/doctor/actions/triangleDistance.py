import itertools
from math import sqrt
import numpy
from numpy.linalg import norm
from typing import Tuple, Union


def __divClamp( num: float, den: float ) -> float:
    """Computes the division `num / den`. and clamps the result between 0 and 1.
    If `den` is zero, the result of the division is set to 0.

    Args:
        num (float): The numerator.
        den (float): The denominator.

    Returns:
        float: The result between 0 and 1.
    """
    if den == 0.:
        return 0.
    tmp: float = num / den
    if tmp < 0:
        return 0.
    elif tmp > 1:
        return 1.
    else:
        return tmp


def distanceBetweenTwoSegments( x0: numpy.ndarray, d0: numpy.ndarray, x1: numpy.ndarray,
                                d1: numpy.ndarray ) -> Tuple[ numpy.ndarray, numpy.ndarray ]:
    """Computes the minimum distance between two segments.

    Args:
        x0 (numpy.ndarray): First point of segment 0.
        d0 (numpy.ndarray): Director vector such that x0 + d0 is the second point of segment 0.
        x1 (numpy.ndarray): First point of segment 1.
        d1 (numpy.ndarray): Director vector such that x1 + d1 is the second point of segment 1.

    Returns:
        Tuple[ numpy.ndarray, numpy.ndarray ]: A tuple containing the two points closest point for segments
                                               0 and 1 respectively.
    """
    # The reference paper is:
    # "On fast computation of distance between line segments" by Vladimir J. Lumelsky.
    # Information Processing Letters, Vol. 21, number 2, pages 55-61, 08/16/1985.

    # In the reference, the indices start at 1, while in this implementation, they start at 0.
    tmp: numpy.ndarray = x1 - x0
    D0: float = numpy.dot( d0, d0 )  # As such, this is D1 in the reference paper.
    D1: float = numpy.dot( d1, d1 )
    R: float = numpy.dot( d0, d1 )
    S0: float = numpy.dot( d0, tmp )
    S1: float = numpy.dot( d1, tmp )

    # `t0` parameterizes line 0:
    #   - when t0 = 0 the point is p0.
    #   - when t0 = 1, the point is p0 + u0, the other side of the segment
    # Same for `t1` and line 1.

    # Step 1 of the algorithm considers degenerate cases.
    # They'll be considered along the line using `divClamp`.

    # Step 2: Computing t0 using eq (11).
    t0: float = __divClamp( S0 * D1 - S1 * R, D0 * D1 - R * R )

    # Step 3: compute t1 for point on line 1 closest to point at t0.
    t1: float = __divClamp( t0 * R - S1, D1 )  # Eq (10, right)
    sol1: numpy.ndarray = x1 + t1 * d1  # Eq (3)
    t0: float = __divClamp( t1 * R + S0, D0 )  # Eq (10, left)
    sol0: numpy.ndarray = x0 + t0 * d0  # Eq (4)

    return sol0, sol1


def __computeNodesToTriangleDistance(
        tri0: numpy.ndarray, edges0,
        tri1: numpy.ndarray ) -> Tuple[ Union[ float, None ], Union[ numpy.ndarray, None ], Union[ numpy.ndarray, None ], bool ]:
    """Computes the distance from nodes of `tri1` points onto `tri0`.

    Args:
        tri0 (numpy.ndarray): First triangle.
        edges0: The edges of triangle 0. First element being edge [0, 1], etc.
        tri1 (numpy.ndarray): Second triangle.

    Returns:
        Tuple[ Union[ float, None ], Union[ numpy.ndarray, None ], Union[ numpy.ndarray, None ], bool ]:
        The distance, the closest point on triangle 0, the closest on triangle 1 and a boolean indicating of the
        triangles are disjoint. If nothing was found, then the first three arguments are None.
        The boolean being still defined.
    """
    areDisjoint: bool = False
    tri0Normal: numpy.ndarray = numpy.cross( edges0[ 0 ], edges0[ 1 ] )
    tri0NormalNorm: float = numpy.dot( tri0Normal, tri0Normal )

    # Forget about degenerate cases.
    if tri0NormalNorm > numpy.finfo( float ).eps:
        # Build projection lengths of `tri1` points.
        tri1Proj = numpy.empty( 3, dtype=float )
        for i in range( 3 ):
            tri1Proj[ i ] = numpy.dot( tri0[ 0 ] - tri1[ i ], tri0Normal )

        # Considering `tri0` separates the space in 2,
        # let's check if `tri1` is on one side only.
        # If so, let's take the closest point.
        point: int = -1
        if numpy.all( tri1Proj > 0 ):
            point = numpy.argmin( tri1Proj )
        elif numpy.all( tri1Proj < 0 ):
            point = numpy.argmax( tri1Proj )

        # So if `tri1` is actually "on one side",
        # point `tri1[point]` is candidate to be the closest point.
        if point > -1:
            areDisjoint = True
            # But we must check that its projection is inside `tri0`.
            if numpy.dot( tri1[ point ] - tri0[ 0 ], numpy.cross( tri0Normal, edges0[ 0 ] ) ) > 0:
                if numpy.dot( tri1[ point ] - tri0[ 1 ], numpy.cross( tri0Normal, edges0[ 1 ] ) ) > 0:
                    if numpy.dot( tri1[ point ] - tri0[ 2 ], numpy.cross( tri0Normal, edges0[ 2 ] ) ) > 0:
                        # It is!
                        sol0 = tri1[ point ]
                        sol1 = tri1[ point ] + ( tri1Proj[ point ] / tri0NormalNorm ) * tri0Normal
                        return norm( sol1 - sol0 ), sol0, sol1, areDisjoint
    return None, None, None, areDisjoint


def distanceBetweenTwoTriangles( tri0: numpy.ndarray,
                                 tri1: numpy.ndarray ) -> Tuple[ float, numpy.ndarray, numpy.ndarray ]:
    """Returns the minimum distance between two triangles, and the two points where this minimum occurs.
    If the two triangles touch, then distance is exactly 0.
    But the two points are dummy and cannot be used as contact points (they are still though).

    Args:
        tri0 (numpy.ndarray): The first 3x3 triangle points.
        tri1 (numpy.ndarray): The second 3x3 triangle points.

    Returns:
        Tuple[ float, numpy.ndarray, numpy.ndarray ]: The distance and the two points.
    """
    # Compute vectors along the 6 sides
    edges0 = numpy.empty( ( 3, 3 ), dtype=float )
    edges1 = numpy.empty( ( 3, 3 ), dtype=float )
    for i in range( 3 ):
        edges0[ i ][ : ] = tri0[ ( i + 1 ) % 3 ] - tri0[ i ]
        edges1[ i ][ : ] = tri1[ ( i + 1 ) % 3 ] - tri1[ i ]

    minSol0 = numpy.empty( 3, dtype=float )
    minSol1 = numpy.empty( 3, dtype=float )
    areDisjoint: bool = False

    minDist = numpy.inf

    # Looping over all the pair of edges.
    for i, j in itertools.product( range( 3 ), repeat=2 ):
        # Find the closest points on edges i and j.
        sol0, sol1 = distanceBetweenTwoSegments( tri0[ i ], edges0[ i ], tri1[ j ], edges1[ j ] )
        # Computing the distance between the two solutions.
        deltaSol = sol1 - sol0
        dist: float = numpy.dot( deltaSol, deltaSol )
        # Update minimum if relevant and check if it's the closest pair of points.
        if dist <= minDist:
            minSol0[ : ] = sol0
            minSol1[ : ] = sol1
            minDist = dist

            # `tri0[(i + 2) % 3]` is the points opposite to edges0[i] where the closest point sol0 lies.
            # Computing those scalar products and checking the signs somehow let us determine
            # if the triangles are getting closer to each other when approaching the sol_(0|1) nodes.
            # If so, we have a minimum.
            a: float = numpy.dot( tri0[ ( i + 2 ) % 3 ] - sol0, deltaSol )
            b: float = numpy.dot( tri1[ ( j + 2 ) % 3 ] - sol1, deltaSol )
            if a <= 0 <= b:
                return sqrt( dist ), sol0, sol1

            if a < 0:
                a = 0
            if b > 0:
                b = 0
            # `dist - a + b` expands to `numpy.dot(tri1[(j + 2) % 3] - tri0[(i + 2) % 3], sol1 - sol0)`.
            # If the "directions" of the (sol1 - sol0) vector and the vector joining the extra points of the triangles
            # (i.e. not involved in the current edge check) re the "same", then the triangles do not intersect.
            if dist - a + b > 0:
                areDisjoint = True
    # No edge pair contained the closest points.
    # Checking the node/face situation.
    distance, sol0, sol1, areDisjointTmp = __computeNodesToTriangleDistance( tri0, edges0, tri1 )
    if distance:
        return distance, sol0, sol1
    areDisjoint = areDisjoint or areDisjointTmp

    distance, sol0, sol1, areDisjointTmp = __computeNodesToTriangleDistance( tri1, edges1, tri0 )
    if distance:
        return distance, sol0, sol1
    areDisjoint = areDisjoint or areDisjointTmp
    # It's not a node/face situation.
    # If the triangles do not overlap, let's return the minimum found during the edges loop.
    # (maybe an edge was parallel to the other face, and we could not decide for a unique closest point).
    if areDisjoint:
        return sqrt( minDist ), minSol0, minSol1
    else:  # Surely overlapping or degenerate triangles.
        return 0., numpy.zeros( 3, dtype=float ), numpy.zeros( 3, dtype=float )
