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

from geos_posp.processing import geosLogReaderFunctions as utils
from geos.utils.enumUnits import Unit, getSIUnits


class TestsFunctionsGeosLogReader(unittest.TestCase):
    def test_replaceSpecialCharactersWithWhitespace(self: Self) -> None:
        """Test replaceSpecialCharactersWithWhitespace function."""
        example: str = "hi '(_there(''&*$^,:;'"
        expected: str = "hi    there           "
        obtained: str = utils.replaceSpecialCharactersWithWhitespace(example)
        self.assertEqual(expected, obtained)

    def test_formatPropertyName(self: Self) -> None:
        """Test formatPropertyName function."""
        example: str = " Delta pressure min"
        expected: str = "DeltaPressureMin"
        obtained: str = utils.formatPropertyName(example)
        self.assertEqual(expected, obtained)

    def test_extractRegion(self: Self) -> None:
        """Test extractRegion function."""
        example: str = (
            "Adding Object CellElementRegion named Reservoir from"
            " ObjectManager::Catalog."
        )
        expected: str = "Reservoir"
        obtained: str = utils.extractRegion(example)
        self.assertEqual(expected, obtained)

    def test_extractStatsName(self: Self) -> None:
        """Test extractStatsName function."""
        example: str = (
            "compflowStatistics, Reservoir: Pressure (min, average, max): "
            "2.86419e+07, 2.93341e+07, 3.006e+07 Pa"
        )
        expected: str = "compflowStatistics"
        obtained: str = utils.extractStatsName(example)
        self.assertEqual(expected, obtained)

    def test_extractPhaseModel(self: Self) -> None:
        """Test extractPhaseModel function."""
        example: str = (
            "   TableFunction: " "fluid_phaseModel1_PhillipsBrineDensity_table"
        )
        expected: str = "PhillipsBrineDensity"
        obtained: str = utils.extractPhaseModel(example)
        self.assertEqual(expected, obtained)

    def test_buildPropertiesNameForPhases(self: Self) -> None:
        """Test buildPropertiesNameForPhases function."""
        example_block: str = " Mobile phase mass"
        example_phases: list[str] = ["CO2", "Water"]
        expected: list[str] = [" Mobile CO2 mass", " Mobile Water mass"]
        obtained: list[str] = utils.buildPropertiesNameForPhases(
            example_block, example_phases
        )
        self.assertEqual(expected, obtained)

    def test_buildPropertiesNameForComponents(self: Self) -> None:
        """Test buildPropertiesNameForComponents function."""
        example: list[str] = ["CO2", "Water"]
        expected: list[str] = [
            "Dissolved mass CO2 in CO2",
            "Dissolved mass Water in CO2",
            "Dissolved mass CO2 in Water",
            "Dissolved mass Water in Water",
        ]
        obtained: list[str] = utils.buildPropertiesNameForComponents(example)
        self.assertEqual(expected, obtained)

    def test_buildPropertiesNameNoPhases(self: Self) -> None:
        """Test buildPropertiesNameNoPhases function."""
        example_name_block: str = " Delta pressure "
        example_extensions: str = "min, max)"
        expected: list[str] = [" Delta pressure  min", " Delta pressure  max"]
        obtained: list[str] = utils.buildPropertiesNameNoPhases(
            example_name_block, example_extensions
        )
        self.assertEqual(expected, obtained)

    def test_buildPropertiesNameNoPhases2(self: Self) -> None:
        """Test buildPropertiesNameNoPhases function."""
        example: str = " Delta pressure "
        expected: list[str] = [" Delta pressure "]
        obtained: list[str] = utils.buildPropertiesNameNoPhases(example)
        self.assertEqual(expected, obtained)

    def test_buildPropertiesNameFromGeosProperties(self: Self) -> None:
        """Test buildPropertiesNameFromGeosProperties function."""
        examples_phases: list[str] = ["CO2", "Water"]
        example: str = " Pressure (min, average, max)"
        expected: list[str] = [" Pressure  min", " Pressure  average", " Pressure  max"]
        obtained: list[str] = utils.buildPropertiesNameFromGeosProperties(
            example, examples_phases
        )
        self.assertEqual(expected, obtained)

        example = " Total dynamic pore volume"
        expected = [" Total dynamic pore volume"]
        obtained = utils.buildPropertiesNameFromGeosProperties(example, examples_phases)
        self.assertEqual(expected, obtained)

        example = " Non-trapped phase mass (metric 1)"
        expected = [" Non-trapped CO2 mass ", " Non-trapped Water mass "]
        obtained = utils.buildPropertiesNameFromGeosProperties(example, examples_phases)
        self.assertEqual(expected, obtained)

        example = " Dissolved component mass"
        expected = [
            "Dissolved mass CO2 in CO2",
            "Dissolved mass Water in CO2",
            "Dissolved mass CO2 in Water",
            "Dissolved mass Water in Water",
        ]
        obtained = utils.buildPropertiesNameFromGeosProperties(example, examples_phases)
        self.assertEqual(expected, obtained)

        example = " Component mass"
        expected = [
            "Dissolved mass CO2 in CO2",
            "Dissolved mass Water in CO2",
            "Dissolved mass CO2 in Water",
            "Dissolved mass Water in Water",
        ]
        obtained = utils.buildPropertiesNameFromGeosProperties(example, examples_phases)
        self.assertEqual(expected, obtained)

    def test_extractPropertiesFlow(self: Self) -> None:
        """Test extractPropertiesFlow function."""
        example_block: str = (
            "compflowStatistics, Reservoir: Trapped phase mass (metric 1):"
            "  { 0, 1.9147e+10 } kg"
        )
        examples_phases: list[str] = ["CO2", "Water"]
        expected: list[str] = [
            "Reservoir__TrappedCO2Mass",
            "Reservoir__TrappedWaterMass",
        ]
        obtained: list[str] = utils.extractPropertiesFlow(
            example_block, examples_phases
        )
        self.assertEqual(expected, obtained)

        example_block = (
            "compflowStatistics, Reservoir: Phase mass:" " { 0, 1.01274e+14 } kg"
        )
        expected = ["Reservoir__CO2Mass", "Reservoir__WaterMass"]
        obtained = utils.extractPropertiesFlow(example_block, examples_phases)
        self.assertEqual(expected, obtained)

        example_block = (
            "compflowStatistics, Region1 (time 4320000 s): Pressure"
            " (min, average, max): 10984659.811871096, 11257138.433702637,"
            " 11535137.236653088 Pa"
        )
        expected = [
            "Region1__PressureMin",
            "Region1__PressureAverage",
            "Region1__PressureMax",
        ]
        obtained = utils.extractPropertiesFlow(example_block, examples_phases)
        self.assertEqual(expected, obtained)

    def test_countNumberLines(self: Self) -> None:
        """Test countNumberLines function."""
        log1: str = os.path.join(dir_path, "Data/job_GEOS_825200.out")
        expected1: int = 24307
        obtained1: int = utils.countNumberLines(log1)
        self.assertEqual(expected1, obtained1)

    def test_extractValuesFlow(self: Self) -> None:
        """Test extractValuesFlow function."""
        example: str = (
            "compflowStatistics, Reservoir: Pressure (min, average, max):"
            " 1.25e+07, 1.25e+07, 1.25e+07 Pa"
        )
        expected: list[float] = [1.25e07, 1.25e07, 1.25e07]
        obtained: list[float] = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

        example = (
            "compflowStatistics, Reservoir: Phase dynamic pore volumes:"
            " { 0, 6.61331e+07 } rm^3"
        )
        expected = [0.0, 6.61331e07]
        obtained = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

        example = (
            "compflowStatistics, Reservoir: Dissolved component mass:"
            " { { 0, 0 }, { 0, 6.38235e+10 } } kg"
        )
        expected = [0.0, 0.0, 0.0, 6.38235e10]
        obtained = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

        example = (
            "compflowStatistics, Reservoir: Cell fluid mass"
            " (min, max): 10765.1, 2.2694e+10 kg"
        )
        expected = [10765.1, 2.2694e10]
        obtained = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

        example = (
            "compflowStatistics, Region1 (time 256800000 s): Pressure"
            " (min, average, max): 10023287.92961521, 10271543.591259222,"
            " 10525096.98374942 Pa"
        )
        expected = [10023287.92961521, 10271543.591259222, 10525096.98374942]
        obtained = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

        example = (
            "compflowStatistics, Region1 (time 4320000 s): Phase dynamic"
            " pore volume: [0, 799999924.1499865] rm^3"
        )
        expected = [0, 799999924.1499865]
        obtained = utils.extractValuesFlow(example)
        self.assertEqual(expected, obtained)

    def test_convertValues(self: Self) -> None:
        """Test convertValues function."""
        propertyNames: list[str] = [" Delta pressure min ", " CO2 volume "]
        propertyValues: list[float] = [1e6, 2e8]
        propertyUnits: dict[str, Unit] = getSIUnits()
        expected: list[float] = [1e6, 2e8]
        obtained: list[float] = utils.convertValues(
            propertyNames, propertyValues, propertyUnits
        )
        self.assertEqual(expected, obtained)

        propertyNames = ["WellControls__TotalFluidDensity"]
        propertyValues = [1e4]
        expected = [1e4]
        obtained = utils.convertValues(propertyNames, propertyValues, propertyUnits)
        self.assertEqual(expected, obtained)

    def test_extractWell(self: Self) -> None:
        """Test extractWell function."""
        line = "   TableFunction: well.CO2001_ConstantBHP_table"
        expected = "well.CO2001"
        obtained = utils.extractWell(line)
        self.assertEqual(expected, obtained)

    def test_identifyCurrentWell(self: Self) -> None:
        """Test identifyCurrentWell function."""
        lastWellName: str = "well1"
        line: str = (
            "The total rate is 0 kg/s, which corresponds to a"
            + "total surface volumetric rate of 0 sm3/s"
        )
        expected: str = "well1"
        obtained: str = utils.identifyCurrentWell(line, lastWellName)
        self.assertEqual(expected, obtained)

        line = (
            "Rank 18: well.CO2001: BHP (at the specified reference"
            + " elevation): 19318538.400682557 Pa"
        )
        expected = "well.CO2001"
        obtained = utils.identifyCurrentWell(line, lastWellName)
        self.assertEqual(expected, obtained)

        line = (
            "wellControls1: BHP (at the specified reference"
            + " elevation): 12337146.157562563 Pa"
        )
        expected = "wellControls1"
        obtained = utils.identifyCurrentWell(line, lastWellName)
        self.assertEqual(expected, obtained)

    def test_extractWellTags(self: Self) -> None:
        """Test extractWellTags function."""
        line: str = (
            "Rank 18: well.CO2001: BHP "
            + "(at the specified reference elevation): 193000 Pa"
        )
        expected: list[str] = ["BHP"]
        obtained: list[str] = utils.extractWellTags(line)
        self.assertEqual(expected, obtained)

        line = (
            "The total rate is 0 kg/s, which corresponds"
            + " to a total surface volumetric rate of 0 sm3/s"
        )
        expected = ["total massRate", "total surface volumetricRate"]
        obtained = utils.extractWellTags(line)
        self.assertEqual(expected, obtained)

    def test_extractValuesWell(self: Self) -> None:
        """Test extractValuesWell function."""
        line: str = (
            "Rank 18: well.CO2001: BHP "
            + "(at the specified reference elevation): 193000 Pa"
        )
        expected: list[float] = [193000.0]
        obtained: list[float] = utils.extractValuesWell(line, 1)
        self.assertEqual(expected, obtained)
        line = (
            "The total rate is 0 kg/s, which corresponds"
            + " to a total surface volumetric rate of 0 sm3/s"
        )
        expected = [0.0, 0.0]
        obtained = utils.extractValuesWell(line, 2)
        self.assertEqual(expected, obtained)

        line = "The phase surface volumetric rate is" + " 1.9466968733035026e-12 sm3/s"
        expected = [1.9466968733035026e-12]
        obtained = utils.extractValuesWell(line, 1)
        self.assertEqual(expected, obtained)

    def test_extractAquifer(self: Self) -> None:
        """Test extractAquifer function."""
        line: str = "   TableFunction:aquifer1_pressureInfluence_table"
        expected: str = "aquifer1"
        obtained: str = utils.extractAquifer(line)
        self.assertEqual(expected, obtained)

    def test_extractValueAndNameAquifer(self: Self) -> None:
        """Test extractValueAndNameAquifer function."""
        line: str = (
            "FlowSolverBase compositionalMultiphaseFlow"
            + " (SimuDeck_aquifer_pression_meme.xml, l.28): at time 100s, the"
            + " <Aquifer> boundary condition 'aquifer1' produces a flux of"
            + " -0.6181975187076816 kg (or moles if useMass=0)."
        )
        expected: tuple[str, float] = ("aquifer1", -0.6181975187076816)
        obtained: tuple[str, float] = utils.extractValueAndNameAquifer(line)
        self.assertEqual(expected, obtained)

        line = (
            "FlowSolverBase compositionalMultiphaseFVMSolver"
            + " (nl_multiphase_with_well_reservoir_homo_for_Pierre_versionPaul"
            + "_hysteresisIX.xml, l.31): at time 25636.406820617773s, the"
            + " <Aquifer> boundary condition 'Aquifer3' produces a flux of"
            + " -0.8441759009606705 kg (or moles if useMass=0). "
        )
        expected = ("Aquifer3", -0.8441759009606705)
        obtained = utils.extractValueAndNameAquifer(line)
        self.assertEqual(expected, obtained)

    def test_extractNewtonIter(self: Self) -> None:
        """Test extractNewtonIter function."""
        line: str = "    Attempt:  2, ConfigurationIter:  1, NewtonIter:  8"
        expected: int = 8
        obtained: int = utils.extractNewtonIter(line)
        self.assertEqual(expected, obtained)

    def test_extractLinearIter(self: Self) -> None:
        """Test extractLinearIter function."""
        line: str = (
            "    Linear Solver | Success | Iterations: 23 | Final Rel Res:"
            + " 5.96636e-05 | Make Restrictor Time: 0 | Compute Auu Time: 0 |"
            + " SC Filter Time: 0 | Setup Time: 1.5156 s | Solve Time:"
            + " 0.041093 s"
        )
        expected: int = 23
        obtained: int = utils.extractLinearIter(line)
        self.assertEqual(expected, obtained)

    def test_timeInSecond(self: Self) -> None:
        """Test timeInSecond function."""
        timeCounter: dict[str, float] = {
            "years": 0,
            "days": 0,
            "hrs": 0,
            "min": 0,
            "s": 0,
        }
        expected: float = 0.0
        obtained: float = utils.timeInSecond(timeCounter)
        self.assertEqual(expected, obtained)

        timeCounter = {"years": 1, "days": 1, "hrs": 1, "min": 1, "s": 1}
        expected = 31647661.0
        obtained = utils.timeInSecond(timeCounter)
        self.assertEqual(expected, obtained)

    def test_extractTimeAndDt(self: Self) -> None:
        """Test extractTimeAndDt function."""
        line: str = "Time: 1 s, dt: 1 s, Cycle: 0"
        expected: tuple[float, float] = (1.0, 1.0)
        obtained: tuple[float, float] = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1s, dt: 1s, Cycle: 0"
        expected = (1.0, 1.0)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1e5s, dt: 1e6s, Cycle: 0"
        expected = (1.0e5, 1.0e6)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1 min, dt: 1 s, Cycle: 0"
        expected = (60.0, 1.0)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1 hrs, dt: 1 s, Cycle: 0"
        expected = (3600.0, 1.0)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1 days, dt: 1 s, Cycle: 0"
        expected = (86400.0, 1.0)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

        line = "Time: 1 years, 1 days, 1 hrs, 1 min, 1 s, dt: 1 s, Cycle: 1"
        expected = (31647661.0, 1.0)
        obtained = utils.extractTimeAndDt(line)
        self.assertEqual(expected, obtained)

    def test_identifyProperties(self: Self) -> None:
        """Test identifyProperties function."""
        properties: list[str] = ["WellControls_TotalFluidDensity"]
        expected: list[str] = ["35:WellControls_TotalFluidDensity"]
        obtained: list[str] = utils.identifyProperties(properties)
        self.assertEqual(expected, obtained)

    def test_findNumberPhasesSimulation(self: Self) -> None:
        """Test findNumberPhasesSimulation function."""
        filename: str = "job_GEOS_825200.out"
        pathToFile: str = os.path.join(dir_path, "Data/")
        filepath: str = os.path.join(pathToFile, filename)
        expected: int = 2
        obtained: int = utils.findNumberPhasesSimulation(filepath)
        self.assertEqual(expected, obtained)

    def test_transformUserChoiceToListPhases(self: Self) -> None:
        """Test phaseNameBuilder function with 3 phases."""
        userChoice: str = "phase0 phase1 phase2"
        expected: list[str] = ["phase0", "phase1", "phase2"]
        obtained: list[str] = utils.transformUserChoiceToListPhases(userChoice)
        self.assertEqual(expected, obtained)

        userChoice = "phase0, phase1, phase2"
        expected = ["phase0", "phase1", "phase2"]
        obtained = utils.transformUserChoiceToListPhases(userChoice)
        self.assertEqual(expected, obtained)

        userChoice = "phase0; phase1; phase2"
        expected = []
        capturedOutput = io.StringIO()
        with contextlib.redirect_stdout(capturedOutput):
            obtained = utils.transformUserChoiceToListPhases(userChoice)
        self.assertEqual(expected, obtained)
        self.assertGreater(len(capturedOutput.getvalue()), 0)

    def test_phaseNamesBuilder(self: Self) -> None:
        """Test phaseNameBuilder function with 4 phases."""
        phasesFromUser: list[str] = []
        expected: list[str] = ["phase0", "phase1", "phase2", "phase3"]
        obtained: list[str] = utils.phaseNamesBuilder(4, phasesFromUser)
        self.assertEqual(expected, obtained)

        phasesFromUser = ["water", "gas"]
        expected = ["water", "gas", "phase2", "phase3"]
        obtained = utils.phaseNamesBuilder(4, phasesFromUser)
        self.assertEqual(expected, obtained)

        phasesFromUser = ["water", "CO2", "N2", "H2", "CH4"]
        expected = ["water", "CO2", "N2", "H2"]
        obtained = utils.phaseNamesBuilder(4, phasesFromUser)
        self.assertEqual(expected, obtained)

    # TODO def test_extractValuesFromBlockWhenMultipleComponents(self :Self)


if __name__ == "__main__":
    unittest.main()
