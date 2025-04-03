# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys

from typing_extensions import Self, Union

dir_path = os.path.dirname(os.path.realpath(__file__))
parent_dir_path = os.path.dirname(dir_path)
if parent_dir_path not in sys.path:
    sys.path.append(parent_dir_path)

import PVplugins #required to update sys path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase,
    smdomain,
    smhint,
    smproperty,
    smproxy,
)
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

from geos_posp.processing.vtkUtils import mergeBlocks
from geos.utils.Logger import Logger, getLogger

__doc__ = """
Merge filter that keep partial attributes using nan values.

Input is a vtkMultiBlockDataSet and output is a vtkUnstructuredGrid.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVMergeBlocksEnhanced.
* Select the mesh you want to create the attributes and containing a region attribute.
* Search and Apply Merge Blocks Keeping Partial Attributes Filter.

"""


@smproxy.filter(
    name="PVMergeBlocksEnhanced", label="Merge Blocks Keeping Partial Attributes"
)
@smhint.xml('<ShowInMenu category="4- Geos Utils"/>')
@smproperty.input(name="Input", port_index=0, label="Input")
@smdomain.datatype(dataTypes=["vtkMultiBlockDataSet"], composite_data_supported=True)
class PVMergeBlocksEnhanced(VTKPythonAlgorithmBase):

    def __init__(self: Self) -> None:
        """Merge filter that keep partial attributes using nan values."""
        super().__init__(
            nInputPorts=1,
            nOutputPorts=1,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkUnstructuredGrid",
        )

        # logger
        self.m_logger: Logger = getLogger("Merge Filter Enhanced")

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger
        self.Modified()

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

        self.m_logger.info(f"Apply filter {__name__}")
        try:
            input: Union[vtkMultiBlockDataSet, vtkCompositeDataSet] = self.GetInputData(
                inInfoVec, 0, 0
            )
            output: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData(outInfoVec)

            assert input is not None, "Input mesh is null."
            assert output is not None, "Output pipeline is null."

            output0 = mergeBlocks(input, True)
            output.ShallowCopy(output0)
            output.Modified()

            mess: str = f"Blocks were successfully merged together."
            self.m_logger.info(mess)
        except AssertionError as e:
            mess1: str = "Block merge failed due to:"
            self.m_logger.error(mess1)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess0: str = "Block merge failed due to:"
            self.m_logger.critical(mess0)
            self.m_logger.critical(e, exc_info=True)
            return 0
        return 1
