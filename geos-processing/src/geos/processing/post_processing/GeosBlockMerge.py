# SPDX-License-Identifier: Apache-2.0
# # SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file

from geos.utils.GeosOutputsConstants import (
    PHASE_SEP,
    FluidPrefixEnum,
    PhaseTypeEnum,
    PostProcessingOutputsEnum,
    getRockSuffixRenaming,
)
from geos.utils.Logger import Logger, getLogger
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import (
    vtkInformation,
    vtkInformationVector,
)
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkDataObjectTreeIterator,
    vtkMultiBlockDataSet,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersCore import vtkArrayRename
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

from geos.mesh.utils.multiblockHelpers import getElementaryCompositeBlockIndexes
from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import createConstantAttribute, fillAllPartialAttributes
from geos.mesh.utils.multiblockHelpers import extractBlock
from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.utils.genericHelpers import (
    computeNormals,
    computeTangents,
)

__doc__ = """
GeosBlockMerge module is a vtk filter that allows to merge Geos ranks, rename
stress and porosity attributes, and identify fluids and rock phases.

Filter input and output types are vtkMultiBlockDataSet.

To use the filter:

.. code-block:: python

    from filters.GeosBlockMerge import GeosBlockMerge

    # filter inputs
    logger :Logger
    input :vtkMultiBlockDataSet

    # instanciate the filter
    mergeBlockFilter :GeosBlockMerge = GeosBlockMerge()
    # set the logger
    mergeBlockFilter.SetLogger(logger)
    # set input data object
    mergeBlockFilter.SetInputDataObject(input)
    # ConvertSurfaceMeshOff or ConvertSurfaceMeshOn to (de)activate the conversion
    # of vtkUnstructuredGrid to surface withNormals and Tangents calculation.
    mergeBlockFilter.ConvertSurfaceMeshOff()
    # do calculations
    mergeBlockFilter.Update()
    # get output object
    output :vtkMultiBlockDataSet = mergeBlockFilter.GetOutputDataObject(0)
"""


