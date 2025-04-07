# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from enum import Enum
from typing import Any, Union, cast

import numpy as np
import numpy.typing as npt
from paraview.simple import (  # type: ignore[import-not-found]
    Render, )
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkDataArraySelection as vtkDAS
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.dirname( dir_path )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import PVplugins # noqa: F401

import geos_posp.visu.mohrCircles.functionsMohrCircle as mcf
import geos_posp.visu.PVUtils.paraviewTreatments as pvt
from geos.geomechanics.model.MohrCircle import MohrCircle
from geos.utils.enumUnits import Pressure, enumerationDomainUnit
from geos.utils.GeosOutputsConstants import (
    FAILURE_ENVELOPE,
    GeosMeshOutputsEnum,
)
from geos.utils.Logger import Logger, getLogger
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_ROCK_COHESION,
)
from geos_posp.processing.vtkUtils import getArrayInObject, mergeBlocks
from geos_posp.visu.PVUtils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )
from geos_posp.visu.PVUtils.DisplayOrganizationParaview import (
    buildNewLayoutWithPythonView, )
from geos_posp.visu.PVUtils.matplotlibOptions import (
    FontStyleEnum,
    FontWeightEnum,
    LegendLocationEnum,
    LineStyleEnum,
    MarkerStyleEnum,
    OptionSelectionEnum,
    optionEnumToXml,
)

__doc__ = """
PVMohrCirclePlot is a Paraview plugin that allows to compute and plot
Mohr's circles of selected cells and times from effective stress attribute.

Input is a vtkMultiBlockDataSet or vtkUnstructuredGrid.

This filter results in opening a new Python View window and displaying
Mohr's circle plot.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVMohrCirclePlot.
* Select the mesh containing the cells you want to plot Mohr's circles.
* Search and Apply Mohr's Circle Plot Filter.

.. WARNING::
    Input vtk must contains a limited number of cells, Paraview may crash
    otherwise. In addition, input pipeline should consist of the minimum number
    of filters since this filter repeats the operations at every time steps.

"""


