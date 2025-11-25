# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Alexandre Benedicto, Martin Lemay, Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
from pathlib import Path
from enum import Enum
from typing import Any, Union, cast

import numpy as np
import numpy.typing as npt
from paraview.simple import (  # type: ignore[import-not-found]
    Render, )
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler, )

from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkDataArraySelection as vtkDAS
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, )

# Update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.geomechanics.model.MohrCircle import MohrCircle
from geos.utils.enumUnits import Pressure, enumerationDomainUnit
from geos.utils.GeosOutputsConstants import (
    FAILURE_ENVELOPE,
    GeosMeshOutputsEnum,
)
from geos.utils.Logger import CustomLoggerFormatter
from geos.utils.PhysicalConstants import (
    DEFAULT_FRICTION_ANGLE_DEG,
    DEFAULT_FRICTION_ANGLE_RAD,
    DEFAULT_ROCK_COHESION,
)
from geos.mesh.utils.arrayHelpers import getArrayInObject

import geos.pv.utils.mohrCircles.functionsMohrCircle as mcf
import geos.pv.utils.paraviewTreatments as pvt
from geos.pv.utils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )
from geos.pv.utils.DisplayOrganizationParaview import (
    buildNewLayoutWithPythonView, )
from geos.pv.pyplotUtils.matplotlibOptions import (
    FontStyleEnum,
    FontWeightEnum,
    LegendLocationEnum,
    LineStyleEnum,
    MarkerStyleEnum,
    OptionSelectionEnum,
    optionEnumToXml,
)
from geos.pv.utils.mohrCircles.functionsMohrCircle import StressConventionEnum

__doc__ = """
PVMohrCirclePlot is a ParaView plugin that allows to compute and plot
Mohr's circles of selected cells and times from effective stress attribute.

Input is a vtkMultiBlockDataSet or vtkUnstructuredGrid.

This filter results in opening a new Python View window and displaying
Mohr's circle plot.

To use it:

This plugin requires the presence of a `stressEffective` attribute in the mesh. Moreover, several timesteps should also be detected.

.. Warning::
    The whole ParaView pipeline will be executed for all timesteps present in the initial PVD file. Please be aware that the number of pipeline filters and timesteps should be as limited as possible. Otherwise, please consider going to get a cup of coffee.

* Load the module in ParaView: Tools > Manage Plugins.... > Load new > PVMohrCirclePlot

If you start from a raw GEOS output, execute the following steps before moving on.
- First, consider removing some unnecessary timesteps manually from the PVD file in order to reduce the calculation time and resources used in the following steps.
- Load the data into ParaView, then apply the `PVGeosExtractMergeBlock*` plugin on it.
- Select the filter output that you want to consider for the Mohr's circle plot.


* Extract a few number of cells with the `ExtractSelection` ParaView Filter, then use the `MergeBlocks` ParaView Filter.
* Select the resulting mesh in the pipeline.
* Select Filters > 3- Geos Geomechanics > Plot Mohr's Circle.
* Select the cell Ids and time steps you want
* (Optional) Set rock cohesion and/or friction angle.
* Apply.



.. Note::
    After a first application, select again cells and time steps to display, then
        * Apply again
        * Click on `Refresh Data` (you may have to click twice to refresh the Python view correctly).
"""


