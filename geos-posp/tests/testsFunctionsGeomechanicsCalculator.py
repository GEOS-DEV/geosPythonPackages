# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.join( os.path.dirname( dir_path ), "src" )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import geos_posp.processing.geomechanicsCalculatorFunctions as fcts
from geos.utils import PhysicalConstants
from geos.utils.algebraFunctions import getAttributeMatrixFromVector
from geos.utils.UnitRepository import Unit, UnitRepository

# geomechanical outputs - Testing variables - Unit is GPa
bulkModulus: npt.NDArray[ np.float64 ] = np.array( [ 9.0, 50.0, 65.0, np.nan, 150.0 ] )
shearModulus: npt.NDArray[ np.float64 ] = np.array( [ 3.2, 24.0, np.nan, 70.0, 100.0 ] )
poissonRatio: npt.NDArray[ np.float64 ] = np.array( [ 0.34, 0.29, np.nan, np.nan, 0.23 ] )
density: npt.NDArray[ np.float64 ] = np.array( [ 2600.0, 3100.0, 2800.0, np.nan, 2900.0 ] )
biotCoefficient: npt.NDArray[ np.float64 ] = np.array( [ 0.1, 0.3, np.nan, 0.5, 0.6 ] )
pressure: npt.NDArray[ np.float64 ] = np.array( [ 10.0, 280.0, np.nan, 80.0, 100.0 ] )
effectiveStress: npt.NDArray[ np.float64 ] = -1.0 * np.array( [
    [ 160.0, 250.0, 180.0, np.nan, 200.0, 190.0 ],
    [ 180.0, 260.0, 190.0, np.nan, 220.0, 210.0 ],
    [ 200.0, 280.0, 210.0, np.nan, 230.0, 230.0 ],
    [ 220.0, 290.0, 220.0, np.nan, 250.0, 250.0 ],
    [ 260.0, 310.0, 230.0, np.nan, 290.0, 270.0 ],
] )
verticalStress: npt.NDArray[ np.float64 ] = effectiveStress[ :, 2 ]
horizontalStress: npt.NDArray[ np.float64 ] = np.min( effectiveStress[ :, :2 ], axis=1 )

stressVector: npt.NDArray[ np.float64 ] = np.array( [ 1.8, 2.5, 5.2, 0.3, 0.4, 0.1 ] )
stressTensor: npt.NDArray[ np.float64 ] = getAttributeMatrixFromVector( stressVector )


