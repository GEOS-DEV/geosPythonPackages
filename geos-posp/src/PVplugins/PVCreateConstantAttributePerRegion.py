# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from typing import Union

import numpy as np
import numpy.typing as npt
from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.dirname( dir_path )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import PVplugins #required to update sys path

import vtkmodules.util.numpy_support as vnp
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from vtk import VTK_DOUBLE  # type: ignore[import-untyped]
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

from geos_posp.processing.multiblockInpectorTreeFunctions import (
    getBlockElementIndexesFlatten,
    getBlockFromFlatIndex,
)
from geos_posp.processing.vtkUtils import isAttributeInObject
from geos.utils.Logger import Logger, getLogger

__doc__ = """
PVCreateConstantAttributePerRegion is a Paraview plugin that allows to
create 2 attributes whom values are constant for each region index.

Input and output are either vtkMultiBlockDataSet or vtkUnstructuredGrid.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVCreateConstantAttributePerRegion.
* Select the mesh you want to create the attributes and containing a region attribute.
* Search and Apply Create Constant Attribute Per Region Filter.

"""

SOURCE_NAME: str = ""
DEFAULT_REGION_ATTRIBUTE_NAME = "region"


@smproxy.filter(
    name="PVCreateConstantAttributePerRegion",
    label="Create Constant Attribute Per Region",
)
@smhint.xml( """<ShowInMenu category="0- Geos Pre-processing"/>""" )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet", "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVCreateConstantAttributePerRegion( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Create an attribute with constant value per region."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkDataSet" )

        self.m_table: list[ tuple[ int, float ] ] = []
        self.m_regionAttributeName: str = DEFAULT_REGION_ATTRIBUTE_NAME
        self.m_attributeName: str = "attribute"

        # logger
        self.m_logger: Logger = getLogger( "Create Constant Attribute Per Region Filter" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    @smproperty.xml( """
        <StringVectorProperty
            name="RegionArray"
            label="Region Array"
            command="a01SetRegionAttributeName"
            default_values="region"
            number_of_elements="1"
            element_types="2">
            <ArrayListDomain
                name="array_list"
                attribute_type="Scalars"
                input_domain_name="inputs_array">
                <RequiredProperties>
                    <Property name="Input" function="Input"/>
                </RequiredProperties>
            </ArrayListDomain>
            <Documentation>
                Select an attribute containing the indexes of the regions
            </Documentation>
        </StringVectorProperty>
        """ )
    def a01SetRegionAttributeName( self: Self, name: str ) -> None:
        """Set region attribute name."""
        self.m_regionAttributeName = name
        self.Modified()

    @smproperty.xml( """
        <StringVectorProperty
            name="AttributeName"
            command="a02SetAttributeName"
            default_values="Attribute"
            number_of_elements="1"
            element_types="2">
            <Documentation>
                Name of the new attribute
            </Documentation>
        </StringVectorProperty>
        """ )
    def a02SetAttributeName( self: Self, value: str ) -> None:
        """Set attribute name.

        Args:
            value (str): attribute name.
        """
        self.m_attributeName = value
        self.Modified()

    @smproperty.xml( """
        <DoubleVectorProperty
            name="AttributeTable"
            command="b01SetAttributeValues"
            repeat_command="1"
            number_of_elements_per_command="2"
            element_types="0 1"
            default_values="0 0.0">
            <Hints>
                <ShowComponentLabels>
                    <ComponentLabel component="0" label="Region Index"/>
                    <ComponentLabel component="1" label="Attribute Value"/>
                </ShowComponentLabels>
            </Hints>
            <Documentation>
                Set new attributes values for each region index.
            </Documentation>
        </DoubleVectorProperty>
        """ )
    def b01SetAttributeValues( self: Self, regionIndex: int, value: float ) -> None:
        """Set attribute values per region.

        Args:
            regionIndex (int): region index.

            value (float): attribute value.
        """
        self.m_table.append( ( regionIndex, value ) )
        self.Modified()

    @smproperty.xml( """<PropertyGroup label="Attribute value per regions"
                        panel_visibility="default">
                    <Property name="AttributeTable"/>
                   </PropertyGroup>""" )
    def b02GroupFlow( self: Self ) -> None:
        """Organize groups."""
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
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
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
        self.m_logger.info( f"Apply filter {__name__}" )
        try:
            input0: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ] = ( self.GetInputData( inInfoVec, 0, 0 ) )
            output: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet ] = ( self.GetOutputData( outInfoVec, 0 ) )

            assert input0 is not None, "Input Surface is null."
            assert output is not None, "Output pipeline is null."

            output.ShallowCopy( input0 )

            assert ( len( self.m_regionAttributeName )
                     > 0 ), "Region attribute is undefined, please select an attribute."
            if isinstance( output, vtkMultiBlockDataSet ):
                self.createAttributesMultiBlock( output )
            else:
                self.createAttributes( output )

            mess: str = ( f"The new attribute {self.m_attributeName} was successfully added." )
            self.Modified()
            self.m_logger.info( mess )
        except AssertionError as e:
            mess1: str = "The new attribute was not added due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "The new attribute was not added due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        self.m_compute = True
        return 1

    def createAttributesMultiBlock( self: Self, output: vtkMultiBlockDataSet ) -> None:
        """Create attributes on vtkMultiBlockDataSet from input data.

        Args:
            output (vtkMultiBlockDataSet): mesh where to create the attributes.
        """
        # for each block
        blockIndexes: list[ int ] = getBlockElementIndexesFlatten( output )
        for blockIndex in blockIndexes:
            block0: vtkDataObject = getBlockFromFlatIndex( output, blockIndex )
            assert block0 is not None, "Block is undefined."
            block: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( block0 )
            try:
                self.createAttributes( block )
            except AssertionError as e:
                self.m_logger.warning( f"Block {blockIndex}: {e}" )
        output.Modified()

    def createAttributes( self: Self, mesh: vtkUnstructuredGrid ) -> None:
        """Create attributes on vtkUnstructuredGrid from input data.

        Args:

             mesh (vtkUnstructuredGrid): mesh where to create the attributes.
        """
        assert isAttributeInObject( mesh, self.m_regionAttributeName,
                                    False ), f"{self.m_regionAttributeName} is not in the mesh."
        regionAttr: vtkDataArray = mesh.GetCellData().GetArray( self.m_regionAttributeName )
        assert regionAttr is not None, "Region attribute is undefined"
        npArray: npt.NDArray[ np.float64 ] = self.createNpArray( regionAttr )
        newAttr: vtkDataArray = vnp.numpy_to_vtk( npArray, True, VTK_DOUBLE )
        newAttr.SetName( self.m_attributeName )
        mesh.GetCellData().AddArray( newAttr )
        mesh.GetCellData().Modified()
        mesh.Modified()

    def createNpArray( self: Self, regionAttr: vtkDataArray ) -> npt.NDArray[ np.float64 ]:
        """Create numpy arrays from input data.

        Args:
            regionAttr (vtkDataArray): Region attribute

        Returns:
            npt.NDArray[np.float64]: numpy array of the new attribute.
        """
        regionNpArray: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( regionAttr )
        npArray: npt.NDArray[ np.float64 ] = np.full_like( regionNpArray, np.nan )
        # for each region
        for regionIndex, value in self.m_table:
            if regionIndex in np.unique( regionNpArray ):
                mask: npt.NDArray[ np.bool_ ] = regionNpArray == regionIndex
                npArray[ mask ] = value
            else:
                self.m_logger.warning( f"Index {regionIndex} is not in the values of the region" +
                                       f" attribute '{regionAttr.GetName()}'" )
        return npArray
