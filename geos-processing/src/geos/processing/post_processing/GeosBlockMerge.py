# SPDX-License-Identifier: Apache-2.0
# # SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import logging
from typing_extensions import Self

from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkMultiBlockDataSet, vtkPolyData,
                                            vtkUnstructuredGrid )
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.GeosOutputsConstants import ( PHASE_SEP, PhaseTypeEnum, FluidPrefixEnum, PostProcessingOutputsEnum,
                                              getRockSuffixRenaming )
from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import ( createConstantAttribute, renameAttribute )
from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.utils.multiblockHelpers import ( getElementaryCompositeBlockIndexes, extractBlock )
from geos.mesh.utils.genericHelpers import ( computeNormals, computeTangents )

__doc__ = """
GeosBlockMerge is a vtk filter that allows to merge for a GEOS domain the ranks per region, identify "Fluids" and "Rock" phases and rename "Rock" attributes.

Filter input and output types are vtkMultiBlockDataSet.

.. Important::
    This filter deals with the domain mesh of GEOS. This domain needs to be extracted before.
    See geos-processing/src/geos/processing/post_processing/GeosBlockExtractor.py to see the type of input requires by this filter.

To use the filter:

.. code-block:: python

    from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge

    # Filter inputs.
    inputMesh: vtkMultiBlockDataSet
    # Optional inputs.
    convertFaultToSurface: bool # Defaults to False
    speHandler: bool # Defaults to False

    # Instantiate the filter
    mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( inputMesh, convertFaultToSurface, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    mergeBlockFilter.setLoggerHandler( yourHandler )

    # Do calculations
    mergeBlockFilter.applyFilter()

    # Get the multiBlockDataSet with one dataSet per region
    outputMesh: vtkMultiBlockDataSet = mergeBlockFilter.getOutput()
"""

loggerTitle: str = "GEOS Block Merge"