@smproxy.filter( name="PVMohrCirclePlot", label="Plot Mohr's Circles" )
@smhint.xml( """
    <ShowInMenu category="3- Geos Geomechanics"/>
    <View type="PythonView"/>
    """ )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid", "vtkMultiBlockDataSet" ],
    composite_data_supported=False,
)
class PVMohrCirclePlot( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to plot Mohr's Circles of selected cells and times.

        Mohr's circles are plotted using a Python View.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkDataObject" )

        # create a new PythonView
        self.m_pythonView: Any = buildNewLayoutWithPythonView()

        #: list of all cell ids
        self.m_cellIds: list[ str ] = []

        #: cell selection object
        self.m_cellIdsDAS: vtkDAS = vtkDAS()
        self.m_cellIdsDAS.AddObserver( 0, createModifiedCallback( self ) )

        #: list of all time steps
        self.m_timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )

        #: time steps selection object
        self.m_timeStepsDAS: vtkDAS = vtkDAS()
        self.m_timeStepsDAS.AddObserver( 0, createModifiedCallback( self ) )

        #: list of all mohr circles
        self.m_mohrCircles: list[ MohrCircle ] = []

        #: failure envelop parameters
        self.m_rockCohesion: float = DEFAULT_ROCK_COHESION
        self.m_frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        #: stress convention (False for GEOS convention)
        self.m_stressConvention: bool = False

        #: curve aspect options - the same variables are set for each selected curve
        self.m_circleIdUsed: str = ""
        self.m_color: tuple[ float, float, float ] = ( 0.0, 0.0, 0.0 )
        self.m_lineStyle: str = LineStyleEnum.SOLID.optionValue
        self.m_lineWidth: float = 1.0
        self.m_markerStyle: str = MarkerStyleEnum.NONE.optionValue
        self.m_markerSize: float = 1.0

        #: figure user choices
        self.m_userChoices: dict[ str, Any ] = {
            "xAxis": "Normal stress",
            "yAxis": "Shear stress",
            "stressUnit": 0,
            "annotateCircles": 1,
            "displayTitle": True,
            "title": "Mohr's circles",
            "titleStyle": FontStyleEnum.NORMAL.optionValue,
            "titleWeight": FontWeightEnum.BOLD.optionValue,
            "titleSize": 12,
            "displayLegend": True,
            "legendPosition": LegendLocationEnum.BEST.optionValue,
            "legendSize": 10,
            "minorticks": False,
            "curvesAspect": {},
            "customAxisLim": False,
            "limMinX": None,
            "limMaxX": None,
            "limMinY": None,
            "limMaxY": None,
        }

        #: request data processing step - incremented each time RequestUpdateExtent is called
        self.m_requestDataStep: int = -1

        #: logger
        self.m_logger: Logger = getLogger( "Mohr's Circle Analysis Filter" )

    def getUserChoices( self: Self ) -> dict[ str, Any ]:
        """Access the m_userChoices attribute.

        Returns:
            dict[str] : the user choices for the figure.
        """
        return self.m_userChoices

    def getCircleIds( self: Self ) -> list[ str ]:
        """Get circle ids to plot.

        Returns:
            list[str]: list of circle ids to plot.
        """
        cellIds: list[ str ] = pvt.getArrayChoices( self.a01GetCellIdsDAS() )
        timeSteps: list[ str ] = pvt.getArrayChoices( self.a02GetTimestepsToPlot() )
        return [ mcf.getMohrCircleId( cellId, timeStep ) for timeStep in timeSteps for cellId in cellIds ]

    def defineCurvesAspect( self: Self ) -> None:
        """Add curve aspect parameters according to user choices."""
        self.m_userChoices[ "curvesAspect" ][ self.m_circleIdUsed ] = {
            "color": self.m_color,
            "linestyle": self.m_lineStyle,
            "linewidth": self.m_lineWidth,
            "marker": self.m_markerStyle,
            "markersize": self.m_markerSize,
        }

    @smproperty.xml( """
        <Property name="Refresh Data"
                  command="a00RefreshData"
                  panel_widget="command_button"/>
        <Documentation>
            Recompute all the Mohr's circles at all time steps and display
            selected ones.
        </Documentation>
        """ )
    def a00RefreshData( self: Self ) -> None:
        """Reset self.m_requestDataStep to reload data from all time steps."""
        self.m_requestDataStep = -1
        self.Modified()

    @smproperty.dataarrayselection( name="CellIdToPlot" )
    def a01GetCellIdsDAS( self: Self ) -> vtkDAS:
        """Get selected cell ids to plot.

        Returns:
            vtkDataArraySelection: selected cell ids.
        """
        return self.m_cellIdsDAS

    @smproperty.dataarrayselection( name="TimeStepsToPlot" )
    def a02GetTimestepsToPlot( self: Self ) -> vtkDAS:
        """Get selected time steps to plot.

        Returns:
            vtkDataArraySelection: selected time steps.
        """
        return self.m_timeStepsDAS

    @smproperty.xml( """<PropertyGroup label="Circle and Time Steps To Plot"
                        panel_visibility="default">
                    <Property name="CellIdToPlot"/>
                    <Property name="TimeStepsToPlot"/>
                   </PropertyGroup>""" )
    def a03GroupTimesteps( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.doublevector(
        name="RockCohesion",
        label="Rock Cohesion (Pa)",
        default_values=DEFAULT_ROCK_COHESION,
    )
    def b01SetCohesion( self: Self, value: float ) -> None:
        """Set rock cohesion.

        Args:
            value (float): rock cohesion (Pa)
        """
        self.m_rockCohesion = value
        self.Modified()

    @smproperty.doublevector(
        name="FrictionAngle",
        label="Friction Angle (°)",
        default_values=DEFAULT_FRICTION_ANGLE_DEG,
    )
    def b02SetFrictionAngle( self: Self, value: float ) -> None:
        """Set friction angle.

        Args:
            value (float): friction angle (°).
        """
        self.m_frictionAngle = value * np.pi / 180.0
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Mohr-Coulomb Parameters"
                        panel_visibility="default">
                    <Property name="RockCohesion"/>
                    <Property name="FrictionAngle"/>
                   </PropertyGroup>""" )
    def b03GroupUnit( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector( name="StressUnit", label="Stress Unit", default_values=0 )
    @smdomain.xml( enumerationDomainUnit( cast( Enum, Pressure ) ) )
    def b04SetStressUnit( self: Self, choice: int ) -> None:
        """Set stress unit.

        Args:
            choice (int): stress unit index in Pressure enum.
        """
        self.m_userChoices[ "stressUnit" ] = choice
        self.Modified()

    @smproperty.intvector(
        name="StressConventionForCompression",
        label="Change stress Convention",
        default_values=0,
    )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b05SetStressCompressionConvention( self: Self, boolean: bool ) -> None:
        """Set stress compression convention in plots.

        Args:
            boolean (bool): False is same as Geos convention, True is usual
            geomechanical convention.
        """
        # need to convert Geos results if use the usual convention
        self.m_stressConvention = boolean
        self.Modified()

    @smproperty.intvector( name="AnnotateCircles", label="Annotate Circles", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b06SetAnnotateCircles( self: Self, boolean: bool ) -> None:
        """Set option to add annotatations to circles.

        Args:
            boolean (bool): user choce.
        """
        self.m_userChoices[ "annotateCircles" ] = boolean
        self.Modified()

    @smproperty.intvector( name="Minorticks", label="Minorticks", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b07SetMinorticks( self: Self, boolean: bool ) -> None:
        """Set option to display minor ticks.

        Args:
            boolean (bool): user choice.
        """
        self.m_userChoices[ "minorticks" ] = boolean
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Properties"
                        panel_visibility="default">
                    <Property name="StressUnit"/>
                    <Property name="StressConventionForCompression"/>
                    <Property name="AnnotateCircles"/>
                    <Property name="Minorticks"/>
                   </PropertyGroup>""" )
    def b08GroupUnit( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector( name="ModifyTitleAndLegend", label="Modify Title And Legend", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def c00SetModifyTitleAndLegend( self: Self, boolean: bool ) -> None:
        """Set option to modify legend and title.

        Args:
            boolean (bool): user choice.
        """
        self.m_userChoices[ "displayTitle" ] = boolean
        self.m_modifyTitleAndLegend = boolean

    @smproperty.stringvector( name="Title", default_values="Mohr's circle" )
    def c01SetTitlePlot( self: Self, title: str ) -> None:
        """Set title.

        Args:
            title (str): title.
        """
        self.m_userChoices[ "title" ] = title
        self.Modified()

    @smproperty.intvector( name="Title Style", label="Title Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontStyleEnum ) ) )
    def c02SetTitleStyle( self: Self, value: int ) -> None:
        """Set title font style.

        Args:
            value (int): title font style index in FontStyleEnum.
        """
        choice = list( FontStyleEnum )[ value ]
        self.m_userChoices[ "titleStyle" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="Title Weight", label="Title Weight", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontWeightEnum ) ) )
    def c03SetTitleWeight( self: Self, value: int ) -> None:
        """Set title font weight.

        Args:
            value (int): title font weight index in FontWeightEnum.
        """
        choice = list( FontWeightEnum )[ value ]
        self.m_userChoices[ "titleWeight" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="Title Size", label="Title Size", default_values=12 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def c04SetTitleSize( self: Self, size: float ) -> None:
        """Set title font size.

        Args:
            size (float): title font size between 1 and 50.
        """
        self.m_userChoices[ "titleSize" ] = size
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Title Properties" panel_visibility="advanced">
                        <Property name="Title"/>
                        <Property name="Title Style"/>
                        <Property name="Title Weight"/>
                        <Property name="Title Size"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="ModifyTitleAndLegend"
                    value="1"/></Hints>
                    </PropertyGroup>""" )
    def c06PropertyGroup( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector( name="LegendPosition", label="Legend Position", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, LegendLocationEnum ) ) )
    def d01SetLegendPosition( self: Self, value: int ) -> None:
        """Set legend position.

        Args:
            value (int): legend position index in LegendLocationEnum.
        """
        choice = list( LegendLocationEnum )[ value ]
        self.m_userChoices[ "legendPosition" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="LegendSize", label="Legend Size", default_values=10 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def d02SetLegendSize( self: Self, size: float ) -> None:
        """Set legend font size.

        Args:
            size (float): legend font size between 1 and 50.
        """
        self.m_userChoices[ "legendSize" ] = size
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Legend Properties" panel_visibility="advanced">
                        <Property name="LegendPosition"/>
                        <Property name="LegendSize"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="ModifyTitleAndLegend"
                    value="1"/></Hints>
                    </PropertyGroup>""" )
    def d03PropertyGroup( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.intvector( name="CustomAxisLim", label="Modify Axis Limits", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def e01SetCustomAxisLim( self: Self, boolean: bool ) -> None:
        """Set option to define axis limits.

        Args:
            boolean (bool): user choice.
        """
        self.m_userChoices[ "customAxisLim" ] = boolean
        self.Modified()

    @smproperty.doublevector( name="LimMinX", label="X min", default_values=-1e36 )
    def e02LimMinX( self: Self, value: float ) -> None:
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
    def e03LimMaxX( self: Self, value: float ) -> None:
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
    def e04LimMinY( self: Self, value: float ) -> None:
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
    def e05LimMaxY( self: Self, value: float ) -> None:
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
    def e06GroupFlow( self: Self ) -> None:
        """Organized groups."""
        self.Modified()

    @smproperty.intvector( name="ModifyCurvesAspect", label="Modify Curves Aspect", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def f01SetModifyCurvesAspect( self: Self, boolean: bool ) -> None:
        """Set option to modify curve aspect.

        Args:
            boolean (bool): user choice.
        """
        self.m_modifyCurvesAspect = boolean

    @smproperty.stringvector( name="CurvesInfo", information_only="1" )
    def f02GetCurveNames( self: Self ) -> list[ str ]:
        """Get curves to modify.

        Returns:
            list[str]: curves to modify
        """
        circleIds: list[ str ] = self.getCircleIds()
        return [ FAILURE_ENVELOPE ] + circleIds

    @smproperty.stringvector( name="CurveToModify", label="Curve name", number_of_elements="1" )
    @smdomain.xml( """<StringListDomain name="list">
        <RequiredProperties><Property name="CurvesInfo"
            function="CurvesInfo"/>
        </RequiredProperties>
        </StringListDomain>""" )
    def f03SetCellID( self: Self, value: str ) -> None:
        """Set circle ids to use.

        Args:
            value (str): circle ids.
        """
        self.m_circleIdUsed = value
        self.Modified()

    @smproperty.intvector( name="LineStyle", label="Line Style", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, LineStyleEnum ) ) )
    def f04SetLineStyle( self: Self, value: int ) -> None:
        """Set line style.

        Args:
           value (int): line style index in LineStyleEnum
        """
        choice = list( LineStyleEnum )[ value ]
        self.m_lineStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="LineWidth", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="10.0" name="range"/>""" )
    def f05SetLineWidth( self: Self, value: float ) -> None:
        """Set line width.

        Args:
           value (float): line width between 1 and 10.
        """
        self.m_lineWidth = value
        self.Modified()

    @smproperty.intvector( name="MarkerStyle", label="Marker Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, MarkerStyleEnum ) ) )
    def f06SetMarkerStyle( self: Self, value: int ) -> None:
        """Set marker style.

        Args:
           value (int): Marker style index in MarkerStyleEnum
        """
        choice = list( MarkerStyleEnum )[ value ]
        self.m_markerStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="MarkerSize", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="30.0" name="range"/>""" )
    def f07SetMarkerSize( self: Self, value: float ) -> None:
        """Set marker size.

        Args:
           value (float): size of markers between 1 and 30.
        """
        self.m_markerSize = value
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Line Edition" panel_visibility="advanced">
                        <Property name="CurvesInfo"/>
                        <Property name="CurveToModify"/>
                        <Property name="LineStyle"/>
                        <Property name="LineWidth"/>
                        <Property name="MarkerStyle"/>
                        <Property name="MarkerSize"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="ModifyCurvesAspect"
                    value="1"/></Hints>
                    </PropertyGroup>""" )
    def f08PropertyGroup( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    @smproperty.doublevector( name="ColorEnvelop", default_values=[ 0, 0, 0 ], number_of_elements=3 )
    @smdomain.xml( """<DoubleRangeDomain max="1" min="0" name="range"/>""" )
    def f09SetColor( self: Self, value0: float, value1: float, value2: float ) -> None:
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
                    mode="visibility" property="ModifyCurvesAspect"
                    value="1"/></Hints>
                    </PropertyGroup>""" )
    def f10PropertyGroup( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

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
        executive = self.GetExecutive()  # noqa: F841
        inInfo = inInfoVec[ 0 ]
        # only at initialization step, no change later
        if self.m_requestDataStep < 0:
            # get cell ids
            inData = self.GetInputData( inInfoVec, 0, 0 )
            self.m_cellIds = pvt.getVtkOriginalCellIds( inData )

            # update vtkDAS
            for circleId in self.m_cellIds:
                if not self.m_cellIdsDAS.ArrayExists( circleId ):
                    self.m_cellIdsDAS.AddArray( circleId )

            self.m_timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS() )  # type: ignore
            for timestep in self.m_timeSteps:
                if not self.m_timeStepsDAS.ArrayExists( str( timestep ) ):
                    self.m_timeStepsDAS.AddArray( str( timestep ) )
        return 1

    def RequestUpdateExtent(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestUpdateExtent.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        self.m_logger.info( f"Apply filter {__name__}" )
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]

        if self.m_requestDataStep < 0:
            self.m_mohrCircles.clear()

        # update requestDataStep
        self.m_requestDataStep += 1

        # update time according to requestDataStep iterator
        if self.m_requestDataStep < len( self.m_timeSteps ):
            inInfo.GetInformationObject( 0 ).Set(
                executive.UPDATE_TIME_STEP(),  # type: ignore[no-any-return]
                self.m_timeSteps[ self.m_requestDataStep ],
            )
            outInfoVec.GetInformationObject( 0 ).Set(
                executive.UPDATE_TIME_STEP(),  # type: ignore[no-any-return]
                self.m_timeSteps[ self.m_requestDataStep ],
            )

            # update all objects according to new time info
            self.Modified()
        return 1

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if ( outData is None ) or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
            self: Self,
            request: vtkInformation,  # noqa: F841
            inInfoVec: list[ vtkInformationVector ],  # noqa: F841
            outInfoVec: vtkInformationVector,  # noqa: F841
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
            input: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
            assert input is not None, "Input data is undefined"

            executive = self.GetExecutive()
            # get mohr circles from all time steps
            if self.m_requestDataStep < len( self.m_timeSteps ):
                request.Set( executive.CONTINUE_EXECUTING(), 1 )  # type: ignore[no-any-return]
                currentTimeStep: float = (
                    inInfoVec[ 0 ].GetInformationObject( 0 ).Get(
                        executive.UPDATE_TIME_STEP() )  # type: ignore[no-any-return]
                )
                self.m_mohrCircles.extend( self.createMohrCirclesAtTimeStep( input, currentTimeStep ) )

            # plot mohr circles
            else:
                # displayed time step, no need to go further
                request.Remove( executive.CONTINUE_EXECUTING() )  # type: ignore[no-any-return]

                assert self.m_pythonView is not None, "No Python View was found."
                self.defineCurvesAspect()
                mohrCircles: list[ MohrCircle ] = self.filterMohrCircles()
                self.m_pythonView.Script = mcf.buildPythonViewScript(
                    parent_dir_path,
                    mohrCircles,
                    self.m_rockCohesion,
                    self.m_frictionAngle,
                    self.getUserChoices(),
                )
                Render()

        except Exception as e:
            self.m_logger.error( "Mohr circles cannot be plotted due to:" )
            self.m_logger.error( str( e ) )
            return 0
        return 1

    def createMohrCirclesAtTimeStep(
        self: Self,
        mesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ],
        currentTimeStep: float,
    ) -> list[ MohrCircle ]:
        """Create mohr circles of all cells at the current time step.

        Args:
            mesh (Union[vtkUnstructuredGrid, vtkMultiBlockDataSet]): input mesh.
            currentTimeStep (float): current time step

        Returns:
            list[MohrCircle]: list of MohrCircles for the current time step.
        """
        # get mesh and merge if needed
        meshMerged: vtkUnstructuredGrid = mergeBlocks( mesh ) if isinstance( mesh, vtkMultiBlockDataSet ) else mesh
        assert meshMerged is not None, "Input data is undefined"

        stressArray: npt.NDArray[ np.float64 ] = getArrayInObject( meshMerged,
                                                                   GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName,
                                                                   False )
        return mcf.createMohrCircleAtTimeStep( stressArray, self.m_cellIds, str( currentTimeStep ),
                                               self.m_stressConvention )

    def filterMohrCircles( self: Self ) -> list[ MohrCircle ]:
        """Filter the list of all MohrCircle to get those to plot.

        Returns:
            list[MohrCircle]: list of MohrCircle to plot.
        """
        # circle ids to plot
        circleIds: list[ str ] = self.getCircleIds()
        return [ mohrCircle for mohrCircle in self.m_mohrCircles if mohrCircle.getCircleId() in circleIds ]
