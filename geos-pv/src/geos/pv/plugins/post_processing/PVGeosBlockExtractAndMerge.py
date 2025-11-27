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
geos_pv_path: Path = Path( __file__ ).parent.parent.parent.parent.parent.parent
sys.path.insert( 0, str( geos_pv_path / "src" ) )
from geos.pv.utils.config import update_paths

update_paths()

from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import ( copyAttribute, createCellCenterAttribute )
from geos.mesh.utils.multiblockHelpers import getBlockNames

from geos.utils.GeosOutputsConstants import ( GeosMeshOutputsEnum, GeosDomainNameEnum,
                                              getAttributeToTransferFromInitialTime )

from geos.pv.utils.paraviewTreatments import getTimeStepIndex
from geos.pv.utils.workflowFunctions import doExtractAndMerge

from vtkmodules.vtkCommonCore import ( vtkInformation, vtkInformationVector )
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet

from paraview.util.vtkAlgorithm import (  # type: ignore[import-not-found]
    VTKPythonAlgorithmBase, smdomain, smproperty, smproxy )
from paraview.detail.loghandler import (  # type: ignore[import-not-found]
    VTKHandler )

__doc__ = """
PVGeosBlockExtractAndMerge is a Paraview plugin processing the input mesh at the current time in two steps:
    1. Extraction of domains (volume, fault and well) from a GEOS output multiBlockDataSet mesh
    2. Actions on each region of a GEOS output domain (volume, fault, wells) to:
        * Merge Ranks
        * Identify "Fluids" and "Rock" phases
        * Rename "Rock" attributes depending on the phase they refer to for more clarity
        * Convert volume meshes to surface if needed
        * Copy "geomechanics" attributes from the initial timestep to the current one if they exist

This filter results in 3 output pipelines with the vtkMultiBlockDataSet:
    - "Volume" contains the volume domain
    - "Fault" contains the fault domain if it exist
    - "Well" contains the well domain if it exist

Input and output meshes are vtkMultiBlockDataSet.

.. Important::
    - The input mesh must be an output of a GEOS simulation or contain at least three blocks labeled with the same domain names:
        * "CellElementRegion" for volume domain
        * "SurfaceElementRegion" for fault domain if the input contains fault
        * "WellElementRegion" for well domain if the input contains well
        * See more https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/ElementRegions.html?_sm_au_=iVVT5rrr5fN00R8sQ0WpHK6H8sjL6#xml-element-elementregions
    - The filter detected automatically the three domains. If one of them if not in the input mesh, the associated output pipeline will be empty

To use it:

* Load the plugin in Paraview: Tools > Manage Plugins ... > Load New ... > .../geosPythonPackages/geos-pv/src/geos/pv/plugins/post_processing/PVGeosBlockExtractAndMerge
* Select the Geos output .pvd file loaded in Paraview to process
* Select the filter: Filters > 2- GEOS Post-Processing > GEOS Extract and Merge Blocks
* Apply

"""

loggerTitle: str = "Extract & Merge GEOS Block"


