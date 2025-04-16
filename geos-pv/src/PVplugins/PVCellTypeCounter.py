# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkPointSet,
    vtkTable,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths
update_paths()

from geos.mesh.stats.CellTypeCounter import CellTypeCounter
from geos.mesh.model.CellTypeCounts import CellTypeCounts

__doc__ = """
Compute cell type counts. Counts are dumped in to Output message window and can be exporter in a file.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVCellTypeCounter.
* Select the input mesh.
* Apply the filter.

"""

@smproxy.filter( name="PVCellTypeCounter", label="Cell Type Counter" )
@smhint.xml( '<ShowInMenu category="5- Geos QC"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkPointSet"],
    composite_data_supported=True,
)
class PVCellTypeCounter(VTKPythonAlgorithmBase):
    def __init__(self:Self) ->None:
        """Merge collocated points."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkPointSet")

        self._filename = None
        self._saveToFile = True

    @smproperty.intvector(
        name="SetSaveToFile",
        label="Save to file",
        default_values=0,
        panel_visibility="default",
    )
    @smdomain.xml( """
                    <BooleanDomain name="SetSaveToFile"/>
                    <Documentation>
                        Specify if mesh statistics are dumped into a file.
                    </Documentation>
                  """ )
    def SetSaveToFile( self: Self, saveToFile: bool) -> None:
        """Setter to save the stats into a file.

        Args:
            saveToFile (bool): if True, a file will be saved.
        """
        if self._saveToFile != saveToFile:
            self._saveToFile = saveToFile
            self.Modified()

    @smproperty.stringvector(name="FilePath", label="File Path")
    @smdomain.xml( """
                    <FileListDomain name="files" />
                    <Documentation>Output file path.</Documentation>
                    <Hints>
                        <FileChooser extensions="txt" file_description="Output text file." />
                        <AcceptAnyFile/>
                    </Hints>
                  """)
    def SetFileName(self: Self, fname :str) -> None:
        """Specify filename for the filter to write.

        Args:
            fname (str): file path
        """
        if self._filename != fname:
            self._filename = fname
            self.Modified()

    @smproperty.xml( """
                    <PropertyGroup
                        panel_visibility="advanced">
                        <Property name="FilePath"/>
                        <Hints>
                            <PropertyWidgetDecorator type="GenericDecorator"
                            mode="visibility"
                            property="SetSaveToFile"
                            value="1" />
                        </Hints>
                    </PropertyGroup>
                    """ )
    def d09GroupAdvancedOutputParameters( self: Self ) -> None:
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
        inData = self.GetInputData(inInfoVec, 0, 0)
        outData = self.GetOutputData(outInfoVec, 0)
        assert inData is not None
        if outData is None or (not outData.IsA(inData.GetClassName())):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject(0).Set(outData.DATA_OBJECT(), outData)
        return super().RequestDataObject(request, inInfoVec, outInfoVec)

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
        inputMesh: vtkPointSet = self.GetInputData( inInfoVec, 0, 0 )
        output: vtkTable = self.GetOutputData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert output is not None, "Output pipeline is null."

        output.ShallowCopy(inputMesh)
        filter: CellTypeCounter = CellTypeCounter()
        filter.SetInputDataObject(inputMesh)
        filter.Update()
        card: CellTypeCounts = filter.GetCellTypeCounts()
        print(card.print())

        if self._saveToFile:
            try:
                with open(self._filename, 'w') as fout:
                    fout.write(card.print())
                    print(f"File {self._filename} was successfully written.")
            except Exception as e:
                print("Error while exporting the file dur to:")
                print(str(e))
        return 1
