# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys

import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

dir_path = os.path.dirname( os.path.realpath( __file__ ) )
parent_dir_path = os.path.dirname( dir_path )
if parent_dir_path not in sys.path:
    sys.path.append( parent_dir_path )

import PVplugins  # noqa: F401

from geos.utils.GeosOutputsConstants import (
    GeosMeshOutputsEnum,
    getAttributeToTransferFromInitialTime,
)
from geos.utils.Logger import ERROR, INFO, Logger, getLogger
from geos_posp.filters.GeosBlockExtractor import GeosBlockExtractor
from geos_posp.filters.GeosBlockMerge import GeosBlockMerge
from geos.mesh.utils.arrayModifiers import (
    copyAttribute,
    createCellCenterAttribute,
)
from geos_posp.visu.PVUtils.paraviewTreatments import getTimeStepIndex
from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smhint, smproperty, smproxy,
)

__doc__ = """
PVExtractMergeBlocksVolumeSurface is a Paraview plugin that allows to merge
ranks of a Geos output objects containing a volumic mesh and surfaces.

Input and output types are vtkMultiBlockDataSet.

This filter results in 2 output pipelines:

* first pipeline contains the volume mesh. If multiple regions were defined in
    the volume mesh, they are preserved as distinct blocks.
* second pipeline contains surfaces. If multiple surfaces were used, they are
    preserved as distinct blocks.

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVExtractMergeBlocksVolumeSurface.
* Select the Geos output .pvd file loaded in Paraview.
* Search and Apply PVExtractMergeBlocksVolumeSurface Filter.

"""


