# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from io import TextIOBase
from typing import Union

import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

import geos_pv.geosLogReaderUtils.geosLogReaderFunctions as fcts
from geos_utils.enumUnits import Unit


class GeosLogReaderFlow:
    def __init__(
        self: Self,
        filepath: str,
        propertiesUnit: dict[str, Unit],
        phaseNames: Union[list[str], None] = None,
    ) -> None:
        """A reader that reads .txt and .out files containing Geos logs.

        To do that, we use specific tags in the current version of this code.
        Supposed tags are:

        * for region names: "Adding Object CellElementRegion" Supposed
            line:"Adding Object CellElementRegion named Reservoir from
            ObjectManager::Catalog".
        * for phase names: "phaseModel" Supposed line: "   TableFunction:
            fluid_phaseModel1_PhillipsBrineDensity_table".
        * for timesteps: "Time:" Supposed line: "Time: 0s, dt:100s, Cycle: 0".
        * for CFL properties: "CFL". Supposed line: "compflowStatistics: Max
            phase CFL number: 0.00696878"

        Another important tag in the log will be the name
        of the flow statistics model used to output 2D data
        in the Geos Log. This one will be found automatically.
        The flow statistics model that can output flow data are:

        * "SinglePhaseStatistics".
        * "CompositionalMultiphaseStatistics".

        Args:
            filepath (str): path to Geos log file
            propertiesUnit (dict[str, Unit]): unit preferences
            phaseNames (list[str], optional): Name of the phases.

                Defaults to [].
        """
        self.m_propertiesUnit = propertiesUnit
        self.m_regionNames: list[str] = []
        numberPhases: int = fcts.findNumberPhasesSimulation(filepath)

        if phaseNames is None:
            phaseNames = []
        self.m_phaseNames: list[str] = fcts.phaseNamesBuilder(numberPhases, phaseNames)
        self.m_computeStatisticsName: str = ""
        self.m_regionsPropertiesValues: dict[str, list[float]] = {}
        self.m_timesteps: list[float] = []

        toFindInLog: list[str] = ["Adding Object CellElementRegion", "Time: 0"]
        if not fcts.elementsAreInLog(filepath, toFindInLog):
            print(
                "Invalid Geos log file. Please check that your log"
                + " did not crash and contains statistics on flow properties."
            )
        else:
            self.readAll(filepath)

    def readRegionNames(self: Self, file: TextIOBase) -> int:
        """Initialize the m_regionNames attribute by reading log file.

        Args:
            file (TextIOBase): Geos Log file

        Returns:
            int: The id of the last line read that contained the tag
            "Adding Object CellElementRegion"
        """
        regionsName: list[str] = []
        line: str = file.readline()
        id_line: int = 1
        while "Adding Object CellElementRegion" not in line:
            line = file.readline()
            id_line += 1
        while "Adding Object CellElementRegion" in line:
            regionName: str = fcts.extractRegion(line)
            regionsName.append(regionName)
            line = file.readline()
            id_line += 1
        self.m_regionNames = regionsName
        return id_line

    def readComputeStatisticsName(
        self: Self, file: TextIOBase, id_line: int, total_lines: int
    ) -> tuple[int, str]:
        """Read flow statistics from the Geos log file.

        Args:
            file (TextIOBase): Geos Log file
            id_line (int): The id of the last line read in readPhaseNames.
            total_lines (int): total number of lines in the file.

        Returns:
            tuple[int, str]: Tuple containingt the id of the last line read and
            the line.
        """
        computeStatisticsName: str = ""
        line: str = file.readline()
        id_line += 1
        while not line.startswith("Time: 0"):
            line = file.readline()
            id_line += 1
        keepReading: bool = True
        while keepReading:
            line = file.readline()
            id_line += 1
            if id_line > total_lines:
                raise ValueError("No statistics name found in the log")
            for regionName in self.m_regionNames:
                if regionName in line:
                    computeStatisticsName = fcts.extractStatsName(line)
                    keepReading = False
                    break
        self.m_computeStatisticsName = computeStatisticsName
        return (id_line, line)

    def readPropertiesValues(
        self: Self, file: TextIOBase, id_line: int, total_lines: int, lineTagStats: str
    ) -> None:
        """Read property values from Geos log file.

        Initialize the m_regionsPropertiesValues and m_timesteps attributes
        by reading the Geos log. If a timestep contains the tag
        m_computeStatisticsName, the current timestep is added to m_timesteps
        and we recover the property values in m_regionsPropertiesValues.

        Args:
            file (TextIOBase): Geos Log file
            id_line (int): The id of the last line read in readPhaseNames.
            total_lines (int): The number of lines in the file.
            lineTagStats (str): The first line containing the tag of
                the flow statistics model.
        """
        regionPropertiesValues: dict[str, list[float]] = {}
        newTimestep: float = 0.0
        timesteps: list[float] = [newTimestep]
        line: str = lineTagStats
        while id_line <= total_lines:
            if line.startswith("Time:"):
                newTimestep, dt = fcts.extractTimeAndDt(line)
                newTimestep = fcts.convertValues(
                    ["Time"], [newTimestep], self.m_propertiesUnit
                )[0]
            if self.m_computeStatisticsName in line and "CFL" not in line:
                if newTimestep not in timesteps and newTimestep > max(
                    timesteps, default=0.0
                ):
                    timesteps.append(newTimestep)
                    for key in regionPropertiesValues:
                        regionPropertiesValues[key].append(0.0)
                propsName: list[str] = fcts.extractPropertiesFlow(
                    line, self.m_phaseNames
                )
                propsNameId: list[str] = fcts.identifyProperties(propsName)
                for propNameId in propsNameId:
                    if propNameId not in regionPropertiesValues:
                        regionPropertiesValues[propNameId] = [0.0]
                propsValue: list[float] = fcts.extractValuesFlow(line)
                valuesConverted: list[float] = fcts.convertValues(
                    propsName, propsValue, self.m_propertiesUnit
                )
                for i, name in enumerate(propsNameId):
                    regionPropertiesValues[name][-1] = valuesConverted[i]
            line = file.readline()
            id_line += 1
        self.m_regionsPropertiesValues = regionPropertiesValues
        self.m_timesteps = timesteps

    def readAll(self: Self, filepath: str) -> None:
        """Initialize all the attributes of the class by reading a Geos log file.

        Args:
            filepath (str): Geos log filepath.
        """
        with open(filepath) as geosFile:
            total_lines: int = fcts.countNumberLines(filepath)
            id_line: int = self.readRegionNames(geosFile)
            id_line, lineTag = self.readComputeStatisticsName(
                geosFile, id_line, total_lines
            )
            self.readPropertiesValues(geosFile, id_line, total_lines, lineTag)

    def createDataframe(self: Self) -> pd.DataFrame:
        """Create and fill and return dataframeFlow.

        Returns:
            pd.DataFrame: dataframe with values from Geos log.
        """
        try:
            colNames: list[str] = []
            colValues: list[float] = []
            for propName, values in self.m_regionsPropertiesValues.items():
                unitObj: Unit = self.m_propertiesUnit["nounit"]
                for propertyType in self.m_propertiesUnit:
                    if propertyType in propName.lower():
                        unitObj = self.m_propertiesUnit[propertyType]
                        break
                if unitObj.unitLabel == "":
                    raise ValueError(
                        "No unit was found for this property name <<" + propName + ">>."
                    )
                columnName: str = propName + "__" + unitObj.unitLabel
                colNames.append(columnName)
                colValues.append(values)  # type: ignore[arg-type]
            timeUnit: str = self.m_propertiesUnit["time"].unitLabel
            timeName: str = "Time__" + timeUnit
            colNames.append(timeName)
            colValues.append(self.m_timesteps)  # type: ignore[arg-type]
            data = {colNames[i]: colValues[i] for i in range(len(colNames))}
            dataframeFlow: pd.DataFrame = pd.DataFrame(data)
            return dataframeFlow
        except ValueError as err:
            print(err.args[0])
