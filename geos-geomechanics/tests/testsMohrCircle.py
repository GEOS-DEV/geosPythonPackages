# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

import numpy as np
import numpy.typing as npt
from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.join( os.path.dirname( dir_path ), "src" )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

from geos.geomechanics.model.MohrCircle import MohrCircle
from geos.geomechanics.model.MohrCoulomb import MohrCoulomb

circleId = "12453"
stressVector: npt.NDArray[ np.float64 ] = np.array( [ 1.8, 2.5, 5.2, 0.3, 0.4, 0.1 ] )

rockCohesion: float = 8.0e8
frictionAngle: float = 10 * np.pi / 180.0  # in radian

principalComponentsExpected: tuple[ float, float, float ] = ( 1.748, 2.471, 5.281 )


class TestsMohrCircle( unittest.TestCase ):

    def test_MohrCircleInit( self: Self ) -> None:
        """Test instanciation of MohrCircle objects."""
        mohrCircle: MohrCircle = MohrCircle( circleId )
        mohrCircle.setPrincipalComponents( *principalComponentsExpected )

        self.assertSequenceEqual( circleId, mohrCircle.getCircleId() )

        obtained: list[ float ] = [ round( val, 3 ) for val in mohrCircle.getPrincipalComponents() ]
        self.assertSequenceEqual( obtained, principalComponentsExpected )

    def test_MohrCircleRadius( self: Self ) -> None:
        """Test the calculation of MohrCircle radius."""
        mohrCircle: MohrCircle = MohrCircle( circleId )
        mohrCircle.computePrincipalComponents( stressVector )

        obtained: float = mohrCircle.getCircleRadius()
        expected: float = ( principalComponentsExpected[ 2 ] - principalComponentsExpected[ 0 ] ) / 2.0
        self.assertAlmostEqual( obtained, expected, 3 )

    def test_MohrCircleCenter( self: Self ) -> None:
        """Test the calculation of MohrCircle center."""
        mohrCircle: MohrCircle = MohrCircle( circleId )
        mohrCircle.computePrincipalComponents( stressVector )

        obtained: float = mohrCircle.getCircleCenter()
        expected: float = ( principalComponentsExpected[ 2 ] + principalComponentsExpected[ 0 ] ) / 2.0
        self.assertAlmostEqual( obtained, expected, 3 )


