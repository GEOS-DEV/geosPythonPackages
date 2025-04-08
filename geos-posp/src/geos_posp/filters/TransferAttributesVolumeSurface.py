# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import vtkmodules.util.numpy_support as vnp
from geos.utils.ConnectionSet import ConnectionSetCollection
from geos.utils.GeosOutputsConstants import GeosMeshSuffixEnum
from geos.utils.Logger import Logger, getLogger
from typing_extensions import Self
from vtk import VTK_DOUBLE  # type: ignore[import-untyped]
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import vtkPolyData, vtkUnstructuredGrid

from geos_posp.filters.VolumeSurfaceMeshMapper import VolumeSurfaceMeshMapper
from geos.mesh.vtkUtils import (
    getArrayInObject,
    getComponentNames,
    isAttributeInObject,
)

__doc__ = """
TransferAttributesVolumeSurface is a vtk filter that allows to transfer volume
mesh attributes to surface mesh.

This filter transfer a cell attribute as a face attribute from each volume cell
adjacent to a surface face. Since a face can be adjacent to 2 cells (one at
each side), 2 attributes are created with the suffix '_plus' and '_minus'
depending on the normal vector direction of the face.

Input and output surface types are vtkPolyData and input volume mesh is
vtkUnstructuredGrid.

.. WARNING::
    This filter must be use very cautiously since its result may have no sense.


To use it:

.. code-block:: python

    from filters.TransferAttributesVolumeSurface import TransferAttributesVolumeSurface

    filter :TransferAttributesVolumeSurface = TransferAttributesVolumeSurface()
    # set input data objects
    filter.AddInputDataObject(0, volumeMesh)
    filter.AddInputDataObject(1, surfaceMesh)
    # set attribute names to transfer
    attributeNames :set[str]
    filter.SetAttributeNamesToTransfer(attributeNames)
    # do calculations
    filter.Update()
    # get filter output surface with new attributes
    output :vtkPolyData = filter.GetOutputDataObject(0)
"""


