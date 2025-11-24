# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import numpy as np
from pathlib import Path

from typing import Any
from typing_extensions import Self

from paraview.util.vtkAlgorithm import VTKPythonAlgorithmBase, smdomain, smproperty  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonDataModel import vtkDataSet

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )

from geos.processing.generic_processing_tools.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion
from geos.pv.utils.details import ( SISOFilter, FilterCategory )

__doc__ = """
PVCreateConstantAttributePerRegion is a Paraview plugin that allows to create an attribute
with constant values per components for each chosen indexes of a reference/region attribute.
If other region indexes exist, values are set to nan for float type, -1 for int type or 0 for uint type.

Input mesh is either vtkMultiBlockDataSet or vtkDataSet and the region attribute must have one component.
The relation index/values is given by a dictionary. Its keys are the indexes and its items are the list of values for each component.

.. Warning::
    The input mesh should contain an attribute corresponding to the regions.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVCreateConstantAttributePerRegion.
* Select the mesh in which you want to create the attributes.
* Select the filter Create Constant Attribute Per Region in filter|0- Geos Pre-processing.
* Choose the region attribute, the relation index/values, the new attribute name, the type of the value, the number of components and their names.
* Apply.

"""


@SISOFilter( category=FilterCategory.GEOS_PROP,
             decoratedLabel="Create Constant Attribute Per Region",
             decoratedType=[ "vtkMultiBlockDataSet", "vtkDataSet" ] )
