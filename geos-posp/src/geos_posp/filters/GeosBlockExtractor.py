# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from geos_posp.processing.multiblockInpectorTreeFunctions import (
    getBlockIndexFromName,
)
from geos_posp.processing.vtkUtils import extractBlock
from geos.utils.GeosOutputsConstants import (
    GeosDomainNameEnum,
    OutputObjectEnum,
)
from geos.utils.Logger import Logger, getLogger

__doc__ = """
GeosBlockExtractor module is a vtk filter that allows to extract Volume mesh,
Wells and Faults from a vtkMultiBlockDataSet.

Filter input and output types are vtkMultiBlockDataSet.

To use the filter:

.. code-block:: python

    from filters.GeosBlockExtractor import GeosBlockExtractor

    # filter inputs
    logger :Logger
    input :vtkMultiBlockDataSet

    # instanciate the filter
    blockExtractor :GeosBlockExtractor = GeosBlockExtractor()
    # set the logger
    blockExtractor.SetLogger(logger)
    # set input data object
    blockExtractor.SetInputDataObject(input)
    # ExtractFaultsOn or ExtractFaultsOff to (de)activate the extraction of Fault blocks
    blockExtractor.ExtractFaultsOn()
    # ExtractWellsOn or ExtractWellsOff to (de)activate the extraction of well blocks
    blockExtractor.ExtractWellsOn()
    # do calculations
    blockExtractor.Update()
    # get output object
    output :vtkMultiBlockDataSet = blockExtractor.GetOutputDataObject(0)
"""