@smproxy.filter(
    name="PVExtractMergeBlocksVolumeSurface",
    label="Geos Extract And Merge Blocks - Volume/Surface",
)
@smhint.xml( """
    <ShowInMenu category="2- Geos Output Mesh Pre-processing"/>
    <OutputPort index="0" name="VolumeMesh"/>
    <OutputPort index="1" name="Surfaces"/>
    """ )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVExtractMergeBlocksVolumeSurface( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to extract and merge ranks from Geos output Mesh.

        To apply in the case of output ".pvd" file contains Volume and Fault
        elements.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=2,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        #: all time steps from input
        self.m_timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )
        #: displayed time step in the IHM
        self.m_currentTime: float = 0.0
        #: time step index of displayed time step
        self.m_currentTimeStepIndex: int = 0
        #: request data processing step - incremented each time RequestUpdateExtent is called
        self.m_requestDataStep: int = -1

        # saved object at initial time step
        self.m_outputT0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        # set logger
        self.m_logger: Logger = getLogger( "Extract and merge block Filter" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set filter logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkMultiBlockDataSet" )
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
        return 1

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
        inData = self.GetInputData( inInfoVec, 0, 0 )
        outDataCells = self.GetOutputData( outInfoVec, 0 )
        outDataFaults = self.GetOutputData( outInfoVec, 1 )
        assert inData is not None
        if outDataCells is None or ( not outDataCells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataCells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 0 ).Set( outDataCells.DATA_OBJECT(), outDataCells )  # type: ignore
        if outDataFaults is None or ( not outDataFaults.IsA( "vtkMultiBlockDataSet" ) ):
            outDataFaults = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 1 ).Set( outDataFaults.DATA_OBJECT(), outDataFaults )  # type: ignore

        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestUpdateExtent(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestUpdateExtent.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]
        # get displayed time step info before updating time
        if self.m_requestDataStep == -1:
            self.m_logger.info( f"Apply filter {__name__}" )
            self.m_timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS() )  # type: ignore
            self.m_currentTime = inInfo.GetInformationObject( 0 ).Get( executive.UPDATE_TIME_STEP() )  # type: ignore
            self.m_currentTimeStepIndex = getTimeStepIndex( self.m_currentTime, self.m_timeSteps )
        # update requestDataStep
        self.m_requestDataStep += 1

        # update time according to requestDataStep iterator
        inInfo.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),  # type: ignore
            self.m_timeSteps[ self.m_requestDataStep ],
        )
        outInfoVec.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),  # type: ignore
            self.m_timeSteps[ self.m_requestDataStep ],
        )

        # update all objects according to new time info
        self.Modified()
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,
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
        try:
            input: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfoVec[ 0 ] )
            outputCells: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )
            outputFaults: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 1 )

            assert input is not None, "Input MultiBlockDataSet is null."
            assert outputCells is not None, "Output volum mesh is null."
            assert outputFaults is not None, "Output surface mesh is null."

            # time controller
            executive = self.GetExecutive()
            if self.m_requestDataStep == 0:
                # first time step
                # do extraction and merge (do not display phase info)
                outputFaults0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
                self.m_logger.setLevel( ERROR )
                self.doExtractAndMerge( input, self.m_outputT0, outputFaults0 )
                self.m_logger.setLevel( INFO )
                request.Set( executive.CONTINUE_EXECUTING(), 1 )  # type: ignore

            if self.m_requestDataStep >= self.m_currentTimeStepIndex:
                # displayed time step, no need to go further
                request.Remove( executive.CONTINUE_EXECUTING() )  # type: ignore
                # reinitialize requestDataStep if filter is recalled later
                self.m_requestDataStep = -1
                # do extraction and merge
                self.doExtractAndMerge( input, outputCells, outputFaults )
                # copy attributes from initial time step
                for (
                        attributeName,
                        attributeNewName,
                ) in getAttributeToTransferFromInitialTime().items():
                    copyAttribute( self.m_outputT0, outputCells, attributeName, attributeNewName )
                # create elementCenter attribute if needed
                cellCenterAttributeName: str = ( GeosMeshOutputsEnum.ELEMENT_CENTER.attributeName )
                createCellCenterAttribute( outputCells, cellCenterAttributeName )

        except AssertionError as e:
            mess: str = "Block extraction and merge failed due to:"
            self.m_logger.error( mess )
            self.m_logger.error( str( e ) )
            return 0
        except Exception as e:
            mess1: str = "Block extraction and merge failed due to:"
            self.m_logger.critical( mess1 )
            self.m_logger.critical( e, exc_info=True )
            return 0

        return 1

    def doExtractAndMerge(
        self: Self,
        input: vtkMultiBlockDataSet,
        outputCells: vtkMultiBlockDataSet,
        outputFaults: vtkMultiBlockDataSet,
    ) -> bool:
        """Apply block extraction and merge.

        Args:
            input (vtkMultiBlockDataSet): input multi block
            outputCells (vtkMultiBlockDataSet): output volume mesh
            outputFaults (vtkMultiBlockDataSet): output surface mesh

        Returns:
            bool: True if extraction and merge successfully eneded, False otherwise
        """
        # extract blocks
        blockExtractor: GeosBlockExtractor = GeosBlockExtractor()
        blockExtractor.SetLogger( self.m_logger )
        blockExtractor.SetInputDataObject( input )
        blockExtractor.ExtractFaultsOn()
        blockExtractor.Update()

        # recover output objects from GeosBlockExtractor filter
        volumeBlockExtracted: vtkMultiBlockDataSet = blockExtractor.getOutputVolume()
        faultBlockExtracted: vtkMultiBlockDataSet = blockExtractor.getOutputFaults()

        # rename attributes and merge blocks
        assert volumeBlockExtracted is not None, "Extracted Volume mesh is null."
        outputCells.ShallowCopy( self.mergeBlocksFilter( volumeBlockExtracted, False ) )
        outputCells.Modified()

        assert faultBlockExtracted is not None, "Extracted Fault mesh is null."
        outputFaults.ShallowCopy( self.mergeBlocksFilter( faultBlockExtracted, True ) )
        outputFaults.Modified()

        self.m_logger.info( "Volume blocks were successfully splitted from surfaces" +
                            " and ranks were merged together." )
        return True

    def mergeBlocksFilter( self: Self,
                           input: vtkMultiBlockDataSet,
                           convertSurfaces: bool = False ) -> vtkMultiBlockDataSet:
        """Apply vtk merge block filter on input multi block mesh.

        Args:
            input (vtkMultiBlockDataSet): multiblock mesh to merge
            convertSurfaces (bool, optional): True to convert surface from vtkUnstructuredGrid to
                vtkPolyData. Defaults to False.

        Returns:
            vtkMultiBlockDataSet: Multiblock mesh composed of internal merged blocks.
        """
        mergeBlockFilter = GeosBlockMerge()
        mergeBlockFilter.SetLogger( self.m_logger )
        mergeBlockFilter.SetInputDataObject( input )
        if convertSurfaces:
            mergeBlockFilter.ConvertSurfaceMeshOn()
        else:
            mergeBlockFilter.ConvertSurfaceMeshOff()
        mergeBlockFilter.Update()
        mergedBlocks: vtkMultiBlockDataSet = mergeBlockFilter.GetOutputDataObject( 0 )
        assert mergedBlocks is not None, "Final merged MultiBlockDataSet is null."
        return mergedBlocks
