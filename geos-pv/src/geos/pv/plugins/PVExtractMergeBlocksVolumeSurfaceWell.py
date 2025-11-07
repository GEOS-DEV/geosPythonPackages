# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import sys
import logging
import numpy as np
import numpy.typing as npt

from pathlib import Path
from typing_extensions import Self

# update sys.path to load all GEOS Python Package dependencies
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.processing.post_processing.GeosBlockExtractor import GeosBlockExtractor
from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge

from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import (
    copyAttribute,
    createCellCenterAttribute
)
from geos.mesh.utils.multiblockHelpers import getBlockNames

from geos.utils.GeosOutputsConstants import (
    GeosMeshOutputsEnum,
    GeosDomainNameEnum,
    getAttributeToTransferFromInitialTime
)

from geos.pv.utils.paraviewTreatments import getTimeStepIndex

from vtkmodules.vtkCommonCore import ( vtkInformation, vtkInformationVector )
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smproperty, smproxy
)
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler
)  # source: https://github.com/Kitware/ParaView/blob/master/Wrapping/Python/paraview/detail/loghandler.py

__doc__ = """
PVGeosBlockExtractAndMerge is a Paraview plugin that:
    Allows to extract domains (volume, fault and well) from a GEOS output multiBlockDataSet mesh
    Acts on each region of a GEOS output domain (volume, fault, wells) to:
        Merge Ranks
        Identify "Fluids" and "Rock" phases
        Rename "Rock" attributes depending on the phase they refer to for more clarity
        Convert volume meshes to surface if needed
        Copy "geomechanics" attributes from the initial timestep to the current one if their exist

This filter results in 3 output pipelines with the vtkMultiBlockDataSet:
    "Volume" contains the volume domain
    "Fault" contains the fault domain if it exist
    "Well" contains the well domain if it exist

Input and output meshes are vtkMultiBlockDataSet.

.. Important::
    The input mesh must be an output of a GEOS simulation or contain at least three blocks labeled with the same domain names:
        "CellElementRegion" for volume domain
        "SurfaceElementRegion" for fault domain if the input contains fault
        "WellElementRegion" for well domain if the input contains well
        See more https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/ElementRegions.html?_sm_au_=iVVT5rrr5fN00R8sQ0WpHK6H8sjL6#xml-element-elementregions
    The filter detected automatically the three domains. If one of them if not in the input mesh, the associated output pipeline will be empty

To use it:

* Load the module in Paraview: Tools>Manage Plugins...>Load new>PVGeosBlockExtractAndMerge.
* Select the Geos output .pvd file loaded in Paraview.
* Search and Apply PVGeosBlockExtractAndMerge Filter.
"""

loggerTitle: str = "Extract & Merge GEOS Block"


@smproxy.filter(
    name="PVGeosBlockExtractAndMerge",
    label="Geos Extract and Merge Blocks",
)
@smproperty.xml( """
    <OutputPort index="0" name="Volume"/>
    <OutputPort index="1" name="Fault"/>
    <OutputPort index="2" name="Well"/>
    <Hints>
        <ShowInMenu category="2- Geos Output Mesh Pre-processing"/>
        <View type="RenderView" port="0"/>
        <View type="None" port="1"/>
        <View type="None" port="2"/>
    </Hints>
    """ )