class GeosBlockExtractor(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> None:
        """VTK Filter that perform GEOS block extraction.

        The filter returns the volume mesh as the first output, Surface mesh as the second
        output, and well mesh as the third output.
        """
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkMultiBlockDataSet")  # type: ignore[no-untyped-call]

        self.m_extractFaults: bool = False
        self.m_extractWells: bool = False
        self.m_outputPortMapping: dict[OutputObjectEnum, int] = {
            OutputObjectEnum.VOLUME: 0,
            OutputObjectEnum.FAULTS: -1,
            OutputObjectEnum.WELLS: -1,
        }

        self.m_input: vtkMultiBlockDataSet
        self.m_outputVolumeMesh: vtkMultiBlockDataSet
        self.m_outputFaults: vtkMultiBlockDataSet
        self.m_outputWells: vtkMultiBlockDataSet

        self.m_logger: Logger = getLogger("Geos Block Extractor Filter")

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

    def RequestData(
        self: Self,
        request: vtkInformation,
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
            self.m_input = vtkMultiBlockDataSet.GetData(inInfoVec[0])
            assert self.m_input is not None, "Input object is null."

            # initialize output objects
            volumeMeshPort: int = self.m_outputPortMapping[OutputObjectEnum.VOLUME]
            self.m_outputVolumeMesh = self.GetOutputData(outInfoVec, volumeMeshPort)  # type: ignore[no-untyped-call]
            assert self.m_outputVolumeMesh is not None, "Output volume mesh is null."

            if self.m_extractFaults:
                faultMeshPort: int = self.m_outputPortMapping[OutputObjectEnum.FAULTS]
                assert faultMeshPort > 0, "Faults output port is undefined."
                assert (
                    faultMeshPort < self.GetNumberOfOutputPorts()
                ), "Number of output ports is unconsistent with output objects."
                self.m_outputFaults = self.GetOutputData(outInfoVec, faultMeshPort)  # type: ignore[no-untyped-call]
                assert self.m_outputFaults is not None, "Output surface mesh is null."

            if self.m_extractWells:
                wellMeshPort: int = self.m_outputPortMapping[OutputObjectEnum.WELLS]
                assert wellMeshPort > 0, "Wells output port is undefined."
                assert (
                    wellMeshPort < self.GetNumberOfOutputPorts()
                ), "Number of output ports is unconsistent with output objects."
                self.m_outputWells = self.GetOutputData(outInfoVec, wellMeshPort)  # type: ignore[no-untyped-call]
                assert self.m_outputWells is not None, "Output well mesh is null."

            self.doExtraction()

        except AssertionError as e:
            mess: str = "Geos block extraction failed due to:"
            self.m_logger.error(mess)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess0: str = "Geos block extraction failed due to:"
            self.m_logger.critical(mess0)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def UpdateOutputPorts(self: Self) -> None:
        """Set the number of output ports and update extraction options."""
        # update number of output port
        nOutputPort: int = 1
        if self.m_extractFaults:
            nOutputPort += 1
        if self.m_extractWells:
            nOutputPort += 1
        self.SetNumberOfOutputPorts(nOutputPort)

        # update output port mapping
        self.m_outputPortMapping[OutputObjectEnum.FAULTS] = -1
        self.m_outputPortMapping[OutputObjectEnum.WELLS] = -1
        if nOutputPort == 2:
            outputObject: OutputObjectEnum = (
                OutputObjectEnum.FAULTS
                if self.m_extractFaults
                else OutputObjectEnum.WELLS
            )
            self.m_outputPortMapping[outputObject] = 1
        else:
            self.m_outputPortMapping[OutputObjectEnum.FAULTS] = 1
            self.m_outputPortMapping[OutputObjectEnum.WELLS] = 2

    def ExtractFaultsOn(self: Self) -> None:
        """Activate the extraction of Faults."""
        self.m_extractFaults = True
        self.UpdateOutputPorts()

    def ExtractFaultsOff(self: Self) -> None:
        """Deactivate the extraction of Faults."""
        self.m_extractFaults = False
        self.UpdateOutputPorts()

    def ExtractWellsOn(self: Self) -> None:
        """Activate the extraction of Wells."""
        self.m_extractWells = True
        self.UpdateOutputPorts()

    def ExtractWellsOff(self: Self) -> None:
        """Deactivate the extraction of Wells."""
        self.m_extractWells = False
        self.UpdateOutputPorts()

    def getOutputVolume(self: Self) -> vtkMultiBlockDataSet:
        """Get output volume mesh.

        Returns:
            vtkMultiBlockDataSet: volume mesh
        """
        return self.m_outputVolumeMesh

    def getOutputFaults(self: Self) -> vtkMultiBlockDataSet:
        """Get output fault mesh.

        Returns:
            vtkMultiBlockDataSet: fault mesh
        """
        assert (
            self.m_extractFaults
        ), "Extract fault option was set to False, turn on first."
        return self.m_outputFaults

    def getOutputWells(self: Self) -> vtkMultiBlockDataSet:
        """Get output well mesh.

        Returns:
            vtkMultiBlockDataSet: well mesh
        """
        assert (
            self.m_extractWells
        ), "Extract well option was set to False, turn on first."
        return self.m_outputWells

    def doExtraction(self: Self) -> int:
        """Apply block extraction.

        Returns:
            bool: True if block extraction successfully ended, False otherwise.
        """
        try:
            assert self.m_input is not None, "Input mesh is null."

            if not self.extractRegion(GeosDomainNameEnum.VOLUME_DOMAIN_NAME):
                self.m_logger.error("Volume mesh extraction failed.")
            if self.m_extractFaults and not self.extractRegion(
                GeosDomainNameEnum.FAULT_DOMAIN_NAME
            ):
                self.m_logger.error("Fault extraction failed.")
            if self.m_extractWells and not self.extractRegion(
                GeosDomainNameEnum.WELL_DOMAIN_NAME
            ):
                self.m_logger.error("Well extraction failed.")
        except AssertionError as e:
            mess: str = "Block extraction failed due to:"
            self.m_logger.error(mess)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess1: str = "Block extraction failed due to:"
            self.m_logger.critical(mess1)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1

    def extractRegion(self: Self, type: GeosDomainNameEnum) -> int:
        """Extract volume mesh from input vtkMultiBlockDataSet.

        Returns:
            bool: True if volume mesh extraction successfully ended, False otherwise.
        """
        block: vtkMultiBlockDataSet
        blockIndex = getBlockIndexFromName(self.m_input, type.value)
        if blockIndex < 0:
            self.m_logger.warning("Cell block index is invalid.")
            return 0

        block = extractBlock(self.m_input, blockIndex)
        assert block is not None, f"Extracted {type.value} block is null."

        if (type is GeosDomainNameEnum.VOLUME_DOMAIN_NAME) and (
            self.m_outputVolumeMesh is not None
        ):
            self.m_outputVolumeMesh.ShallowCopy(block)
            self.m_outputVolumeMesh.Modified()
        elif (type is GeosDomainNameEnum.FAULT_DOMAIN_NAME) and (
            self.m_outputFaults is not None
        ):
            self.m_outputFaults.ShallowCopy(block)
            self.m_outputFaults.Modified()
        elif (type is GeosDomainNameEnum.WELL_DOMAIN_NAME) and (
            self.m_outputWells is not None
        ):
            self.m_outputWells.ShallowCopy(block)
            self.m_outputWells.Modified()
        else:
            raise TypeError(f"Output object for domain {type.value} is null.")
        return 1
