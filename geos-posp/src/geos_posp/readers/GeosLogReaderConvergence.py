# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
from io import TextIOBase

import pandas as pd  # type: ignore[import-untyped]
from geos.utils.enumUnits import Unit
from typing_extensions import Self

import geos_posp.processing.geosLogReaderFunctions as fcts


class GeosLogReaderConvergence:

    def __init__( self: Self, filepath: str, propertiesUnit: dict[ str, Unit ] ) -> None:
        """Reader for Convergence information.

        Args:
            filepath (str): path to geos log file.
            propertiesUnit ( dict[str, Unit]): unit preferences
        """
        self.m_propertiesUnit: dict[ str, Unit ] = propertiesUnit
        self.m_solversIterationsValues: dict[ str, list[ float ] ] = {}
        self.m_timesteps: list[ float ] = []
        self.m_dts: list[ float ] = []

        toFindInLog: list[ str ] = [ "Time:" ]
        if not fcts.elementsAreInLog( filepath, toFindInLog ):
            print( "Invalid Geos log file. Please check that your log did not crash." )
        else:
            self.readAll( filepath )
            self.calculateExtraValues()

    def readIterationsValues( self: Self, file: TextIOBase, total_lines: int ) -> None:
        """Read iteration values from Geos log file.

        Initialize the m_aquifersPropertiesValues and m_timesteps attributes
        by reading the Geos log. If a timestep contains the tag
        m_computeStatisticsName, the current timestep is added to m_timesteps
        and we recover the property values in m_regionsPropertiesValues.

        Args:
            file (TextIOBase): Geos Log file
            total_lines (int): The number of lines in the file.
        """
        newtonIterId, linearIterId = fcts.identifyProperties( [ "NewtonIter", "LinearIter" ] )
        iterationsValues: dict[ str, list[ float ] ] = { newtonIterId: [], linearIterId: [] }
        timesteps: list[ float ] = []
        dts: list[ float ] = []
        line: str = file.readline()
        id_line = 1
        while not line.startswith( "Time:" ):
            line = file.readline()
            id_line += 1
        while id_line <= total_lines:
            if line.startswith( "Time:" ):
                timestep, dt = fcts.extractTimeAndDt( line )
                timestep, dt = fcts.convertValues( [ "Time", "Time" ], [ timestep, dt ], self.m_propertiesUnit )
                if timestep > max( timesteps, default=-9.9e99 ):
                    timesteps.append( timestep )
                    dts.append( dt )
                    iterationsValues[ newtonIterId ].append( 0.0 )
                    iterationsValues[ linearIterId ].append( 0.0 )
            elif "NewtonIter:" in line:
                newtonIter: int = fcts.extractNewtonIter( line )
                if newtonIter > 0:
                    iterationsValues[ newtonIterId ][ -1 ] += 1.0
            elif "Linear Solver" in line:
                linearIter: int = fcts.extractLinearIter( line )
                iterationsValues[ linearIterId ][ -1 ] += linearIter
            line = file.readline()
            id_line += 1
        self.m_solversIterationsValues = iterationsValues
        self.m_timesteps = timesteps
        self.m_dts = dts

    def readAll( self: Self, filepath: str ) -> None:
        """Initialize all the attributes of the class by reading a Geos log file.

        Args:
            filepath (str): Geos log filepath.
        """
        with open( filepath ) as geosFile:
            total_lines: int = fcts.countNumberLines( filepath )
            self.readIterationsValues( geosFile, total_lines )

    def calculateExtraValues( self: Self ) -> None:
        """Add cumulated columns for newtonIter and linearIter."""
        siv: dict[ str, list[ float ] ] = self.m_solversIterationsValues
        cumulatedNewtonIter, cumulatedLinearIter = fcts.identifyProperties(
            [ "CumulatedNewtonIter", "CumulatedLinearIter" ] )
        siv[ cumulatedNewtonIter ] = []
        siv[ cumulatedLinearIter ] = []
        newtonIterId, linearIterId = fcts.identifyProperties( [ "NewtonIter", "LinearIter" ] )
        newtonIter: list[ float ] = siv[ newtonIterId ]
        linearIter: list[ float ] = siv[ linearIterId ]
        sumNewtonIter: float = 0.0
        sumLinearIter: float = 0.0
        for i in range( len( newtonIter ) ):
            sumNewtonIter += newtonIter[ i ]
            sumLinearIter += linearIter[ i ]
            siv[ cumulatedNewtonIter ].append( sumNewtonIter )
            siv[ cumulatedLinearIter ].append( sumLinearIter )

    def createDataframe( self: Self ) -> pd.DataFrame:
        """Create and fill and return dataframeSolversIterations.

        Returns:
            pd.DataFrame: dataframe with values from Geos log.
        """
        colNames: list[ str ] = []
        colValues: list[ float ] = []
        for propName, values in self.m_solversIterationsValues.items():
            colNames.append( propName )
            colValues.append( values )  # type: ignore[arg-type]
        timeUnit: str = self.m_propertiesUnit[ "time" ].unitLabel
        timeName: str = "Time__" + timeUnit
        dtName: str = "dt__" + timeUnit
        colNames.append( timeName )
        colNames.append( dtName )
        colValues.append( self.m_timesteps )  # type: ignore[arg-type]
        colValues.append( self.m_dts )  # type: ignore[arg-type]
        data = { colNames[ i ]: colValues[ i ] for i in range( len( colNames ) ) }
        dataframeSolversIterations: pd.DataFrame = pd.DataFrame( data )
        return dataframeSolversIterations
