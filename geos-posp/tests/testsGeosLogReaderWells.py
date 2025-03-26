# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import contextlib
import io
import os
import sys
import unittest

from typing_extensions import Self

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.join(os.path.dirname(dir_path), "src")
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

import pandas as pd  # type: ignore[import-untyped]

from geos_posp.readers.GeosLogReaderWells import GeosLogReaderWells
from geos_posp.utils.UnitRepository import Unit, UnitRepository

unitsObjSI = UnitRepository()
conversionFactors: dict[str, Unit] = unitsObjSI.getPropertiesUnit()
pathFlowSim2: str = os.path.join(dir_path, "Data/small_job_GEOS_825200_wells.out")
pathFlowSim3: str = os.path.join(dir_path, "Data/runsinglephase.txt")
pathFlowSim4: str = os.path.join(dir_path, "Data/small_job_GEOS_891567.out")
pathFlowSim5: str = os.path.join(dir_path, "Data/job_GEOS_935933.out")


class TestsGeosLogReaderWells(unittest.TestCase):
    def test1_readAllSimulation2(self: Self) -> None:
        """Test reading wells with 3 wells and 2 phases."""
        obj: GeosLogReaderWells = GeosLogReaderWells(
            pathFlowSim2, conversionFactors, ["CO2", "water"], 3
        )
        self.assertEqual(obj.m_phaseNames, ["CO2", "water"])
        self.assertEqual(
            obj.m_wellNames, ["wellControls1", "wellControls2", "wellControls3"]
        )
        expectedPropertiesValues = {
            "11:WellControls1__BHP": [12337146.157562563, 27252686.916117527],
            "12:WellControls1__TotalMassRate": [56.37348443784919, 56.32837354192296],
            "13:WellControls1__TotalSurfaceVolumetricRate": [30.024025669350802, 30],
            "14:WellControls1__SurfaceVolumetricRateCO2": [
                30.023748128796043,
                29.9997226815373,
            ],
            "14:WellControls1__SurfaceVolumetricRateWater": [
                0.00027754055475897704,
                0.00027731846270264625,
            ],
            "11:WellControls2__BHP": [13268440.020500632, 27450836.07294756],
            "12:WellControls2__TotalMassRate": [56.38455514210006, 56.32837354192296],
            "13:WellControls2__TotalSurfaceVolumetricRate": [30.029921829787227, 30],
            "14:WellControls2__SurfaceVolumetricRateCO2": [
                30.029644234728664,
                29.9997226815373,
            ],
            "14:WellControls2__SurfaceVolumetricRateWater": [
                0.0002775950585639181,
                0.00027731846270264126,
            ],
            "11:WellControls3__BHP": [12318458.650753867, 26935804.208137162],
            "12:WellControls3__TotalMassRate": [56.379144772078966, 56.32837354192296],
            "13:WellControls3__TotalSurfaceVolumetricRate": [30.027040313946728, 30],
            "14:WellControls3__SurfaceVolumetricRateCO2": [
                30.02676274552475,
                29.9997226815373,
            ],
            "14:WellControls3__SurfaceVolumetricRateWater": [
                0.0002775684219790799,
                0.00027731846270264625,
            ],
            "15:MeanBHP": [12641348.276272355, 27213109.065734085],
            "16:MeanTotalMassRate": [56.37906145067607, 56.32837354192296],
            "17:MeanTotalVolumetricRate": [30.02699593769492, 30],
            "18:MeanSurfaceVolumetricRateCO2": [30.026718369683152, 29.999722681537303],
            "18:MeanSurfaceVolumetricRateWater": [
                0.00027756801176732497,
                0.00027731846270264457,
            ],
        }
        self.assertEqual(
            list(obj.m_wellsPropertiesValues.keys()),
            list(expectedPropertiesValues.keys()),
        )
        self.assertEqual(obj.m_wellsPropertiesValues, expectedPropertiesValues)
        expectedTimesteps: list[float] = [0.0, 3.1536e07]
        self.assertEqual(obj.m_timesteps, expectedTimesteps)
        expectedDF: pd.DataFrame = pd.DataFrame()
        columns_name = [
            "11:WellControls1__BHP__Pa",
            "12:WellControls1__TotalMassRate__kg/s",
            "13:WellControls1__TotalSurfaceVolumetricRate__m3/s",
            "14:WellControls1__SurfaceVolumetricRateCO2__m3/s",
            "14:WellControls1__SurfaceVolumetricRateWater__m3/s",
            "11:WellControls2__BHP__Pa",
            "12:WellControls2__TotalMassRate__kg/s",
            "13:WellControls2__TotalSurfaceVolumetricRate__m3/s",
            "14:WellControls2__SurfaceVolumetricRateCO2__m3/s",
            "14:WellControls2__SurfaceVolumetricRateWater__m3/s",
            "11:WellControls3__BHP__Pa",
            "12:WellControls3__TotalMassRate__kg/s",
            "13:WellControls3__TotalSurfaceVolumetricRate__m3/s",
            "14:WellControls3__SurfaceVolumetricRateCO2__m3/s",
            "14:WellControls3__SurfaceVolumetricRateWater__m3/s",
            "15:MeanBHP__Pa",
            "16:MeanTotalMassRate__kg/s",
            "17:MeanTotalVolumetricRate__m3/s",
            "18:MeanSurfaceVolumetricRateCO2__m3/s",
            "18:MeanSurfaceVolumetricRateWater__m3/s",
            "Time__s",
        ]
        values = [
            [12337146.157562563, 27252686.916117527],
            [56.37348443784919, 56.32837354192296],
            [30.024025669350802, 30],
            [30.023748128796043, 29.9997226815373],
            [0.00027754055475897704, 0.00027731846270264625],
            [13268440.020500632, 27450836.07294756],
            [56.38455514210006, 56.32837354192296],
            [30.029921829787227, 30],
            [30.029644234728664, 29.9997226815373],
            [0.0002775950585639181, 0.00027731846270264126],
            [12318458.650753867, 26935804.208137162],
            [56.379144772078966, 56.32837354192296],
            [30.027040313946728, 30],
            [30.02676274552475, 29.9997226815373],
            [0.0002775684219790799, 0.00027731846270264625],
            [12641348.276272355, 27213109.065734085],
            [56.37906145067607, 56.32837354192296],
            [30.02699593769492, 30],
            [30.026718369683152, 29.999722681537303],
            [0.00027756801176732497, 0.00027731846270264457],
            [0.0, 3.1536e07],
        ]
        for column_name, value in zip(columns_name, values):
            expectedDF[column_name] = value
        obtainedDF: pd.DataFrame = obj.createDataframe()
        self.assertEqual(list(obtainedDF.columns), columns_name)
        self.assertTrue(expectedDF.equals(obtainedDF))

    def test3_readAllSimulation4(self: Self) -> None:
        """Test reading wells with 1 well and 2 phases."""
        obj: GeosLogReaderWells = GeosLogReaderWells(
            pathFlowSim4, conversionFactors, ["CO2", "water"], 1
        )
        self.assertEqual(obj.m_phaseNames, ["CO2", "water"])
        self.assertEqual(obj.m_wellNames, ["well_1Control"])
        expectedPropertiesValues = {
            "11:Well1Control__BHP": [23960094.51907003, 23318529.329811733],
            "12:Well1Control__TotalMassRate": [
                0.00029566997749602594,
                0.00029566997749602507,
            ],
            "13:Well1Control__TotalSurfaceVolumetricRate": [
                2.0000000000000063e-05,
                2e-05,
            ],
            "14:Well1Control__SurfaceVolumetricRateCO2": [
                1.9999999999987377e-05,
                1.999999999998732e-05,
            ],
            "14:Well1Control__SurfaceVolumetricRateWater": [
                1.2681312543855673e-17,
                1.2681312543888312e-17,
            ],
            "15:MeanBHP": [23960094.51907003, 23318529.329811733],
            "16:MeanTotalMassRate": [0.00029566997749602594, 0.00029566997749602507],
            "17:MeanTotalVolumetricRate": [2.0000000000000063e-05, 2e-05],
            "18:MeanSurfaceVolumetricRateCO2": [
                1.9999999999987377e-05,
                1.999999999998732e-05,
            ],
            "18:MeanSurfaceVolumetricRateWater": [
                1.2681312543855673e-17,
                1.2681312543888312e-17,
            ],
        }
        self.assertEqual(
            list(obj.m_wellsPropertiesValues.keys()),
            list(expectedPropertiesValues.keys()),
        )
        self.assertEqual(obj.m_wellsPropertiesValues, expectedPropertiesValues)
        expectedTimesteps: list[float] = [0.0, 100.0]
        self.assertEqual(obj.m_timesteps, expectedTimesteps)
        expectedDF: pd.DataFrame = pd.DataFrame()
        columns_name = [
            "11:Well1Control__BHP__Pa",
            "12:Well1Control__TotalMassRate__kg/s",
            "13:Well1Control__TotalSurfaceVolumetricRate__m3/s",
            "14:Well1Control__SurfaceVolumetricRateCO2__m3/s",
            "14:Well1Control__SurfaceVolumetricRateWater__m3/s",
            "15:MeanBHP__Pa",
            "16:MeanTotalMassRate__kg/s",
            "17:MeanTotalVolumetricRate__m3/s",
            "18:MeanSurfaceVolumetricRateCO2__m3/s",
            "18:MeanSurfaceVolumetricRateWater__m3/s",
            "Time__s",
        ]
        values = [
            [23960094.51907003, 23318529.329811733],
            [0.00029566997749602594, 0.00029566997749602507],
            [2.0000000000000063e-05, 2e-05],
            [1.9999999999987377e-05, 1.999999999998732e-05],
            [1.2681312543855673e-17, 1.2681312543888312e-17],
            [23960094.51907003, 23318529.329811733],
            [0.00029566997749602594, 0.00029566997749602507],
            [2.0000000000000063e-05, 2e-05],
            [1.9999999999987377e-05, 1.999999999998732e-05],
            [1.2681312543855673e-17, 1.2681312543888312e-17],
            [0.0, 100.0],
        ]
        for column_name, value in zip(columns_name, values):
            expectedDF[column_name] = value
        obtainedDF: pd.DataFrame = obj.createDataframe()
        self.assertEqual(list(obtainedDF.columns), columns_name)
        self.assertTrue(expectedDF.equals(obtainedDF))

    def test_invalidWellName(self: Self) -> None:
        """Test output message in case of invalid well names."""
        # TODO
        # Message being output is not tested in itself :Self, only its appearance
        capturedOutput = io.StringIO()
        with contextlib.redirect_stdout(capturedOutput):
            obj: GeosLogReaderWells = GeosLogReaderWells(
                pathFlowSim5, conversionFactors, ["CO2", "water"], 1
            )
        self.assertGreater(len(capturedOutput.getvalue()), 0)
        self.assertEqual(obj.m_phaseNames, ["CO2", "water"])
        self.assertEqual(obj.m_wellNames, ["well_1Control"])


if __name__ == "__main__":
    unittest.main()
