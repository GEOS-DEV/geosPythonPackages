# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
from pathlib import Path

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/util/vtkAlgorithm.py
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler,
) # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

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
    dataTypes=[ "vtkMultiBlockDataSet"],
    composite_data_supported=True,
)
class PVClipToMainFrame( VTKPythonAlgorithmBase ):

    def __init__(self):
        VTKPythonAlgorithmBase.__init__(self,
                                        nInputPorts=1,
                                        nOutputPorts=1,
                                        inputType="vtkMultiBlockDataSet",
                                        outputType="vtkMultiBlockDataSet"
                                          )
        
        self.__realFilter = ClipToMainFrame()
        if not self.__realFilter.logger.hasHandlers():
            self.__realFilter.setLoggerHandler( VTKHandler() )
        
    def RequestData(self, request : vtkInformation, inInfo: list[vtkInformationVector],
                     outInfo:vtkInformationVector) -> int:
        inputMesh: vtkMultiBlockDataSet | vtkUnstructuredGrid = self.GetInputData(inInfo,0,0)
        outputMesh : vtkMultiBlockDataSet | vtkUnstructuredGrid = self.GetOutputData(outInfo,0)
        
        # outputMesh.ShallowCopy(inputMesh)
        # struct
        self.__realFilter.logger.info(f"size Info {outInfo.GetNumberOfInformationObjects()}")
        def logInfos(obj, logger, header):
            logger.info(f"--{header}--")
            logger.info(f"mesh has {obj.GetNumberOfPoints()} points")
            logger.info(f"mesh has {obj.GetNumberOfCells()} cells")
            logger.info(f"type {obj.GetClassName()}")

        self.__realFilter.SetInputData(inputMesh)
        logInfos(inputMesh, self.__realFilter.logger,"input")

        self.__realFilter.ComputeTransform()
        self.__realFilter.Update()
 
        outputMesh.ShallowCopy( self.__realFilter.GetOutputDataObject(0) )

        logInfos(outputMesh, self.__realFilter.logger,"output")

        return 1

        
