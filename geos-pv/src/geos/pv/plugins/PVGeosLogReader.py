# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import logging
from pathlib import Path
from enum import Enum
from typing import Union, cast

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

import vtkmodules.util.numpy_support as vnp
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy )
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonCore import vtkDataArraySelection as vtkDAS
from vtkmodules.vtkCommonCore import vtkDoubleArray, vtkInformation, vtkInformationVector, VTK_DOUBLE
from vtkmodules.vtkCommonDataModel import vtkTable

from geos.pv.geosLogReaderUtils.geosLogReaderFunctions import ( identifyProperties, transformUserChoiceToListPhases )
from geos.pv.geosLogReaderUtils.GeosLogReaderAquifers import GeosLogReaderAquifers
from geos.pv.geosLogReaderUtils.GeosLogReaderConvergence import GeosLogReaderConvergence
from geos.pv.geosLogReaderUtils.GeosLogReaderFlow import GeosLogReaderFlow
from geos.pv.geosLogReaderUtils.GeosLogReaderWells import GeosLogReaderWells
from geos.utils.enumUnits import ( Mass, MassRate, Pressure, Time, Unit, Volume, VolumetricRate, enumerationDomainUnit )
from geos.utils.UnitRepository import UnitRepository
from geos.pv.utils.checkboxFunction import createModifiedCallback  # type: ignore[attr-defined]
from geos.pv.utils.paraviewTreatments import strListToEnumerationDomainXml

__doc__ = """
``PVGeosLogReader`` is a Paraview plugin that allows to read Geos output log.

Input is a file and output is a vtkTable containing log information.

.. WARNING::
    The reader is compliant with GEOS log before commit version **#9365098**.
    For more recent version, use the csv or hdf5 export options from GEOS.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVGeosLogReader.
* Open (File>Open...) and Select Geos output log .out/.txt file.
* In the "Open data with..." window, Select PVGeosLogReader reader.

"""


