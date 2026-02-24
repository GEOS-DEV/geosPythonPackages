# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path
from typing_extensions import Self, Optional

from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy )
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import VTKHandler  # type: ignore[import-not-found]
# source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from geos.processing.pre_processing.TetQualityAnalysis import TetQualityAnalysis
from geos.pv.utils.details import FilterCategory

__doc__ = f"""
Tetrahedra QC is a ParaView plugin filter that analyze and compare the tetrahedras of two given vtkUnstructured grid datasets.

A figure with relevant quality metrics is saved at the end of the process for a visual comparison.

To use it:

* Load the plugin in ParaView: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/qc/PVTetQualityAnalysis
* Select the first dataset
* Select the filter: Filters > { FilterCategory.QC.value } > Tetrahedras QC
* In the dialog box, select the `mesh 1` and the `mesh 2`
* Change the output filename if needed
* Apply
"""


@smproxy.filter( name="PVTetQualityAnalysis", label="Tetrahedra QC" )
@smhint.xml( f'<ShowInMenu category="{ FilterCategory.QC.value }"/>' )
@smproperty.input( name="inputMesh", port_index=0, label="mesh 1" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
@smproperty.input( name="inputMesh2", port_index=1, label="mesh 2" )
@smdomain.datatype(
    dataTypes=[ "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVTetQualityAnalysis( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """QC analysis of the tetrahedras from two meshes."""
        super().__init__( nInputPorts=2, inputType="vtkObject" )

        self._filename: Optional[ str ] = None
        self._meshes: dict[ str, vtkUnstructuredGrid ] = {}
        self._outputFilename: bool = True

    @smproperty.stringvector( name="FilePath", label="File Path" )
    @smdomain.xml( """
                    <FileListDomain name="files" />
                    <Documentation>Output file path.</Documentation>
                    <Hints>
                        <FileChooser extensions="png" file_description="Output plot file." />
                        <AcceptAnyFile/>
                    </Hints>
                  """ )
    def SetFileName( self: Self, fname: str ) -> None:
        """Specify filename for the output figure.

        Args:
            fname (str): File path
        """
        if self._filename != fname:
            self._filename = fname
        self.Modified()

    def RequestData(
        self: Self,
        request: vtkInformation,  #noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): Request.
            inInfoVec (list[vtkInformationVector]): Input objects.
            outInfoVec (vtkInformationVector): Output objects.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        for n in range( 2 ):
            self._meshes[ str( n ) ] = self.GetInputData( inInfoVec, n, 0 )

        tetQualityAnalysisFilter: TetQualityAnalysis = TetQualityAnalysis( self._meshes, True )

        if len( tetQualityAnalysisFilter.logger.handlers ) == 0:
            tetQualityAnalysisFilter.setLoggerHandler( VTKHandler() )

        try:
            tetQualityAnalysisFilter.setFilename( self._filename )
            tetQualityAnalysisFilter.applyFilter()
        except Exception as e:
            tetQualityAnalysisFilter.logger.error( f' FATAL ERROR due to:\n{e}' )

        return 1