@smproperty.input( name="Input", port_index=0 )
@smdomain.datatype( dataTypes=[ "vtkMultiBlockDataSet" ], composite_data_supported=True )
class PVGeosBlockExtractAndMerge( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Paraview plugin to extract and merge ranks from Geos output Mesh.

        To apply in the case of output ".pvd" file contains Volume, Fault and
        Well elements.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=3,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        self.extractFault: bool = False
        self.extractWell: bool = False

        #: all time steps from input
        self.m_timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )
        #: displayed time step in the IHM
        self.m_currentTime: float = 0.0
        #: time step index of displayed time step
        self.m_currentTimeStepIndex: int = 0
        #: request data processing step - incremented each time RequestUpdateExtent is called
        self.m_requestDataStep: int = -1

        self.outputCellsT0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        self.logger = logging.getLogger( loggerTitle )
        self.logger.setLevel( logging.INFO )
        self.logger.addHandler( VTKHandler() )

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
        outDataWells = self.GetOutputData( outInfoVec, 2 )
        assert inData is not None
        if outDataCells is None or ( not outDataCells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataCells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 0 ).Set(
                outDataCells.DATA_OBJECT(),
                outDataCells  # type: ignore
            )

        if outDataFaults is None or ( not outDataFaults.IsA( "vtkMultiBlockDataSet" ) ):
            outDataFaults = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 1 ).Set(
                outDataFaults.DATA_OBJECT(),
                outDataFaults  # type: ignore
            )

        if outDataWells is None or ( not outDataWells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataWells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 2 ).Set(
                outDataWells.DATA_OBJECT(),
                outDataWells  # type: ignore
            )

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
            self.m_timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS()  # type: ignore
                                                                    )
            self.m_currentTime = inInfo.GetInformationObject( 0 ).Get( executive.UPDATE_TIME_STEP()  # type: ignore
                                                                      )
            self.m_currentTimeStepIndex = getTimeStepIndex( self.m_currentTime, self.m_timeSteps )
        # update requestDataStep
        self.m_requestDataStep += 1

        # update time according to requestDataStep iterator
        inInfo.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),
            self.m_timeSteps[ self.m_requestDataStep ]  # type: ignore
        )
        outInfoVec.GetInformationObject( 0 ).Set(
            executive.UPDATE_TIME_STEP(),
            self.m_timeSteps[ self.m_requestDataStep ]  # type: ignore
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
        self.logger.info( f"Apply plugin { self.logger.name }." )
        print(self.m_requestDataStep)
        try:
            inputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfoVec[ 0 ] )

            # Time controller, only the first and the current time step are computed
            executive = self.GetExecutive()
            if self.m_requestDataStep == 0:
                blockNames: list[ str ]  = getBlockNames( inputMesh )
                if GeosDomainNameEnum.VOLUME_DOMAIN_NAME.value in blockNames:
                    self.extractFault = True

                if GeosDomainNameEnum.WELL_DOMAIN_NAME.value in blockNames:
                    self.extractWell = True

                outputFaultsT0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
                outputWellsT0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
                self.doExtractAndMerge( inputMesh, self.outputCellsT0, outputFaultsT0, outputWellsT0 )
                request.Set( executive.CONTINUE_EXECUTING(), 1 ) # type: ignore
            if self.m_requestDataStep == self.m_currentTimeStepIndex:
                outputCells: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )
                outputFaults: vtkMultiBlockDataSet
                outputWells: vtkMultiBlockDataSet
                if self.extractFault:
                    outputFaults = self.GetOutputData( outInfoVec, 1 )
                else:
                    outputFaults = vtkMultiBlockDataSet()
                    outInfoVec.GetInformationObject( 1 ).Remove( vtkMultiBlockDataSet().DATA_OBJECT() )

                if self.extractWell:
                    outputWells = self.GetOutputData( outInfoVec, 2 )
                else:
                    outputWells = vtkMultiBlockDataSet()
                    outInfoVec.GetInformationObject( 2 ).Remove( vtkMultiBlockDataSet().DATA_OBJECT() )

                self.doExtractAndMerge( inputMesh, outputCells, outputFaults, outputWells )
                # Copy attributes from the initial time step
                meshAttributes: set[ str ] = getAttributeSet( self.outputCellsT0, False )
                for ( attributeName, attributeNewName ) in getAttributeToTransferFromInitialTime().items():
                    if attributeName in meshAttributes:
                        copyAttribute( self.outputCellsT0, outputCells, attributeName, attributeNewName, False, self.logger )
                # Create elementCenter attribute in the volume mesh if needed
                cellCenterAttributeName: str = GeosMeshOutputsEnum.ELEMENT_CENTER.attributeName
                createCellCenterAttribute( outputCells, cellCenterAttributeName )
                # Stop the computation
                request.Remove( executive.CONTINUE_EXECUTING() )  # type: ignore
                self.m_requestDataStep = -1
        except AssertionError as e:
            self.logger.error( f"The plugin failed.\n{e}" )
            return 0
        except Exception as e:
            mess1: str = "Block extraction and merge failed due to:"
            self.logger.critical( mess1 )
            self.logger.critical( e, exc_info=True )
            return 0
        return 1

    def doExtractAndMerge(
        self: Self,
        mesh: vtkMultiBlockDataSet,
        outputCells: vtkMultiBlockDataSet,
        outputFaults: vtkMultiBlockDataSet,
        outputWells: vtkMultiBlockDataSet,
    ) -> None:
        """Apply block extraction and merge.

        Args:
            mesh (vtkMultiBlockDataSet): Mesh to process.
            outputCells (vtkMultiBlockDataSet): Output volume mesh.
            outputFaults (vtkMultiBlockDataSet): Output surface mesh.
            outputWells (vtkMultiBlockDataSet): Output well mesh.
        """
        # Extract blocks
        blockExtractor: GeosBlockExtractor = GeosBlockExtractor( mesh, extractFault=self.extractFault, extractWell=self.extractWell, speHandler=True )
        if not blockExtractor.logger.hasHandlers():
            blockExtractor.setLoggerHandler( VTKHandler() )
        blockExtractor.applyFilter()

        # recover output objects from GeosBlockExtractor filter and merge internal blocks
        volumeBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.volume
        outputCells.ShallowCopy( self.mergeBlocksFilter( volumeBlockExtracted, False ) )
        outputCells.Modified()

        if self.extractFault:
            faultBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.fault
            outputFaults.ShallowCopy( self.mergeBlocksFilter( faultBlockExtracted, True ) )
            outputFaults.Modified()

        if self.extractWell:
            wellBlockExtracted: vtkMultiBlockDataSet = blockExtractor.extractedGeosDomain.well
            outputWells.ShallowCopy( self.mergeBlocksFilter( wellBlockExtracted, False ) )
            outputWells.Modified()

        return

    def mergeBlocksFilter( self: Self,
                           mesh: vtkMultiBlockDataSet,
                           convertSurfaces: bool = False ) -> vtkMultiBlockDataSet:
        """Apply vtk merge block filter on input multi block mesh.

        Args:
            mesh (vtkMultiBlockDataSet): Mesh to merge.
            convertSurfaces (bool, optional): True to convert surface from vtkUnstructuredGrid to vtkPolyData.
                Defaults to False.

        Returns:
            vtkMultiBlockDataSet: Mesh composed of internal merged blocks.
        """
        mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( mesh, convertSurfaces, True )
        if not mergeBlockFilter.logger.hasHandlers():
            mergeBlockFilter.setLoggerHandler( VTKHandler() )
        mergeBlockFilter.applyFilter()
        mergedBlocks: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        mergedBlocks.ShallowCopy( mergeBlockFilter.getOutput() )
        return mergedBlocks