class TestsFunctionsGeomechanicsCalculator( unittest.TestCase ):

    def test_SpecificGravity( self: Self ) -> None:
        """Test calculation of specific Gravity."""
        specificDensity: float = 1000.0

        obtained: npt.NDArray[ np.float64 ] = fcts.specificGravity( density, specificDensity )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 2.6, 3.1, 2.8, np.nan, 2.9 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_YoungModulus( self: Self ) -> None:
        """Test calculation of young Modulus."""
        obtained: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 8.58, 62.07, np.nan, np.nan, 245.45 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_PoissonRatio( self: Self ) -> None:
        """Test calculation of poisson Ratio."""
        obtained: npt.NDArray[ np.float64 ] = fcts.poissonRatio( bulkModulus, shearModulus )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.34, 0.29, np.nan, np.nan, 0.23 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_BulkModulus( self: Self ) -> None:
        """Test calculation of bulk Modulus."""
        E: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
        u: npt.NDArray[ np.float64 ] = fcts.poissonRatio( bulkModulus, shearModulus )

        obtained: npt.NDArray[ np.float64 ] = fcts.bulkModulus( E, u )
        expected: npt.NDArray[ np.float64 ] = bulkModulus
        expected[ 2 ] = np.nan
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_ShearModulus( self: Self ) -> None:
        """Test calculation of shear Modulus."""
        E: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
        u: npt.NDArray[ np.float64 ] = fcts.poissonRatio( bulkModulus, shearModulus )

        obtained: npt.NDArray[ np.float64 ] = fcts.shearModulus( E, u )
        expected: npt.NDArray[ np.float64 ] = shearModulus
        expected[ 3 ] = np.nan
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_lambdaCoefficient( self: Self ) -> None:
        """Test calculation of shear Modulus."""
        E: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
        u: npt.NDArray[ np.float64 ] = fcts.poissonRatio( bulkModulus, shearModulus )

        obtained: npt.NDArray[ np.float64 ] = fcts.lambdaCoefficient( E, u )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 6.87, 34.0, np.nan, np.nan, 83.33 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_OedometricModulus( self: Self ) -> None:
        """Test calculation of oedometric Modulus."""
        Edef: npt.NDArray[ np.float64 ] = np.array( [ 9.0, 50.0, 65.0, np.nan, 150.0 ] )

        obtained: npt.NDArray[ np.float64 ] = fcts.oedometricModulus( Edef, poissonRatio )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 13.85, 65.52, np.nan, np.nan, 173.89 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_BiotCoefficient( self: Self ) -> None:
        """Test calculation of biot Coefficient."""
        Kgrain: float = 150.0
        obtained: npt.NDArray[ np.float64 ] = fcts.biotCoefficient( Kgrain, bulkModulus )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.94, 0.67, 0.57, np.nan, 0.0 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_TotalStress( self: Self ) -> None:
        """Test calculation of Total Stress."""
        obtained: npt.NDArray[ np.float64 ] = fcts.totalStress( effectiveStress, biotCoefficient, pressure )
        expected: npt.NDArray[ np.float64 ] = np.array( [
            [ -161.0, -251.0, -181.0, np.nan, -200.0, -190.0 ],
            [ -264.0, -344.0, -274.0, np.nan, -220.0, -210.0 ],
            [ np.nan, np.nan, np.nan, np.nan, -230.0, -230.0 ],
            [ -260.0, -330.0, -260.0, np.nan, -250.0, -250.0 ],
            [ -320.0, -370.0, -290.0, np.nan, -290.0, -270.0 ],
        ] )

        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_StressRatio( self: Self ) -> None:
        """Test calculation of Stress Ratio."""
        obtained: npt.NDArray[ np.float64 ] = fcts.stressRatio( horizontalStress, verticalStress )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 1.39, 1.37, 1.33, 1.32, 1.35 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_LithostaticStress( self: Self ) -> None:
        """Test calculation of lithostatic Stress."""
        zCoords: npt.NDArray[ np.float64 ] = np.array( [ -2.0, -100.0, -500.0, np.nan, -2500.0 ] )
        gravity: float = PhysicalConstants.GRAVITY

        obtained: npt.NDArray[ np.float64 ] = fcts.lithostaticStress( zCoords, density, gravity )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 51012.0, 3041100.0, 13734000.0, np.nan, 71122500.0 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_ElasticStrainFromBulkShear( self: Self ) -> None:
        """Test calculation of Elastic Strain."""
        deltaEffectiveStress: npt.NDArray[ np.float64 ] = -1.3 * effectiveStress
        deltaEffectiveStress[ np.isnan( deltaEffectiveStress ) ] = 150.0
        obtained: npt.NDArray[ np.float64 ] = fcts.elasticStrainFromBulkShear( deltaEffectiveStress, bulkModulus,
                                                                               shearModulus )
        expected: npt.NDArray[ np.float64 ] = np.array( [
            [ 2.02, 20.3, 6.08, 46.88, 81.25, 77.19 ],
            [ 1.01, 3.17, 1.28, 6.25, 11.92, 11.38 ],
            [ np.nan, np.nan, np.nan, np.nan, np.nan, np.nan ],
            [ np.nan, np.nan, np.nan, np.nan, np.nan, np.nan ],
            [ 0.73, 1.05, 0.53, 1.5, 3.77, 3.51 ],
        ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_ElasticStrainFromYoungPoisson( self: Self ) -> None:
        """Test calculation of Elastic Strain."""
        deltaEffectiveStress: npt.NDArray[ np.float64 ] = -1.3 * effectiveStress
        deltaEffectiveStress[ np.isnan( deltaEffectiveStress ) ] = 150.0
        young: npt.NDArray[ np.float64 ] = fcts.youngModulus( bulkModulus, shearModulus )
        obtained: npt.NDArray[ np.float64 ] = fcts.elasticStrainFromYoungPoisson( deltaEffectiveStress, young,
                                                                                  poissonRatio )
        print( np.round( obtained, 2 ).tolist() )

        expected: npt.NDArray[ np.float64 ] = np.array( [
            [ 2.09, 20.36, 6.15, 46.84, 81.19, 77.13 ],
            [ 1.04, 3.2, 1.31, 6.24, 11.89, 11.35 ],
            [ np.nan, np.nan, np.nan, np.nan, np.nan, np.nan ],
            [ np.nan, np.nan, np.nan, np.nan, np.nan, np.nan ],
            [ 0.72, 1.04, 0.52, 1.5, 3.78, 3.52 ],
        ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_DeviatoricStressPathOed( self: Self ) -> None:
        """Test calculation of deviatoric Stress Path Oedometric conditions."""
        obtained: npt.NDArray[ np.float64 ] = fcts.deviatoricStressPathOed( poissonRatio )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.52, 0.41, np.nan, np.nan, 0.3 ] )

        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_ReservoirStressPathReal( self: Self ) -> None:
        """Test calculation of reservoir Stress Path Real conditions."""
        deltaStress: npt.NDArray[ np.float64 ] = -0.1 * effectiveStress
        deltaPressure: npt.NDArray[ np.float64 ] = 0.2 * pressure
        obtained: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathReal( deltaStress, deltaPressure )
        expected: npt.NDArray[ np.float64 ] = np.array( [
            [ 8.0, 12.5, 9.0 ],
            [ 0.32, 0.46, 0.34 ],
            [ np.nan, np.nan, np.nan ],
            [ 1.38, 1.81, 1.38 ],
            [ 1.30, 1.55, 1.15 ],
        ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_ReservoirStressPathOed( self: Self ) -> None:
        """Test calculation of reservoir Stress Path Oedometric conditions."""
        obtained: npt.NDArray[ np.float64 ] = fcts.reservoirStressPathOed( biotCoefficient, poissonRatio )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.05, 0.18, np.nan, np.nan, 0.42 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_criticalTotalStressRatio( self: Self ) -> None:
        """Test calculation of fracture Index."""
        obtained: npt.NDArray[ np.float64 ] = fcts.criticalTotalStressRatio( pressure, verticalStress )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.06, 1.47, np.nan, 0.36, 0.43 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_totalStressRatioThreshold( self: Self ) -> None:
        """Test calculation of fracture Threshold."""
        obtained: npt.NDArray[ np.float64 ] = fcts.totalStressRatioThreshold( pressure, horizontalStress )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.04, 1.08, np.nan, 0.28, 0.32 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_CriticalPorePressure( self: Self ) -> None:
        """Test calculation of critical Pore Pressure."""
        rockCohesion: float = 20  # GPa
        frictionAngle: float = 30 * np.pi / 180.0  # friction angle in radian
        effectiveStress2: npt.NDArray[ np.float64 ] = -1.0 * effectiveStress
        effectiveStress2[ np.isnan( effectiveStress ) ] = 180.0
        obtained: npt.NDArray[ np.float64 ] = fcts.criticalPorePressure( effectiveStress2, rockCohesion, frictionAngle )
        expected: npt.NDArray[ np.float64 ] = np.array( [ -302.43, -333.72, -348.1, -383.01, -438.03 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_CriticalPorePressureThreshold( self: Self ) -> None:
        """Test calculation of critical Pore Pressure Index."""
        criticalPorePressure: npt.NDArray[ np.float64 ] = np.array( [ 149.64, 174.64, 194.64, 219.64, 224.64 ] )

        obtained: npt.NDArray[ np.float64 ] = fcts.criticalPorePressureThreshold( pressure, criticalPorePressure )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.07, 1.6, np.nan, 0.36, 0.45 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 2 ), np.round( expected, 2 ), equal_nan=True ) )

    def test_compressibility( self: Self ) -> None:
        """Test calculation of compressibility from elastic moduli."""
        porosity: npt.NDArray[ np.float64 ] = np.array( [ 0.05, 0.1, 0.15, 0.30, 0.20 ] )

        # multiply by 1000 to prevent from to small values
        obtained: npt.NDArray[ np.float64 ] = 1000.0 * fcts.compressibility( poissonRatio, bulkModulus, biotCoefficient,
                                                                             porosity )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 110.438, 49.016, np.nan, np.nan, 18.991 ] )
        self.assertTrue( np.array_equal( np.round( obtained, 3 ), np.round( expected, 3 ), equal_nan=True ) )

    def test_shearCapacityUtilization( self: Self ) -> None:
        """Test calculation of shear capacity utilization."""
        # inputs
        traction: npt.NDArray[ np.float64 ] = np.copy( effectiveStress[ :, :3 ] )
        # replace nan values for calculation
        traction[ np.isnan( traction ) ] = 150.0
        rockCohesion = 250.0
        frictionAngle = 10.0 * np.pi / 180.0

        # calculation
        obtained: npt.NDArray[ np.float64 ] = fcts.shearCapacityUtilization( traction, rockCohesion, frictionAngle )
        expected: npt.NDArray[ np.float64 ] = np.array( [ 0.899, 0.923, 0.982, 1.004, 1.048 ] )

        self.assertSequenceEqual( np.round( obtained, 3 ).flatten().tolist(), expected.tolist() )

    def test_computeStressPrincipalComponents( self: Self ) -> None:
        """Test calculation of stress principal components from stress tensor."""
        obtained: list[ float ] = [ round( val, 3 ) for val in fcts.computeStressPrincipalComponents( stressTensor ) ]
        expected: tuple[ float, float, float ] = ( 1.748, 2.471, 5.281 )
        self.assertSequenceEqual( tuple( obtained ), expected )

    def test_computeStressPrincipalComponentsFromStressVector( self: Self ) -> None:
        """Test calculation of stress principal components from stress vector."""
        obtained: list[ float ] = [
            round( val, 3 ) for val in fcts.computeStressPrincipalComponentsFromStressVector( stressVector )
        ]
        expected: tuple[ float, float, float ] = ( 1.748, 2.471, 5.281 )
        self.assertSequenceEqual( tuple( obtained ), expected )

    def test_computeNormalShearStress( self: Self ) -> None:
        """Test calculation of normal and shear stress."""
        directionVector = np.array( [ 1.0, 1.0, 0.0 ] )
        obtained: list[ float ] = [
            round( val, 3 ) for val in fcts.computeNormalShearStress( stressTensor, directionVector )
        ]
        expected: tuple[ float, float ] = ( 2.250, 0.606 )
        self.assertSequenceEqual( tuple( obtained ), expected )


if __name__ == "__main__":
    unittest.main()
