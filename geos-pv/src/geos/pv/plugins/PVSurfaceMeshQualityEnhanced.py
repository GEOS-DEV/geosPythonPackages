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

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
    vtkDataArraySelection,
)
from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid, )

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
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
    getTriangleQualityMeasure,
    getCommonPolygonQualityMeasure,
)
from geos.pv.utils.checkboxFunction import (  # type: ignore[attr-defined]
    createModifiedCallback, )
from geos.pv.utils.paraviewTreatments import getArrayChoices

__doc__ = """
Compute mesh quality metrics on surface meshes.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVSurfaceMeshQualityEnhanced.
* Select the input mesh.
* Select the metric to compute
* Apply the filter.

"""


@smproxy.filter( name="PVSurfaceMeshQualityEnhanced", label="Surface Mesh Quality Enhanced" )
@smhint.xml( '<ShowInMenu category="5- Geos QC"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVSurfaceMeshQualityEnhanced( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Merge collocated points."""
        super().__init__( nInputPorts=1, nOutputPorts=1, outputType="vtkUnstructuredGrid" )

        self._filename: Optional[ str ] = None
        self._saveToFile: bool = True
        self._blockIndex: int = 0
        # used to concatenate results if vtkMultiBlockDataSet
        self._metricsAll: list[ float ] = []
        self._commonMeshQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._commonCellQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._triangleQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._quadsQualityMetric: vtkDataArraySelection = vtkDataArraySelection()
        self._initQualityMetricSelection()

    def _initQualityMetricSelection( self: Self ) -> None:
        self._commonCellQualityMetric.RemoveAllArrays()
        self._commonCellQualityMetric.AddObserver(
            "ModifiedEvent",  # type: ignore[arg-type]
            createModifiedCallback( self ) )
        commonCellMetrics: set[ int ] = getCommonPolygonQualityMeasure()
        for measure in commonCellMetrics:
            self._commonCellQualityMetric.AddArray( getQualityMeasureNameFromIndex( measure ) )

        self._triangleQualityMetric.RemoveAllArrays()
        self._triangleQualityMetric.AddObserver(
            "ModifiedEvent",  # type: ignore[arg-type]
            createModifiedCallback( self ) )
        for measure in getTriangleQualityMeasure().difference( commonCellMetrics ):
            self._triangleQualityMetric.AddArray( getQualityMeasureNameFromIndex( measure ) )

        self._quadsQualityMetric.RemoveAllArrays()
        self._quadsQualityMetric.AddObserver(
            "ModifiedEvent",  # type: ignore[arg-type]
            createModifiedCallback( self ) )
        for measure in getQuadQualityMeasure().difference( commonCellMetrics ):
            self._quadsQualityMetric.AddArray( getQualityMeasureNameFromIndex( measure ) )

        otherMetrics: set[ int ] = getQualityMetricsOther()
        for measure in otherMetrics:
            self._commonMeshQualityMetric.AddArray( getQualityMeasureNameFromIndex( measure ) )

    @smproperty.dataarrayselection( name="CommonCellQualityMetric" )
    def a01SetCommonMetrics( self: Self ) -> vtkDataArraySelection:
        """Set polygon quality metrics selection."""
        return self._commonCellQualityMetric

    @smproperty.dataarrayselection( name="TriangleSpecificQualityMetric" )
    def a02SetTriangleMetrics( self: Self ) -> vtkDataArraySelection:
        """Set triangle quality metrics selection."""
        return self._triangleQualityMetric

    @smproperty.dataarrayselection( name="QuadSpecificQualityMetric" )
    def a03sSetQuadMetrics( self: Self ) -> vtkDataArraySelection:
        """Set quad quality metrics selection."""
        return self._quadsQualityMetric

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
    def b01SetSaveToFile( self: Self, saveToFile: bool ) -> None:
        """Setter to save the stats into a file.

        Args:
            saveToFile (bool): if True, a file will be saved.
        """
        if self._saveToFile != saveToFile:
            self._saveToFile = saveToFile
            self.Modified()

    @smproperty.stringvector( name="FilePath", label="File Path" )
    @smdomain.xml( """
                    <FileListDomain name="files" />
                    <Documentation>Output file path.</Documentation>
                    <Hints>
                        <FileChooser extensions="png" file_description="Output file." />
                        <AcceptAnyFile/>
                    </Hints>
                  """ )
    def b02SetFileName( self: Self, fname: str ) -> None:
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

    def Modified( self: Self ) -> None:
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
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )

    def _getQualityMetricsToUse( self: Self, selection: vtkDataArraySelection ) -> set[ int ]:
        """Get mesh quality metric indexes from user selection.

        Returns:
            list[int]: List of quality metric indexes
        """
        metricsNames: set[ str ] = getArrayChoices( selection )
        return { getQualityMeasureIndexFromName( name ) for name in metricsNames }

    def RequestData(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request
            inInfoVec (list[vtkInformationVector]): Input objects
            outInfoVec (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: vtkUnstructuredGrid = self.GetInputData( inInfoVec, 0, 0 )
        outputMesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( outInfoVec, 0 )
        assert inputMesh is not None, "Input server mesh is null."
        assert outputMesh is not None, "Output pipeline is null."

        triangleMetrics: set[ int ] = self._getQualityMetricsToUse( self._commonCellQualityMetric ).union(
            self._getQualityMetricsToUse( self._triangleQualityMetric ) )
        quadMetrics: set[ int ] = self._getQualityMetricsToUse( self._commonCellQualityMetric ).union(
            self._getQualityMetricsToUse( self._quadsQualityMetric ) )
        otherMetrics: set[ int ] = self._getQualityMetricsToUse( self._commonMeshQualityMetric )
        filter: MeshQualityEnhanced = MeshQualityEnhanced()
        filter.SetInputDataObject( inputMesh )
        filter.SetCellQualityMetrics( triangleMetrics=triangleMetrics, quadMetrics=quadMetrics )
        filter.SetOtherMeshQualityMetrics( otherMetrics )
        filter.Update()

        outputMesh.ShallowCopy( filter.GetOutputDataObject( 0 ) )

        # save to file if asked
        if self._saveToFile:
            stats: QualityMetricSummary = filter.GetQualityMetricSummary()
            self.saveFile( stats )
        self._blockIndex += 1
        return 1

    def saveFile( self: Self, stats: QualityMetricSummary ) -> None:
        """Export mesh quality metric summary file."""
        try:
            if self._filename is None:
                print( "Mesh quality summary report file path is undefined." )
                return
            # add index for multiblock meshes
            index: int = self._filename.rfind( '.' )
            filename: str = self._filename[ :index ] + f"_{self._blockIndex}" + self._filename[ index: ]
            fig = stats.plotSummaryFigure()
            fig.savefig( filename, dpi=150 )
            print( f"File {filename} was successfully written." )
        except Exception as e:
            print( "Error while exporting the file due to:" )
            print( str( e ) )