class TestsMohrCoulomb( unittest.TestCase ):

    def test_MohrCoulombInit( self: Self ) -> None:
        """Test instanciation of MohrCoulomb objects."""
        # expected values
        expectedSlope: float = np.tan( frictionAngle )
        expectedSigmaMin: float = -rockCohesion / expectedSlope
        # instantiate object
        mohrCoulomb: MohrCoulomb = MohrCoulomb( rockCohesion, frictionAngle )
        # test results
        self.assertEqual( mohrCoulomb.m_rockCohesion, rockCohesion )
        self.assertEqual( mohrCoulomb.m_slope, expectedSlope )
        self.assertEqual( mohrCoulomb.m_sigmaMin, expectedSigmaMin )

    def test_computeShearStress( self: Self ) -> None:
        """Test calculation of shear stress from normal stress."""
        # inputs
        stressNormal: npt.NDArray[ np.float64 ] = np.linspace( 5.0e8, 1.0e9, 100 )
        # expected values
        expectedValues: npt.NDArray[ np.float64 ] = np.array( [
            888163490.0,
            889054031.0,
            889944571.0,
            890835111.0,
            891725652.0,
            892616192.0,
            893506732.0,
            894397273.0,
            895287813.0,
            896178353.0,
            897068893.0,
            897959434.0,
            898849974.0,
            899740514.0,
            900631055.0,
            901521595.0,
            902412135.0,
            903302676.0,
            904193216.0,
            905083756.0,
            905974296.0,
            906864837.0,
            907755377.0,
            908645917.0,
            909536458.0,
            910426998.0,
            911317538.0,
            912208079.0,
            913098619.0,
            913989159.0,
            914879700.0,
            915770240.0,
            916660780.0,
            917551320.0,
            918441861.0,
            919332401.0,
            920222941.0,
            921113482.0,
            922004022.0,
            922894562.0,
            923785103.0,
            924675643.0,
            925566183.0,
            926456724.0,
            927347264.0,
            928237804.0,
            929128344.0,
            930018885.0,
            930909425.0,
            931799965.0,
            932690506.0,
            933581046.0,
            934471586.0,
            935362127.0,
            936252667.0,
            937143207.0,
            938033748.0,
            938924288.0,
            939814828.0,
            940705368.0,
            941595909.0,
            942486449.0,
            943376989.0,
            944267530.0,
            945158070.0,
            946048610.0,
            946939151.0,
            947829691.0,
            948720231.0,
            949610772.0,
            950501312.0,
            951391852.0,
            952282392.0,
            953172933.0,
            954063473.0,
            954954013.0,
            955844554.0,
            956735094.0,
            957625634.0,
            958516175.0,
            959406715.0,
            960297255.0,
            961187795.0,
            962078336.0,
            962968876.0,
            963859416.0,
            964749957.0,
            965640497.0,
            966531037.0,
            967421578.0,
            968312118.0,
            969202658.0,
            970093199.0,
            970983739.0,
            971874279.0,
            972764819.0,
            973655360.0,
            974545900.0,
            975436440.0,
            976326981.0,
        ] )
        # instantiate object
        mohrCoulomb: MohrCoulomb = MohrCoulomb( rockCohesion, frictionAngle )
        obtained: npt.NDArray[ np.float64 ] = np.array( mohrCoulomb.computeShearStress( stressNormal ) )

        # test results
        self.assertSequenceEqual( expectedValues.tolist(), np.round( obtained ).tolist() )

    def test_computeFailureEnvelop1( self: Self ) -> None:
        """Test calculation of failure envelop from minimum normal stress."""
        # inputs
        stressNormalMax: float = 1.0e9
        # expected values
        normalStressExpected: npt.NDArray[ np.float64 ] = np.array( [
            -4537025456.0,
            -3921800405.0,
            -3306575354.0,
            -2691350304.0,
            -2076125253.0,
            -1460900203.0,
            -845675152.0,
            -230450101.0,
            384774949.0,
            1000000000.0,
        ] )
        shearStressExpected: npt.NDArray[ np.float64 ] = np.array( [
            0.0,
            108480776.0,
            216961551.0,
            325442327.0,
            433923103.0,
            542403878.0,
            650884654.0,
            759365429.0,
            867846205.0,
            976326981.0,
        ] )

        # instantiate object
        mohrCoulomb: MohrCoulomb = MohrCoulomb( rockCohesion, frictionAngle )
        normalStressObtained, shearStressObtained = mohrCoulomb.computeFailureEnvelop( stressNormalMax, n=10 )

        # test results
        self.assertSequenceEqual( normalStressExpected.tolist(), np.round( normalStressObtained ).tolist() )
        self.assertSequenceEqual( shearStressExpected.tolist(), np.round( shearStressObtained ).tolist() )

    def test_computeFailureEnvelop2( self: Self ) -> None:
        """Test calculation of failure envelop in user-defined range."""
        # inputs
        stressNormalMin: float = 8.0e8
        stressNormalMax: float = 1.0e9
        # expected values
        normalStressExpected: npt.NDArray[ np.float64 ] = np.array( [
            800000000.0,
            822222222.0,
            844444444.0,
            866666667.0,
            888888889.0,
            911111111.0,
            933333333.0,
            955555556.0,
            977777778.0,
            1000000000.0,
        ] )
        shearStressExpected: npt.NDArray[ np.float64 ] = np.array( [
            941061585.0,
            944979962.0,
            948898339.0,
            952816717.0,
            956735094.0,
            960653471.0,
            964571849.0,
            968490226.0,
            972408603.0,
            976326981.0,
        ] )

        # instantiate object
        mohrCoulomb: MohrCoulomb = MohrCoulomb( rockCohesion, frictionAngle )
        normalStressObtained, shearStressObtained = mohrCoulomb.computeFailureEnvelop( stressNormalMax,
                                                                                       stressNormalMin,
                                                                                       n=10 )

        # test results
        self.assertSequenceEqual( normalStressExpected.tolist(), np.round( normalStressObtained ).tolist() )
        self.assertSequenceEqual( shearStressExpected.tolist(), np.round( shearStressObtained ).tolist() )