class PVCreateConstantAttributePerRegion( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Create an attribute with constant value per region."""
        self.clearDictRegionValues: bool = True

        # Region attribute settings.
        self.regionName: str = ""
        self.dictRegionValues: dict[ Any, Any ] = {}

        # New attribute settings.
        self.newAttributeName: str = "newAttribute"
        self.valueNpType: type = np.float32
        self.nbComponents: int = 1
        self.componentNames: tuple[ str, ...] = ()

        # Use the handler of paraview for the log.
        self.speHandler: bool = True

    # Settings of the attribute with the region indexes:
    @smproperty.stringvector(
        name="ChooseRegionAttribute",
        label="Attribute with region indexes",
        default_values="Choose an attribute",
        number_of_elements="1",
        element_types="2",
    )
    @smdomain.xml( """
        <ArrayListDomain
            name="array_list"
            attribute_type="Scalars"
            input_domain_name="inputs_array">
            <RequiredProperties>
                <Property name="Input" function="Input"/>
            </RequiredProperties>
        </ArrayListDomain>
        <Documentation>
            Select the attribute to consider for regions indexes.
        </Documentation>
        <Hints>
            <NoDefault />
        </Hints>
    """ )
    def setRegionAttributeName( self: Self, regionName: str ) -> None:
        """Set region attribute name.

        Args:
            regionName (str): The name of the attribute to consider as the region attribute.
        """
        self.regionName = regionName
        self.Modified()

    @smproperty.xml( """
        <StringVectorProperty
            name="SetDictRegionValues"
            number_of_elements="2"
            command="setDictRegionValues"
            repeat_command="1"
            number_of_elements_per_command="2">
            <Documentation>
                Set the value of the new attribute for each region indexes, use a comma between the value of each components:\n
                    valueRegionIndex : valueComponent1, valueComponent2 ...\n
                If the region attribute has other indexes than those given, a default value is use:\n
                    0 for uint type, -1 for int type and nan for float type.
            </Documentation>
            <Hints>
                <AllowRestoreDefaults />
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Region Indexes"/>
                    <ComponentLabel component="1" label="New Attribute Values"/>
                </ShowComponentLabels>
            </Hints>
        </StringVectorProperty>
    """ )
    def setDictRegionValues( self: Self, regionIndex: str, value: str ) -> None:
        """Set the dictionary with the region indexes and its corresponding list of values for each components.

        Args:
            regionIndex (str): Region index of the region attribute to consider.
            value (str): List of value to use for the regionIndex. If multiple components use a comma between the value of each component.
        """
        if self.clearDictRegionValues:
            self.dictRegionValues = {}
            self.clearDictRegionValues = False

        if regionIndex is not None and value is not None:
            self.dictRegionValues[ regionIndex ] = list( value.split( "," ) )

        self.Modified()

    @smproperty.xml( """
        <PropertyGroup
            label="Settings of the attribute with the region indexes"
            panel_visibility="default">
            <Property name="ChooseRegionAttribute"/>
            <Property name="SetDictRegionValues"/>
        </PropertyGroup>
    """ )
    def groupRegionAttributeSettingsWidgets( self: Self ) -> None:
        """Group the widgets to set the settings of the region attribute."""
        self.Modified()

    # Settings of the new attribute:
    @smproperty.xml( """
        <StringVectorProperty
            name="AttributeName"
            label="The name of the new attribute:"
            default_values="newAttribute"
            number_of_elements="1"
            element_types="2">
            <Documentation>
                Name of the new attribute to create.
            </Documentation>
        </StringVectorProperty>
    """ )
    def setAttributeName( self: Self, newAttributeName: str ) -> None:
        """Set attribute name.

        Args:
            newAttributeName (str): Name of the new attribute to create.
        """
        self.newAttributeName = newAttributeName
        self.Modified()

    @smproperty.intvector(
        name="ValueType",
        label="The type of the values:",
        number_of_elements=1,
        default_values=10,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <EnumerationDomain name="enum">
            <Entry value="2" text="int8"/>
            <Entry value="4" text="int16"/>
            <Entry value="6" text="int32"/>
            <Entry value="16" text="int64"/>
            <Entry value="3" text="uint8"/>
            <Entry value="5" text="uint16"/>
            <Entry value="7" text="uint32"/>
            <Entry value="17" text="uint64"/>
            <Entry value="10" text="float32"/>
            <Entry value="11" text="float64"/>
        </EnumerationDomain>
        <Documentation>
            The requested numpy scalar type for values of the new attribute.
        </Documentation>
    """ )
    def setValueType( self: Self, valueType: int ) -> None:
        """Set the type for the value used to create the new attribute.

        Args:
            valueType (int): The numpy scalar type encoding with int (vtk typecode).
        """
        dictType: dict[ int, Any ] = vnp.get_vtk_to_numpy_typemap()
        self.valueNpType = dictType[ valueType ]
        self.Modified()

    @smproperty.intvector(
        name="NumberOfComponents",
        label="Number of components:",
        number_of_elements=1,
        default_values=1,
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            The number of components for the new attribute to create.
        </Documentation>
    """ )
    def setNbComponent( self: Self, nbComponents: int ) -> None:
        """Set the number of components of the attribute to create.

        Args:
            nbComponents (int): Number of components of the new attribute.
        """
        self.nbComponents = nbComponents
        self.Modified()

    @smproperty.stringvector(
        name="ComponentNames",
        label="Names of components:",
        number_of_elements=1,
        default_values="Change if multiple components",
        panel_visibility="default",
    )
    @smdomain.xml( """
        <Documentation>
            Names of components if multiple for the new attribute to create.
            Use the coma and a coma between each component name:\n
                Names of components: X, Y, Z
        </Documentation>
        """ )
    def setComponentNames( self: Self, componentNames: str ) -> None:
        """Set the names of the components of the attribute to create.

        Args:
            componentNames (str): Names of component for the new attribute. Use a coma between each component names.
        """
        if componentNames == "" or componentNames == "Change if multiple components" or self.nbComponents == 1:
            self.componentNames = ()
        else:
            self.componentNames = tuple( componentNames.split( "," ) )

        self.Modified()

    @smproperty.xml( """
        <PropertyGroup
            label="Settings of the new attribute"
            panel_visibility="default">
            <Property name="AttributeName"/>
            <Property name="ValueType"/>
            <Property name="NumberOfComponents"/>
            <Property name="ComponentNames"/>
        </PropertyGroup>""" )
    def groupNewAttributeSettingsWidgets( self: Self ) -> None:
        """Group the widgets to set the settings of the new attribute."""
        self.Modified()

    def ApplyFilter( self, inputMesh: vtkDataSet, outputMesh: vtkDataSet ) -> None:
        """Is applying CreateConstantAttributePerRegion filter.

        Args:
            inputMesh : A mesh to transform
            outputMesh : A mesh transformed.
        """
        createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
            outputMesh,
            self.regionName,
            self.dictRegionValues,
            self.newAttributeName,
            self.valueNpType,
            self.nbComponents,
            self.componentNames,
            self.speHandler,
        )

        if len( createConstantAttributePerRegionFilter.logger.handlers ) == 0:
            createConstantAttributePerRegionFilter.setLoggerHandler( VTKHandler() )

        try:
            createConstantAttributePerRegionFilter.applyFilter()
        except ( ValueError, AttributeError ) as e:
            createConstantAttributePerRegionFilter.logger.error(
                f"The filter { createConstantAttributePerRegionFilter.logger.name } failed du to:\n{ e }" )
        except Exception as e:
            mess: str = f"The filter { createConstantAttributePerRegionFilter.logger.name } failed du to:\n{ e }"
            createConstantAttributePerRegionFilter.logger.critical( mess, exc_info=True )

        self.clearDictRegion = True

        return
