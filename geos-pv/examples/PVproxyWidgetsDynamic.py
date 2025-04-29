# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from enum import Enum
from pathlib import Path
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.pv.utils.paraviewTreatments import (
    strListToEnumerationDomainXml,
    strEnumToEnumerationDomainXml,
    getArrayChoices
)
from geos_posp.visu.PVUtils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )

from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    smdomain, smproperty, smproxy, smhint,
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkDataArraySelection,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkUnstructuredGrid,
)

__doc__ = """
Example of a Paraview plugin that defines various dynamic input widgets.

Dynamic inputs vary according to input data object or context.
See `Plugin HowTo page <https://www.paraview.org/paraview-docs/latest/cxx/PluginHowto.html>`_
and `property hints documentation <https://www.paraview.org/paraview-docs/latest/cxx/PropertyHints.html>`_

<InputArrayDomain/> tag from filter @smdomain.xml allows to filter arrays: attribute_type keyword filters array
if they are supported by point, cell, or field; number_of_components keyword filters on the number of components.

<BoundsDomain/> tag required 2 arguments:
* mode options are defined by `vtkSMBoundsDomain::Modes enum <https://gitlab.kitware.com/paraview/paraview/-/blob/master/Remoting/ServerManager/vtkSMBoundsDomain.h>`_
  (may have a way to select which axis, but not found)
* scale_factor: factor by which extent is multiplied for display.

"""

# TODO: try this https://discourse.paraview.org/t/difficulties-to-use-propertygroup-in-python-plugin-of-a-filter/12070

DROP_DOWN_LIST_ELEMENTS: tuple[str, str, str] = ("Choice1", "Choice2", "Choice3")
class DROP_DOWN_LIST_ENUM(Enum):
    CHOICE1 = "Enum1"
    CHOICE2 = "Enum2"
    CHOICE3 = "Enum3"


@smproxy.filter( name="PVproxyWidgetsDynamic", label="Dynamic Widget Examples" )
@smhint.xml("""<ShowInMenu category="Filter Examples"/>""")

