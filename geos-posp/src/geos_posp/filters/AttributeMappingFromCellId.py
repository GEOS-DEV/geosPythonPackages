# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid

from geos_posp.processing.vtkUtils import createAttribute, getArrayInObject
from geos_posp.utils.Logger import Logger, getLogger

__doc__ = """
AttributeMappingFromCellId module is a vtk filter that transfer a attribute from a
server mesh to a client mesh.

Filter input and output types are vtkPolyData.

To use the filter:

.. code-block:: python

    from filters.AttributeMappingFromCellId import AttributeMappingFromCellId

    # filter inputs
    logger :Logger
    input :vtkPolyData
    TransferAttributeName : str

    # instanciate the filter
    filter :AttributeMappingFromCellId = AttributeMappingFromCellId()
    # set the logger
    filter.SetLogger(logger)
    # set input data object
    filter.SetInputDataObject(input)
    # set Attribute to transfer
    filter.SetTransferAttributeName(AttributeName)
    # set Attribute to compare
    filter.SetIDAttributeName(AttributeName)
    # do calculations
    filter.Update()
    # get output object
    output :vtkPolyData = filter.GetOutputDataObject(0)
    # get created attribute names
    newAttributeNames :set[str] = filter.GetNewAttributeNames()
"""


class AttributeMappingFromCellId(VTKPythonAlgorithmBase):

    def __init__(self: Self) -> None:
        """Map the properties of a source mesh to a receiver mesh."""
        super().__init__(
            nInputPorts=2, nOutputPorts=1, outputType="vtkUnstructuredGrid"
        )

        # Transfer Attribute name
        self.m_transferedAttributeName: str = ""
        # ID Attribute name
        self.m_idAttributeName: str = ""
        # logger
        self.m_logger: Logger = getLogger("Attribute Mapping From Cell Id Filter")

    def SetLogger(self: Self, logger: Logger) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger
        self.Modified()

    def SetTransferAttributeName(self: Self, name: str) -> None:
        """Set Transfer attribute name."""
        self.m_transferedAttributeName = name
        self.Modified()

    def SetIDAttributeName(self: Self, name: str) -> None:
        """Set ID attribute name."""
        self.m_idAttributeName = name
        self.Modified()

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
        inData = self.GetInputData(inInfoVec, 0, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
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
            serverMesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData(inInfoVec[0])
            clientMesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData(inInfoVec[1])
            outData: vtkUnstructuredGrid = self.GetOutputData(outInfoVec, 0)

            assert serverMesh is not None, "Server mesh is null."
            assert clientMesh is not None, "Client mesh is null."
            assert outData is not None, "Output pipeline is null."

            outData.ShallowCopy(clientMesh)

            cellIdMap: npt.NDArray[np.int64] = self.getCellMap(serverMesh, clientMesh)

            attributeArrayServer: npt.NDArray[np.float64] = getArrayInObject(
                serverMesh, self.m_transferedAttributeName, False
            )
            attributeArrayClient: npt.NDArray[np.float64] = np.full_like(
                attributeArrayServer, np.nan
            )
            for i in range(serverMesh.GetNumberOfCells()):
                k: int = cellIdMap[i]
                attributeArrayClient[k] = attributeArrayServer[i]
            createAttribute(
                clientMesh,
                attributeArrayClient,
                self.m_transferedAttributeName,
                (),
                False,
            )
            outData.Modified()

        except AssertionError as e:
            mess1: str = "Attribute mapping failed due to:"
            self.m_logger.error(mess1)
            self.m_logger.error(e, exc_info=True)
            return 0
        except Exception as e:
            mess0: str = "Attribute mapping failed due to:"
            self.m_logger.critical(mess0)
            self.m_logger.critical(e, exc_info=True)
            return 0
        mess2: str = (
            f"Attribute {self.m_transferedAttributeName} was successfully transferred."
        )
        self.m_logger.info(mess2)

        return 1

    def getCellMap(
        self: Self, serverMesh: vtkUnstructuredGrid, clientMesh: vtkUnstructuredGrid
    ) -> npt.NDArray[np.int64]:
        """Compute the mapping between both mesh from cell ids.

        Args:
            serverMesh (vtkUnstructuredGrid): server mesh
            clientMesh (vtkUnstructuredGrid): client mesh

        Returns:
            npt.NDArray[np.int64]: the map where for each cell index of the
                client mesh, the cell index of the server mesh.

        """
        cellIdArrayServer: npt.NDArray[np.int64] = getArrayInObject(
            serverMesh, self.m_idAttributeName, False
        ).astype(int)
        cellIdArrayClient: npt.NDArray[np.int64] = getArrayInObject(
            clientMesh, self.m_idAttributeName, False
        ).astype(int)
        cellMap: npt.NDArray[np.int64] = np.zeros(serverMesh.GetNumberOfCells()).astype(
            int
        )
        for i, cellId in enumerate(cellIdArrayServer):
            k: int = np.argwhere(cellIdArrayClient == cellId)[0]
            cellMap[i] = k
        return cellMap
