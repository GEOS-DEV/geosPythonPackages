# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from io import TextIOBase

import pandas as pd  # type: ignore[import-untyped]
from geos.utils.enumUnits import Unit
from typing_extensions import Self

import geos_posp.processing.geosLogReaderFunctions as fcts


class GeosLogReaderAquifers:

    def __init__( self: Self, filepath: str, propertiesUnit: dict[ str, Unit ] ) -> None:
        """Reader for Aquifer.

        Args:
            filepath (str): path to geos log file.
            propertiesUnit ( dict[str, Unit]): unit preferences
        """
        self.m_propertiesUnit = propertiesUnit
        self.m_aquiferNames: list[ str ] = []
        self.m_aquifersPropertiesValues: dict[ str, list[ float ] ] = {}
        self.m_timesteps: list[ float ] = []

        toFindInLog: list[ str ] = [ "_pressureInfluence_table", "Time: 0" ]
        if not fcts.elementsAreInLog( filepath, toFindInLog ):
            print( "Invalid Geos log file. Please check that your log" + " did not crash and contains aquifers." )
        else:
            self.readAll( filepath )
            self.calculateExtraValues()

    def readAquiferNames( self: Self, file: TextIOBase ) -> tuple[ str, int ]:
        """Initialize the m_aquiferNames attribute by reading log file.

        Args:
            file (TextIOBase): Geos Log file

        Returns:
            tuple(str, int): The last line with time info read.
            The id of the last line read that contained the tag "_pressureInfluence_table".,
            which will be the line containing the first positive timestep at 0s.
        """
        aquiferNames: list[ str ] = []
        line: str = file.readline()
        id_line = 1
        while not line.startswith( "Time: 0" ):
            if "_pressureInfluence_table" in line:
                aquiferName: str = fcts.extractAquifer( line )
                aquiferNames.append( aquiferName )
            line = file.readline()
            id_line += 1
        self.m_aquiferNames = aquiferNames
        return ( line, id_line )

    def readPropertiesValues( self: Self, file: TextIOBase, line: str, id_line: int, total_lines: int ) -> None:
        """Read aquifer property values from geos log file.

        Initialize the m_aquifersPropertiesValues and m_timesteps attributes by reading
        the Geos log. If a timestep contains the tag m_computeStatisticsName, the
        current timestep is added to m_timesteps and we recover the property values
        in m_regionsPropertiesValues.

        Args:
            file (TextIOBase): Geos Log file
            line (str): last line read in the file.
            id_line (int): The id of the last line read in readPhaseNames.
            total_lines (int): The number of lines in the file.
        """
        aquifsPropertiesValues: dict[ str, list[ float ] ] = {}
        for aquifName in self.m_aquiferNames:
            propVolume: str = aquifName + "__Volume"
            propVolumeId: str = fcts.identifyProperties( [ propVolume ] )[ 0 ]
            propRate: str = aquifName + "__VolumetricRate"
            propRateId: str = fcts.identifyProperties( [ propRate ] )[ 0 ]
            aquifsPropertiesValues[ propVolumeId ] = [ 0.0 ]
            aquifsPropertiesValues[ propRateId ] = [ 0.0 ]
        newTimestep, currentDT = fcts.extractTimeAndDt( line )
        timesteps: list[ float ] = [ newTimestep ]
        line = file.readline()
        id_line += 1
        while id_line <= total_lines:
            if line.startswith( "Time:" ):
                newTimestep, currentDT = fcts.extractTimeAndDt( line )
                newTimestep = fcts.convertValues( [ "Time" ], [ newTimestep ], self.m_propertiesUnit )[ 0 ]
            if " produces a flux of " in line:
                if newTimestep not in timesteps and newTimestep > max( timesteps, default=0.0 ):
                    timesteps.append( newTimestep )
                    for key in aquifsPropertiesValues:
                        aquifsPropertiesValues[ key ].append( 0.0 )
                aquifName, volume = fcts.extractValueAndNameAquifer( line )
                rate: float = volume / currentDT
                propVol: str = aquifName + "__Volume"
                propVolId: str = fcts.identifyProperties( [ propVol ] )[ 0 ]
                propRate = aquifName + "__VolumetricRate"
                propRateId = fcts.identifyProperties( [ propRate ] )[ 0 ]
                aquifsPropertiesValues[ propVolId ][ -1 ] = fcts.convertValues( [ propVol ], [ volume ],
                                                                                self.m_propertiesUnit )[ 0 ]
                aquifsPropertiesValues[ propRateId ][ -1 ] = fcts.convertValues( [ propRate ], [ rate ],
                                                                                 self.m_propertiesUnit )[ 0 ]
            line = file.readline()
            id_line += 1
        self.m_aquifersPropertiesValues = aquifsPropertiesValues
        self.m_timesteps = timesteps

    def readAll( self: Self, filepath: str ) -> None:
        """Initialize all the attributes of the class by reading a Geos log file.

        Args:
            filepath (str): Geos log filepath.
        """
        with open( filepath ) as geosFile:
            total_lines: int = fcts.countNumberLines( filepath )
            line, id_line = self.readAquiferNames( geosFile )
            self.readPropertiesValues( geosFile, line, id_line, total_lines )

    def calculateExtraValues( self: Self ) -> None:
        """Add cumulated columns for each aquifer volume and aquifer rate."""
        for aquifName in self.m_aquiferNames:
            propVolume: str = aquifName + "__Volume"
            propVolumeId: str = fcts.identifyProperties( [ propVolume ] )[ 0 ]
            propRate: str = aquifName + "__VolumetricRate"
            propRateId: str = fcts.identifyProperties( [ propRate ] )[ 0 ]
            volumes: list[ float ] = self.m_aquifersPropertiesValues[ propVolumeId ]
            rates: list[ float ] = self.m_aquifersPropertiesValues[ propRateId ]
            cumuVol_name = aquifName + "__CumulatedVolume"
            cumuVolId: str = fcts.identifyProperties( [ cumuVol_name ] )[ 0 ]
            cumuRate_name = aquifName + "__CumulatedVolumetricRate"
            cumuRateId: str = fcts.identifyProperties( [ cumuRate_name ] )[ 0 ]
            cumuVol_values: list[ float ] = [ volumes[ 0 ] ]
            cumuRate_values: list[ float ] = [ rates[ 0 ] ]
            for i in range( 1, len( volumes ) ):
                cumuVol_values.append( cumuVol_values[ i - 1 ] + volumes[ i ] )
                cumuRate_values.append( cumuRate_values[ i - 1 ] + rates[ i ] )
            self.m_aquifersPropertiesValues[ cumuVolId ] = cumuVol_values
            self.m_aquifersPropertiesValues[ cumuRateId ] = cumuRate_values

    def createDataframe( self: Self ) -> pd.DataFrame:
        """Create and fill and return dataframeAquifers.

        Returns:
            pd.DataFrame: dataframe with values from Geos log.
        """
        try:
            colNames: list[ str ] = []
            colValues: list[ float ] = []
            for propName, values in self.m_aquifersPropertiesValues.items():
                unitObj: Unit = self.m_propertiesUnit[ "nounit" ]
                for propertyType in self.m_propertiesUnit:
                    if propertyType.lower() in propName.lower():
                        unitObj = self.m_propertiesUnit[ propertyType ]
                        break
                if unitObj.unitLabel == "":
                    raise ValueError( "No unit was found for this property name <<" + propName + ">>." )
                columnName: str = propName + "__" + unitObj.unitLabel
                colNames.append( columnName )
                colValues.append( values )  # type: ignore[arg-type]
            timeUnit: Unit = self.m_propertiesUnit[ "time" ]
            timeName: str = "Time__" + timeUnit.unitLabel
            colNames.append( timeName )
            colValues.append( self.m_timesteps )  # type: ignore[arg-type]
            data = { colNames[ i ]: colValues[ i ] for i in range( len( colNames ) ) }
            dataframeAquifers: pd.DataFrame = pd.DataFrame( data )
            return dataframeAquifers
        except ValueError as err:
            print( err.args[ 0 ] )
