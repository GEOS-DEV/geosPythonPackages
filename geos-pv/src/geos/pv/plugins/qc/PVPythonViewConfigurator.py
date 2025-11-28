# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing import Any, Union, cast

import pandas as pd  # type: ignore[import-untyped]
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.utils.multiblockModifiers import mergeBlocks
import geos.pv.utils.paraviewTreatments as pvt
from geos.pv.utils.checkboxFunction import createModifiedCallback  # type: ignore[attr-defined]
from geos.pv.utils.DisplayOrganizationParaview import DisplayOrganizationParaview
from geos.pv.pyplotUtils.matplotlibOptions import ( FontStyleEnum, FontWeightEnum, LegendLocationEnum, LineStyleEnum,
                                                    MarkerStyleEnum, OptionSelectionEnum, optionEnumToXml )
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

from paraview.simple import (  # type: ignore[import-not-found]
    GetActiveSource, GetActiveView, Render, Show, servermanager )
from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py

from vtkmodules.vtkCommonCore import vtkDataArraySelection, vtkInformation
from vtkmodules.vtkCommonDataModel import vtkDataObject, vtkMultiBlockDataSet

__doc__ = f"""
PVPythonViewConfigurator is a Paraview plugin that allows to create cross-plots
from input data using the PythonView.

Input type is vtkDataObject.

This filter results in opening a new Python View window and displaying cross-plot.

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/qc/PVPythonViewConfigurator.
* Select the vtkDataObject containing the data to plot
* Select the filter: Filters > { FilterCategory.QC.value } > Python View Configurator
* Configure the plot with the widgets
* Apply

"""


@SISOFilter( category=FilterCategory.QC,
             decoratedLabel="Python View Configurator",
             decoratedType="vtkDataObject" )
