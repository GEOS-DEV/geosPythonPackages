# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.join( os.path.dirname( dir_path ), "src" )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

from geos.utils.UnitRepository import Unit, UnitRepository
from geos_posp.readers.GeosLogReaderConvergence import GeosLogReaderConvergence

unitsObjSI: UnitRepository = UnitRepository()
conversionFactors: dict[ str, Unit ] = unitsObjSI.getPropertiesUnit()
pathFlowSim: str = os.path.join( dir_path, "Data/small_job_GEOS_246861.out" )


class TestsFunctionsGeosLogReaderConvergence( unittest.TestCase ):

    def test1_readAllSimulation( self: Self ) -> None:
        """Test convergence reader."""
        obj: GeosLogReaderConvergence = GeosLogReaderConvergence( pathFlowSim, conversionFactors )
        expectedPropertiesValues = {
            "23:NewtonIter": [ 1, 1, 1 ],
            "24:LinearIter": [ 1, 2, 2 ],
            "23:CumulatedNewtonIter": [ 1, 2, 3 ],
            "24:CumulatedLinearIter": [ 1, 3, 5 ],
        }
        self.assertEqual(
            list( obj.m_solversIterationsValues.keys() ),
            list( expectedPropertiesValues.keys() ),
        )
        self.assertEqual( obj.m_solversIterationsValues, expectedPropertiesValues )
        expectedTimesteps: list[ float ] = [ 0.0, 8600.0, 25724.3 ]
        self.assertEqual( obj.m_timesteps, expectedTimesteps )
        expectedDts: list[ float ] = [ 8600.0, 17124.3, 34165.3 ]
        self.assertEqual( obj.m_dts, expectedDts )
        expectedDF: pd.DataFrame = pd.DataFrame()
        columns_name = [
            "23:NewtonIter",
            "24:LinearIter",
            "23:CumulatedNewtonIter",
            "24:CumulatedLinearIter",
            "Time__s",
            "dt__s",
        ]
        values: list[ list[ float ] ] = [
            [ 1.0, 1.0, 1.0 ],
            [ 1.0, 2.0, 2.0 ],
            [ 1.0, 2.0, 3.0 ],
            [ 1.0, 3.0, 5.0 ],
            [ 0.0, 8600.0, 25724.3 ],
            [ 8600.0, 17124.3, 34165.3 ],
        ]
        for column_name, value in zip( columns_name, values, strict=False ):
            expectedDF[ column_name ] = value
        obtainedDF: pd.DataFrame = obj.createDataframe()
        self.assertEqual( list( obtainedDF.columns ), columns_name )
        self.assertTrue( expectedDF.equals( obtainedDF ) )


if __name__ == "__main__":
    unittest.main()
