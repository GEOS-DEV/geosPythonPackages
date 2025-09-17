# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

from vtkmodules.vtkCommonDataModel import (
    vtkMultiBlockDataSet,
    vtkUnstructuredGrid,
)

from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.processing.ClipToMainFrame import ClipToMainFrame

__doc__ = """
Clip the input mesh to the main frame applying the correct LandmarkTransform

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVClipToMainFrame.
* Apply.

"""


@smproxy.filter( name="PVClipToMainFrame", label="Clip to the main frame" )
@smhint.xml( '<ShowInMenu category="4- Geos Utils"/>' )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype(
    dataTypes=[ "vtkMultiBlockDataSet", "vtkUnstructuredGrid" ],
    composite_data_supported=True,
)
class PVClipToMainFrame( VTKPythonAlgorithmBase ):

    def __init__( self ) -> None:
        """Init motherclass, filter and logger."""
        VTKPythonAlgorithmBase.__init__( self,
                                         nInputPorts=1,
                                         nOutputPorts=1,
                                         inputType="vtkDataObject",
                                         outputType="vtkDataObject" )

        self.__realFilter = ClipToMainFrame()
        if not self.__realFilter.logger.hasHandlers():
            self.__realFilter.setLoggerHandler( VTKHandler() )

    #ensure I/O consistency
    def RequestDataObject( self, request: vtkInformation, inInfoVec: list[ vtkInformationVector ],
                           outInfoVec: vtkInformationVector ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestDataObject.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outData = self.GetOutputData( outInfoVec, 0 )
        assert inData is not None
        if outData is None or ( not outData.IsA( inData.GetClassName() ) ):
            outData = inData.NewInstance()
            outInfoVec.GetInformationObject( 0 ).Set( outData.DATA_OBJECT(), outData )
        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestData( self, request: vtkInformation, inInfo: list[ vtkInformationVector ],
                     outInfo: vtkInformationVector ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData. Apply ClipToMainFrame filter.

        Args:
            request (vtkInformation): Request
            inInfo (list[vtkInformationVector]): Input objects
            outInfo (vtkInformationVector): Output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        inputMesh: vtkMultiBlockDataSet | vtkUnstructuredGrid = self.GetInputData( inInfo, 0, 0 )
        outputMesh: vtkMultiBlockDataSet | vtkUnstructuredGrid = self.GetOutputData( outInfo, 0 )

        print( inputMesh.GetClassName() )

        # struct
        self.__realFilter.SetInputData( inputMesh )
        self.__realFilter.ComputeTransform()
        self.__realFilter.Update()
        outputMesh.ShallowCopy( self.__realFilter.GetOutputDataObject( 0 ) )
        print( outputMesh.GetClassName() )

        return 1
