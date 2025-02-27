# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Self

import vtkmodules.all as vtk
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase

from geos_xml_viewer.algorithms.deck import SimulationDeck, build_model, read


class GeosDeckReader(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> Self:
        """VTK GEOS deck reader filter."""
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSetCollection",
        )  # type: ignore
        self.__filename: str = ""
        self.__attributeName: str = ""
        self.__simulationDeck: SimulationDeck

    def SetFileName(self: Self, name: str) -> None:
        """Set the filename.

        Args:
            name (str): filename
        """
        if name != self.__filename:
            self.__filename = name
            self.Modified()

    def GetFileName(self: Self) -> str:
        """Get the filename."""
        return self.__filename

    def SetAttributeName(self: Self, name: str) -> None:
        """Set the attribute name.

        Args:
            name (str): attribute name
        """
        if name != self.__attributeName:
            self.__attributeName = name
            self.Modified()

    def GetAttributeName(self: Self) -> str:
        """Get the attribute name."""
        return self.__attributeName

    def RequestData(
        self: Self,
        request: vtk.vtkInformation,
        inInfoVec: vtk.vtkInformationVector,
        outInfoVec: vtk.vtkInformationVector,
    ) -> int:
        """RequestData function of the vtk pipeline.

        Args:
            request (vtkInformation): information about the request
            inInfoVec (vtkInformationVector): input information vector
            outInfoVec (vtkInformationVector): output information vector

        Returns:
            int: Returns 1 if the pipeline is successful
        """
        self.__simulationDeck = read(self.__filename)
        opt = vtk.vtkPartitionedDataSetCollection.GetData(outInfoVec)

        output = vtk.vtkPartitionedDataSetCollection()
        build_model(self.__simulationDeck, output, self.__attributeName)

        opt.ShallowCopy(output)

        return 1