class TransferAttributesVolumeSurface( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to transfer attributes from volume to surface mesh.

        Input volume is vtkUnstructuredGrid and input, output surface mesh
        is vtkPolyData, and the list of names of the attributes to transfer.
        """
        super().__init__( nInputPorts=2, nOutputPorts=1, outputType="vtkPolyData" )

        #: input volume mesh attributes are from
        self.m_volumeMesh: vtkUnstructuredGrid
        #: input surface mesh where to transfer attributes
        self.m_surfaceMesh: vtkPolyData
        #: output surface mesh
        self.m_outputSurfaceMesh: vtkPolyData
        #: set of attribute names to transfer
        self.m_attributeNames: set[ str ] = set()
        #: create attribute names
        self.m_newAttributeNames: set[ str ] = set()
        # logger
        self.m_logger: Logger = getLogger( "Attribute Transfer from Volume to Surface Filter" )

    def GetAttributeNamesToTransfer( self: Self ) -> set[ str ]:
        """Get the set of attribute names to transfer from volume to surface.

        Returns:
            set[str]: set of attributes names.
        """
        return self.m_attributeNames

    def SetAttributeNamesToTransfer( self: Self, names: set[ str ] ) -> None:
        """Set the set of attribute names to transfer from volume to surface.

        Args:
            names (set[str]): set of attributes names.
        """
        self.m_attributeNames = names

    def GetNewAttributeNames( self: Self ) -> set[ str ]:
        """Get the set of attribute names created in the output surface.

        Returns:
            set[str]: Set of new attribute names in the surface.
        """
        return self.m_newAttributeNames

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
        else:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkPolyData" )
        return 1

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
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
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
        inData2 = self.GetInputData( inInfoVec, 1, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData1 is not None
        assert inData2 is not None
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
        try:
            # input volume mesh
            self.m_volumeMesh = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
            # input surface
            self.m_surfaceMesh = vtkPolyData.GetData( inInfoVec[ 1 ] )
            # output volume mesh
            self.m_outputSurfaceMesh = self.GetOutputData( outInfoVec, 0 )
            self.m_outputSurfaceMesh.ShallowCopy( self.m_surfaceMesh )

            # compute cell adjacency mapping
            meshMap: ConnectionSetCollection = self.getMeshMapping()
            # do transfer of attributes
            self.doTransferAttributes( meshMap )
            self.m_logger.info( "Attribute transfer was successfully computed." )
        except AssertionError as e:
            mess: str = "Attribute transfer failed due to:"
            self.m_logger.error( mess )
            self.m_logger.error( e, exc_info=True )
            return 0
        except Exception as e:
            mess0: str = "Attribute transfer failed due to:"
            self.m_logger.critical( mess0 )
            self.m_logger.critical( e, exc_info=True )
            return 0
        return 1

    def getMeshMapping( self: Self ) -> ConnectionSetCollection:
        """Compute cell mapping between volume and surface mesh.

        Returns:
            dict[int, dict[int, bool]]: dictionnary of face ids as keys and
            volume cell ids and side as values.
        """
        filter: VolumeSurfaceMeshMapper = VolumeSurfaceMeshMapper()
        filter.AddInputDataObject( 0, self.m_volumeMesh )
        filter.AddInputDataObject( 1, self.m_surfaceMesh )
        filter.SetCreateAttribute( False )
        filter.Update()
        return filter.GetSurfaceToVolumeConnectionSets()

    def doTransferAttributes( self: Self, meshMap: ConnectionSetCollection ) -> bool:
        """Transfer all attributes from the set of attribute names.

        Except on boundaries, surfaces are bounded by cells along each side.
        Two attributes are then created on the surface, one corresponding to
        positive side cell values, one corresponding to negative side cell
        values.

        Args:
            meshMap (dict[int, dict[int, bool]]): map of surface face ids to
                volume mesh cell ids and side.

        Returns:
            bool: True if transfer successfully ended, False otherwise.
        """
        for attributeName in self.m_attributeNames:
            # negative side attribute
            self.transferAttribute( attributeName, False, meshMap )
            # positive side attribute
            self.transferAttribute( attributeName, True, meshMap )
        return True

    def transferAttribute(
        self: Self,
        attributeName: str,
        surfaceSide: bool,
        meshMap: ConnectionSetCollection,
    ) -> bool:
        """Transfer the attribute attributeName from volume to surface mesh.

        Created surface attribute will have the same name as input attribute
        name with suffix "_Plus" for positive (True) side and "_Minus" for
        negative (False) side.

        Args:
            attributeName (str): Name of the attribute to transfer.
            surfaceSide (bool): Side of the surface the attribute is from.
            meshMap (dict[int, dict[int, bool]]): map of surface face ids to
                volume mesh cell ids and side.

        Returns:
            bool: True if transfer successfully ended, False otherwise.
        """
        # get volume mesh attribute
        if isAttributeInObject( self.m_volumeMesh, attributeName, False ):
            attr: npt.NDArray[ np.float64 ] = getArrayInObject( self.m_volumeMesh, attributeName, False )
            attrComponentNames: tuple[ str, ...] = getComponentNames( self.m_volumeMesh, attributeName, False )
            # creates attribute arrays on the surface
            nbFaces: int = self.m_surfaceMesh.GetNumberOfCells()
            nbComponents: int = ( len( attrComponentNames ) if len( attrComponentNames ) > 0 else 1 )
            suffix: str = ( GeosMeshSuffixEnum.SURFACE_PLUS_SUFFIX.value
                            if surfaceSide else GeosMeshSuffixEnum.SURFACE_MINUS_SUFFIX.value )
            surfaceAttributeName: str = attributeName + suffix
            attributeValues: npt.NDArray[ np.float64 ] = np.full( ( nbFaces, nbComponents ), np.nan )

            # for each face of the surface
            for connectionSet in meshMap:
                # for each cell of the volume mesh
                for cellId, side in connectionSet.getConnectedCellIds().items():
                    if side == surfaceSide:
                        attributeValues[ connectionSet.getCellIdRef() ] = attr[ cellId ]

            surfaceAttribute: vtkDataArray = vnp.numpy_to_vtk( attributeValues, deep=True, array_type=VTK_DOUBLE )
            surfaceAttribute.SetName( surfaceAttributeName )
            if surfaceAttribute.GetNumberOfComponents() > 1:
                for i in range( surfaceAttribute.GetNumberOfComponents() ):
                    surfaceAttribute.SetComponentName( i, attrComponentNames[ i ] )

            self.m_outputSurfaceMesh.GetCellData().AddArray( surfaceAttribute )
            self.m_outputSurfaceMesh.GetCellData().Modified()
            self.m_outputSurfaceMesh.Modified()

            # add new attribute names to the set
            self.m_newAttributeNames.add( surfaceAttributeName )
        else:
            self.m_logger.warning( f"{attributeName} was skipped since it not" + " in the input volume mesh." )

        return True