class PVPythonViewConfigurator( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to create cross-plots in a Python View.

        Input is a vtkDataObject.
        """
        # super().__init__( nInputPorts=1, nOutputPorts=1 )
        # Python view layout and object.
        self.m_layoutName: str = ""
        self.m_pythonView: Any
        self.m_organizationDisplay = DisplayOrganizationParaview()
        self.buildNewLayoutWithPythonView()

        # Input source and curve names.
        inputSource = GetActiveSource()
        dataset = servermanager.Fetch( inputSource )
        # Handle vtkMultiBlockDataSet by merging blocks first
        if isinstance( dataset, vtkMultiBlockDataSet ):
            dataset = mergeBlocks( dataset, keepPartialAttributes=True )
        dataframe: pd.DataFrame = pvt.vtkToDataframe( dataset )
        self.m_pathPythonViewScript: Path = geos_pv_path / "src/geos/pv/pythonViewUtils/mainPythonView.py"

        # Checkboxes.
        self.m_modifyInputs: int = 1
        self.m_modifyCurves: int = 1
        self.m_multiplyCurves: int = 0

        # Checkboxes curves available from the data of pipeline.
        self.m_validSources = vtkDataArraySelection()
        self.m_curvesToPlot = vtkDataArraySelection()
        self.m_curvesMinus1 = vtkDataArraySelection()
        self.m_validSources.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        self.m_curvesToPlot.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        self.m_curvesMinus1.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        validSourceNames: set[ str ] = pvt.getPossibleSourceNames()
        for sourceName in validSourceNames:
            self.m_validSources.AddArray( sourceName )
        validColumnsDataframe: list[ str ] = list( dataframe.columns )
        for name in list( dataframe.columns ):
            for axis in [ "X", "Y", "Z" ]:
                if "Points" + axis in name and "Points" + axis + "__" in name:
                    doublePosition: int = validColumnsDataframe.index( "Points" + axis )
                    validColumnsDataframe.pop( doublePosition )
                    break
        self.m_validColumnsDataframe: list[ str ] = sorted( validColumnsDataframe, key=lambda x: x.lower() )
        for curveName in validColumnsDataframe:
            self.m_curvesToPlot.AddArray( curveName )
            self.m_curvesMinus1.AddArray( curveName )
        self.m_validSources.DisableAllArrays()
        self.m_curvesToPlot.DisableAllArrays()
        self.m_curvesMinus1.DisableAllArrays()
        self.m_curveToUse: str = ""
        # To change the aspects of curves.
        self.m_curvesToModify: set[ str ] = pvt.integrateSourceNames( validSourceNames, set( validColumnsDataframe ) )
        self.m_color: tuple[ float, float, float ] = ( 0.0, 0.0, 0.0 )
        self.m_lineStyle: str = LineStyleEnum.SOLID.optionValue
        self.m_lineWidth: float = 1.0
        self.m_markerStyle: str = MarkerStyleEnum.NONE.optionValue
        self.m_markerSize: float = 1.0

        # User choices.
        self.m_userChoices: dict[ str, Any ] = {
            "variableName": "",
            "curveNames": [],
            "curveConvention": [],
            "inputNames": [],
            "plotRegions": False,
            "reverseXY": False,
            "logScaleX": False,
            "logScaleY": False,
            "minorticks": False,
            "displayTitle": True,
            "title": "title1",
            "titleStyle": FontStyleEnum.NORMAL.optionValue,
            "titleWeight": FontWeightEnum.BOLD.optionValue,
            "titleSize": 12,
            "legendDisplay": True,
            "legendPosition": LegendLocationEnum.BEST.optionValue,
            "legendSize": 10,
            "removeJobName": True,
            "removeRegions": False,
            "curvesAspect": {},
        }

    def getUserChoices( self: Self ) -> dict[ str, Any ]:
        """Access the m_userChoices attribute.

        Returns:
            dict[str] : The user choices for the figure.
        """
        return self.m_userChoices

    def getInputNames( self: Self ) -> set[ str ]:
        """Get source names from user selection.

        Returns:
            set[str] : Source names from ParaView pipeline.
        """
        inputAvailable = self.a01GetInputSources()
        inputNames: set[ str ] = set( pvt.getArrayChoices( inputAvailable ) )
        return inputNames

    def defineInputNames( self: Self ) -> None:
        """Adds the input names to the userChoices."""
        inputNames: set[ str ] = self.getInputNames()
        self.m_userChoices[ "inputNames" ] = inputNames

    def defineUserChoicesCurves( self: Self ) -> None:
        """Define user choices for curves to plot."""
        sourceNames: set[ str ] = self.getInputNames()
        dasPlot = self.b02GetCurvesToPlot()
        dasMinus1 = self.b07GetCurveConvention()
        curveNames: set[ str ] = set( pvt.getArrayChoices( dasPlot ) )
        minus1Names: set[ str ] = set( pvt.getArrayChoices( dasMinus1 ) )
        toUse1: set[ str ] = pvt.integrateSourceNames( sourceNames, curveNames )
        toUse2: set[ str ] = pvt.integrateSourceNames( sourceNames, minus1Names )
        self.m_userChoices[ "curveNames" ] = tuple( toUse1 )
        self.m_userChoices[ "curveConvention" ] = tuple( toUse2 )

    def defineCurvesAspect( self: Self ) -> None:
        """Define user choices for curve aspect properties."""
        curveAspect: tuple[ tuple[ float, float, float ], str, float, str, float ] = ( self.getCurveAspect() )
        curveName: str = self.getCurveToUse()
        self.m_userChoices[ "curvesAspect" ][ curveName ] = curveAspect

    def buildPythonViewScript( self: Self ) -> str:
        """Builds the Python script used to launch the Python View.

        The script is returned as a string to be then injected in the Python
        View.

        Returns:
            str: Complete Python View script.
        """
        sourceNames: set[ str ] = self.getInputNames()
        userChoices: dict[ str, Any ] = self.getUserChoices()
        script: str = f"timestep = '{str(GetActiveView().ViewTime)}'\n"
        script += f"sourceNames = {sourceNames}\n"
        script += f"variableName = '{userChoices['variableName']}'\n"
        script += f"dir_path = '{geos_pv_path}'\n"
        script += f"userChoices = {userChoices}\n\n\n"
        with self.m_pathPythonViewScript.open() as file:
            fileContents = file.read()
        script += fileContents
        return script

    def buildNewLayoutWithPythonView( self: Self ) -> None:
        """Create a new Python View layout."""
        # We first built the new layout.
        layout_names: list[ str ] = self.m_organizationDisplay.getLayoutsNames()
        nb_layouts: int = len( layout_names )
        # Imagine two layouts already exists, the new one will be named "Layout #3".
        layoutName: str = "Layout #" + str( nb_layouts + 1 )
        # Check that we that the layoutName is new and does not belong to the list of layout_names,
        # if not we modify the layoutName until it is a new one.
        if layoutName in layout_names:
            cpt: int = 2
            while layoutName in layout_names:
                layoutName = "Layout #" + str( nb_layouts + cpt )
                cpt += 1
        self.m_organizationDisplay.addLayout( layoutName )
        self.m_layoutName = layoutName

        # We then build the new python view.
        self.m_organizationDisplay.addViewToLayout( "PythonView", layoutName, 0 )
        self.m_pythonView = self.m_organizationDisplay.getLayoutViews()[ layoutName ][ 0 ]
        Show( GetActiveSource(), self.m_pythonView, "PythonRepresentation" )

    # Widgets definition
    """The names of the @smproperty methods command names below have a letter in lower case in
    front because PARAVIEW displays properties in the alphabetical order.
    See https://gitlab.kitware.com/paraview/paraview/-/issues/21493 for possible improvements on
    this issue."""

    @smproperty.dataarrayselection( name="InputSources" )
    def a01GetInputSources( self: Self ) -> vtkDataArraySelection:
        """Get all valid sources for the filter.

        Returns:
            vtkDataArraySelection: Valid data sources.
        """
        return self.m_validSources

    @smproperty.xml( """<PropertyGroup label="Select Input Sources">
                    <Property name="InputSources"/>
                    </PropertyGroup>""" )
    def a02GroupFlow( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.stringvector( name="CurvesAvailable", information_only="1" )
    def b00GetCurvesAvailable( self: Self ) -> list[ str ]:
        """Get the available curves.

        Returns:
            list[str]: List of curves.
        """
        return self.m_validColumnsDataframe

    @smproperty.stringvector( name="Abscissa", number_of_elements="1" )
    @smdomain.xml( """<StringListDomain name="list">
        <RequiredProperties><Property name="CurvesAvailable"
        function="CurvesAvailable"/></RequiredProperties>
        </StringListDomain>""" )
    def b01SetVariableName( self: Self, name: str ) -> None:
        """Set the name of X axis variable.

        Args:
            name (str): Name of the variable.
        """
        self.m_userChoices[ "variableName" ] = name
        self.Modified()

    @smproperty.dataarrayselection( name="Ordinate" )
    def b02GetCurvesToPlot( self: Self ) -> vtkDataArraySelection:
        """Get the curves to plot.

        Returns:
            vtkDataArraySelection: Data to plot.
        """
        return self.m_curvesToPlot

    @smproperty.intvector( name="PlotsPerRegion", label="PlotsPerRegion", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b03SetPlotsPerRegion( self: Self, boolean: bool ) -> None:
        """Set plot per region option.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "plotRegions" ] = boolean
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Curves To Plot">
                    <Property name="Abscissa"/>
                    <Property name="Ordinate"/>
                    <Property name="PlotsPerRegion"/>
                   </PropertyGroup>""" )
    def b04GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector(
        name="CurveConvention",
        label="Select Curves To Change Convention",
        default_values=0,
    )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b05SetCurveConvention( self: Self, boolean: bool ) -> None:
        """Select Curves To Change Convention.

        Args:
            boolean (bool): User choice.
        """
        self.m_multiplyCurves = boolean

    @smproperty.xml( """<PropertyGroup label="Curve Convention">
                    <Property name="CurveConvention"/>
                   </PropertyGroup>""" )
    def b06GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.dataarrayselection( name="CurveConventionSelection" )
    def b07GetCurveConvention( self: Self ) -> vtkDataArraySelection:
        """Get the curves to change convention.

        Returns:
            vtkDataArraySelection: Selected curves to change convention.
        """
        return self.m_curvesMinus1

    @smproperty.xml( """<PropertyGroup
                    panel_visibility="advanced">
                    <Property name="CurveConventionSelection"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="CurveConvention" value="1"/></Hints>
                   </PropertyGroup>""" )
    def b08GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="EditAxisProperties", label="Edit Axis Properties", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c01SetEditAxisProperties( self: Self, boolean: bool ) -> None:
        """Set option to edit axis properties.

        Args:
            boolean (bool): User choice.
        """
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Axis Properties">
                    <Property name="EditAxisProperties"/>
                   </PropertyGroup>""" )
    def c02GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="ReverseXY", label="Reverse XY Axes", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c02SetReverseXY( self: Self, boolean: bool ) -> None:
        """Set option to reverse X and Y axes.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "reverseXY" ] = boolean
        self.Modified()

    @smproperty.intvector( name="LogScaleX", label="X Axis Log Scale", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c03SetReverseXY( self: Self, boolean: bool ) -> None:
        """Set option to log scale for X axis.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "logScaleX" ] = boolean
        self.Modified()

    @smproperty.intvector( name="LogScaleY", label="Y Axis Log Scale", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c04SetReverseXY( self: Self, boolean: bool ) -> None:
        """Set option to log scale for Y axis.

        Args:
            boolean (bool): user choice.
        """
        self.m_userChoices[ "logScaleY" ] = boolean
        self.Modified()

    @smproperty.intvector( name="Minorticks", label="Display Minor ticks", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c05SetMinorticks( self: Self, boolean: bool ) -> None:
        """Set option to display minor ticks.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "minorticks" ] = boolean
        self.Modified()

    @smproperty.intvector( name="CustomAxisLim", label="Use Custom Axis Limits", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c06SetCustomAxisLim( self: Self, boolean: bool ) -> None:
        """Set option to define axis limits.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "customAxisLim" ] = boolean
        self.Modified()

    @smproperty.doublevector( name="LimMinX", label="X min", default_values=-1e36 )
    def c07LimMinX( self: Self, value: float ) -> None:
        """Set X axis min.

        Args:
            value (float): X axis min.
        """
        value2: Union[ float, None ] = value
        if value2 == -1e36:
            value2 = None
        self.m_userChoices[ "limMinX" ] = value2
        self.Modified()

    @smproperty.doublevector( name="LimMaxX", label="X max", default_values=1e36 )
    def c08LimMaxX( self: Self, value: float ) -> None:
        """Set X axis max.

        Args:
            value (float): X axis max.
        """
        value2: Union[ float, None ] = value
        if value2 == 1e36:
            value2 = None
        self.m_userChoices[ "limMaxX" ] = value2
        self.Modified()

    @smproperty.doublevector( name="LimMinY", label="Y min", default_values=-1e36 )
    def c09LimMinY( self: Self, value: float ) -> None:
        """Set Y axis min.

        Args:
            value (float): Y axis min.
        """
        value2: Union[ float, None ] = value
        if value2 == -1e36:
            value2 = None
        self.m_userChoices[ "limMinY" ] = value2
        self.Modified()

    @smproperty.doublevector( name="LimMaxY", label="Y max", default_values=1e36 )
    def c10LimMaxY( self: Self, value: float ) -> None:
        """Set Y axis max.

        Args:
            value (float): Y axis max.
        """
        value2: Union[ float, None ] = value
        if value2 == 1e36:
            value2 = None
        self.m_userChoices[ "limMaxY" ] = value2
        self.Modified()

    @smproperty.xml( """<PropertyGroup
                    panel_visibility="advanced">
                    <Property name="LimMinX"/>
                    <Property name="LimMaxX"/>
                    <Property name="LimMinY"/>
                    <Property name="LimMaxY"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="CustomAxisLim" value="1"/></Hints>
                   </PropertyGroup>""" )
    def c11GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.xml( """<PropertyGroup
                    panel_visibility="advanced">
                    <Property name="ReverseXY"/>
                    <Property name="LogScaleX"/>
                    <Property name="LogScaleY"/>
                    <Property name="CustomAxisLim"/>
                    <Property name="Minorticks"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="EditAxisProperties" value="1"/></Hints>
                   </PropertyGroup>""" )
    def c12GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="DisplayTitle", label="Display Title", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def d01SetDisplayTitle( self: Self, boolean: bool ) -> None:
        """Set option to display title.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "displayTitle" ] = boolean
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Title Properties">
                    <Property name="DisplayTitle"/>
                   </PropertyGroup>""" )
    def d02GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.stringvector( name="Title", default_values="title1" )
    def d03SetTitlePlot( self: Self, title: str ) -> None:
        """Set title.

        Args:
            title (str): Title.
        """
        self.m_userChoices[ "title" ] = title
        self.Modified()

    @smproperty.intvector( name="TitleStyle", label="Title Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontStyleEnum ) ) )
    def d04SetTitleStyle( self: Self, value: int ) -> None:
        """Set title font style.

        Args:
            value (int): Title font style index in FontStyleEnum.
        """
        choice = list( FontStyleEnum )[ value ]
        self.m_userChoices[ "titleStyle" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="TitleWeight", label="Title Weight", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontWeightEnum ) ) )
    def d05SetTitleWeight( self: Self, value: int ) -> None:
        """Set title font weight.

        Args:
            value (int): Title font weight index in FontWeightEnum.
        """
        choice = list( FontWeightEnum )[ value ]
        self.m_userChoices[ "titleWeight" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="TitleSize", label="Title Size", default_values=12 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def d06SetTitleSize( self: Self, size: float ) -> None:
        """Set title font size.

        Args:
            size (float): Title font size between 1 and 50.
        """
        self.m_userChoices[ "titleSize" ] = size
        self.Modified()

    @smproperty.xml( """<PropertyGroup>
                        panel_visibility="advanced">
                        <Property name="Title"/>
                        <Property name="TitleStyle"/>
                        <Property name="TitleWeight"/>
                        <Property name="TitleSize"/>
                        <Hints><PropertyWidgetDecorator type="GenericDecorator"
                        mode="visibility" property="DisplayTitle" value="1"/></Hints>
                    </PropertyGroup>""" )
    def d07PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="DisplayLegend", label="Display Legend", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def e00SetDisplayLegend( self: Self, boolean: bool ) -> None:
        """Set option to display legend.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "displayLegend" ] = boolean
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Legend Properties">
                        <Property name="DisplayLegend"/>
                    </PropertyGroup>""" )
    def e01PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="LegendPosition", label="Legend Position", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, LegendLocationEnum ) ) )
    def e02SetLegendPosition( self: Self, value: int ) -> None:
        """Set legend position.

        Args:
            value (int): Legend position index in LegendLocationEnum.
        """
        choice = list( LegendLocationEnum )[ value ]
        self.m_userChoices[ "legendPosition" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="LegendSize", label="Legend Size", default_values=10 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def e03SetLegendSize( self: Self, size: float ) -> None:
        """Set legend font size.

        Args:
            size (float): Legend font size between 1 and 50.
        """
        self.m_userChoices[ "legendSize" ] = size
        self.Modified()

    @smproperty.intvector( name="RemoveJobName", label="Remove Job Name in legend", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def e04SetRemoveJobName( self: Self, boolean: bool ) -> None:
        """Set option to remove job names from legend.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "removeJobName" ] = boolean
        self.Modified()

    @smproperty.intvector(
        name="RemoveRegionsName",
        label="Remove Regions Name in legend",
        default_values=0,
    )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def e05SetRemoveRegionsName( self: Self, boolean: bool ) -> None:
        """Set option to remove region names from legend.

        Args:
            boolean (bool): User choice.
        """
        self.m_userChoices[ "removeRegions" ] = boolean
        self.Modified()

    @smproperty.xml( """<PropertyGroup>
                        <Property name="LegendPosition"/>
                        <Property name="LegendSize"/>
                        <Property name="RemoveJobName"/>
                        <Property name="RemoveRegionsName"/>
                        <Hints><PropertyWidgetDecorator type="GenericDecorator"
                        mode="visibility" property="DisplayLegend" value="1"/></Hints>
                    </PropertyGroup>""" )
    def e06PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="ModifyCurvesAspect", label="Edit Curve Graphics", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def f01SetModifyCurvesAspect( self: Self, boolean: bool ) -> None:
        """Set option to change curve aspects.

        Args:
            boolean (bool): User choice.
        """
        self.m_modifyCurvesAspect = boolean

    @smproperty.xml( """<PropertyGroup label="Curve Properties">
                        <Property name="ModifyCurvesAspect"/>
                    </PropertyGroup>""" )
    def f02PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.stringvector( name="CurvesInfo", information_only="1" )
    def f03GetCurveNames( self: Self ) -> list[ str ]:
        """Get curves to modify aspects.

        Returns:
            set[str]: Curves to modify aspects.
        """
        return list( self.m_curvesToModify )

    @smproperty.stringvector( name="CurveToModify", number_of_elements="1" )
    @smdomain.xml( """<StringListDomain name="list">
        <RequiredProperties><Property name="CurvesInfo"
        function="CurvesInfo"/></RequiredProperties>
        </StringListDomain>""" )
    def f04SetCircleID( self: Self, value: str ) -> None:
        """Set m_curveToUse.

        Args:
           value (float): Value of m_curveToUse.
        """
        self.m_curveToUse = value
        self.Modified()

    def getCurveToUse( self: Self ) -> str:
        """Get m_curveToUse."""
        return self.m_curveToUse

    @smproperty.intvector( name="LineStyle", label="Line Style", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, LineStyleEnum ) ) )
    def f05SetLineStyle( self: Self, value: int ) -> None:
        """Set line style.

        Args:
           value (int): Line style index in LineStyleEnum.
        """
        choice = list( LineStyleEnum )[ value ]
        self.m_lineStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="LineWidth", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="10.0" name="range"/>""" )
    def f06SetLineWidth( self: Self, value: float ) -> None:
        """Set line width.

        Args:
           value (float): Line width between 1 and 10.
        """
        self.m_lineWidth = value
        self.Modified()

    @smproperty.intvector( name="MarkerStyle", label="Marker Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( LegendLocationEnum, MarkerStyleEnum ) ) )
    def f07SetMarkerStyle( self: Self, value: int ) -> None:
        """Set marker style.

        Args:
           value (int): Marker style index in MarkerStyleEnum.
        """
        choice = list( MarkerStyleEnum )[ value ]
        self.m_markerStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="MarkerSize", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="30.0" name="range"/>""" )
    def f08SetMarkerSize( self: Self, value: float ) -> None:
        """Set marker size.

        Args:
           value (float): Size of markers between 1 and 30.
        """
        self.m_markerSize = value
        self.Modified()

    @smproperty.xml( """<PropertyGroup panel_visibility="advanced">
                        <Property name="CurvesInfo"/>
                        <Property name="CurveToModify"/>
                        <Property name="LineStyle"/>
                        <Property name="LineWidth"/>
                        <Property name="MarkerStyle"/>
                        <Property name="MarkerSize"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="ModifyCurvesAspect" value="1"/></Hints>
                    </PropertyGroup>""" )
    def f09PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.doublevector( name="ColorEnvelop", default_values=[ 0, 0, 0 ], number_of_elements=3 )
    @smdomain.xml( """<DoubleRangeDomain max="1" min="0" name="range"/>""" )
    def f10SetColor( self: Self, value0: float, value1: float, value2: float ) -> None:
        """Set envelope color.

        Args:
           value0 (float): Red color between 0 and 1.
           value1 (float): Green color between 0 and 1.
           value2 (float): Blue color between 0 and 1.
        """
        self.m_color = ( value0, value1, value2 )
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="" panel_widget="FontEditor"
                    panel_visibility="default">
                    <Property name="ColorEnvelop" function="Color"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="ModifyCurvesAspect" value="1"/></Hints>
                    </PropertyGroup>""" )
    def f11PropertyGroup( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    def getCurveAspect( self: Self, ) -> tuple[ tuple[ float, float, float ], str, float, str, float ]:
        """Get curve aspect properties according to user choices.

        Returns:
            tuple: (color, lineStyle, linewidth, marker, markerSize)
        """
        return (
            self.m_color,
            self.m_lineStyle,
            self.m_lineWidth,
            self.m_markerStyle,
            self.m_markerSize,
        )

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): Input port.
            info (vtkInformationVector): Info.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkDataObject" )
        else:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkDataObject" )
        return 1

    def ApplyFilter( self, inputMesh: vtkDataObject, outputMesh: vtkDataObject ) -> None:
        """Dummy interface for plugin to fit decorator reqs.

        Args:
            inputMesh : A dummy mesh to transform.
            outputMesh : A dummy mesh transformed.

        """
        assert self.m_pythonView is not None, "No Python View was found."
        viewSize = GetActiveView().ViewSize
        self.m_userChoices[ "ratio" ] = viewSize[ 0 ] / viewSize[ 1 ]
        self.defineInputNames()
        self.defineUserChoicesCurves()
        self.defineCurvesAspect()
        self.m_pythonView.Script = self.buildPythonViewScript()
        Render()
        return