@smproxy.filter( name="PVMohrCirclePlot", label="Plot Mohr's Circles" )
@smhint.xml( """
    <ShowInMenu category="3- Geos Geomechanics"/>
    <View type="PythonView"/>
    """ )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=False,
)
class PVMohrCirclePlot( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """ParaView plugin to plot Mohr's Circles of selected cells and times.

        Mohr's circles are plotted using a Python View.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkDataObject" )

        # Create a new PythonView
        self.pythonView: Any = buildNewLayoutWithPythonView()

        # List of all cell ids in the mesh
        self.cellIds: list[ str ] = []

        # List of all time steps
        self.timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )

        # Cell selection object
        self.cellIdsDAS: vtkDAS = vtkDAS()
        self.cellIdsDAS.AddObserver( 0, createModifiedCallback( self ) )

        # Time steps selection object
        self.timeStepsDAS: vtkDAS = vtkDAS()
        self.timeStepsDAS.AddObserver( 0, createModifiedCallback( self ) )

        # Requested cell ids and time steps
        self.requestedCellIds: list[ str ] = []
        self.requestedTimeStepsIndexes: list[ int ] = []

        # List of mohr circles
        self.mohrCircles: set[ MohrCircle ] = set()

        # Failure envelop parameters
        self.rockCohesion: float = DEFAULT_ROCK_COHESION
        self.frictionAngle: float = DEFAULT_FRICTION_ANGLE_RAD

        # Stress convention (Geos: negative compression, Usual: positive)
        self.useGeosStressConvention: bool = True

        # Curve aspect options - the same variables are set for each selected curve
        self.circleIdUsed: str = ""
        self.color: tuple[ float, float, float ] = ( 0.0, 0.0, 0.0 )
        self.lineStyle: str = LineStyleEnum.SOLID.optionValue
        self.lineWidth: float = 1.0
        self.markerStyle: str = MarkerStyleEnum.NONE.optionValue
        self.markerSize: float = 1.0

        # Figure user choices
        self.userChoices: dict[ str, Any ] = {
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

        # Request data processing step - incremented each time RequestUpdateExtent is called
        self.requestDataStep: int = -1

        # Logger
        self.logger: logging.Logger = logging.getLogger( "MohrCircle" )
        self.logger.setLevel( logging.INFO )
        if not self.logger.hasHandlers():
            handler = VTKHandler()
            handler.setFormatter( CustomLoggerFormatter( False ) )

            self.logger.addHandler( handler )

    @smproperty.xml( """
        <Property name="Refresh Data"
                  command="a00RefreshData"
                  panel_widget="command_button"/>
        <Documentation>
            Recompute Mohr's circles for requested time steps and cell ids.
        </Documentation>
        """ )
    def a00RefreshData( self: Self ) -> None:
        """Reset self.requestDataStep to reload data from all time steps."""
        self.requestDataStep = -1
        self.logger.info( "Recomputing data for selected time steps and cell ids." )
        self.Modified()

    @smproperty.dataarrayselection( name="CellIdToPlot" )
    def a01GetCellIdsDAS( self: Self ) -> vtkDAS:
        """Get selected cell ids to plot.

        Returns:
            vtkDataArraySelection: Selected cell ids.
        """
        return self.cellIdsDAS

    @smproperty.dataarrayselection( name="TimeStepsToPlot" )
    def a02GetTimestepsToPlot( self: Self ) -> vtkDAS:
        """Get selected time steps to plot.

        Returns:
            vtkDataArraySelection: Selected time steps.
        """
        return self.timeStepsDAS

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
            value (float): Rock cohesion (Pa).
        """
        self.rockCohesion = value
        self.Modified()

    @smproperty.doublevector(
        name="FrictionAngle",
        label="Friction Angle (°)",
        default_values=DEFAULT_FRICTION_ANGLE_DEG,
    )
    def b02SetFrictionAngle( self: Self, value: float ) -> None:
        """Set friction angle.

        Args:
            value (float): Friction angle (°).
        """
        self.frictionAngle = value * np.pi / 180.0
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
            choice (int): Stress unit index in Pressure enum.
        """
        self.userChoices[ "stressUnit" ] = choice
        self.Modified()

    @smproperty.intvector(
        name="StressConventionForCompression",
        label="Use GEOS stress Convention",
        default_values=1,
    )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b05SetStressCompressionConvention( self: Self, useGeosConvention: bool ) -> None:
        """Set stress compression convention in plots.

        Args:
            useGeosConvention (bool): True is Geos convention, False is usual geomechanical convention.
        """
        # Specify if data is from GEOS
        self.useGeosStressConvention = useGeosConvention
        self.Modified()

    @smproperty.intvector( name="AnnotateCircles", label="Annotate Circles", default_values=1 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b06SetAnnotateCircles( self: Self, boolean: bool ) -> None:
        """Set option to add annotatations to circles.

        Args:
            boolean (bool): True to annotate circles, False otherwise.
                                Default is True.
        """
        self.userChoices[ "annotateCircles" ] = boolean
        self.Modified()

    @smproperty.intvector( name="Minorticks", label="Minorticks", default_values=0 )
    @smdomain.xml( """<BooleanDomain name="bool"/>""" )
    def b07SetMinorticks( self: Self, boolean: bool ) -> None:
        """Set option to display minor ticks.

        Args:
            boolean (bool): True to display the minor ticks, False otherwise.
                                Defaults is False.
        """
        self.userChoices[ "minorticks" ] = boolean
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
            boolean (bool): True to modify the title and legend, False otherwise.
                                Defaults is False.
        """
        self.userChoices[ "displayTitle" ] = boolean
        self.modifyTitleAndLegend = boolean

    @smproperty.stringvector( name="Title", default_values="Mohr's circle" )
    def c01SetTitlePlot( self: Self, title: str ) -> None:
        """Set title.

        Args:
            title (str): Requested title. Defaults is "Mohr's circle".
        """
        self.userChoices[ "title" ] = title
        self.Modified()

    @smproperty.intvector( name="Title Style", label="Title Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontStyleEnum ) ) )
    def c02SetTitleStyle( self: Self, value: int ) -> None:
        """Set title font style.

        Args:
            value (int): Title font style index in FontStyleEnum.
        """
        choice = list( FontStyleEnum )[ value ]
        self.userChoices[ "titleStyle" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="Title Weight", label="Title Weight", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, FontWeightEnum ) ) )
    def c03SetTitleWeight( self: Self, value: int ) -> None:
        """Set title font weight.

        Args:
            value (int): Title font weight index in FontWeightEnum.
        """
        choice = list( FontWeightEnum )[ value ]
        self.userChoices[ "titleWeight" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="Title Size", label="Title Size", default_values=12 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def c04SetTitleSize( self: Self, size: float ) -> None:
        """Set title font size.

        Args:
            size (float): Title font size between 1 and 50.
        """
        self.userChoices[ "titleSize" ] = size
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
            value (int): Legend position index in LegendLocationEnum.
        """
        choice = list( LegendLocationEnum )[ value ]
        self.userChoices[ "legendPosition" ] = choice.optionValue
        self.Modified()

    @smproperty.intvector( name="LegendSize", label="Legend Size", default_values=10 )
    @smdomain.xml( """<IntRangeDomain name="range" min="1" max="50"/>""" )
    def d02SetLegendSize( self: Self, size: float ) -> None:
        """Set legend font size.

        Args:
            size (float): Legend font size between 1 and 50.
        """
        self.userChoices[ "legendSize" ] = size
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
            boolean (bool): True to define manually the axis limits, False otherwise.
                                Defaults is False.
        """
        self.userChoices[ "customAxisLim" ] = boolean
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
        self.userChoices[ "limMinX" ] = value2
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
        self.userChoices[ "limMaxX" ] = value2
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
        self.userChoices[ "limMinY" ] = value2
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
        self.userChoices[ "limMaxY" ] = value2
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
            boolean (bool): True to modify curve aspect, False otherwise.
                                Defaults is False.
        """
        self.modifyCurvesAspect = boolean

    @smproperty.stringvector( name="CurvesInfo", information_only="1" )
    def f02GetCurveNames( self: Self ) -> list[ str ]:
        """Get curves to modify.

        Returns:
            list[str]: Curves to modify
        """
        circleIds: list[ str ] = self._getCircleIds()
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
            value (str): Circle ids.
        """
        self.circleIdUsed = value
        self.Modified()

    @smproperty.intvector( name="LineStyle", label="Line Style", default_values=1 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, LineStyleEnum ) ) )
    def f04SetLineStyle( self: Self, value: int ) -> None:
        """Set line style.

        Args:
           value (int): Line style index in LineStyleEnum.
        """
        choice = list( LineStyleEnum )[ value ]
        self.lineStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="LineWidth", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="10.0" name="range"/>""" )
    def f05SetLineWidth( self: Self, value: float ) -> None:
        """Set line width.

        Args:
           value (float): Line width between 1 and 10.
        """
        self.lineWidth = value
        self.Modified()

    @smproperty.intvector( name="MarkerStyle", label="Marker Style", default_values=0 )
    @smdomain.xml( optionEnumToXml( cast( OptionSelectionEnum, MarkerStyleEnum ) ) )
    def f06SetMarkerStyle( self: Self, value: int ) -> None:
        """Set marker style.

        Args:
           value (int): Marker style index in MarkerStyleEnum.
        """
        choice = list( MarkerStyleEnum )[ value ]
        self.markerStyle = choice.optionValue
        self.Modified()

    @smproperty.doublevector( name="MarkerSize", default_values=1.0 )
    @smdomain.xml( """<DoubleRangeDomain min="0.1" max="30.0" name="range"/>""" )
    def f07SetMarkerSize( self: Self, value: float ) -> None:
        """Set marker size.

        Args:
           value (float): Size of markers between 1 and 30.
        """
        self.markerSize = value
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
        self.color = ( value0, value1, value2 )
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
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        inInfo = inInfoVec[ 0 ]

        # Only at initialization step, no change later
        if self.requestDataStep < 0:
            # Get cell ids
            inData = self.GetInputData( inInfoVec, 0, 0 )
            self.cellIds = pvt.getVtkOriginalCellIds( inData, self.logger )

            # Update vtkDAS
            for circleId in self.cellIds:
                if not self.cellIdsDAS.ArrayExists( circleId ):
                    self.cellIdsDAS.AddArray( circleId )

            # Get the possible timesteps of execution
            self.timeSteps: float = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS() )  # type: ignore

            for timestep in self.timeSteps:
                if not self.timeStepsDAS.ArrayExists( str( timestep ) ):
                    self.timeStepsDAS.AddArray( str( timestep ) )
        return 1

    def RequestUpdateExtent(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestUpdateExtent.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]

        # Update requestDataStep
        self.requestDataStep += 1
        # Update time according to requestDataStep iterator
        if self.requestDataStep == 0:
            self._updateRequestedTimeSteps()

        if self.requestDataStep < len( self.timeSteps ):
            inInfo.GetInformationObject( 0 ).Set(
                executive.UPDATE_TIME_STEP(),  # type: ignore[no-any-return]
                self.timeSteps[ self.requestDataStep ],
            )
            outInfoVec.GetInformationObject( 0 ).Set(
                executive.UPDATE_TIME_STEP(),  # type: ignore[no-any-return]
                self.timeSteps[ self.requestDataStep ],
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
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

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
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        try:
            inputMesh: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
            executive = self.GetExecutive()

            if self.requestDataStep == 1:
                self.logger.info( "Computing Mohr circles for requested time steps and cell Ids." )

            if self.requestDataStep < len( self.timeSteps ):
                request.Set( executive.CONTINUE_EXECUTING(), 1 )  # type: ignore[no-any-return]
                currentTimeStep: float = (
                    inInfoVec[ 0 ].GetInformationObject( 0 ).Get(
                        executive.UPDATE_TIME_STEP() )  # type: ignore[no-any-return]
                )

                if self.requestDataStep in self.requestedTimeStepsIndexes:
                    self.mohrCircles.update( self._createMohrCirclesAtTimeStep( inputMesh, currentTimeStep ) )

            # Plot mohr circles
            else:
                self.logger.info( "Displaying Mohr's Circles" )
                # Displayed time step, no need to go further
                request.Remove( executive.CONTINUE_EXECUTING() )  # type: ignore[no-any-return]

                assert self.pythonView is not None, "No Python View was found."
                self._defineCurvesAspect()
                mohrCircles: list[ MohrCircle ] = self._filterMohrCircles()

                self.pythonView.Script = mcf.buildPythonViewScript(
                    geos_pv_path,
                    mohrCircles,
                    self.rockCohesion,
                    self.frictionAngle,
                    self._getUserChoices(),
                )
                Render()

        except Exception as e:
            self.logger.error( "Mohr circles cannot be plotted due to:" )
            self.logger.error( e )
            return 0
        return 1

    def _createMohrCirclesAtTimeStep(
        self: Self,
        mesh: vtkUnstructuredGrid,
        currentTimeStep: float,
    ) -> set[ MohrCircle ]:
        """Create mohr circles of all cells at the current time step.

        Args:
            mesh (Union[vtkUnstructuredGrid, vtkMultiBlockDataSet]): input mesh.
            currentTimeStep (float): current time step

        Returns:
            list[MohrCircle]: list of MohrCircles for the current time step.
        """
        # Get effective stress array
        stressArray: npt.NDArray[ np.float64 ] = getArrayInObject( mesh,
                                                                   GeosMeshOutputsEnum.STRESS_EFFECTIVE.attributeName,
                                                                   False )
        # Get stress convention
        stressConvention = StressConventionEnum.GEOS_STRESS_CONVENTION if self.useGeosStressConvention else StressConventionEnum.COMMON_STRESS_CONVENTION

        # Get the cell IDs requested by the user
        self._updateRequestedCellIds()

        return mcf.createMohrCircleAtTimeStep( stressArray, self.requestedCellIds, str( currentTimeStep ),
                                               stressConvention )

    def _filterMohrCircles( self: Self ) -> list[ MohrCircle ]:
        """Filter the list of all MohrCircle to get those to plot.

        Returns:
            list[MohrCircle]: list of MohrCircle to plot.
        """
        # Circle ids to plot
        circleIds: list[ str ] = self._getCircleIds()
        return [ mohrCircle for mohrCircle in self.mohrCircles if mohrCircle.getCircleId() in circleIds ]

    def _updateRequestedTimeSteps( self: Self ) -> None:
        """Update the requestedTimeStepsIndexes attribute from user choice."""
        requestedTimeSteps: list[ str ] = pvt.getArrayChoices( self.a02GetTimestepsToPlot() )

        self.requestedTimeStepsIndexes = [
            pvt.getTimeStepIndex( float( ts ), self.timeSteps ) for ts in requestedTimeSteps
        ]

    def _updateRequestedCellIds( self: Self ) -> None:
        """Update the requestedCellIds attribute from user choice."""
        self.requestedCellIds = pvt.getArrayChoices( self.a01GetCellIdsDAS() )

    def _getUserChoices( self: Self ) -> dict[ str, Any ]:
        """Access the userChoices attribute.

        Returns:
            dict[str, Any] : the user choices for the figure.
        """
        return self.userChoices

    def _getCircleIds( self: Self ) -> list[ str ]:
        """Get circle ids to plot.

        Returns:
            list[str]: list of circle ids to plot.
        """
        cellIds: list[ str ] = pvt.getArrayChoices( self.a01GetCellIdsDAS() )
        timeSteps: list[ str ] = pvt.getArrayChoices( self.a02GetTimestepsToPlot() )

        return [ mcf.getMohrCircleId( cellId, timeStep ) for timeStep in timeSteps for cellId in cellIds ]

    def _defineCurvesAspect( self: Self ) -> None:
        """Add curve aspect parameters according to user choices."""
        self.userChoices[ "curvesAspect" ][ self.circleIdUsed ] = {
            "color": self.color,
            "linestyle": self.lineStyle,
            "linewidth": self.lineWidth,
            "marker": self.markerStyle,
            "markersize": self.markerSize,
        }