class GeosBlockMerge():

    def __init__(
        self: Self,
        inputMesh: vtkMultiBlockDataSet,
        convertFaultToSurface: bool = False,
        speHandler: bool = False,
    ) -> None:
        """VTK Filter that merge ranks of GEOS output mesh.

        for all the composite blocks of the input mesh:
            - Ranks are merged
            - "Rock" attributes are renamed
            - Volume mesh are convert to surface if needed

        Args:
            inputMesh (vtkMultiBlockDataSet): The mesh with the blocks to merge.
            convertFaultToSurface (bool, optional): True if the merged block need to be convert to vtp, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.

        """
        self.inputMesh: vtkMultiBlockDataSet = inputMesh
        self.convertFaultToSurface: bool = convertFaultToSurface

        self.outputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        self.phaseNameDict: dict[ str, set[ str ] ] = {
            PhaseTypeEnum.ROCK.type: set(),
            PhaseTypeEnum.FLUID.type: set(),
        }

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            self.logger.warning(
                "The logger already has an handler, to use yours set the argument 'speHandler' to True during the filter initialization."
            )

    def getOutput( self: Self ) -> vtkMultiBlockDataSet:
        """Get the mesh with the composite blocks merged."""
        return self.outputMesh

    def applyFilter( self: Self ) -> None:
        """Apply the filter on the mesh."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        try:
            # Display phase names
            self.computePhaseNames()
            for phase, phaseNames in self.phaseNameDict.items():
                if len( phaseNames ) > 0:
                    self.logger.info( f"Identified { phase } phase(s) are: { phaseNames }." )
                else:
                    self.logger.info( f"No { phase } phase has been identified." )

            # Parse all the composite blocks
            compositeBlockIndexesToMerge: dict[ str, int ] = getElementaryCompositeBlockIndexes( self.inputMesh )
            nbBlocks: int = len( compositeBlockIndexesToMerge )
            self.outputMesh.SetNumberOfBlocks( nbBlocks )
            for newIndex, ( blockName, blockIndex ) in enumerate( compositeBlockIndexesToMerge.items() ):
                # Set the name of the composite block
                self.outputMesh.GetMetaData( newIndex ).Set( vtkCompositeDataSet.NAME(), blockName )

                # Merge blocks
                blockToMerge: vtkMultiBlockDataSet = extractBlock( self.inputMesh, blockIndex )
                volumeMesh: vtkUnstructuredGrid = mergeBlocks( blockToMerge,
                                                               keepPartialAttributes=True,
                                                               logger=self.logger )

                # Create index attribute keeping the index in initial mesh
                if not createConstantAttribute( volumeMesh, [ blockIndex ],
                                                PostProcessingOutputsEnum.BLOCK_INDEX.attributeName,
                                                onPoints=False,
                                                logger=self.logger ):
                    self.logger.warning( "BlockIndex attribute was not created." )

                # Rename attributes
                self.renameAttributes( volumeMesh )

                # Convert the volume mesh to a surface mesh
                if self.convertFaultToSurface:
                    surfaceMesh: vtkPolyData = self.convertBlockToSurface( volumeMesh )
                    assert surfaceMesh is not None, "Surface extraction from block failed."
                    surfaceMesh.ShallowCopy( computeNormals( surfaceMesh, logger=self.logger ) )
                    assert surfaceMesh is not None, "Normal calculation failed."
                    surfaceMesh.ShallowCopy( computeTangents( surfaceMesh, logger=self.logger ) )
                    assert surfaceMesh is not None, "Tangent calculation failed."
                    # Add the merged block to the output mesh
                    self.outputMesh.SetBlock( newIndex, surfaceMesh )
                else:
                    self.outputMesh.SetBlock( newIndex, volumeMesh )

            self.logger.info( "The filter succeeded." )
        except ( ValueError, TypeError, RuntimeError, AssertionError ) as e:
            self.logger.critical( f"The filter failed.\n{ e }" )

        return

    def renameAttributes(
        self: Self,
        mesh: vtkUnstructuredGrid,
    ) -> None:
        """Rename attributes to harmonize GEOS output, see more geos.utils.OutputsConstants.py.

        Args:
            mesh (vtkUnstructuredGrid): The mesh with the attribute to rename.
        """
        # All the attributes to rename are on cells
        for attributeName in getAttributeSet( mesh, False ):
            for suffix, newName in getRockSuffixRenaming().items():
                if suffix in attributeName:
                    # Fluid and Rock density attribute have the same suffix, only the rock density need to be renamed
                    if suffix == "_density":
                        for phaseName in self.phaseNameDict[ PhaseTypeEnum.ROCK.type ]:
                            if phaseName in attributeName:
                                renameAttribute( mesh, attributeName, newName, False )
                    else:
                        renameAttribute( mesh, attributeName, newName, False )

    def computePhaseNames( self: Self ) -> None:
        """Get the names of the phases in the mesh from Cell attributes."""
        # All the phase attributes are on cells
        for name in getAttributeSet( self.inputMesh, False ):
            if PHASE_SEP in name:
                phaseName: str
                suffixName: str
                phaseName, suffixName = name.split( PHASE_SEP )
                # Fluid and Rock density attribute have the same suffix, common fluid name are used to separated the two phases
                if f"{ PHASE_SEP }{ suffixName }" == "_density":
                    if any( phaseName in fluidPrefix.value for fluidPrefix in list( FluidPrefixEnum ) ):
                        self.phaseNameDict[ PhaseTypeEnum.FLUID.type ].add( phaseName )
                    else:
                        self.phaseNameDict[ PhaseTypeEnum.ROCK.type ].add( phaseName )
                elif f"{ PHASE_SEP }{ suffixName }" in PhaseTypeEnum.ROCK.attributes:
                    self.phaseNameDict[ PhaseTypeEnum.ROCK.type ].add( phaseName )
                elif f"{ PHASE_SEP }{ suffixName }" in PhaseTypeEnum.FLUID.attributes:
                    self.phaseNameDict[ PhaseTypeEnum.FLUID.type ].add( phaseName )

        return

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
