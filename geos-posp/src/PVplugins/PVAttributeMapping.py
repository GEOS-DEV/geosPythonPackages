# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
from typing import Union

from typing_extensions import Self

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.dirname( dir_path )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import PVplugins  # noqa: F401

from geos.utils.Logger import Logger, getLogger
from geos_posp.filters.AttributeMappingFromCellCoords import (
    AttributeMappingFromCellCoords, )
from geos.mesh.utils.arrayModifiers import fillPartialAttributes
from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.utils.arrayHelpers import (
    getAttributeSet, )
from geos_posp.visu.PVUtils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )
from geos_posp.visu.PVUtils.paraviewTreatments import getArrayChoices
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArraySelection,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObjectTreeIterator,
    vtkDataSet,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

__doc__ = """
Map the attributes from a source mesh to a client mesh.

Input and output are vtkUnstructuredGrid.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVAttributeMapping.
* Select the server mesh.
* Search and Select Attribute Mapping Filter.
* Select the client mesh.
* Select the attributes to transfer and Apply.

"""


@smproxy.filter( name="PVAttributeMapping", label="Attribute Mapping" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Client", port_index=1, label="Client mesh" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid", "vtkMultiBlockDataSet" ],
    composite_data_supported=True,
)
@smproperty.input( name="Server", port_index=0, label="Server mesh" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=False,
)
class PVAttributeMapping( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Map the properties of a server mesh to a client mesh."""
        super().__init__( nInputPorts=2, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        # boolean to check if first use of the filter for attribute list initialization
        self.m_firstUse = True

        # list of attribute names to transfer
        self.m_attributes: vtkDataArraySelection = vtkDataArraySelection()
        self.m_attributes.AddObserver( 0, createModifiedCallback( self ) )

        # logger
        self.m_logger: Logger = getLogger( "Attribute Mapping" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger
        self.Modified()

    @smproperty.dataarrayselection( name="AttributesToTransfer" )
    def a02GetAttributeToTransfer( self: Self ) -> vtkDataArraySelection:
        """Get selected attribute names to transfer.

        Returns:
            vtkDataArraySelection: selected attribute names.
        """
        return self.m_attributes

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
        # only at initialization step, no change later
        if self.m_firstUse:
            # get cell ids
            inData = self.GetInputData( inInfoVec, 0, 0 )
            assert isinstance( inData, ( vtkDataSet, vtkMultiBlockDataSet ) ), "Input object type is not supported."

            # update vtkDAS
            attributeNames: set[ str ] = getAttributeSet( inData, False )
            for attributeName in attributeNames:
                if not self.m_attributes.ArrayExists( attributeName ):
                    self.m_attributes.AddArray( attributeName )

            self.m_firstUse = False
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
        inData = self.GetInputData( inInfoVec, 1, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
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
        self.m_logger.info( f"Apply filter {__name__}" )
        try:
            serverMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet,
                               vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 0, 0 )
            clientMesh: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet,
                               vtkCompositeDataSet ] = self.GetInputData( inInfoVec, 1, 0 )
            outData: Union[ vtkUnstructuredGrid, vtkMultiBlockDataSet,
                            vtkCompositeDataSet ] = self.GetOutputData( outInfoVec, 0 )

            assert serverMesh is not None, "Input server mesh is null."
            assert clientMesh is not None, "Input client mesh is null."
            assert outData is not None, "Output pipeline is null."

            outData.ShallowCopy( clientMesh )
            attributeNames: set[ str ] = set( getArrayChoices( self.a02GetAttributeToTransfer() ) )
            for attributeName in attributeNames:
                fillPartialAttributes( serverMesh, attributeName, False )

            mergedServerMesh: vtkUnstructuredGrid
            if isinstance( serverMesh, vtkUnstructuredGrid ):
                mergedServerMesh = serverMesh
            elif isinstance( serverMesh, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
                mergedServerMesh = mergeBlocks( serverMesh )
            else:
                raise ValueError( "Server mesh data type is not supported. " +
                                  "Use either vtkUnstructuredGrid or vtkMultiBlockDataSet" )

            if isinstance( outData, vtkUnstructuredGrid ):
                self.doTransferAttributes( mergedServerMesh, outData, attributeNames )
            elif isinstance( outData, ( vtkMultiBlockDataSet, vtkCompositeDataSet ) ):
                self.transferAttributesMultiBlockDataSet( mergedServerMesh, outData, attributeNames )
            else:
                raise ValueError( "Client mesh data type is not supported. " +
                                  "Use either vtkUnstructuredGrid or vtkMultiBlockDataSet" )

            outData.Modified()

            mess: str = "Attributes were successfully transferred ."
            self.m_logger.info( mess )
        except AssertionError as e:
            mess1: str = "Attribute transfer failed due to:"
            self.m_logger.error( mess1 )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "Attribute transfer failed due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        return 1

    def doTransferAttributes(
        self: Self,
        serverMesh: vtkUnstructuredGrid,
        clientMesh: vtkUnstructuredGrid,
        attributeNames: set[ str ],
    ) -> bool:
        """Transfer attributes between two vtkUnstructuredGrids.

        Args:
            serverMesh (vtkUnstructuredGrid): server mesh
            clientMesh (vtkUnstructuredGrid): client mesh
            attributeNames (set[str]): set of attribut names to transfer

        Returns:
            bool: True if attributes were successfully transferred.

        """
        filter: AttributeMappingFromCellCoords = AttributeMappingFromCellCoords()
        filter.AddInputDataObject( 0, serverMesh )
        filter.AddInputDataObject( 1, clientMesh )
        filter.SetTransferAttributeNames( attributeNames )
        filter.Update()
        clientMesh.ShallowCopy( filter.GetOutputDataObject( 0 ) )
        return True

    def transferAttributesMultiBlockDataSet(
        self: Self,
        serverBlock: vtkUnstructuredGrid,
        clientMesh: Union[ vtkMultiBlockDataSet, vtkCompositeDataSet ],
        attributeNames: set[ str ],
    ) -> bool:
        """Transfer attributes from a vtkUnstructuredGrid to a multiblock.

        Args:
            serverBlock (vtkUnstructuredGrid): server mesh
            clientMesh (vtkMultiBlockDataSet | vtkCompositeDataSet): client mesh
            attributeNames (set[str]): set of attribut names to transfer

        Returns:
            bool: True if attributes were successfully transferred.

        """
        iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iter.SetDataSet( clientMesh )
        iter.VisitOnlyLeavesOn()
        iter.GoToFirstItem()
        while iter.GetCurrentDataObject() is not None:
            clientBlock: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iter.GetCurrentDataObject() )
            self.doTransferAttributes( serverBlock, clientBlock, attributeNames )
            clientBlock.Modified()
            iter.GoToNextItem()
        return True
