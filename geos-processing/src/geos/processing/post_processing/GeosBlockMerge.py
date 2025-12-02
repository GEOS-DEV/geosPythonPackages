# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import logging
from typing_extensions import Self

from vtkmodules.vtkCommonDataModel import ( vtkCompositeDataSet, vtkMultiBlockDataSet, vtkPolyData,
                                            vtkUnstructuredGrid )

from geos.utils.Errors import VTKError
from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.GeosOutputsConstants import ( PHASE_SEP, PhaseTypeEnum, FluidPrefixEnum, PostProcessingOutputsEnum,
                                              getRockSuffixRenaming )
from geos.utils.pieceEnum import Piece

from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import ( createConstantAttribute, renameAttribute )
from geos.mesh.utils.multiblockModifiers import mergeBlocks
from geos.mesh.utils.multiblockHelpers import ( getElementaryCompositeBlockIndexes, extractBlock )
from geos.mesh.utils.genericHelpers import ( computeNormals, computeTangents, convertUnstructuredGridToPolyData,
                                             triangulateMesh, isTriangulate )

__doc__ = """
GeosBlockMerge is a vtk filter that acts on each region of a GEOS output domain (volume, fault, wells):
    - Ranks are merged.
    - "Fluids" and "Rock" phases are identified.
    - "Rock" attributes are renamed depending on the phase they refer to for more clarity.
    - Volume meshes are converted to surface if needed.

Filter input and output types are vtkMultiBlockDataSet.

.. Important::
    This filter cannot be used directly on GEOS output. The domain needs to be extracted with the help of `GeosBlockExtractor` filter.
    Please refer to the `documentation <https://geosx-geosx.readthedocs-hosted.com/projects/geosx-geospythonpackages/en/latest/geos_processing_docs/post_processing.html>`_ for more information.

To use the filter:

.. code-block:: python

    from geos.processing.post_processing.GeosBlockMerge import GeosBlockMerge

    # Filter inputs.
    inputMesh: vtkMultiBlockDataSet
    # Optional inputs.
    convertFaultToSurface: bool # Defaults to False
    speHandler: bool # Defaults to False
    loggerName: str # Defaults to "GEOS Block Merge"

    # Instantiate the filter
    mergeBlockFilter: GeosBlockMerge = GeosBlockMerge( inputMesh, convertFaultToSurface, speHandler, loggerName )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    mergeBlockFilter.setLoggerHandler( yourHandler )

    # Do calculations
    mergeBlockFilter.applyFilter()

    # Get the multiBlockDataSet with one dataSet per region
    outputMesh: vtkMultiBlockDataSet = mergeBlockFilter.getOutput()
"""


class GeosBlockMerge():

    def __init__(
        self: Self,
        inputMesh: vtkMultiBlockDataSet,
        convertFaultToSurface: bool = False,
        speHandler: bool = False,
        loggerName: str = "GEOS Block Merge",
    ) -> None:
        """VTK Filter that merges ranks of GEOS output mesh.

        For each composite block of the input mesh:
            - Ranks are merged.
            - "Rock" attributes are renamed.
            - Volume meshes are converted to surface if requested.

        Args:
            inputMesh (vtkMultiBlockDataSet): The mesh with the blocks to merge.
            convertFaultToSurface (bool, optional): If True, merged blocks are converted to surface (vtp), False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
            loggerName (str, optional): Name of the filter logger.
                Defaults to "GEOS Block Merge".

        """
        self.inputMesh: vtkMultiBlockDataSet = inputMesh
        self.convertFaultToSurface: bool = convertFaultToSurface
        self.handler: None | logging.Handler = None

        self.outputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        self.phaseNameDict: dict[ str, set[ str ] ] = {
            PhaseTypeEnum.ROCK.type: set(),
            PhaseTypeEnum.FLUID.type: set(),
        }

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerName, True )
        else:
            self.logger = logging.getLogger( loggerName )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical, be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.handler = handler
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
                                                piece=Piece.CELLS,
                                                logger=self.logger ):
                    self.logger.warning( "BlockIndex attribute was not created." )

                # Rename attributes
                self.renameAttributes( volumeMesh )

                # Convert the volume mesh to a surface mesh
                if self.convertFaultToSurface:
                    if not isTriangulate( volumeMesh ):
                        volumeMesh.ShallowCopy( triangulateMesh( volumeMesh, self.logger ) )
                    surfaceMesh: vtkPolyData = convertUnstructuredGridToPolyData( volumeMesh, self.logger )
                    surfaceMesh.ShallowCopy( computeNormals( surfaceMesh, logger=self.logger ) )
                    surfaceMesh.ShallowCopy( computeTangents( surfaceMesh, logger=self.logger ) )
                    # Add the merged block to the output mesh
                    self.outputMesh.SetBlock( newIndex, surfaceMesh )
                else:
                    self.outputMesh.SetBlock( newIndex, volumeMesh )

            self.logger.info( f"The filter { self.logger.name } succeeded." )
        except ( ValueError, TypeError, RuntimeError, AssertionError, VTKError ) as e:
            self.logger.error( f"The filter { self.logger.name } failed.\n{ e }" )

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
        for attributeName in getAttributeSet( mesh, piece=Piece.CELLS ):
            for suffix, newName in getRockSuffixRenaming().items():
                if suffix in attributeName:
                    # Fluid and Rock density attribute have the same suffix, only the rock density need to be renamed
                    if suffix == "_density":
                        for phaseName in self.phaseNameDict[ PhaseTypeEnum.ROCK.type ]:
                            if phaseName in attributeName:
                                renameAttribute( mesh, attributeName, newName, piece=Piece.CELLS )
                    else:
                        renameAttribute( mesh, attributeName, newName, piece=Piece.CELLS )

        return

    def computePhaseNames( self: Self ) -> None:
        """Get the names of the phases in the mesh from Cell attributes."""
        # All the phase attributes are on cells
        for name in getAttributeSet( self.inputMesh, piece=Piece.CELLS ):
            if PHASE_SEP in name and "dofIndex" not in name:
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