@smproperty.input( name="Input", port_index=0, label="Input" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
@smdomain.xml("""
              <InputArrayDomain name="points_array" attribute_type="point" />
              <InputArrayDomain name="cells_array" attribute_type="cell" />
              <InputArrayDomain name="fields_array" attribute_type="field" />
              <InputArrayDomain name="cells_scalar_array" attribute_type="cell" number_of_components="1" />
              <InputArrayDomain name="cells_vector_array" attribute_type="cell" number_of_components="3" />
              """
)
class PVproxyWidgetsDynamic( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        self._strSingle: str = ""
        self._intSingle: str = 0
        self._doubleSingle: str = 0.0

        self._dropDownListSelection: int = 0
        self._dropDownListSelection2: int = 0

        self._selectedAttributeSingle: str = ""
        self._clearSelectedAttributeMulti: bool = True
        self._selectedAttributeMulti: list[str] = []

        # used to init data
        self._initArraySelections: bool = True
        self._selectedTimes: vtkDataArraySelection = vtkDataArraySelection()
        self._selectedTimes.AddObserver( 0, createModifiedCallback( self ) )

        self._extentSlider: list[float] = [0.0, 1.0]

        self._selectedAttributeSingleType: str= ""
        self._componentIndex: int = 0

        self.clearBlockNames: bool = True
        self._blockNames: list[str] = []

    @smproperty.intvector(
        name="BoolSingle",
        label="Show/Hide More Widgets",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """<BooleanDomain name="BoolSingle"/>""" )
    def a00BoolSingle( self: Self, value: bool ) -> None:
        """Define boolean input.

        Args:
            value (bool): input bool.
        """
        # no necessarily need to store the checkbox state
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

    @smproperty.intvector(
        name="IntSingle",
        label="Int Single",
        number_of_elements="1",
        default_values=0,
        panel_visibility="default",
    )
    def a02IntSingle( self: Self, value: int ) -> None:
        """Define an input int field.

        Args:
            value (int): input
        """
        if value != self._intSingle:
            self._intSingle = value
            self.Modified()

    @smproperty.doublevector(
        name="DoubleSingle",
        label="Double Single",
        number_of_elements="1",
        default_values=0.0,
        panel_visibility="default",
    )
    def a03DoubleSingle( self: Self, value: float ) -> None:
        """Define an input double field.

        Args:
            value (float): input
        """
        if value != self._doubleSingle:
            self._doubleSingle = value
            self.Modified()

    @smproperty.xml( """<PropertyGroup label="Show/Hide Widgets" panel_visibility="advanced">
                        <Property name="StringSingle"/>
                        <Property name="IntSingle"/>
                        <Property name="DoubleSingle"/>
                    <Hints><PropertyWidgetDecorator type="GenericDecorator"
                    mode="visibility" property="BoolSingle"
                    value="1"/></Hints>
                    </PropertyGroup>""" )
    def a04ShowHideGroup(self: Self) ->None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.intvector(
        name="DropDownListFromVariable",
        number_of_elements=1,
        label="Dropdown List From Variable",
        default_values=0,
    )
    @smdomain.xml( strListToEnumerationDomainXml( DROP_DOWN_LIST_ELEMENTS ) )
    def b01DropDownListFromVariable(self: Self, intValue: int) -> None:
        """Set selection from drop down list filled with variable elements.

        Args:
            intValue (int): int value.
        """
        if intValue != self._dropDownListSelection:
            self._dropDownListSelection = intValue
        self.Modified()

    @smproperty.intvector(
        name="DropDownListFromEnum",
        number_of_elements=1,
        label="Dropdown List From Enum",
        default_values=0,
    )
    @smdomain.xml( strEnumToEnumerationDomainXml( DROP_DOWN_LIST_ENUM ) )
    def b02DropDownListFromEnum(self: Self, intValue: int) -> None:
        """Set selection from drop down list filled with enumeration elements.

        Args:
            intValue (int): int value.
        """
        if intValue != self._dropDownListSelection2:
            self._dropDownListSelection2 = intValue
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Dropdown List Inputs" panel_visibility="default">
                        <Property name="DropDownListFromVariable"/>
                        <Property name="DropDownListFromEnum"/>
                    </PropertyGroup>""" )
    def b03DropDownListGroup(self: Self) ->None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.stringvector(
        name="SelectSingleAttribute",
        label="Select Single Attribute",
        number_of_elements="1",
        element_types="2",
        default_values="",
        panel_visibility="default",
    )
    @smdomain.xml("""
                <ArrayListDomain
                    name="array_list"
                    attribute_type="Scalars"
                    input_domain_name="cells_array">
                    <RequiredProperties>
                        <Property name="Input" function="Input"/>
                    </RequiredProperties>
                </ArrayListDomain>
                <Documentation>
                    Select a unique attribute from all the scalars cell attributes from input object.
                    Input object is defined by its name Input that must corresponds to the name in @smproperty.input
                    Attribute support is defined by input_domain_name: inputs_array (all arrays) or user defined
                    function from <InputArrayDomain/> tag from filter @smdomain.xml.
                    Attribute type is defined by keyword `attribute_type`: Scalars or Vectors
                </Documentation>
                  """)
    def a01SelectSingleAttribute( self: Self, name: str ) -> None:
        """Set selected attribute name.

        Args:
            name (str): input value
        """
        if name != self._selectedAttributeSingle:
            self._selectedAttributeSingle = name
            self.Modified()

    @smproperty.stringvector(
        name="SelectMultipleAttribute",
        label="Select Multiple Attribute",
        repeat_command = 1,
        number_of_elements_per_command="1",
        element_types="2",
        default_values="",
        panel_visibility="default",
    )
    @smdomain.xml("""
                <ArrayListDomain
                    name="array_list"
                    attribute_type="Vectors"
                    input_domain_name="cells_vector_array">
                    <RequiredProperties>
                        <Property name="Input" function="Input"/>
                    </RequiredProperties>
                </ArrayListDomain>
                <Documentation>
                    Select a unique attribute from all the scalars cell attributes from input object.
                    Input object is defined by its name Input that must corresponds to the name in @smproperty.input
                    Attribute support is defined by input_domain_name: inputs_array (all arrays) or user defined
                    function from <InputArrayDomain/> tag from filter @smdomain.xml.
                    Attribute type is defined by keyword `attribute_type`: Scalars or Vectors
                </Documentation>
                  """)
    def a02SelectMultipleAttribute( self: Self, name: str ) -> None:
        """Set selected attribute name.

        Args:
            name (str): input value
        """
        if self._clearSelectedAttributeMulti:
            self._selectedAttributeMulti.clear()
        self._clearSelectedAttributeMulti = False
        self._selectedAttributeMulti.append(name)
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Attribute selection" panel_visibility="default">
                        <Property name="SelectSingleAttribute"/>
                        <Property name="SelectMultipleAttribute"/>
                    </PropertyGroup>""" )
    def a05AttributeSelectionGroup(self: Self) ->None:
        """Create a group of widgets."""
        self.Modified()

    @smproperty.xml( """
        <Property name="Refresh Array Data"
                  command="d01ActionButton"
                  panel_widget="command_button"/>
        """ )
    def d01ActionButton( self: Self ) -> None:
        """Action button to reset self._initArraySelections."""
        self._initArraySelections = True
        self.Modified()

    @smproperty.dataarrayselection( name="TimeSelection" )
    def d02GetSelectedTimes( self: Self ) -> vtkDataArraySelection:
        """Get selected times.

        Returns:
            vtkDataArraySelection: selected attribute names.
        """
        return self._selectedTimes

    @smproperty.doublevector(
            name="ExtentSlider",
            label="Extent Slider",
            number_of_elements=2,
            default_values=(0.0, 0.0),
            panel_visibility="default",
            panel_widget="double_range"
    )
    @smdomain.xml( """
                    <BoundsDomain mode="normal" name="bounds" scale_factor="1">
                        <RequiredProperties>
                            <Property function="Input" name="Input" />
                        </RequiredProperties>
                    </BoundsDomain>
                    <Hints>
                        <MinimumLabel text="Minimum Limit"/>
                        <MaximumLabel text="Maximum Limit" />
                    </Hints>
                    """)
    def d05ExtentSlider( self: Self, mini: float, maxi: float) -> None:
        """Define a double slider.

        Args:
            mini (float): minimum
            maxi (float): maximum
        """
        if mini != self._extentSlider[0]:
            self._extentSlider[0] = mini
            self.Modified()
        if maxi != self._extentSlider[1]:
            self._extentSlider[1] = maxi
            self.Modified()

    # use mode="leaves" to display only leaves, or discard it to display the whole tree
    @smproperty.intvector(name="CompositeDataSetIndex",
                          default_values=1,
                          number_of_elements=1,
                          number_of_elements_per_command=1,
                          panel_visibility="default",
                          repeat_command=1
    )
    @smdomain.xml("""<CompositeTreeDomain mode="leaves" name="tree">
                        <RequiredProperties>
                            <Property function="Input" name="Input" />
                        </RequiredProperties>
                    </CompositeTreeDomain>
                    <Hints>
                        <!-- we don't want to show this property, except for MBs. -->
                        <PropertyWidgetDecorator type="InputDataTypeDecorator"
                            mode="visibility" name="vtkMultiBlockDataSet" />
                    </Hints>""")
    def e00SetBlockNames( self: Self, value: str) -> None:
        """Define component selector.

        Args:
            value (int): component index
        """
        if self.clearBlockNames:
            self._blockNames.clear()
        self.clearBlockNames = False
        self._blockNames.append(value)
        self.Modified()

    @smproperty.intvector(name="AttributeType",
                          default_values=0,
                          number_of_elements=1
    )
    @smdomain.xml("""<FieldDataDomain enable_field_data="1" name="enum">
                        <RequiredProperties>
                            <Property function="Input" name="Input" />
                        </RequiredProperties>
                    </FieldDataDomain>""")
    def e01SetFieldAssociation(self: Self, value: int) ->None:
        """Set attribute support for next attribute selector.

        Args:
            value  (int): input value
        """
        self.Modified()


    @smproperty.xml("""
        <StringVectorProperty command="e02SelectSingleAttributeWithType"
                            element_types="0 0 0 0 2"
                            name="SelectSingleAttributeWithTypeFilter"
                            label="Select Single Attribute With Type Filter"
                            number_of_elements="5">
        <ArrayListDomain name="array_list">
            <RequiredProperties>
                <Property function="Input" name="Input" />
                <Property function="FieldDataSelection" name="AttributeType" />
                <Property function="CompositeIndexSelection" name="CompositeDataSetIndex" />
            </RequiredProperties>
        </ArrayListDomain>
        <Documentation>
            This property indicates the name of the array to be extracted.
        </Documentation>
        </StringVectorProperty>
    """)
    def e02SelectSingleAttributeWithType(self: Self, v1: int, v2: int, v3: int, support: int, name :str) ->None:
        """Set selected attribute name.

        Args:
            v1 (int): input value 1
            v2 (int): input value 2
            v3 (int): input value 3
            support (int): attribute support (point 0, cell 1, field 2)
            name (str): input value
        """
        if name != self._selectedAttributeSingleType:
            self._selectedAttributeSingleType = name
            self.Modified()

    @smproperty.xml(""" <IntVectorProperty
                            name="SetInputArrayComponent"
                            label="Select Component"
                            animateable="0"
                            command="e04SetInputArrayComponent"
                            default_values="0"
                            number_of_elements="1">
                            <NumberOfComponentsDomain name="comps">
                                <RequiredProperties>
                                    <Property function="Input" name="Input" />
                                    <Property function="ArraySelection" name="SelectSingleAttributeWithTypeFilter" />
                                </RequiredProperties>
                            </NumberOfComponentsDomain>
                            <Documentation>
                            This property indicates the component of the array to be extracted.
                            </Documentation>
                        </IntVectorProperty>
                    """)
    def e04SetInputArrayComponent( self: Self, value: int) -> None:
        """Define component selector.

        Args:
            value (int): component index
        """
        if value != self._componentIndex:
            self._componentIndex = value
            self.Modified()

    @smproperty.xml( """<PropertyGroup label="Interdependant Widgets" panel_visibility="default">
                        <Property name="CompositeDataSetIndex"/>
                        <Property name="AttributeType"/>
                        <Property name="SelectSingleAttributeWithTypeFilter"/>
                        <Property name="SetInputArrayComponent"/>
                    </PropertyGroup>""" )
    def e05SelectorGroup(self: Self) ->None:
        """Create a group of widgets."""
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
        # init arrays only if self._initArraySelections is True
        # self._initArraySelections is True only when filter is selected
        # or after hitting `Reset Arrays button`
        if self._initArraySelections:
            executive = self.GetExecutive()  # noqa: F841
            inInfo = inInfoVec[ 0 ]
            self.m_timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS() )  # type: ignore
            for timestep in self.m_timeSteps:
                if not self._selectedTimes.ArrayExists( str( timestep ) ):
                    self._selectedTimes.AddArray( str( timestep ) )
        self._initArraySelections = False
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
        inData1 = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None, "Input object is undefined"
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
        print(f"Single String {self._strSingle}")
        print(f"Single int {self._intSingle}")
        print(f"Single double {self._doubleSingle}")
        print(f"Single Attribute selection {self._selectedAttributeSingle}")
        print(f"Single Attribute selection with type {self._selectedAttributeSingleType}")
        print(f"Multiple Attribute selection {self._selectedAttributeMulti}")

        selectedTimes = getArrayChoices( self.d02GetSelectedTimes() )
        print(f"Selected times: {selectedTimes}")

        print(f"Bounds slider: {self._extentSlider}")
        print(f"Attribute {self._selectedAttributeSingleType} component: {self._componentIndex}")
        print(f"Selected Block names: {self._blockNames}")
        self._clearSelectedAttributeMulti = True
        self.clearBlockNames = True
        return 1
