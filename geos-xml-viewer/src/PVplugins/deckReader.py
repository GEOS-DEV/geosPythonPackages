# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Lionel Untereiner
from typing import Self

from paraview.util.vtkAlgorithm import smdomain, smhint, smproperty, smproxy
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkPartitionedDataSetCollection

paraview_plugin_version = "0.1.0"


@smproxy.reader(
    name="PythonGeosDeckReader",
    label="Python-based Deck Reader for GEOS",
    extensions="xml",
    file_description="XML files",
)
class PVGeosDeckReader(VTKPythonAlgorithmBase):
    def __init__(self: Self) -> Self:
        """Constructor of the reader."""
        VTKPythonAlgorithmBase.__init__(
            self,
            nInputPorts=0,
            nOutputPorts=1,
            outputType="vtkPartitionedDataSetCollection",
        )  # type: ignore
        self.__filename: str
        from geos_xml_viewer.filters.geosDeckReader import GeosDeckReader

        self.__realAlgorithm = GeosDeckReader()

    @smproperty.stringvector(name="FileName")  # type: ignore
    @smdomain.filelist()  # type: ignore
    @smhint.filechooser(extensions="xml", file_description="GEOS XML files")  # type: ignore
    def SetFileName(self: Self, name: str) -> None:
        """Specify filename for the file to read.

        Args:
            name (str): filename
        """
        if self.__filename != name:
            self.__filename = name
            self.__realAlgorithm.SetFileName(self.__filename)
            self.__realAlgorithm.Update()
            self.Modified()

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[vtkInformationVector],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """RequestData function of the vtk pipeline.

        Args:
            request (vtkInformation): information about the request
            inInfoVec (list[vtkInformationVector]): input information vector
            outInfoVec (vtkInformationVector): output information vector

        Raises:
            RuntimeError: Raises an error if no filename is specified

        Returns:
            int: Returns 1 if the pipeline is successful
        """
        if self.__filename is None:
            raise RuntimeError("No filename specified")

        output = vtkPartitionedDataSetCollection.GetData(inInfoVec, 0)
        output.ShallowCopy(self.__realAlgorithm.GetOutputDataObject(0))
        return 1
