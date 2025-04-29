# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smproperty, smproxy, smhint,
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkUnstructuredGrid,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

__doc__ = """
Example of a Paraview plugin that defines various static input widgets.

Static inputs do not depend on input data object or context but are entirely defined by the decorators.
See `Plugin HowTo page <https://www.paraview.org/paraview-docs/latest/cxx/PluginHowto.html>`_
and `property hints documentation <https://www.paraview.org/paraview-docs/latest/cxx/PropertyHints.html>`_
"""


@smproxy.filter( name="PVproxyWidgetsStatic", label="Static Widget Examples" )
@smhint.xml( """<ShowInMenu category="Filter Examples"/>""" )
@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVproxyWidgetsStatic( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        self._strSingle: str = ""
        self._strMultiline: str = ""
        self._inputFilePath: str = ""
        self._outputFilePath: str = ""
        self._directoryPath: str = ""
        self._intSingle: float = 0
        self._intMulti: list[ float ] = [ 0, 0, 0 ]
        self._boolSingle: bool = False
        self._doubleSingle: float = 0.0
        self._doubleMulti: list[ float ] = [ 0.0, 0.0, 0.0 ]
        self._singleSliderValue: float = 0.0
        self._singleIntSliderValue: int = 0
        self._doubleSlider: list[ float ] = [ 0.0, 0.0 ]
        self._color: list[ float ] = [ 0.0, 0.0, 0.0 ]
        self._table: list[ tuple[ int, float, str ] ] = []
        self._clearTable: bool = True
        self._dropDownListSelection: int = 0

    @smproperty.xml( """
        <Property name="Action Button"
                  command="a00ActionButton"
                  panel_widget="command_button"/>
        """ )
    def a00ActionButton( self: Self ) -> None:
        """Action button example."""
        print( "Executes action" )
        self.Modified()

    @smproperty.stringvector(
        name="StringSingle",
        label="String Single",
        number_of_elements="1",
        default_values="-",
        panel_visibility="default",
    )
    def a01StringSingle( self: Self, value: str ) -> None:
        """Define an input string field.

        Args:
            value (str): input
        """
        if value != self._strSingle:
            self._strSingle = value
            self.Modified()


#     <StringVectorProperty command="SetFunction"
#                             name="Function"
#                             number_of_elements="1"
#                             panel_widget="calculator" >
#         <Documentation>
# This property contains the equation for computing the new
# array.
#         </Documentation>
#       </StringVectorProperty>

# use syntax=<language> to highlight text with language color

    @smproperty.stringvector(
        name="StringMultiline",
        label="MultiLine String",
        number_of_elements="1",
        default_values="-",
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Hints>
            <Widget type="multi_line" syntax="python"/>
        </Hints>
    """ )
    def a02StringMultiLine( self: Self, value: str ) -> None:
        """Define an input string field.

        Args:
            value (str): input
        """
        if value != self._strMultiline:
            self._strMultiline = value
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="String Inputs"
                            panel_visibility="default">
                            <Property name="StringSingle"/>
                            <Property name="StringMultiline"/>
                        </PropertyGroup>""" )
    def a03StringInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.stringvector(
        name="InputFilePath",
        label="Input File Path",
        number_of_elements="1",
        default_values="Select Input .txt file...",
        panel_visibility="default",
    )
    @smdomain.filelist()
    @smhint.filechooser( extensions=[ "txt" ], file_description="Input text file." )
    def b01InputFilePath( self: Self, value: str ) -> None:
        """Define an input file path.

        Args:
            value (str): input
        """
        if value != self._inputFilePath:
            self._inputFilePath = value
            self.Modified()

    # @smdomain.filelist() and @smhint.filechooser may be replaced by this @smdomain.xml
    # @smdomain.xml("""
    #                 <FileListDomain name="files" />
    #                 <Hints>
    #                     <FileChooser extensions="txt" file_description="Output text file." />
    #                     <AcceptAnyFile/>
    #                 </Hints>
    #               """)
    @smproperty.stringvector(
        name="OutputFilePath",
        label="Output File Path",
        number_of_elements="1",
        default_values="Select output file...",
        panel_visibility="default",
    )
    @smdomain.filelist()
    @smhint.filechooser( extensions=[ "txt" ], file_description="Output text file." )
    @smdomain.xml( """
                    <Hints>
                        <AcceptAnyFile/>
                    </Hints>
                  """ )
    def b02OutputFilePath( self: Self, value: str ) -> None:
        """Define an input file path.

        Args:
            value (str): input
        """
        if value != self._outputFilePath:
            self._outputFilePath = value
            self.Modified()

    # @smdomain.filelist() and @smhint.filechooser may be replaced by this @smdomain.xml
    # @smdomain.xml("""
    #                 <FileListDomain name="files" />
    #                 <Hints>
    #                     <FileChooser extensions="" file_description="Output directory." />
    #                     <UseDirectoryName/>
    #                 </Hints>

    @smproperty.stringvector(
        name="DirectoryPath",
        label="Directory Path",
        number_of_elements="1",
        default_values="Select a directory...",
        panel_visibility="default",
    )
    @smdomain.filelist()
    @smhint.filechooser( extensions="", file_description="Output directory." )
    @smdomain.xml( """
                    <Hints>
                        <UseDirectoryName/>
                    </Hints>
                  """ )
    def b03DirectoryPath( self: Self, value: str ) -> None:
        """Define an input string field.

        Args:
            value (str): input
        """
        if value != self._directoryPath:
            self._directoryPath = value
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="File/Directory Inputs"
                            panel_visibility="default">
                            <Property name="InputFilePath"/>
                            <Property name="OutputFilePath"/>
                            <Property name="DirectoryPath"/>
                        </PropertyGroup>""" )
    def b04FileInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.intvector(
        name="IntSingle",
        label="Int Single",
        number_of_elements="1",
        default_values=0,
        panel_visibility="default",
    )
    def c01IntSingle( self: Self, value: int ) -> None:
        """Define an input int field.

        Args:
            value (int): input
        """
        if value != self._intSingle:
            self._intSingle = value
            self.Modified()

    @smproperty.intvector(
        name="IntMulti",
        label="Int Multi",
        number_of_elements="3",
        default_values=( 0, 0, 0 ),
        panel_visibility="default",
    )
    def c02IntMulti( self: Self, value0: int, value1: int, value2: int ) -> None:
        """Define an input int field.

        Args:
            value0 (int): input 0
            value1 (int): input 1
            value2 (int): input 2
        """
        if value0 != self._intMulti[ 0 ]:
            self._intMulti[ 0 ] = value0
            self.Modified()
        if value1 != self._intMulti[ 1 ]:
            self._intMulti[ 1 ] = value1
            self.Modified()
        if value2 != self._intMulti[ 2 ]:
            self._intMulti[ 2 ] = value2
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="Int Inputs"
                            panel_visibility="default">
                            <Property name="IntSingle"/>
                            <Property name="IntMulti"/>
                        </PropertyGroup>""" )
    def c03IntInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.intvector(
        name="BoolSingle",
        label="Single Boolean Input",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """<BooleanDomain name="BoolSingle"/>""" )
    def c04BoolSingle( self: Self, value: bool ) -> None:
        """Define boolean input.

        Args:
            value (bool): input bool.
        """
        self._boolSingle = value
        self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="Boolean Inputs"
                            panel_visibility="default">
                            <Property name="BoolSingle"/>
                        </PropertyGroup>""" )
    def c03BoolInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.doublevector(
        name="DoubleSingle",
        label="Double Single",
        number_of_elements="1",
        default_values=0.0,
        panel_visibility="default",
    )
    def d01DoubleSingle( self: Self, value: float ) -> None:
        """Define an input double field.

        Args:
            value (float): input
        """
        if value != self._doubleSingle:
            self._doubleSingle = value
            self.Modified()

    @smproperty.doublevector(
        name="DoubleMulti",
        label="Double Multi",
        number_of_elements="3",
        default_values=( 0.0, 0.0, 0.0 ),
        panel_visibility="default",
    )
    def d02DoubleMulti( self: Self, value0: float, value1: float, value2: float ) -> None:
        """Define an input double field.

        Args:
            value0 (float): input 0
            value1 (float): input 1
            value2 (float): input 2
        """
        if value0 != self._doubleMulti[ 0 ]:
            self._doubleMulti[ 0 ] = value0
            self.Modified()
        if value1 != self._doubleMulti[ 1 ]:
            self._doubleMulti[ 1 ] = value1
            self.Modified()
        if value2 != self._doubleMulti[ 2 ]:
            self._doubleMulti[ 2 ] = value2
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="Double Inputs"
                            panel_visibility="default">
                            <Property name="DoubleSingle"/>
                            <Property name="DoubleMulti"/>
                        </PropertyGroup>""" )
    def d03DoubleInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.intvector( name="SingleIntSlider",
                           label="Single Int Slider",
                           number_of_elements=1,
                           default_values=0.0,
                           panel_visibility="default",
                           panel_widget="range" )
    @smdomain.xml( """
                <IntRangeDomain name="range" min="0" max="20" />
                """ )
    def d04SingleIntSlider( self: Self, value: int ) -> None:
        """Define a slider.

        Args:
            value (float): input value
        """
        if value != self._singleIntSliderValue:
            self._singleIntSliderValue = value
            self.Modified()

    @smproperty.xml( """
                <DoubleVectorProperty
                    name="SingleFloatSlider"
                    command="d05SingleFloatSlider"
                    number_of_elements="1"
                    default_values="0.1">
                    <DoubleRangeDomain name="range" min="0.0" max="1.0" />
                </DoubleVectorProperty>
                """ )
    def d05SingleFloatSlider( self: Self, value: float ) -> None:
        """Define a slider.

        Args:
            value (float): input value
        """
        if value != self._singleSliderValue:
            self._singleSliderValue = value
            self.Modified()

    # add or remove <HideResetButton/> inside Hints tag
    @smproperty.xml( """
                    <DoubleVectorProperty
                        name="DoubleSlider"
                        command="d06DoubleSlider"
                        number_of_elements="2"
                        default_values="0.0 1.0"
                        panel_visibility="default"
                        panel_widget="double_range">
                        <DoubleRangeDomain
                            max="1.0"
                            min="0.0"
                            name="range" />
                        <Hints>
                            <MinimumLabel text="Minimum Limit"/>
                            <MaximumLabel text="Maximum Limit" />
                        </Hints>
                    </DoubleVectorProperty>
                    """ )
    def d06DoubleSlider( self: Self, mini: float, maxi: float ) -> None:
        """Define a double slider.

        Args:
            mini (float): minimum
            maxi (float): maximum
        """
        if mini != self._doubleSlider[ 0 ]:
            self._doubleSlider[ 0 ] = mini
            self.Modified()
        if maxi != self._doubleSlider[ 1 ]:
            self._doubleSlider[ 1 ] = maxi
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            label="Sliders"
                            panel_visibility="default">
                            <Property name="SingleIntSlider"/>
                            <Property name="SingleFloatSlider"/>
                            <Property name="DoubleSlider"/>
                        </PropertyGroup>""" )
    def d07SliderInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.doublevector( name="Color",
                              label="Color",
                              number_of_elements="3",
                              default_values=( 0.0, 0.0, 0.0 ),
                              panel_visibility="default",
                              panel_widget="color_selector_with_palette" )
    @smdomain.xml( """
                    <Hints>
                        <PropertyLink group="settings" proxy="ColorPalette" property="BackgroundColor" unlink_if_modified="1" />
                    </Hints>
                    """ )
    def d07Color( self: Self, value0: float, value1: float, value2: float ) -> None:
        """Define an input double field.

        Args:
            value0 (float): input 0
            value1 (float): input 1
            value2 (float): input 2
        """
        if value0 != self._color[ 0 ]:
            self._color[ 0 ] = value0
            self.Modified()
        if value1 != self._color[ 1 ]:
            self._color[ 1 ] = value1
            self.Modified()
        if value2 != self._color[ 2 ]:
            self._color[ 2 ] = value2
            self.Modified()

    @smproperty.xml( """<PropertyGroup
                            panel_visibility="default">
                            <Property name="Color"/>
                        </PropertyGroup>""" )
    def d08ColorInputsGroup( self: Self ) -> None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.intvector(
        name="DropDownList",
        label="Drop Down List",
        number_of_elements=1,
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <EnumerationDomain name="enum">
                        <Entry value="6" text="Choice1"/>
                        <Entry value="7" text="Choice2"/>
                        <Entry value="12" text="Choice3"/>
                    </EnumerationDomain>
                    """ )
    def e01DropDownList( self: Self, intValue: int ) -> None:
        """Set selection from predefined drop down list.

        Args:
            intValue (int): int value.
        """
        if intValue != self._dropDownListSelection:
            self._dropDownListSelection = intValue
            self.Modified()

    @smproperty.xml( """
        <DoubleVectorProperty
            name="VariableTableMultiType"
            command="f01VariableTableMultiType"
            repeat_command="1"
            number_of_elements_per_command="3"
            default_values="0 1 -"
            element_types="0 1 2">
            <Hints>
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Int value"/>
                    <ComponentLabel component="1" label="Double Value"/>
                    <ComponentLabel component="2" label="String Value"/>
                </ShowComponentLabels>
            </Hints>
        </DoubleVectorProperty>
        """ )
    def f01VariableTableMultiType( self: Self, intValue: int, floatValue: float, strValue: str ) -> None:
        """Set multi type table with undefined size.

        Args:
            intValue (int): int value.
            floatValue (float): float value.
            strValue (str): string value.
        """
        # clear the table the first time the method is called
        if self._clearTable:
            self._table.clear()
        self._clearTable = False
        self._table.append( ( int( intValue ), float( floatValue ), str( strValue ) ) )
        self.Modified()

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
        inData1 = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        if outData is None or ( not outData.IsA( inData1.GetClassName() ) ):
            outData = inData1.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
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
        input: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outData: vtkPointSet = self.GetOutputData( outInfoVec, 0 )

        assert input is not None, "input 0 server mesh is null."
        assert outData is not None, "Output pipeline is null."

        # do something...
        print( f"Single String {self._strSingle}" )
        print( f"Multiline String {self._strMultiline}" )
        print( f"Input file path {self._inputFilePath}" )
        print( f"Output file path {self._outputFilePath}" )
        print( f"Directory path {self._directoryPath}" )
        print( f"Single int {self._intSingle}" )
        print( f"Multiple int {self._intMulti}" )
        print( f"Boolean {self._boolSingle}" )
        print( f"Single double {self._doubleSingle}" )
        print( f"Multiple double {self._doubleMulti}" )
        print( f"Single Slider {self._singleIntSliderValue}" )
        print( f"Single Slider {self._singleSliderValue}" )
        print( f"Double Slider {self._doubleSlider}" )
        print( f"Color {self._color}" )
        print( f"Variable table {self._table}" )

        # set self._clearTable to True for the next time the table is updated
        self._clearTable = True
        return 1
