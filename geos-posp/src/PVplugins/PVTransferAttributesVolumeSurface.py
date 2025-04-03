# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys

from typing_extensions import Self

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.dirname(dir_path)
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

import PVplugins #required to update sys path

from paraview.simple import (  # type: ignore[import-not-found]
    FindSource,
    GetActiveSource,
    GetSources,
    servermanager,
)
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
    smdomain,
    smhint,
    smproperty,
    smproxy,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArray,
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonCore import (
    vtkDataArraySelection as vtkDAS,
)
from vtkmodules.vtkCommonDataModel import (
    vtkDataObject,
    vtkMultiBlockDataSet,
    vtkPolyData,
    vtkUnstructuredGrid,
)

from geos_posp.filters.TransferAttributesVolumeSurface import (
    TransferAttributesVolumeSurface,
)
from geos_posp.processing.multiblockInpectorTreeFunctions import (
    getBlockElementIndexesFlatten,
    getBlockFromFlatIndex,
)
from geos_posp.processing.vtkUtils import getAttributeSet, mergeBlocks
from geos.utils.Logger import Logger, getLogger
from geos_posp.visu.PVUtils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback,
)
from geos_posp.visu.PVUtils.paraviewTreatments import getArrayChoices

__doc__ = """
PVTransferAttributesVolumeSurface is a Paraview plugin that allows to map face ids from
surface mesh with cell ids from volume mesh.

Input and output types are vtkMultiBlockDataSet.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVTransferAttributesVolumeSurface.
* Select first a volume mesh, then a surface mesh, both of type vtkMultiBlockDataSet
* Search and Apply 'Geos Volume Surface Mesh Mapper' Filter.

"""


