# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import contextlib
import io
import os
import sys
import unittest

import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.join(os.path.dirname(dir_path), "src")
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

from geos_posp.readers.GeosLogReaderFlow import GeosLogReaderFlow
from geos_posp.utils.UnitRepository import Unit, UnitRepository

unitsObjSI: UnitRepository = UnitRepository()
conversionFactors: dict[str, Unit] = unitsObjSI.getPropertiesUnit()
pathFlowSim: str = os.path.join(dir_path, "Data/job_GEOS_825200.out")
pathFlowSim2: str = os.path.join(dir_path, "Data/small_job_GEOS_825200.out")
pathFlowSim8: str = os.path.join(
    dir_path, "Data/depleted_gas_reservoir_newwell_report.out"
)


class TestsFunctionsGeosLogReader(unittest.TestCase):

    def test0_regionsPropertiesKeysSimulation1(self: Self) -> None:
        """Test case 2 phases, 5 regions, for time steps."""
        obj: GeosLogReaderFlow = GeosLogReaderFlow(
            pathFlowSim, conversionFactors, ["CO2", "water"]
        )
        self.assertEqual(
            obj.m_regionNames,
            ["Reservoir", "Caprock", "Overburden", "Underburden", "Salt"],
        )
        self.assertEqual(obj.m_computeStatisticsName, "compflowStatistics")
        self.assertEqual(obj.m_phaseNames, ["CO2", "water"])
        expected: list[str] = [
            "1:Reservoir__PressureMin",
            "1:Reservoir__PressureAverage",
            "1:Reservoir__PressureMax",
            "0:Reservoir__DeltaPressureMin",
            "0:Reservoir__DeltaPressureMax",
            "2:Reservoir__TemperatureMin",
            "2:Reservoir__TemperatureAverage",
            "2:Reservoir__TemperatureMax",
            "3:Reservoir__TotalDynamicPoreVolume",
            "4:Reservoir__CO2DynamicPoreVolumes",
            "4:Reservoir__WaterDynamicPoreVolumes",
            "10:Reservoir__CO2Mass",
            "10:Reservoir__WaterMass",
            "6:Reservoir__TrappedCO2Mass",
            "6:Reservoir__TrappedWaterMass",
            "5:Reservoir__NonTrappedCO2Mass",
            "5:Reservoir__NonTrappedWaterMass",
            "7:Reservoir__ImmobileCO2Mass",
            "7:Reservoir__ImmobileWaterMass",
            "8:Reservoir__MobileCO2Mass",
            "8:Reservoir__MobileWaterMass",
            "9:Reservoir__DissolvedMassCO2InCO2",
            "9:Reservoir__DissolvedMassWaterInCO2",
            "9:Reservoir__DissolvedMassCO2InWater",
            "9:Reservoir__DissolvedMassWaterInWater",
            "1:Caprock__PressureMin",
            "1:Caprock__PressureAverage",
            "1:Caprock__PressureMax",
            "0:Caprock__DeltaPressureMin",
            "0:Caprock__DeltaPressureMax",
            "2:Caprock__TemperatureMin",
            "2:Caprock__TemperatureAverage",
            "2:Caprock__TemperatureMax",
            "3:Caprock__TotalDynamicPoreVolume",
            "4:Caprock__CO2DynamicPoreVolumes",
            "4:Caprock__WaterDynamicPoreVolumes",
            "10:Caprock__CO2Mass",
            "10:Caprock__WaterMass",
            "6:Caprock__TrappedCO2Mass",
            "6:Caprock__TrappedWaterMass",
            "5:Caprock__NonTrappedCO2Mass",
            "5:Caprock__NonTrappedWaterMass",
            "7:Caprock__ImmobileCO2Mass",
            "7:Caprock__ImmobileWaterMass",
            "8:Caprock__MobileCO2Mass",
            "8:Caprock__MobileWaterMass",
            "9:Caprock__DissolvedMassCO2InCO2",
            "9:Caprock__DissolvedMassWaterInCO2",
            "9:Caprock__DissolvedMassCO2InWater",
            "9:Caprock__DissolvedMassWaterInWater",
            "1:Overburden__PressureMin",
            "1:Overburden__PressureAverage",
            "1:Overburden__PressureMax",
            "0:Overburden__DeltaPressureMin",
            "0:Overburden__DeltaPressureMax",
            "2:Overburden__TemperatureMin",
            "2:Overburden__TemperatureAverage",
            "2:Overburden__TemperatureMax",
            "3:Overburden__TotalDynamicPoreVolume",
            "4:Overburden__CO2DynamicPoreVolumes",
            "4:Overburden__WaterDynamicPoreVolumes",
            "10:Overburden__CO2Mass",
            "10:Overburden__WaterMass",
            "6:Overburden__TrappedCO2Mass",
            "6:Overburden__TrappedWaterMass",
            "5:Overburden__NonTrappedCO2Mass",
            "5:Overburden__NonTrappedWaterMass",
            "7:Overburden__ImmobileCO2Mass",
            "7:Overburden__ImmobileWaterMass",
            "8:Overburden__MobileCO2Mass",
            "8:Overburden__MobileWaterMass",
            "9:Overburden__DissolvedMassCO2InCO2",
            "9:Overburden__DissolvedMassWaterInCO2",
            "9:Overburden__DissolvedMassCO2InWater",
            "9:Overburden__DissolvedMassWaterInWater",
            "1:Underburden__PressureMin",
            "1:Underburden__PressureAverage",
            "1:Underburden__PressureMax",
            "0:Underburden__DeltaPressureMin",
            "0:Underburden__DeltaPressureMax",
            "2:Underburden__TemperatureMin",
            "2:Underburden__TemperatureAverage",
            "2:Underburden__TemperatureMax",
            "3:Underburden__TotalDynamicPoreVolume",
            "4:Underburden__CO2DynamicPoreVolumes",
            "4:Underburden__WaterDynamicPoreVolumes",
            "10:Underburden__CO2Mass",
            "10:Underburden__WaterMass",
            "6:Underburden__TrappedCO2Mass",
            "6:Underburden__TrappedWaterMass",
            "5:Underburden__NonTrappedCO2Mass",
            "5:Underburden__NonTrappedWaterMass",
            "7:Underburden__ImmobileCO2Mass",
            "7:Underburden__ImmobileWaterMass",
            "8:Underburden__MobileCO2Mass",
            "8:Underburden__MobileWaterMass",
            "9:Underburden__DissolvedMassCO2InCO2",
            "9:Underburden__DissolvedMassWaterInCO2",
            "9:Underburden__DissolvedMassCO2InWater",
            "9:Underburden__DissolvedMassWaterInWater",
            "1:Salt__PressureMin",
            "1:Salt__PressureAverage",
            "1:Salt__PressureMax",
            "0:Salt__DeltaPressureMin",
            "0:Salt__DeltaPressureMax",
            "2:Salt__TemperatureMin",
            "2:Salt__TemperatureAverage",
            "2:Salt__TemperatureMax",
            "3:Salt__TotalDynamicPoreVolume",
            "4:Salt__CO2DynamicPoreVolumes",
            "4:Salt__WaterDynamicPoreVolumes",
            "10:Salt__CO2Mass",
            "10:Salt__WaterMass",
            "6:Salt__TrappedCO2Mass",
            "6:Salt__TrappedWaterMass",
            "5:Salt__NonTrappedCO2Mass",
            "5:Salt__NonTrappedWaterMass",
            "7:Salt__ImmobileCO2Mass",
            "7:Salt__ImmobileWaterMass",
            "8:Salt__MobileCO2Mass",
            "8:Salt__MobileWaterMass",
            "9:Salt__DissolvedMassCO2InCO2",
            "9:Salt__DissolvedMassWaterInCO2",
            "9:Salt__DissolvedMassCO2InWater",
            "9:Salt__DissolvedMassWaterInWater",
        ]
        obtained: list[str] = list(obj.m_regionsPropertiesValues.keys())
        self.assertEqual(expected, obtained)
        expectedTimesteps: list[float] = [
            0.0,
            3.1536e07,
            6.3072e07,
            9.4608e07,
            1.26144e08,
            1.5768e08,
            1.89216e08,
            2.20752e08,
            2.52288e08,
            2.83824e08,
            3.1536e08,
            3.46896e08,
            3.78432e08,
            4.09968e08,
            4.41504e08,
            4.7304e08,
        ]
        self.assertEqual(obj.m_timesteps, expectedTimesteps)

    def test1_readAllSimulation2(self: Self) -> None:
        """Test case 2 phases, 2 regions, for time steps."""
        obj: GeosLogReaderFlow = GeosLogReaderFlow(
            pathFlowSim2, conversionFactors, ["CO2", "water"]
        )
        self.assertEqual(obj.m_regionNames, ["Reservoir", "Caprock"])
        self.assertEqual(obj.m_phaseNames, ["CO2", "water"])
        self.assertEqual(obj.m_computeStatisticsName, "compflowStatistics")
        regionPropertiesValuesExpected: dict[str, list[float]] = {
            "1:Reservoir__PressureMin": [1.25e07, 2.80948e07],
            "1:Reservoir__PressureAverage": [1.25e07, 2.99421e07],
            "1:Reservoir__PressureMax": [1.25e07, 3.12538e07],
            "8:Reservoir__MobileCO2Mass": [0.0, 1.3012e07],
            "8:Reservoir__MobileWaterMass": [6.38235e10, 6.51497e10],
            "1:Caprock__PressureMin": [1.25e07, 2.76478e07],
            "1:Caprock__PressureAverage": [1.25e07, 2.89944e07],
            "1:Caprock__PressureMax": [1.25e07, 2.98486e07],
            "8:Caprock__MobileCO2Mass": [0.0, 2.19936e07],
            "8:Caprock__MobileWaterMass": [1.25037e10, 1.27238e10],
        }
        self.assertEqual(obj.m_regionsPropertiesValues, regionPropertiesValuesExpected)
        expectedTimesteps: list[float] = [0.0, 3.1536e07]
        self.assertEqual(obj.m_timesteps, expectedTimesteps)

    def test2_DataframeFlowSimulation2(self: Self) -> None:
        """Test case 2 phases, 2 regions, for dataframe creation."""
        obj: GeosLogReaderFlow = GeosLogReaderFlow(
            pathFlowSim2, conversionFactors, ["CO2", "water"]
        )
        data: dict[str, list[float]] = {
            "1:Reservoir__PressureMin__Pa": [1.25e07, 2.80948e07],
            "1:Reservoir__PressureAverage__Pa": [1.25e07, 2.99421e07],
            "1:Reservoir__PressureMax__Pa": [1.25e07, 3.12538e07],
            "8:Reservoir__MobileCO2Mass__kg": [0.0, 1.3012e07],
            "8:Reservoir__MobileWaterMass__kg": [6.38235e10, 6.51497e10],
            "1:Caprock__PressureMin__Pa": [1.25e07, 2.76478e07],
            "1:Caprock__PressureAverage__Pa": [1.25e07, 2.89944e07],
            "1:Caprock__PressureMax__Pa": [1.25e07, 2.98486e07],
            "8:Caprock__MobileCO2Mass__kg": [0.0, 2.19936e07],
            "8:Caprock__MobileWaterMass__kg": [1.25037e10, 1.27238e10],
            "Time__s": [0.0, 3.1536e07],
        }
        expected: pd.DataFrame = pd.DataFrame(data)
        obtained: pd.DataFrame = obj.createDataframe()
        self.assertTrue(expected.equals(obtained))

    def test_depleted_gas_reservoir_newwell_report(self: Self) -> None:
        """Test case dt is missing."""
        obj: GeosLogReaderFlow = GeosLogReaderFlow(pathFlowSim8, conversionFactors)
        self.assertEqual(obj.m_regionNames, ["Region1"])
        self.assertEqual(obj.m_phaseNames, ["phase0", "phase1"])
        self.assertEqual(obj.m_computeStatisticsName, "compflowStatistics")


if __name__ == "__main__":
    unittest.main()