class GeosBlockMerge():

    def __init__( self: Self, inputMesh: vtkMultiBlockDataSet ) -> None:
        """VTK Filter that perform GEOS rank merge.

        The filter returns a multiblock mesh composed of elementary blocks.

        """

        self.m_input: vtkMultiBlockDataSet = inputMesh
        self.m_output: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        self.m_convertFaultToSurface: bool = True

        # set logger
        self.m_logger: Logger = getLogger( "Geos Block Merge Filter" )

    def applyFilter( self: Self ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        try:
            self.doMerge()
        except ( ValueError, TypeError, RuntimeError ) as e:
            self.m_logger.critical( "Geos block merge failed due to:" )
            self.m_logger.critical( e, exc_info=True )
            return 0
        else:
            return 1

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def ConvertSurfaceMeshOn( self: Self ) -> None:
        """Activate surface conversion from vtkUnstructredGrid to vtkPolyData."""
        self.m_convertFaultToSurface = True

    def ConvertSurfaceMeshOff( self: Self ) -> None:
        """Deactivate surface conversion from vtkUnstructredGrid to vtkPolyData."""
        self.m_convertFaultToSurface = False

    def doMerge( self: Self ) -> int:
        """Apply block merge.

        Returns:
            bool: True if block merge successfully ended, False otherwise.
        """
        self.mergeRankBlocks()
        if self.m_convertFaultToSurface:
            self.convertFaultsToSurfaces()

        self.m_output.ShallowCopy( self.m_outputMesh )
        return 1

    def mergeRankBlocks( self: Self ) -> bool:
        """Merge all elementary node that belong to a same parent node.

        Returns:
            bool: True if calculation successfully ended, False otherwise
        """
        # display phase names
        try:
            phaseClassification: dict[ str, PhaseTypeEnum ] = self.getPhases( True )
            if phaseClassification is not None:
                for phaseTypeRef in list( PhaseTypeEnum ):
                    phases = [
                        phaseName for phaseName, phaseType in phaseClassification.items() if phaseType is phaseTypeRef
                    ]
                    if len( phases ) > 0:
                        self.m_logger.info( f"Identified {phaseTypeRef.type} phase(s) are: {phases}" )
        except AssertionError as e:
            self.m_logger.warning( "Phases were not identified due to:" )
            self.m_logger.warning( e )

        compositeBlockIndexesToMerge: dict[ str, int ] = ( getElementaryCompositeBlockIndexes( self.m_input ) )
        nbBlocks: int = len( compositeBlockIndexesToMerge )
        self.m_outputMesh = vtkMultiBlockDataSet()
        self.m_outputMesh.SetNumberOfBlocks( nbBlocks )
        for newIndex, ( blockName, blockIndex ) in enumerate( compositeBlockIndexesToMerge.items() ):
            # extract composite block
            blockToMerge1: vtkMultiBlockDataSet = extractBlock( self.m_input, blockIndex )
            assert blockToMerge1 is not None, "Extracted block to merge is null."

            # rename attributes
            blockToMerge2: vtkMultiBlockDataSet = self.renameAttributes( blockToMerge1, phaseClassification )
            assert blockToMerge2 is not None, "Attribute renaming failed."

            # merge all its children
            mergedBlock: vtkUnstructuredGrid = self.mergeChildBlocks( blockToMerge2 )

            # create index attribute keeping the index in intial mesh
            if not createConstantAttribute(
                    mergedBlock,
                [
                    blockIndex,
                ],
                    PostProcessingOutputsEnum.BLOCK_INDEX.attributeName,
                (),
                    False,
            ):
                self.m_logger.warning( "BlockIndex attribute was not created." )

            # set this composite block into the output
            self.m_outputMesh.SetBlock( newIndex, mergedBlock )
            self.m_outputMesh.GetMetaData( newIndex ).Set( vtkCompositeDataSet.NAME(), blockName )

        assert ( self.m_outputMesh.GetNumberOfBlocks() == nbBlocks ), "Final number of merged blocks is wrong."
        return True

    def renameAttributes(
        self: Self,
        mesh: vtkMultiBlockDataSet,
        phaseClassification: dict[ str, PhaseTypeEnum ],
    ) -> vtkMultiBlockDataSet:
        """Rename attributes to harmonize throughout the mesh.

        Args:
            mesh (vtkMultiBlockDataSet): input mesh
            phaseClassification (dict[str, PhaseTypeEnum]): phase classification
                detected from attributes

        Returns:
            vtkMultiBlockDataSet: output mesh with renamed attributes
        """
        assert phaseClassification is not None, "Phases were not correctly identified."

        renameFilter: vtkArrayRename = vtkArrayRename()
        renameFilter.SetInputData( mesh )
        rockPhase: list[ str ] = [
            phaseName for phaseName, phaseType in phaseClassification.items() if phaseType is PhaseTypeEnum.ROCK
        ]
        for attributeName in getAttributeSet( mesh, False ):
            for phaseName in rockPhase:
                if phaseName in attributeName:
                    for suffix, newName in getRockSuffixRenaming().items():
                        if suffix in attributeName:
                            renameFilter.SetCellArrayName( attributeName, newName )

        renameFilter.Update()
        output: vtkMultiBlockDataSet = renameFilter.GetOutput()
        return output

    def getPhaseNames( self: Self, attributeSet: set[ str ] ) -> set[ str ]:
        """Get the names of the phases in the mesh from Point/Cell attributes.

        Args:
            attributeSet (set[str]): list of attributes where to find phases

        Returns:
             set[str]: the list of phase names that appear at least twice.
        """
        phaseNameDict: dict[ str, int ] = {}
        for name in attributeSet:
            if PHASE_SEP in name:
                # use the last occurence of PHASE_SEP to split phase name from
                # property name
                index = name.rindex( PHASE_SEP )
                phaseName: str = name[ :index ]
                if phaseName in phaseNameDict:
                    phaseNameDict[ phaseName ] += 1
                else:
                    phaseNameDict[ phaseName ] = 1

        # remove names that appear only once
        return set( phaseNameDict.keys() )

    def getPhases( self: Self, onCells: bool = True ) -> dict[ str, PhaseTypeEnum ]:
        """Get the dictionnary of phases classified according to PhaseTypeEnum.

        Args:
            onCells (bool, optional): Attributes are on Cells (Default) or on
                Points.

                Defaults to True.

        Returns:
            dict[str, PhaseTypeEnum]: a dictionnary with phase names as keys and
            phase type as value.
        """
        attributeSet: set[ str ] = getAttributeSet( self.m_input, not onCells )
        assert len( attributeSet ) > 0, "Input object does not have any attribute."

        phaseClassification: dict[ str, PhaseTypeEnum ] = {}
        phaseNames: set[ str ] = self.getPhaseNames( attributeSet )
        for phaseName in phaseNames:
            # check for fluid phase names (most often the same names: fluid, water, or gas)
            if any( fluidPrefix.value.lower() in phaseName.lower() for fluidPrefix in list( FluidPrefixEnum ) ):
                phaseClassification[ phaseName ] = PhaseTypeEnum.FLUID
                continue

            for attributeName in attributeSet:
                if phaseName in attributeName:
                    index = attributeName.index( phaseName ) + len( phaseName )
                    suffix = attributeName[ index: ]
                    for phaseType in list( PhaseTypeEnum ):
                        if suffix in phaseType.attributes:
                            if ( phaseName in phaseClassification ) and ( phaseType
                                                                          is not phaseClassification[ phaseName ] ):
                                self.m_logger.warning( f"The phase {phaseName} may be misclassified " +
                                                       "since the same name is used for both " +
                                                       "{phaseType.type} and " +
                                                       "{phaseClassification[phaseName].type} types" )
                            phaseClassification[ phaseName ] = phaseType

        return phaseClassification

    def mergeChildBlocks( self: Self, compositeBlock: vtkMultiBlockDataSet ) -> vtkUnstructuredGrid:
        """Merge all children of the input composite block.

        Args:
            compositeBlock (vtkMultiBlockDataSet): composite block

        Returns:
            vtkUnstructuredGrid: merged block
        """
        # fill partial attributes in all children blocks
        if not fillAllPartialAttributes( compositeBlock ):
            self.m_logger.warning( "Some partial attributes may not have been propagated to the whole mesh." )

        # merge blocks
        mergedBlocks = mergeBlocks( compositeBlock )
        return mergedBlocks

    def convertFaultsToSurfaces( self: Self ) -> bool:
        """Convert blocks corresponding to faults to surface.

        Returns:
            bool: True if calculation succesfully ended, False otherwise
        """
        assert self.m_outputMesh is not None, "Output surface is null."

        transientMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        nbSurfaces: int = self.m_outputMesh.GetNumberOfBlocks()
        transientMesh.SetNumberOfBlocks( nbSurfaces )

        # initialize data object tree iterator
        iter: vtkDataObjectTreeIterator = vtkDataObjectTreeIterator()
        iter.SetDataSet( self.m_outputMesh )
        iter.VisitOnlyLeavesOn()
        iter.GoToFirstItem()
        surfaceIndex: int = 0
        while iter.GetCurrentDataObject() is not None:
            surfaceName: str = iter.GetCurrentMetaData().Get( vtkCompositeDataSet.NAME() )
            # convert block to surface
            surface0: vtkUnstructuredGrid = vtkUnstructuredGrid.SafeDownCast( iter.GetCurrentDataObject() )
            surface1: vtkPolyData = self.convertBlockToSurface( surface0 )
            assert surface1 is not None, "Surface extraction from block failed."
            # compute normals
            surface2: vtkPolyData = computeNormals( surface1 )
            assert surface2 is not None, "Normal calculation failed."
            # compute tangents
            surface3: vtkPolyData = computeTangents( surface2 )
            assert surface3 is not None, "Tangent calculation failed."

            # set surface to output multiBlockDataSet
            transientMesh.SetBlock( surfaceIndex, surface3 )
            transientMesh.GetMetaData( surfaceIndex ).Set( vtkCompositeDataSet.NAME(), surfaceName )

            iter.GoToNextItem()
            surfaceIndex += 1

        self.m_outputMesh.ShallowCopy( transientMesh )
        return True

    def convertBlockToSurface( self: Self, block: vtkUnstructuredGrid ) -> vtkPolyData:
        """Convert vtkUnstructuredGrid to a surface vtkPolyData.

        .. WARNING:: work only with triangulated surfaces

        .. TODO:: need to convert quadrangular to triangulated surfaces first


        Args:
            block (vtkUnstructuredGrid): block from which to extract the surface

        Returns:
            vtkPolyData: extracted surface
        """
        extractSurfaceFilter: vtkDataSetSurfaceFilter = vtkDataSetSurfaceFilter()
        extractSurfaceFilter.SetInputData( block )
        # fast mode should be used for rendering only
        extractSurfaceFilter.FastModeOff()
        # Delegation activated allow to accelerate the processing with unstructured mesh
        # see https://vtk.org/doc/nightly/html/classvtkDataSetSurfaceFilter.html
        extractSurfaceFilter.DelegationOn()
        extractSurfaceFilter.Update()
        output: vtkPolyData = extractSurfaceFilter.GetOutput()
        return output