@smproxy.filter(
    name="PVTransferAttributesVolumeSurface",
    label="Geos Transfer Attributes From Volume to Surface",
)
@smhint.xml('<ShowInMenu category="4- Geos Utils"/>')
@smproperty.input(name="SurfaceMesh", port_index=1)
@smdomain.datatype(
    dataTypes=["vtkMultiBlockDataSet", "vtkUnstructuredGrid", "vtkPolyData"],
    composite_data_supported=True,
)
@smproperty.input(name="VolumeMesh", port_index=0)
@smdomain.datatype(
    dataTypes=["vtkMultiBlockDataSet", "vtkUnstructuredGrid"],
    composite_data_supported=True,
)
class PVTransferAttributesVolumeSurface(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> None:
        """Paraview plugin to compute additional geomechanical surface outputs.

        Input is either a vtkMultiBlockDataSet that contains surfaces with
        Normals and Tangential attributes.
        """
        super().__init__(
            nInputPorts=2, nOutputPorts=1, outputType="vtkMultiBlockDataSet"
        )

        #: input volume mesh
        self.m_volumeMesh: vtkMultiBlockDataSet
        #: output surface mesh
        self.m_outputSurfaceMesh: vtkMultiBlockDataSet
        # volume mesh source
        self.m_sourceNameVolume: str = [
            k for (k, v) in GetSources().items() if v == GetActiveSource()
        ][0][0]

        # list of attributes
        self.m_attributes: vtkDAS = self.createAttributeVTKDas()
        # logger
        self.m_logger: Logger = getLogger("Volume Surface Mesh Mapper Filter")

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def createAttributeVTKDas(self: Self) -> vtkDAS:
        """Create the vtkDataArraySelection with cell attribute names.

        Returns:
            vtkDAS: vtkDataArraySelection with attribute names
        """
        source = FindSource(self.m_sourceNameVolume)
        dataset = servermanager.Fetch(source)
        attributes: set[str] = getAttributeSet(dataset, False)
        attributesDAS: vtkDAS = vtkDAS()
        for attribute in attributes:
            attributesDAS.AddArray(attribute, False)
        attributesDAS.AddObserver("ModifiedEvent", createModifiedCallback(self))  # type: ignore[arg-type]
        return attributesDAS

    @smproperty.dataarrayselection(name="AttributesToTransfer")
    def a02GetAttributeToTransfer(self: Self) -> vtkDAS:
        """Get selected attribute names to transfer.

        Returns:
            vtkDataArraySelection: selected attribute names.
        """
        return self.m_attributes

    def FillInputPortInformation(self: Self, port: int, info: vtkInformation) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkMultiBlockDataSet")
        else:
            info.Set(self.INPUT_REQUIRED_DATA_TYPE(), "vtkMultiBlockDataSet")
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[vtkInformationVector],  # noqa: F841
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
        outInfo = outInfoVec.GetInformationObject(0)  # noqa: F841
        return 1

    def RequestDataObject(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
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
        inData1 = self.GetInputData(inInfoVec, 0, 0)
        inData2 = self.GetInputData(inInfoVec, 1, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData1 is not None
        assert inData2 is not None
        if outData is None or (not outData.IsA(inData2.GetClassName())):
            outData = inData2.NewInstance()
            outInfoVec.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfoVec, outInfoVec)  # type: ignore[no-any-return]

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[vtkInformationVector],
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
            self.m_logger.info(f"Apply filter {__name__}")
            self.SetProgressText("Computation in progress...")
            self.SetProgressShiftScale(50, 100)

            self.m_volumeMesh = vtkMultiBlockDataSet.GetData(inInfoVec[0])
            surfaceMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData(
                inInfoVec[1]
            )
            self.m_outputSurfaceMesh = self.GetOutputData(outInfoVec, 0)

            assert self.m_volumeMesh is not None, "Input Volume mesh is null."
            assert surfaceMesh is not None, "Input Surface mesh is null."
            assert self.m_outputSurfaceMesh is not None, "Output pipeline is null."

            self.m_outputSurfaceMesh.ShallowCopy(surfaceMesh)
            self.transferAttributes()

            self.m_logger.info("Attributes were successfully transfered.")
        except AssertionError as e:
            mess: str = "Attribute transfer failed due to:"
            self.m_logger.error(mess)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess0: str = "Attribute transfer failed due to:"
            self.m_logger.critical(mess0)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1

    def transferAttributes(self: Self) -> bool:
        """Do transfer attributes from volume to surface.

        Returns:
            bool: True if transfer is successfull, False otherwise.
        """

        attributeNames: set[str] = set(
            getArrayChoices(self.a02GetAttributeToTransfer())
        )
        volumeMeshMerged: vtkUnstructuredGrid = mergeBlocks(self.m_volumeMesh)
        surfaceBlockIndexes: list[int] = getBlockElementIndexesFlatten(
            self.m_outputSurfaceMesh
        )
        for blockIndex in surfaceBlockIndexes:
            surfaceBlock0: vtkDataObject = getBlockFromFlatIndex(
                self.m_outputSurfaceMesh, blockIndex
            )
            assert surfaceBlock0 is not None, "surfaceBlock0 is undefined."
            surfaceBlock: vtkPolyData = vtkPolyData.SafeDownCast(surfaceBlock0)
            assert surfaceBlock is not None, "surfaceBlock is undefined."

            assert isinstance(surfaceBlock, vtkPolyData), "Wrong object type."

            # do transfer of attributes
            filter: TransferAttributesVolumeSurface = TransferAttributesVolumeSurface()
            filter.AddInputDataObject(0, volumeMeshMerged)
            filter.AddInputDataObject(1, surfaceBlock)
            filter.SetAttributeNamesToTransfer(attributeNames)
            filter.Update()
            outputSurface: vtkUnstructuredGrid = filter.GetOutputDataObject(0)

            # add attributes to output surface mesh
            for attributeName in filter.GetNewAttributeNames():
                attr: vtkDataArray = outputSurface.GetCellData().GetArray(attributeName)
                surfaceBlock.GetCellData().AddArray(attr)
                surfaceBlock.GetCellData().Modified()
            surfaceBlock.Modified()

        self.m_outputSurfaceMesh.Modified()
        return True