@smproxy.filter(
    name="PVGeosBlockExtractAndMerge",
    label="GEOS Extract and Merge Blocks",
)
@smproperty.xml( """
    <OutputPort index="0" name="Volume"/>
    <OutputPort index="1" name="Fault"/>
    <OutputPort index="2" name="Well"/>
    <Hints>
        <ShowInMenu category="2- Geos Post-Processing"/>
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

        To apply in the case of output ".pvd" file contains Volume, Fault or
        Well elements.
        """
        super().__init__(
            nInputPorts=1,
            nOutputPorts=3,
            inputType="vtkMultiBlockDataSet",
            outputType="vtkMultiBlockDataSet",
        )

        self.extractFault: bool = True
        self.extractWell: bool = True

        # All time steps from input
        self.timeSteps: npt.NDArray[ np.float64 ] = np.array( [] )
        # The time step of the input when the plugin is called or updated
        self.currentTimeStepIndex: int = 0
        # The time step studies. It is incremental -1 during the initialization, from 0 to self.currentTimeStepIndex during the computation and -2 at the end of the computation
        self.requestDataStep: int = -1

        self.outputCellsT0: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        self.logger = logging.getLogger( loggerTitle )
        self.logger.setLevel( logging.INFO )
        self.logger.addHandler( VTKHandler() )
        self.logger.propagate = False

        self.logger.info( f"Apply plugin { self.logger.name }." )

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
        assert inData is not None

        outDataCells = self.GetOutputData( outInfoVec, 0 )
        if outDataCells is None or ( not outDataCells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataCells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 0 ).Set( outDataCells.DATA_OBJECT(), outDataCells )  # type: ignore

        outDataFaults = self.GetOutputData( outInfoVec, 1 )
        if outDataFaults is None or ( not outDataFaults.IsA( "vtkMultiBlockDataSet" ) ):
            outDataFaults = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 1 ).Set( outDataFaults.DATA_OBJECT(), outDataFaults )  # type: ignore

        outDataWells = self.GetOutputData( outInfoVec, 2 )
        if outDataWells is None or ( not outDataWells.IsA( "vtkMultiBlockDataSet" ) ):
            outDataWells = vtkMultiBlockDataSet()
            outInfoVec.GetInformationObject( 2 ).Set( outDataWells.DATA_OBJECT(), outDataWells )  # type: ignore

        return super().RequestDataObject( request, inInfoVec, outInfoVec )  # type: ignore[no-any-return]

    def RequestInformation(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
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
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]
        self.timeSteps = inInfo.GetInformationObject( 0 ).Get( executive.TIME_STEPS() )

        # The time of the input mesh
        currentTime = inInfo.GetInformationObject( 0 ).Get( executive.UPDATE_TIME_STEP() )

        self.currentTimeStepIndex = getTimeStepIndex( currentTime, self.timeSteps )

        inputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfo )
        blockNames: list[ str ] = getBlockNames( inputMesh )
        if GeosDomainNameEnum.FAULT_DOMAIN_NAME.value not in blockNames:
            self.extractFault = False
            self.logger.warning(
                f"The mesh to process does not contains the block named { GeosDomainNameEnum.FAULT_DOMAIN_NAME.value }. The output 'Fault' will be an empty mesh."
            )

        if GeosDomainNameEnum.WELL_DOMAIN_NAME.value not in blockNames:
            self.extractWell = False
            self.logger.warning(
                f"The mesh to process does not contains the block named { GeosDomainNameEnum.WELL_DOMAIN_NAME.value }. The output 'Well' will be an empty mesh."
            )

        return 1

    def RequestUpdateExtent(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestUpdateExtent.

        This function is call at each change of time:
            on Paraview with the widget Time
            if request.Set( self.GetExecutive.CONTINUE_EXECUTING(), 1 ) is set (time steps iterator)

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()
        inInfo = inInfoVec[ 0 ]

        # Get update time step from Paraview
        if self.requestDataStep == -2:
            currentTime = inInfo.GetInformationObject( 0 ).Get( executive.UPDATE_TIME_STEP() )
            self.currentTimeStepIndex = getTimeStepIndex( currentTime, self.timeSteps )
            self.requestDataStep = self.currentTimeStepIndex

        # Update requestDataStep
        else:
            self.requestDataStep += 1

        # Update time according to requestDataStep iterator
        inInfo.GetInformationObject( 0 ).Set( executive.UPDATE_TIME_STEP(), self.timeSteps[ self.requestDataStep ] )

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
            inputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet.GetData( inInfoVec[ 0 ] )
            executive = self.GetExecutive()

            # First time step, compute the initial properties (useful for geomechanics analyses)
            if self.requestDataStep == 0:
                self.logger.info( "Apply the plugin for the first time step to get the initial properties." )
                doExtractAndMerge( inputMesh, self.outputCellsT0, vtkMultiBlockDataSet(), vtkMultiBlockDataSet(),
                                   self.extractFault, self.extractWell )
                request.Set( executive.CONTINUE_EXECUTING(), 1 )

            # Current time step, extract, merge, rename and transfer properties
            if self.requestDataStep == self.currentTimeStepIndex:
                self.logger.info( f"Apply the filter for the current time step: { self.currentTimeStepIndex }." )
                outputCells: vtkMultiBlockDataSet = self.GetOutputData( outInfoVec, 0 )
                outputFaults: vtkMultiBlockDataSet = self.GetOutputData(
                    outInfoVec, 1 ) if self.extractFault else vtkMultiBlockDataSet()
                outputWells: vtkMultiBlockDataSet = self.GetOutputData(
                    outInfoVec, 2 ) if self.extractWell else vtkMultiBlockDataSet()
                doExtractAndMerge( inputMesh, outputCells, outputFaults, outputWells, self.extractFault,
                                   self.extractWell )

                # Copy attributes from the initial time step
                meshAttributes: set[ str ] = getAttributeSet( self.outputCellsT0, False )
                for ( attributeName, attributeNewName ) in getAttributeToTransferFromInitialTime().items():
                    if attributeName in meshAttributes:
                        copyAttribute( self.outputCellsT0, outputCells, attributeName, attributeNewName, False,
                                       self.logger )

                # Create elementCenter attribute in the volume mesh if needed
                cellCenterAttributeName: str = GeosMeshOutputsEnum.ELEMENT_CENTER.attributeName
                createCellCenterAttribute( outputCells, cellCenterAttributeName )

                # Stop the time step iteration
                request.Remove( executive.CONTINUE_EXECUTING() )

                # Set to -2 in case time changes on Paraview
                self.requestDataStep = -2

                self.logger.info( f"The plugin { self.logger.name } succeeded." )
        except AssertionError as e:
            self.logger.error( f"The plugin failed.\n{e}" )
            return 0
        except Exception as e:
            mess1: str = "Block extraction and merge failed due to:"
            self.logger.critical( mess1 )
            self.logger.critical( e, exc_info=True )
            return 0
        return 1
