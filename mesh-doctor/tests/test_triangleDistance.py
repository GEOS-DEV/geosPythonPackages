from dataclasses import dataclass
import numpy
import numpy.typing as npt
from numpy.linalg import norm
import pytest
from typing import Iterable
from geos.mesh_doctor.actions.triangleDistance import distanceBetweenTwoSegments, distanceBetweenTwoTriangles


@dataclass( frozen=True )
class ExpectedSeg:
    p0: npt.NDArray[ numpy.float64 ]
    u0: npt.NDArray[ numpy.float64 ]
    p1: npt.NDArray[ numpy.float64 ]
    u1: npt.NDArray[ numpy.float64 ]
    x: npt.NDArray[ numpy.float64 ]
    y: npt.NDArray[ numpy.float64 ]

    @classmethod
    def fromTuples( cls, p0: tuple[ float, float, float ], u0: tuple[ float, float, float ],
                    p1: tuple[ float, float, float ], u1: tuple[ float, float, float ], x: tuple[ float, float, float ],
                    y: tuple[ float, float, float ] ) -> "ExpectedSeg":
        """Creates an ExpectedSeg from tuples."""
        return cls( numpy.array( p0 ), numpy.array( u0 ), numpy.array( p1 ), numpy.array( u1 ), numpy.array( x ),
                    numpy.array( y ) )


def __getSegmentsReferences() -> Iterable[ ExpectedSeg ]:
    """Provides reference segments for testing."""
    # Node to node configuration.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., 0. ),
        u0=( 1., 0., 0. ),
        p1=( 2., 0., 0. ),
        u1=( 1., 0., 0. ),
        x=( 1., 0., 0. ),
        y=( 2., 0., 0. ),
    )
    # Node to edge configuration.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., 0. ),
        u0=( 1., 0., 0. ),
        p1=( 2., -1., -1. ),
        u1=( 0., 1., 1. ),
        x=( 1., 0., 0. ),
        y=( 2., 0., 0. ),
    )
    # Edge to edge configuration.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., -1. ),
        u0=( 0., 0., 2. ),
        p1=( 1., -1., -1. ),
        u1=( 0., 2., 2. ),
        x=( 0., 0., 0. ),
        y=( 1., 0., 0. ),
    )
    # Example from "On fast computation of distance between line segments" by Vladimir J. Lumelsky.
    # Information Processing Letters, Vol. 21, number 2, pages 55-61, 08/16/1985.
    # It's a node to edge configuration.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., 0. ),
        u0=( 1., 2., 1. ),
        p1=( 1., 0., 0. ),
        u1=( 1., 1., 0. ),
        x=( 1. / 6., 2. / 6., 1. / 6. ),
        y=( 1., 0., 0. ),
    )
    # Overlapping edges.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., 0. ),
        u0=( 2., 0., 0. ),
        p1=( 1., 0., 0. ),
        u1=( 2., 0., 0. ),
        x=( 0., 0., 0. ),
        y=( 0., 0., 0. ),
    )
    # Crossing edges.
    yield ExpectedSeg.fromTuples(
        p0=( 0., 0., 0. ),
        u0=( 2., 0., 0. ),
        p1=( 1., -1., 0. ),
        u1=( 0., 2., 0. ),
        x=( 0., 0., 0. ),
        y=( 0., 0., 0. ),
    )


@pytest.mark.parametrize( "expected", __getSegmentsReferences() )
def test_segments( expected: ExpectedSeg ) -> None:
    """Tests the distance between two segments.

    Args:
        expected (ExpectedSeg): The expected segment data.
    """
    eps = numpy.finfo( float ).eps
    x, y = distanceBetweenTwoSegments( expected.p0, expected.u0, expected.p1, expected.u1 )
    if norm( expected.x - expected.y ) == 0:
        assert norm( x - y ) == 0.
    else:
        assert norm( expected.x - x ) < eps
        assert norm( expected.y - y ) < eps


@dataclass( frozen=True )
class ExpectedTri:
    t0: npt.NDArray[ numpy.float64 ]
    t1: npt.NDArray[ numpy.float64 ]
    d: float
    p0: npt.NDArray[ numpy.float64 ]
    p1: npt.NDArray[ numpy.float64 ]

    @classmethod
    def fromTuples( cls, t0: tuple[ tuple[ float, float, float ], ... ], t1: tuple[ tuple[ float, float, float ], ... ],
                    d: float, p0: tuple[ float, float, float ], p1: tuple[ float, float, float ] ) -> "ExpectedTri":
        """Creates an ExpectedTri from tuples."""
        return cls( numpy.array( t0 ), numpy.array( t1 ), float( d ), numpy.array( p0 ), numpy.array( p1 ) )


def __getTrianglesReferences() -> Iterable[ ExpectedTri ]:
    """Provides reference triangles for testing."""
    # Node to node configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 1. ) ),
                                  t1=( ( 2., 0., 0. ), ( 3., 0., 0. ), ( 2., 1., 1. ) ),
                                  d=1.,
                                  p0=( 1., 0., 0. ),
                                  p1=( 2., 0., 0. ) )
    # Node to edge configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 1. ) ),
                                  t1=( ( 2., -1., 0. ), ( 3., 0., 0. ), ( 2., 1., 0. ) ),
                                  d=1.,
                                  p0=( 1., 0., 0. ),
                                  p1=( 2., 0., 0. ) )
    # Edge to edge configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 1., 1., 1. ), ( 1., -1., -1. ) ),
                                  t1=( ( 2., -1., 0. ), ( 2., 1., 0. ), ( 3., 0., 0. ) ),
                                  d=1.,
                                  p0=( 1., 0., 0. ),
                                  p1=( 2., 0., 0. ) )
    # Point to face configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 1. ) ),
                                  t1=( ( 2., -1., 0. ), ( 2., 1., -1. ), ( 2, 1., 1. ) ),
                                  d=1.,
                                  p0=( 1., 0., 0. ),
                                  p1=( 2., 0., 0. ) )
    # Same triangles configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 1. ) ),
                                  t1=( ( 0., 0., 0. ), ( 1., 0., 0. ), ( 0., 1., 1. ) ),
                                  d=0.,
                                  p0=( 0., 0., 0. ),
                                  p1=( 0., 0., 0. ) )
    # Crossing triangles configuration.
    yield ExpectedTri.fromTuples( t0=( ( 0., 0., 0. ), ( 2., 0., 0. ), ( 2., 0., 1. ) ),
                                  t1=( ( 1., -1., 0. ), ( 1., 1., 0. ), ( 1., 1., 1. ) ),
                                  d=0.,
                                  p0=( 0., 0., 0. ),
                                  p1=( 0., 0., 0. ) )


@pytest.mark.parametrize( "expected", __getTrianglesReferences() )
def test_triangles( expected: ExpectedTri ) -> None:
    """Tests the distance between two triangles.

    Args:
        expected (ExpectedTri): The expected triangle data.
    """
    eps = numpy.finfo( float ).eps
    d, p0, p1 = distanceBetweenTwoTriangles( expected.t0, expected.t1 )
    assert abs( d - expected.d ) < eps
    if d != 0:
        assert norm( p0 - expected.p0 ) < eps
        assert norm( p1 - expected.p1 ) < eps