@smproxy.reader(
    name="PVGeosLogReader",
    label="Geos Log Reader",
    extensions=[ "txt", "out" ],
    file_description="txt and out files of GEOS log files",
)
class PVGeosLogReader( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview reader for Geos log files ."txt" or ".out".

        Output is a vtkTable with data extracted from the log.
        """
        super().__init__( nInputPorts=0, nOutputPorts=1, outputType="vtkTable" )
        self.m_filepath: str = ""
        self.m_phasesUserChoice: list[ str ] = []
        self.m_dataframeChoice: int = 0
        self.m_dataframe: pd.DataFrame
        self.m_numberWellsMean: int = 1

        # checkboxes values
        self.m_useSIUnits: int = 0
        self.m_pressureUnit: int = 0
        self.m_bhpUnit: int = 0
        self.m_stressUnit: int = 0
        self.m_timeUnit: int = 0
        self.m_massUnit: int = 0
        self.m_volumeUnit: int = 0
        self.m_volumetricRateUnit: int = 0
        self.m_massRateUnit: int = 0
        self.m_densityUnit: int = 0

        # for selection of properties
        self.m_propertiesFlow: vtkDAS = vtkDAS()
        self.m_propertiesFlow.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        propsFlow: list[ str ] = [
            "DeltaPressure",
            "Pressure",
            "Temperature",
            "TotalDynamicPoreVolume",
            "DynamicPoreVolumes",
            "NonTrapped",
            "Trapped",
            "Immobile",
            "Mobile",
            "Dissolved",
            "TotalFluidMass",
            "CellFluidMass",
        ]
        for prop in propsFlow:
            self.m_propertiesFlow.AddArray( prop )

        self.m_propertiesWells: vtkDAS = vtkDAS()
        self.m_propertiesWells.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        propsWells: list[ str ] = [
            "MeanBHP",
            "MeanTotalMassRate",
            "MeanTotalVolumetricRate",
            "MeanSurfaceVolumetricRate",
            "TotalMassRate",
            "TotalVolumetricRate",
            "SurfaceVolumetricRate",
            "Mass",
            "BHP",
        ]
        for prop in propsWells:
            self.m_propertiesWells.AddArray( prop )

        self.m_propertiesAquifers: vtkDAS = vtkDAS()
        self.m_propertiesAquifers.AddObserver(
            "ModifiedEvent",  # type: ignore[arg-type]
            createModifiedCallback( self ) )
        propsAquifers: list[ str ] = [
            "Volume",
            "VolumetricRate",
            "CumulatedVolume",
            "CumulatedVolumetricRate",
        ]
        for prop in propsAquifers:
            self.m_propertiesAquifers.AddArray( prop )

        self.m_convergence: vtkDAS = vtkDAS()
        self.m_convergence.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        propsSolvers: list[ str ] = [ "NewtonIter", "LinearIter" ]
        for prop in propsSolvers:
            self.m_convergence.AddArray( prop )

        self.logger: logging.Logger = logging.getLogger( "Geos Log Reader" )
        self.logger.setLevel( logging.INFO )
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( VTKHandler() )
        self.logger.propagate = False
        self.logger.info( f"Apply plugin { self.logger.name }." )

    @smproperty.stringvector( name="DataFilepath", default_values="Enter a filepath to your data" )
    @smdomain.filelist()
    @smhint.filechooser( extensions=[ "txt", "out" ], file_description="Data files" )
    def a01SetFilepath( self: Self, filepath: str ) -> None:
        """Set Geos log file path.

        Args:
            filepath (str): path to the file.

        Raises:
            FileNotFoundError: file not found.
        """
        if filepath != "Enter a filepath to your data":
            if not os.path.exists( filepath ):
                raise FileNotFoundError( f"Invalid filepath {filepath}" )
            else:
                self.m_filepath = filepath
                self.Modified()

    def getFilepath( self: Self ) -> str:
        """Get Geos log file path.

        Returns:
            str: filepath.
        """
        return self.m_filepath

    @smproperty.stringvector( name="EnterPhaseNames", label="Enter Phase Names", default_values="" )
    @smdomain.xml( """<Documentation>
                  Please enter your phase names as phase0, phase1, phase2.
                  </Documentation>""" )
    def a02SetPhaseNames( self: Self, value: str ) -> None:
        """Set phase names.

        Args:
            value (str): list of phase names separated by space.
        """
        self.m_phasesUserChoice = transformUserChoiceToListPhases( value )
        self.Modified()

    def getPhasesUserChoice( self: Self ) -> list[ str ]:
        """Access the phases from the user input.

        Returns:
            list[str]: phase names.
        """
        return self.m_phasesUserChoice

    @smproperty.intvector(
        name="DataframeChoice",
        number_of_elements=1,
        label="DataframeChoice",
        default_values=0,
    )
    @smdomain.xml( strListToEnumerationDomainXml( [ "Flow", "Wells", "Aquifers", "Convergence" ] ) )
    def a03SetDataFrameChoice( self: Self, value: int ) -> None:
        """Set reader choice: 0:Flow, 1:Wells, 2:Aquifers, 3:Convergence.

        Args:
            value (int): user choice.
        """
        self.m_dataframeChoice = value
        self.Modified()

    def getDataframeChoice( self: Self ) -> int:
        """Accesses the choice of dataframe from the user.

        Returns:
            int: The value corresponding to a certain dataframe.
                "Flow" has value "0", "Wells" has value "1",
                "Aquifers" has value "2", "Convergence" has
                value "3".
        """
        return self.m_dataframeChoice

    @smproperty.xml( """<PropertyGroup label="Log informations">
                        <Property name="DataFilepath"/>
                        <Property name="EnterPhaseNames"/>
                        <Property name="DataframeChoice"/>
                    </PropertyGroup>""" )
    def a04PropertyGroup( self: Self ) -> None:
        """Organized group."""
        self.Modified()

    @smproperty.dataarrayselection( name="FlowProperties" )
    def a05SetPropertiesFlow( self: Self ) -> vtkDAS:
        """Use Flow."""
        return self.m_propertiesFlow

    @smproperty.xml( """<PropertyGroup label="PropertiesSelection" panel_visibility="advanced">
                    <Property name="FlowProperties"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="DataframeChoice" value="0" /></Hints>
                   </PropertyGroup>""" )
    def a06GroupFlow( self: Self ) -> None:
        """Organized group."""
        self.Modified()

    @smproperty.dataarrayselection( name="WellsProperties" )
    def a07SetPropertiesWells( self: Self ) -> vtkDAS:
        """Use wells."""
        return self.m_propertiesWells

    @smproperty.intvector( name="NumberOfWellsForMeanCalculation", default_values=1 )
    def a08SetTheNumberOfWellsMean( self: Self, number: int ) -> None:
        """Set number of wells.

        Args:
            number (int): number of wells.
        """
        self.m_numberWellsMean = number
        self.Modified()

    def getNumberOfWellsMean( self: Self ) -> int:
        """Get the number of wells.

        Returns:
            int: The number of wells to consider.
        """
        return self.m_numberWellsMean

    @smproperty.xml( """<PropertyGroup label="PropertiesSelection" panel_visibility="advanced">
                    <Property name="WellsProperties"/>
                    <Property name="NumberOfWellsForMeanCalculation"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="DataframeChoice" value="1" /></Hints>
                   </PropertyGroup>""" )
    def a09GroupWells( self: Self ) -> None:
        """Organized group."""
        self.Modified()

    @smproperty.dataarrayselection( name="AquifersProperties" )
    def a10SetPropertiesAquifers( self: Self ) -> vtkDAS:
        """Use aquifers."""
        return self.m_propertiesAquifers

    @smproperty.xml( """<PropertyGroup label="PropertiesSelection" panel_visibility="advanced">
                    <Property name="AquifersProperties"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="DataframeChoice" value="2" /></Hints>
                   </PropertyGroup>""" )
    def a11GroupAquifers( self: Self ) -> None:
        """Organized group."""
        self.Modified()

    @smproperty.dataarrayselection( name="Convergence" )
    def a12SetConvergence( self: Self ) -> vtkDAS:
        """Use convergence."""
        return self.m_convergence

    @smproperty.xml( """<PropertyGroup label="PropertiesSelection" panel_visibility="advanced">
                    <Property name="Convergence"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="DataframeChoice" value="3" /></Hints>
                   </PropertyGroup>""" )
    def a13GroupSolvers( self: Self ) -> None:
        """Organized group."""
        self.Modified()

    def getIdsToUse( self: Self ) -> list[ str ]:
        """Get property ids.

        Using the checkbox choices of the user for metaproperties,
        we get the list of ids to map the dataframe properties with the
        properties.

        Returns:
            list(str): Ids of the metaproperties.
        """
        dataArrays: dict[ int, vtkDAS ] = {
            0: self.m_propertiesFlow,
            1: self.m_propertiesWells,
            2: self.m_propertiesAquifers,
            3: self.m_convergence,
        }
        dataArrayToUse = dataArrays[ self.getDataframeChoice() ]
        propertyNames: list[ str ] = []
        for i in range( dataArrayToUse.GetNumberOfArrays() ):
            propName: str = dataArrayToUse.GetArrayName( i )
            if dataArrayToUse.ArrayIsEnabled( propName ) == 1:
                propertyNames.append( propName )
        propertiesWithId: list[ str ] = identifyProperties( propertyNames )
        onlyIds: list[ str ] = []
        for propId in propertiesWithId:
            idFound: str = propId.split( ":" )[ 0 ]
            onlyIds.append( idFound )
        return onlyIds

    @smproperty.intvector( name="UseSIUnits", label="UseSIUnits", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b01SetUseSIUnits( self: Self, value: int ) -> None:
        """Set Use SI Units.

        Args:
            value (int): user choice.
        """
        self.m_useSIUnits = value
        self.Modified()

    @smproperty.intvector( name="Pressure", label="Pressure", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Pressure ) ) )
    def b02SetPressureUnit( self: Self, value: int ) -> None:
        """Set pressure unit.

        Args:
            value (int): user choice.
        """
        self.m_pressureUnit = value
        self.Modified()

    @smproperty.intvector( name="BHP", label="BHP", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Pressure ) ) )
    def b03SetBHPUnit( self: Self, value: int ) -> None:
        """Set BHP unit.

        Args:
            value (int): user choice.
        """
        self.m_bhpUnit = value
        self.Modified()

    @smproperty.intvector( name="Time", label="Time", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Time ) ) )
    def b04SetTimeUnit( self: Self, value: int ) -> None:
        """Set time unit.

        Args:
            value (int): user choice.
        """
        self.m_timeUnit = value
        self.Modified()

    @smproperty.intvector( name="Mass", label="Mass", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Mass ) ) )
    def b05SetMassUnit( self: Self, value: int ) -> None:
        """Set mass unit.

        Args:
            value (int): user choice.
        """
        self.m_massUnit = value
        self.Modified()

    @smproperty.intvector( name="Volume", label="Volume", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Volume ) ) )
    def b06SetVolumeUnit( self: Self, value: int ) -> None:
        """Set volume unit.

        Args:
            value (int): user choice.
        """
        self.m_volumeUnit = value
        self.Modified()

    @smproperty.intvector(
        name="VolumetricRate",
        label="VolumetricRate",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, VolumetricRate ) ) )
    def b07SetVolumetricRateUnit( self: Self, value: int ) -> None:
        """Set volumetric rate unit.

        Args:
            value (int): user choice.
        """
        self.m_volumetricRateUnit = value
        self.Modified()

    @smproperty.intvector( name="MassRate", label="MassRate", default_values=0, panel_visibility="default" )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, MassRate ) ) )
    def b08SetMassRateUnit( self: Self, value: int ) -> None:
        """Set Mass rate unit.

        Args:
            value (int): user choice.
        """
        """"""
        self.m_massRateUnit = value
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Units Choice">
                        <Property name="Pressure"/>
                        <Property name="BHP"/>
                        <Property name="Time"/>
                        <Property name="Mass"/>
                        <Property name="Volume"/>
                        <Property name="VolumetricRate"/>
                        <Property name="MassRate"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="UseSIUnits" value="0" /></Hints>
                    </PropertyGroup>""" )
    def b09GroupUnitsToUse( self: Self ) -> None:
        """Organize group."""
        self.Modified()

    def getUseSIUnits( self: Self ) -> int:
        """Acess the choice to use SI units or not.

        Returns:
            int: 0 to not use SI units or 1 to use SI units.
        """
        return self.m_useSIUnits

    def getUnitChoices( self: Self ) -> dict[ str, int ]:
        """Get the units choosen by the user.

        Based on the choice of using SI units or not, and if
        not with the units chosen by the user, returns a dict
        with metaproperties such as pressure, volume etc ...
        with the unit associated.

        Returns:
            dict[str, int]: empty dictionary if use SI unit, or
                property name as keys and unit choice as values.
        """
        unitChoices: dict[ str, int ] = {}
        if not self.getUseSIUnits():
            unitChoices = {
                "pressure": self.m_pressureUnit,
                "stress": self.m_stressUnit,
                "bhp": self.m_bhpUnit,
                "mass": self.m_massUnit,
                "massRate": self.m_massRateUnit,
                "time": self.m_timeUnit,
                "volume": self.m_volumeUnit,
                "volumetricRate": self.m_volumetricRateUnit,
                "density": self.m_densityUnit,
            }
        return unitChoices

    def createDataframe( self: Self ) -> pd.DataFrame:
        """Create dataframe with values from Geos log based on user choices.

        Returns:
            pd.DataFrame: Dataframe with log values according to user choice.
        """
        filepath: str = self.getFilepath()
        phaseNames: list[ str ] = self.getPhasesUserChoice()
        choice: int = self.getDataframeChoice()
        userPropertiesUnits: dict[ str, int ] = self.getUnitChoices()
        unitObj: UnitRepository = UnitRepository( userPropertiesUnits )
        propertiesUnit: dict[ str, Unit ] = unitObj.getPropertiesUnit()
        reader: Union[
            GeosLogReaderFlow,
            GeosLogReaderWells,
            GeosLogReaderAquifers,
            GeosLogReaderConvergence,
        ]
        if choice == 0:
            reader = GeosLogReaderFlow( filepath, propertiesUnit, phaseNames )
        elif choice == 1:
            nbrWells: int = self.getNumberOfWellsMean()
            reader = GeosLogReaderWells( filepath, propertiesUnit, phaseNames, nbrWells )
        elif choice == 2:
            reader = GeosLogReaderAquifers( filepath, propertiesUnit )
        elif choice == 3:
            reader = GeosLogReaderConvergence( filepath, propertiesUnit )
        return reader.createDataframe()

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()
        outInfo = outInfoVec.GetInformationObject( 0 )
        outInfo.Remove( executive.TIME_STEPS() )
        outInfo.Remove( executive.TIME_RANGE() )
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        try:
            # we choose which dataframe to build and get it
            idsToUse = self.getIdsToUse()
            dataframe = self.createDataframe()
            usefulColumns = []
            for column_name in list( dataframe.columns ):
                if ":" not in column_name:
                    usefulColumns.append( column_name )
                else:
                    idFound = column_name.split( ":" )[ 0 ]
                    if idFound in idsToUse:
                        usefulColumns.append( column_name )
            # we build the output vtkTable
            output: vtkTable = vtkTable.GetData( outInfoVec, 0 )
            for column in usefulColumns:
                pandas_series: pd.Series = dataframe[ column ]
                array: npt.NDArray[ np.float64 ] = pandas_series.values
                if ":" in column:
                    column = column.split( ":" )[ 1 ]

                newAttr: vtkDoubleArray = vnp.numpy_to_vtk( array, deep=True,
                                                            array_type=VTK_DOUBLE )  # type: ignore[no-untyped-call]
                newAttr.SetName( column )
                output.AddColumn( newAttr )
            self.logger.info( f"The plugin { self.logger.name } succeeded." )
        except Exception as e:
            self.logger.error( f"The plugin { self.logger.name } failed.\n{ e }" )
            return 0
        return 1
