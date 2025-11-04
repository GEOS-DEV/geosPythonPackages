# SPDX-License-Identifier: Apache-2.0
# # SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file

from geos.utils.GeosOutputsConstants import (
    PHASE_SEP,
    PhaseTypeEnum,
    FluidPrefixEnum,
    PostProcessingOutputsEnum,
    getRockSuffixRenaming,
)
from geos.utils.Logger import Logger, getLogger
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import (
    vtkCompositeDataSet,
    vtkMultiBlockDataSet,
    vtkPolyData,
    vtkUnstructuredGrid,
)
from vtkmodules.vtkFiltersGeometry import vtkDataSetSurfaceFilter

from geos.mesh.utils.multiblockHelpers import getElementaryCompositeBlockIndexes, extractBlock
from geos.mesh.utils.arrayHelpers import getAttributeSet
from geos.mesh.utils.arrayModifiers import createConstantAttribute, renameAttribute
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

    # instantiate the filter
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
        self.m_inputMesh: vtkMultiBlockDataSet = inputMesh
        self.m_outputMesh: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        self.m_convertFaultToSurface: bool = False
        self.phaseNameDict: dict[ str, set[ str ] ] = {
            PhaseTypeEnum.ROCK.type: set(),
            PhaseTypeEnum.FLUID.type: set(),
        }

        # set logger
        self.m_logger: Logger = getLogger( "Geos Block Merge Filter" )

    def SetLogger( self: Self, logger: Logger ) -> None:
        """Set the logger.

        Args:
            logger (Logger): logger
        """
        self.m_logger = logger

    def ConvertSurfaceMeshOn( self: Self ) -> None:
        """Activate surface conversion from vtkUnstructuredGrid to vtkPolyData."""
        self.m_convertFaultToSurface = True

    def ConvertSurfaceMeshOff( self: Self ) -> None:
        """Deactivate surface conversion from vtkUnstructuredGrid to vtkPolyData."""
        self.m_convertFaultToSurface = False

    def getOutput ( self: Self ) -> vtkMultiBlockDataSet:
        """Get the mesh with the composite blocks merged."""
        return self.m_outputMesh

    def applyFilter( self: Self ) -> None:
        """Merge all elementary node that belong to a same parent node."""
        try:
            # Display phase names
            self.commutePhaseNames()
            for phase, phaseNames in self.phaseNameDict.items():
                if len( phaseNames ) > 0:
                    self.m_logger.info( f"Identified { phase } phase(s) are: { phaseNames }." )
                else:
                    self.m_logger.info( f"No { phase } phase has been identified." )

            # Merge all the composite blocks
            compositeBlockIndexesToMerge: dict[ str, int ] = getElementaryCompositeBlockIndexes( self.m_inputMesh )
            nbBlocks: int = len( compositeBlockIndexesToMerge )
            self.m_outputMesh.SetNumberOfBlocks( nbBlocks )
            for newIndex, ( blockName, blockIndex ) in enumerate( compositeBlockIndexesToMerge.items() ):
                # Set the name of the merged block
                self.m_outputMesh.GetMetaData( newIndex ).Set( vtkCompositeDataSet.NAME(), blockName )

                # Merge blocks
                blockToMerge: vtkMultiBlockDataSet = extractBlock( self.m_inputMesh, blockIndex )
                volumeMesh: vtkUnstructuredGrid = mergeBlocks( blockToMerge, keepPartialAttributes=True, logger=self.m_logger )

                # Create index attribute keeping the index in initial mesh
                if not createConstantAttribute( volumeMesh, [ blockIndex ], PostProcessingOutputsEnum.BLOCK_INDEX.attributeName, onPoints=False, logger=self.m_logger ):
                    self.m_logger.warning( "BlockIndex attribute was not created." )

                # Rename attributes
                self.renameAttributes( volumeMesh )

                # Convert the volume mesh to a surface mesh
                if self.m_convertFaultToSurface:
                    surfaceMesh: vtkPolyData = self.convertBlockToSurface( volumeMesh )
                    assert surfaceMesh is not None, "Surface extraction from block failed."
                    surfaceMesh.ShallowCopy( computeNormals( surfaceMesh, logger=self.m_logger ) )
                    assert surfaceMesh is not None, "Normal calculation failed."
                    surfaceMesh.ShallowCopy( computeTangents( surfaceMesh, logger=self.m_logger ) )
                    assert surfaceMesh is not None, "Tangent calculation failed."
                # Add the merged block to the output
                    self.m_outputMesh.SetBlock( newIndex, surfaceMesh )
                else:
                    self.m_outputMesh.SetBlock( newIndex, volumeMesh )
        except ( ValueError, TypeError, RuntimeError ) as e:
            self.m_logger.critical( "Geos block merge failed due to:" )
            self.m_logger.critical( e, exc_info=True )

        return

    def renameAttributes(
        self: Self,
        mesh: vtkUnstructuredGrid,
    ) -> None:
        """Rename attributes to harmonize throughout the mesh.

        Args:
            mesh (vtkMultiBlockDataSet): input mesh
            phaseClassification (dict[str, PhaseTypeEnum]): phase classification
                detected from attributes
        """
        for attributeName in getAttributeSet( mesh, False ):
            for suffix, newName in getRockSuffixRenaming().items():
                if suffix in attributeName:
                    if suffix == "_density":
                        for phaseName in self.phaseNameDict[ PhaseTypeEnum.ROCK.type ]:
                            if phaseName in attributeName:
                                renameAttribute( mesh, attributeName, newName, False )
                    elif suffix != "_density":
                        renameAttribute( mesh, attributeName, newName, False )

    def commutePhaseNames( self: Self ) -> None:
        """Get the names of the phases in the mesh from Cell attributes."""
        for name in getAttributeSet( self.m_inputMesh, False ):
            if PHASE_SEP in name:
                index = name.rindex( PHASE_SEP )
                phaseName: str = name[ :index ]
                suffixName: str = name[ index: ]
                if suffixName == "_density":
                    if any( phaseName in fluidPrefix.value for fluidPrefix in list( FluidPrefixEnum ) ):
                        self.phaseNameDict[ PhaseTypeEnum.FLUID.type ].add( phaseName )
                    else:
                        self.phaseNameDict[ PhaseTypeEnum.ROCK.type ].add( phaseName )
                elif suffixName in PhaseTypeEnum.ROCK.attributes:
                    self.phaseNameDict[ PhaseTypeEnum.ROCK.type ].add( phaseName )
                elif suffixName in PhaseTypeEnum.FLUID.attributes:
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
