import numpy
from geos.mesh.doctor.actions.generate_cube import buildRectilinearBlocksMesh, XYZ
from geos.mesh.doctor.actions.non_conformal import Options, __action


def test_twoCloseHexs():
    delta = 1.e-6
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + delta, tmp, tmp )
    mesh = buildRectilinearBlocksMesh( ( xyz0, xyz1 ) )

    # Close enough, but points tolerance is too strict to consider the faces matching.
    options = Options( angleTolerance=1., pointTolerance=delta / 2, faceTolerance=delta * 2 )
    results = __action( mesh, options )
    assert len( results.nonConformalCells ) == 1
    assert set( results.nonConformalCells[ 0 ] ) == { 0, 1 }

    # Close enough, and points tolerance is loose enough to consider the faces matching.
    options = Options( angleTolerance=1., pointTolerance=delta * 2, faceTolerance=delta * 2 )
    results = __action( mesh, options )
    assert len( results.nonConformalCells ) == 0


def test_twoDistantHexs():
    delta = 1
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + delta, tmp, tmp )
    mesh = buildRectilinearBlocksMesh( ( xyz0, xyz1 ) )

    options = Options( angleTolerance=1., pointTolerance=delta / 2., faceTolerance=delta / 2. )

    results = __action( mesh, options )
    assert len( results.nonConformalCells ) == 0


def test_twoCloseShiftedHexs():
    deltaX, deltaY = 1.e-6, 0.5
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp, tmp )
    xyz1 = XYZ( tmp + 1 + deltaX, tmp + deltaY, tmp + deltaY )
    mesh = buildRectilinearBlocksMesh( ( xyz0, xyz1 ) )

    options = Options( angleTolerance=1., pointTolerance=deltaX * 2, faceTolerance=deltaX * 2 )

    results = __action( mesh, options )
    assert len( results.nonConformalCells ) == 1
    assert set( results.nonConformalCells[ 0 ] ) == { 0, 1 }


def test_bigElemNextToSmallElem():
    delta = 1.e-6
    tmp = numpy.arange( 2, dtype=float )
    xyz0 = XYZ( tmp, tmp + 1, tmp + 1 )
    xyz1 = XYZ( 3 * tmp + 1 + delta, 3 * tmp, 3 * tmp )
    mesh = buildRectilinearBlocksMesh( ( xyz0, xyz1 ) )

    options = Options( angleTolerance=1., pointTolerance=delta * 2, faceTolerance=delta * 2 )

    results = __action( mesh, options )
    assert len( results.nonConformalCells ) == 1
    assert set( results.nonConformalCells[ 0 ] ) == { 0, 1 }
