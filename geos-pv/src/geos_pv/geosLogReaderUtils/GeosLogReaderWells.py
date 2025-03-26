# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from io import TextIOBase
from typing import Union

import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

import geos_pv.geosLogReaderUtils.geosLogReaderFunctions as fcts
from geos_utils.enumUnits import Unit


class GeosLogReaderWells:
    def __init__(
        self: Self,
        filepath: str,
        propertiesUnit: dict[str, Unit],
        phaseNames: Union[list[str], None] = None,
        numberWellsForMean: int = 1,
    ) -> None:
        """Read for Wells from Geos log file.

        To do that, we use specific tags in the current version of this code.
        Supposed tags are :

        * for well names : "Adding object WellElementRegion"
            and "_ConstantBHP_table" Supposed lines:
            "Adding Object WellElementRegion named
            wellRegion1 from ObjectManager::Catalog".
            "   TableFunction: wellControls1_ConstantBHP_table".
        * for phase names: "phaseModel"
            Supposed line: "   TableFunction:
            fluid_phaseModel1_PhillipsBrineDensity_table".
        * for timesteps: "Time:"
            Supposed line : "Time: 0s, dt:100s, Cycle: 0"
            When it comes to well properties, special tags are used :
            " BHP " ; " total rate" ; " total surface volumetric rate" ;
            "phase surface volumetric rate" ; "well is shut" ;
            "density of phase" ; "total fluid density".

        Args:
            filepath (str): path of Geos log file
            propertiesUnit (dict[str, Unit]): unit preferences
            phaseNames (list[str] | None, optional): Name of the phases.

                Defaults to None.
            numberWellsForMean (int, optional): Number of wells. Defaults to 1.
        """
        self.m_propertiesUnit: dict[str, Unit] = propertiesUnit
        self.m_numberWellsForMean: int = numberWellsForMean
        self.m_wellNames: list[str] = []
        numberPhases: int = fcts.findNumberPhasesSimulation(filepath)

        if phaseNames is None:
            phaseNames = []
        self.m_phaseNames: list[str] = fcts.phaseNamesBuilder(numberPhases, phaseNames)
        self.m_wellsPropertiesValues: dict[str, list[float]] = {}
        self.m_timesteps: list[float] = []

        toFindInLog1: list[str] = [
            "_ConstantBHP_table",
            "Time: 0",
            "   TableFunction: ",
        ]
        toFindInLog2: list[str] = [
            "_ConstantPhaseRate_table",
            "Time: 0",
            "   TableFunction: ",
        ]
        foundInLog1: bool = fcts.elementsAreInLog(filepath, toFindInLog1)
        foundInLog2: bool = fcts.elementsAreInLog(filepath, toFindInLog2)
        if not foundInLog1 or not foundInLog2:
            print(
                "Invalid Geos log file. Please check that your log"
                + " did not crash and contains wells."
            )
        else:
            self.readAll(filepath)
            self.calculateMeanValues()

    def readWellNames(self: Self, file: TextIOBase) -> int:
        """Read well names from Geos log file.

        Args:
            file (TextIOBase): Geos Log file
            id_line (int): The id of the last line read in readPhaseNames.

        Returns:
            int: The id of the last line read that contains the tag
            "Adding Object WellElementRegion".
        """
        wellsName: list[str] = []
        line: str = file.readline()
        id_line: int = 1
        intoWellNames: bool = False
        while not intoWellNames:
            line = file.readline()
            id_line += 1
            if "_ConstantBHP_table" in line or "_ConstantPhaseRate_table" in line:
                intoWellNames = True
        intoTableFunctions: bool = True
        while intoTableFunctions:
            if "_ConstantBHP_table" in line or "_ConstantPhaseRate_table" in line:
                wellName: str = fcts.extractWell(line)
                if wellName not in wellsName:
                    wellsName.append(wellName)
            line = file.readline()
            id_line += 1
            if "   TableFunction: " not in line:
                intoTableFunctions = False
        self.m_wellNames = wellsName
        return id_line

    def initWellPropertiesValues(self: Self) -> None:
        """Initialize the m_wellPropertiesValues."""
        props: dict[str, list[float]] = {}
        for name in self.m_wellNames:
            wName: str = fcts.formatPropertyName(name)
            bhp: str = wName + "__BHP"
            totalMassRate: str = wName + "__TotalMassRate"
            totalSVR: str = wName + "__TotalSurfaceVolumetricRate"
            propsNoId: list[str] = [bhp, totalMassRate, totalSVR]
            if len(self.m_phaseNames) > 1:
                for phase in self.m_phaseNames:
                    pName: str = fcts.formatPropertyName(phase)
                    phaseSVR: str = wName + "__SurfaceVolumetricRate" + pName
                    propsNoId.append(phaseSVR)
            propsWithId = fcts.identifyProperties(propsNoId)
            for propName in propsWithId:
                props[propName] = [0.0]
        self.m_wellsPropertiesValues = props

    def readPropertiesValues(
        self: Self, file: TextIOBase, id_line: int, total_lines: int
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
        """
        line: str = file.readline()
        id_line += 1
        while not line.startswith("Time: 0"):
            line = file.readline()
            id_line += 1
        wellsPropertiesValues: dict[str, list[float]] = self.m_wellsPropertiesValues
        currentWellName: str = self.m_wellNames[0]
        currentPhaseName: str = self.m_phaseNames[0]
        newTimestep: float = 0.0
        timesteps: list[float] = [newTimestep]
        while id_line <= total_lines:
            wellTags = fcts.extractWellTags(line)
            if line.startswith("Time:"):
                newTimestep, dt = fcts.extractTimeAndDt(line)
                newTimestep = fcts.convertValues(
                    ["Time"], [newTimestep], self.m_propertiesUnit
                )[0]
            # If at least one well tag is found, this is a well line
            if len(wellTags) > 0:
                if newTimestep not in timesteps and newTimestep > max(
                    timesteps, default=0.0
                ):
                    timesteps.append(newTimestep)
                    for key in wellsPropertiesValues:
                        wellsPropertiesValues[key].append(0.0)
                newWellName: str = fcts.identifyCurrentWell(line, currentWellName)
                if newWellName != currentWellName:
                    if newWellName in self.m_wellNames:
                        currentWellName = newWellName
                    else:
                        print(
                            f"Invalid well name <<{newWellName}>> found"
                            + f" at timestep <<{str(newTimestep)}>>"
                            + f" in line :\n<<{line}>>.\nAnother correct well"
                            + f" name <<{currentWellName}>> was used to"
                            + " correct this.\nExpected well names are :"
                            + f" {str(self.m_wellNames)}.\n"
                        )
                if ("phase" in line.lower()) and ("phase surface" not in line.lower()):
                    newPhaseId: int = fcts.extractPhaseId(line)
                    if self.m_phaseNames[newPhaseId] != currentWellName:
                        currentPhaseName = self.m_phaseNames[newPhaseId]
                propsName: list[str] = fcts.extractPropertiesWell(
                    line, currentWellName, currentPhaseName
                )
                for name in propsName:
                    if "density" in name.lower():
                        propsName.pop(propsName.index(name))
                if len(propsName) > 0 and "IsShut" not in propsName[0]:
                    propsNameId: list[str] = fcts.identifyProperties(propsName)
                    propsValue: list[float] = fcts.extractValuesWell(
                        line, len(propsName)
                    )
                    valuesConverted: list[float] = fcts.convertValues(
                        propsName, propsValue, self.m_propertiesUnit
                    )
                    for i, name in enumerate(propsNameId):
                        wellsPropertiesValues[name][-1] = valuesConverted[i]

            line = file.readline()
            id_line += 1
        self.m_wellsPropertiesValues = wellsPropertiesValues
        self.m_timesteps = timesteps

    def readAll(self: Self, filepath: str) -> None:
        """Initialize all the attributes of the class by reading a Geos log file.

        Args:
            filepath (str): Geos log filepath.
            singlephase (bool): True if its a singlephase simulation,
                False if multiphase.
        """
        with open(filepath) as geosFile:
            total_lines: int = fcts.countNumberLines(filepath)
            id_line = self.readWellNames(geosFile)
            self.initWellPropertiesValues()
            self.readPropertiesValues(geosFile, id_line, total_lines)

    def calculateMeanValues(self: Self) -> None:
        """Calculate mean values of all wells."""
        nbr: int = self.m_numberWellsForMean
        wNames: list[str] = self.m_wellNames
        pNames: list[str] = self.m_phaseNames
        wpv: dict[str, list[float]] = self.m_wellsPropertiesValues
        cNames: list[str] = list(wpv.keys())
        bhpNames: list[str] = [n for n in cNames if "bhp" in n.lower()]
        totalMassRateNames: list[str] = [
            n for n in cNames if "totalmassrate" in n.lower()
        ]
        totalSVRNames: list[str] = [
            n for n in cNames if "totalsurfacevolumetricrate" in n.lower()
        ]
        differentMeanColumns: dict[str, list[str]] = {
            "MeanBHP": bhpNames,
            "MeanTotalMassRate": totalMassRateNames,
            "MeanTotalVolumetricRate": totalSVRNames,
        }
        for pName in pNames:
            pName = fcts.formatPropertyName(pName)
            meanName: str = "MeanSurfaceVolumetricRate" + pName
            differentMeanColumns[meanName] = []
            for wName in wNames:
                wName = fcts.formatPropertyName(wName)
                n: str = wName + "__SurfaceVolumetricRate" + pName
                n = fcts.identifyProperties([n])[0]
                if n in cNames:
                    differentMeanColumns[meanName].append(n)
        for meanName, columns in differentMeanColumns.items():
            if len(columns) > 0:
                values: list[list[float]] = [wpv[c] for c in columns]
                meanValues: list[float] = [sum(item) / nbr for item in zip(*values)]
                meanNameWithId: str = fcts.identifyProperties([meanName])[0]
                self.m_wellsPropertiesValues[meanNameWithId] = meanValues

    def createDataframe(self: Self) -> pd.DataFrame:
        """Create and fill and return dataframeWells.

        Return:
            pd.DataFrame: dataframe with log values.
        """
        colNames: list[str] = []
        colValues: list[float] = []
        try:
            for propName, values in self.m_wellsPropertiesValues.items():
                unitObj: Unit = self.m_propertiesUnit["nounit"]
                for propertyType in self.m_propertiesUnit:
                    if propertyType.lower() in propName.lower():
                        unitObj = self.m_propertiesUnit[propertyType]
                        break
                if unitObj.unitLabel == "":
                    raise ValueError(
                        "No unit was found for this property name <<" + propName + ">>."
                    )
                columnName: str = propName + "__" + unitObj.unitLabel
                colNames.append(columnName)
                colValues.append(values)  # type: ignore[arg-type]
        except ValueError as err:
            print(err.args[0])
        timeUnit: str = self.m_propertiesUnit["time"].unitLabel
        timeName: str = "Time__" + timeUnit
        colNames.append(timeName)
        colValues.append(self.m_timesteps)  # type: ignore[arg-type]
        data = {colNames[i]: colValues[i] for i in range(len(colNames))}
        dataframeWells: pd.DataFrame = pd.DataFrame(data)
        return dataframeWells
