# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self, Optional

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)

from vtkmodules.vtkFiltersVerdict import vtkMeshQuality
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkDataArraySelection,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths
update_paths()

from geos.mesh.model.QualityMetricSummary import QualityMetricSummary
from geos.mesh.stats.MeshQualityEnhanced import MeshQualityEnhanced

from geos.mesh.processing.meshQualityMetricHelpers import (
    getQualityMetricsOther,
    getQualityMeasureNameFromIndex,
    getQualityMeasureIndexFromName,
    getQuadQualityMeasure,
    getTetQualityMeasure,
    getPyramidQualityMeasure,
    getWedgeQualityMeasure,
    getHexQualityMeasure,
    getCommonPolyhedraQualityMeasure,
)
from geos.pv.utils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )
from geos.pv.utils.paraviewTreatments import getArrayChoices

__doc__ = """
Compute mesh quality metrics on volume meshes.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVVolumeMeshQualityEnhanced.
* Select the input mesh.
* Select the metric to compute
* Apply the filter.

"""

@smproxy.filter( name="PVVolumeMeshQualityEnhanced", label="Volume Mesh Quality Enhanced" )
@smhint.xml( '<ShowInMenu category="5- Geos QC"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid"],
    composite_data_supported=True,
)
class PVVolumeMeshQualityEnhanced(VTKPythonAlgorithmBase):
    def __init__(self:Self) ->None:
        """Merge collocated points."""
        super().__init__(nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid")

        self._filename: Optional[str] = None
        self._saveToFile: bool = True
        self._blockIndex: int = 0
        # used to concatenate results if vtkMultiBlockDataSet
        self._metricsAll: list[float] = []
        self._commonMeshQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._commonCellQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._tetQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._PyrQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._WedgeQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._HexQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._initQualityMetricSelection()

    def _initQualityMetricSelection(self: Self) ->None:
        self._commonCellQualityMetric.RemoveAllArrays()
        self._commonCellQualityMetric.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        commonCellMetrics: set[int] = getCommonPolyhedraQualityMeasure()
        for measure in commonCellMetrics:
            self._commonCellQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )

        self._tetQualityMetric.RemoveAllArrays()
        self._tetQualityMetric.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        for measure in getTetQualityMeasure().difference(commonCellMetrics):
            self._tetQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )

        self._PyrQualityMetric.RemoveAllArrays()
        self._PyrQualityMetric.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        for measure in getPyramidQualityMeasure().difference(commonCellMetrics):
            self._PyrQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )

        self._WedgeQualityMetric.RemoveAllArrays()
        self._WedgeQualityMetric.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        for measure in getWedgeQualityMeasure().difference(commonCellMetrics):
            self._WedgeQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )

        self._HexQualityMetric.RemoveAllArrays()
        self._HexQualityMetric.AddObserver( "ModifiedEvent", createModifiedCallback( self ) )  # type: ignore[arg-type]
        for measure in getHexQualityMeasure().difference(commonCellMetrics):
            self._HexQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )

        otherMetrics: set[int] = getQualityMetricsOther()
        for measure in otherMetrics:
            self._commonMeshQualityMetric.AddArray( getQualityMeasureNameFromIndex(measure) )


    @smproperty.dataarrayselection( name="CommonCellQualityMetric" )
    def a01SetCommonMetrics( self: Self ) -> vtkDataArraySelection:
        """Set polygon quality metrics selection."""
        return self._commonCellQualityMetric

    @smproperty.dataarrayselection( name="TetrahedronSpecificQualityMetric" )
    def a02SetTetMetrics( self: Self ) -> vtkDataArraySelection:
        """Set tetra quality metrics selection."""
        return self._tetQualityMetric

    @smproperty.dataarrayselection( name="PyramidSpecificQualityMetric" )
    def a03sSetPyrMetrics( self: Self ) -> vtkDataArraySelection:
        """Set Pyramid quality metrics selection."""
        return self._PyrQualityMetric

    @smproperty.dataarrayselection( name="WedgeSpecificQualityMetric" )
    def a03sSetWedgeMetrics( self: Self ) -> vtkDataArraySelection:
        """Set Wedge quality metrics selection."""
        return self._WedgeQualityMetric

    @smproperty.dataarrayselection( name="HexahedronSpecificQualityMetric" )
    def a03sSetHexMetrics( self: Self ) -> vtkDataArraySelection:
        """Set Hexahdron quality metrics selection."""
        return self._HexQualityMetric

    @smproperty.dataarrayselection( name="OtherMeshQualityMetric" )
    def a04SetOtherMeshMetrics( self: Self ) -> vtkDataArraySelection:
        """Set other mesh quality metrics selection."""
        return self._commonMeshQualityMetric

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
    def b01SetSaveToFile( self: Self, saveToFile: bool) -> None:
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
                        <FileChooser extensions="png" file_description="Output file." />
                        <AcceptAnyFile/>
                    </Hints>
                  """)
    def b02SetFileName(self: Self, fname :str) -> None:
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
    def b03GroupAdvancedOutputParameters( self: Self ) -> None:
        """Organize groups."""
        self.Modified()

    def Modified(self: Self) ->None:
        """Overload Modified method to reset _blockIndex."""
        self._blockIndex = 0
        super().Modified()

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
        inputMesh: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData(outInfoVec, 0)
        assert inputMesh is not None, "Input server mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        tetraMetrics: set[int] = self._getQualityMetricsToUse(self._commonCellQualityMetric).union(self._getQualityMetricsToUse(self._tetQualityMetric))
        pyrMetrics: set[int] = self._getQualityMetricsToUse(self._commonCellQualityMetric).union(self._getQualityMetricsToUse(self._PyrQualityMetric))
        wedgeMetrics: set[int] = self._getQualityMetricsToUse(self._commonCellQualityMetric).union(self._getQualityMetricsToUse(self._PyrQualityMetric))
        hexaMetrics: set[int] = self._getQualityMetricsToUse(self._commonCellQualityMetric).union(self._getQualityMetricsToUse(self._PyrQualityMetric))
        otherMetrics: set[int] = self._getQualityMetricsToUse(self._commonMeshQualityMetric)
        filter: MeshQualityEnhanced = MeshQualityEnhanced()
        filter.SetInputDataObject(inputMesh)
        filter.SetCellQualityMetrics(tetraMetrics=tetraMetrics, pyramidMetrics=pyrMetrics, wedgeMetrics=wedgeMetrics, hexaMetrics=hexaMetrics)
        filter.SetOtherMeshQualityMetrics(otherMetrics)
        filter.Update()

        outputMesh.ShallowCopy(filter.GetOutputDataObject(0))

        # save to file if asked
        if self._saveToFile:
            stats: QualityMetricSummary = filter.GetQualityMetricSummary()
            self._saveFile(stats)
        self._blockIndex += 1
        return 1

    def _getQualityMetricsToUse(self :Self, selection: vtkDataArraySelection) -> set[int]:
        """Get mesh quality metric indexes from user selection.

        Returns:
            list[int]: list of quality metric indexes
        """
        metricsNames: set[str] = getArrayChoices(selection)
        return {getQualityMeasureIndexFromName(name) for name in metricsNames}

    def _saveFile(self: Self, stats: QualityMetricSummary) ->None:
        """Export mesh quality metric summary file."""
        try:
            # add index for multiblock meshes
            index: int = self._filename.rfind('.')
            filename: str = self._filename[:index] + f"_{self._blockIndex}" + self._filename[index:]
            fig = stats.plotSummaryFigure()
            fig.savefig(filename, dpi=150)
            print(f"File {filename} was successfully written.")
        except Exception as e:
            print("Error while exporting the file due to:")
            print(str(e))

