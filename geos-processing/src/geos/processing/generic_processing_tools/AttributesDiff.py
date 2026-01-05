# SPDX-License-Identifier: Apache 2.0
# SPDX-FileCopyrightText: Copyright 2023-2025 TotalEnergies
# SPDX-FileContributor: Jacques Franc, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import logging

import numpy as np
import numpy.typing as npt
from typing_extensions import Self, Any

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet

from geos.mesh.utils.arrayModifiers import createAttribute
from geos.mesh.utils.arrayHelpers import ( getAttributeSet, getNumberOfComponents, getArrayInObject )
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.pieceEnum import Piece

__doc__ = """
Attributes Diff is a vtk that compute L1 and L2 differences between attributes shared by two identical meshes.

Input meshes cans be vtkDataSet or vtkMultiBlockDataSet.

To use the filter:

.. code-block:: python

    import logging
    from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet
    from geos.processing.generic_processing_tools.AttributesDiff import AttributesDiff
    from geos.utils.pieceEnum import Piece

    # Filter inputs:
    speHandler: bool  # defaults to False

    # Instantiate the filter:
    attributesDiffFilter: AttributesDiff = AttributesDiff( speHandler )

    # Set the handler of yours (only if speHandler is True):
    yourHandler: logging.Handler
    attributesDiffFilter.setLoggerHandler( yourHandler )

    # Set the meshes to compare:
    listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ]
    attributesDiffFilter.setMeshes( listMeshes )

    # Log the shared attributes info (optional):
    attributesDiffFilter.logSharedAttributeInfo()

    # Get the shared attributes (optional):
    dicSharedAttributes: dict[ Piece, set[ str ] ]
    dicSharedAttributes = attributesDiffFilter.getDicSharedAttribute()

    # Set the attributes to compare:
    dicAttributesToCompare: dict[ Piece, set[ str ] ]
    attributesDiffFilter.setDicAttributesToCompare( dicAttributesToCompare )

    # Set the inf norm computation (if wanted):
    computeInfNorm: bool
    attributesDiffFilter.setComputeInfNorm( computeInfNorm )

    # Do calculations:
    attributesDiffFilter.applyFilter()

    # Get the mesh with the computed attributes differences as new attributes:
    outputMesh: vtkMultiBlockDataSet | vtkDataSet
    outputMesh = attributesDiffFilter.getOutput()
"""

loggerTitle: str = "Attributes Diff"


class AttributesDiff:

    def __init__(
        self: Self,
        speHandler: bool = False,
    ) -> None:
        """Compute differences (L1 and inf norm) between two identical meshes attributes.

        By defaults, only the L1 diff is computed, to compute the inf norm, use the setter function.

        Args:
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ] = []
        self.dicNbElements: dict[ Piece, int ] = {}

        self.dicSharedAttributes: dict[ Piece, set[ str ] ] = {}
        self.dicAttributesToCompare: dict[ Piece, set[ str ] ] = {}
        self.dicAttributesDiffNames: dict[ Piece, list[ str ] ] = {}
        self.dicAttributesArray: dict[ Piece, npt.NDArray[ np.float32 ] ] = {}

        self.computeInfNorm: bool = False

        self.outputMesh: vtkMultiBlockDataSet | vtkDataSet = vtkMultiBlockDataSet()

        # Logger.
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if not self.logger.hasHandlers():
            self.logger.addHandler( handler )
        else:
            # This warning does not count for the number of warning created during the application of the filter.
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler' to True"
                                 " during the filter initialization." )

    def setMeshes(
        self: Self,
        listMeshes: list[ vtkMultiBlockDataSet | vtkDataSet ],
    ) -> None:
        """Setter of the two meshes with the attributes to compare.

        Setting the two meshes will automatically compute the dictionary with the shared attribute per localization.

        Args:
            listMeshes (list[vtkMultiBlockDataSet | vtkDataSet]): The list of the meshes to compare.

        Raises:
            TypeError: The meshes do not have the same type.
            ValueError: The meshes do not have the same cells or points number or datasets indexes or the number of meshes is to small.
        """
        if len( listMeshes ) != 2:
            raise ValueError( "The list of meshes must contain two meshes." )

        if listMeshes[ 0 ].GetClassName() != listMeshes[ 1 ].GetClassName():
            raise TypeError( "The meshes must have the same type." )

        dicMeshesMaxElementId: dict[ Piece, list[ int ] ] = {
            Piece.CELLS: [ 0, 0 ],
            Piece.POINTS: [ 0, 0 ],
        }
        if isinstance( listMeshes[ 0 ], vtkDataSet ):
            for meshId, mesh in enumerate( listMeshes ):
                for piece in dicMeshesMaxElementId:
                    dicMeshesMaxElementId[ piece ][ meshId ] = np.max(
                        getArrayInObject( mesh, "localToGlobalMap", piece ) )
        elif isinstance( listMeshes[ 0 ], vtkMultiBlockDataSet ):
            setDatasetType: set[ str ] = set()
            for meshId, mesh in enumerate( listMeshes ):
                listMeshBlockId: list[ int ] = getBlockElementIndexesFlatten( mesh )
                for meshBlockId in listMeshBlockId:
                    setDatasetType.add( mesh.GetDataSet( meshBlockId ).GetClassName() )  # type: ignore[union-attr]
                    dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( meshBlockId ) )  # type: ignore[union-attr]
                    for piece in dicMeshesMaxElementId:
                        dicMeshesMaxElementId[ piece ][ meshId ] = max(
                            dicMeshesMaxElementId[ piece ][ meshId ],
                            np.max( getArrayInObject( dataset, "localToGlobalMap", piece ) ) )
                if len( setDatasetType ) != 1:
                    raise TypeError( "All datasets of the meshes must have the same type." )
        else:
            raise TypeError( "The meshes must be inherited from vtkMultiBlockDataSet or vtkDataSet." )

        for piece, listMeshMaxElementId in dicMeshesMaxElementId.items():
            if listMeshMaxElementId[ 0 ] != listMeshMaxElementId[ 1 ]:
                raise ValueError( f"The total number of { piece.value } in the meshes must be the same." )

        self.listMeshes = listMeshes
        self.dicNbElements[ Piece.CELLS ] = dicMeshesMaxElementId[ Piece.CELLS ][ 0 ] + 1
        self.dicNbElements[ Piece.POINTS ] = dicMeshesMaxElementId[ Piece.POINTS ][ 0 ] + 1
        self.outputMesh = listMeshes[ 0 ].NewInstance()
        self.outputMesh.ShallowCopy( listMeshes[ 0 ] )
        self._computeDicSharedAttributes()

        return

    def _computeDicSharedAttributes( self: Self ) -> None:
        """Compute the dictionary with the shared attributes per localization between the two meshes.

        Keys of the dictionary are the attribute localization and the value are the shared attribute per localization.
        """
        for piece in [ Piece.POINTS, Piece.CELLS ]:
            setSharedAttributes: set[ str ] = getAttributeSet( self.listMeshes[ 0 ], piece ).intersection(
                getAttributeSet( self.listMeshes[ 1 ], piece ) )
            if setSharedAttributes != set():
                self.dicSharedAttributes[ piece ] = setSharedAttributes

        return

    def getDicSharedAttribute( self: Self ) -> dict[ Piece, set[ str ] ]:
        """Getter of the dictionary with the shared attributes per localization."""
        return self.dicSharedAttributes

    def logSharedAttributeInfo( self: Self ) -> None:
        """Log the shared attributes per localization."""
        if self.dicSharedAttributes == {}:
            self.logger.warning( "The two meshes do not share any attribute." )
        else:
            for piece, sharedAttributes in self.dicSharedAttributes.items():
                self.logger.info( f"Shared attributes on { piece.value } are { sharedAttributes }." )

        return

    def setDicAttributesToCompare( self: Self, dicAttributesToCompare: dict[ Piece, set[ str ] ] ) -> None:
        """Setter of the dictionary with the shared attribute per localization to compare.

        Args:
            dicAttributesToCompare (dict[Piece, set[str]]): The dictionary with the attributes to compare per localization.

        Raises:
            ValueError: At least one attribute to compare is not a shared attribute.
        """
        for piece, setSharedAttributesToCompare in dicAttributesToCompare.items():
            if not setSharedAttributesToCompare.issubset( self.dicSharedAttributes[ piece ] ):
                wrongAttributes: set[ str ] = setSharedAttributesToCompare.difference(
                    self.dicSharedAttributes[ piece ] )
                raise ValueError( f"The attributes to compare { wrongAttributes } are not shared attributes." )

        dicNbComponents: dict[ Piece, int ] = {}
        dicAttributesDiffNames: dict[ Piece, list[ str ] ] = {}
        dicAttributesArray: dict[ Piece, npt.NDArray[ np.float32 ] ] = {}
        for piece, setSharedAttributesToCompare in dicAttributesToCompare.items():
            dicNbComponents[ piece ] = 0
            dicAttributesDiffNames[ piece ] = []
            for attributeName in setSharedAttributesToCompare:
                nbAttributeComponents = getNumberOfComponents( self.outputMesh, attributeName, piece )
                dicNbComponents[ piece ] += nbAttributeComponents
                diffAttributeName: str = f"diff_{ attributeName }"
                if nbAttributeComponents > 1:
                    dicAttributesDiffNames[ piece ].extend( [
                        diffAttributeName + "_component" + str( idAttributeComponent )
                        for idAttributeComponent in range( nbAttributeComponents )
                    ] )
                else:
                    dicAttributesDiffNames[ piece ].append( diffAttributeName )
            dicAttributesArray[ piece ] = np.zeros( shape=( self.dicNbElements[ piece ], dicNbComponents[ piece ], 2 ),
                                                    dtype=np.float32 )

        self.dicAttributesArray = dicAttributesArray
        self.dicAttributesToCompare = dicAttributesToCompare
        self.dicAttributesDiffNames = dicAttributesDiffNames

        return

    def getDicAttributesToCompare( self: Self ) -> dict[ Piece, set[ str ] ]:
        """Getter of the dictionary of the attribute to compare per localization."""
        return self.dicAttributesToCompare

    def getDicAttributesDiffNames( self: Self ) -> dict[ Piece, list[ str ] ]:
        """Getter of the dictionary with the name of the attribute created with the calculated attributes diff."""
        return self.dicAttributesDiffNames

    def setComputeInfNorm( self: Self, computeInfNorm: bool ) -> None:
        """Setter of computeInfNorm to compute the info norm in addition to the l1 diff.

        Args:
            computeInfNorm (bool): True to compute the inf norm, False otherwise.
        """
        self.computeInfNorm = computeInfNorm

    def applyFilter( self: Self ) -> None:
        """Apply the diffFieldsFilter."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        if self.listMeshes == []:
            raise ValueError( "Set a list of meshes to compare." )

        if self.dicAttributesToCompare == {}:
            raise ValueError( "Set the attribute to compare per localization." )

        self._computeDicAttributesArray()
        self._computeDiffs()

        self.logger.info( f"The filter { self.logger.name } succeed." )

        return

    def _computeDicAttributesArray( self: Self ) -> None:
        """Compute the dictionary with one array per localization with all the values of all the attributes to compare."""
        for piece, sharedAttributesToCompare in self.dicAttributesToCompare.items():
            idComponents: int = 0
            for attributeName in sharedAttributesToCompare:
                arrayAttributeData: npt.NDArray[ Any ]
                nbAttributeComponents: int
                for meshId, mesh in enumerate( self.listMeshes ):
                    if isinstance( mesh, vtkDataSet ):
                        arrayAttributeData = getArrayInObject( mesh, attributeName, piece )
                        nbAttributeComponents = getNumberOfComponents( mesh, attributeName, piece )
                        self.dicAttributesArray[ piece ][ :, idComponents:idComponents + nbAttributeComponents,
                                                          meshId ] = arrayAttributeData.reshape(
                                                              self.dicNbElements[ piece ], nbAttributeComponents )
                    else:
                        listMeshBlockId: list[ int ] = getBlockElementIndexesFlatten( mesh )
                        for meshBlockId in listMeshBlockId:
                            dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( meshBlockId ) )
                            arrayAttributeData = getArrayInObject( dataset, attributeName, piece )
                            nbAttributeComponents = getNumberOfComponents( dataset, attributeName, piece )
                            lToG: npt.NDArray[ Any ] = getArrayInObject( dataset, "localToGlobalMap", piece )
                            self.dicAttributesArray[ piece ][ lToG, idComponents:idComponents + nbAttributeComponents,
                                                              meshId ] = arrayAttributeData.reshape(
                                                                  len( lToG ), nbAttributeComponents )

                idComponents += nbAttributeComponents

        return

    def _computeDiffs( self: Self ) -> None:
        """Compute for all the wanted attributes differences between the meshes.

        The differences computed are:
            - L1 diff (absolute difference), the result is a new attribute created on the first mesh
            - Inf norm (square root difference), the result is logged (if self.computeInfNorm is True)
        """
        for piece in self.dicAttributesDiffNames:
            for attributeId, attributeDiffName in enumerate( self.dicAttributesDiffNames[ piece ] ):
                attributeArray: npt.NDArray[ Any ]
                l2: Any
                if isinstance( self.outputMesh, vtkDataSet ):
                    attributeArray = self.dicAttributesArray[ piece ][ :, attributeId, 0 ] - self.dicAttributesArray[
                        piece ][ :, attributeId, 1 ]
                    createAttribute( self.outputMesh,
                                     np.abs( attributeArray ),
                                     attributeDiffName,
                                     piece=piece,
                                     logger=self.logger )
                    if self.computeInfNorm:
                        l2 = np.linalg.norm( attributeArray, ord=np.inf )
                        self.logger.info( f"The inf norm of { attributeDiffName } is { l2 }." )
                else:
                    listBlockId: list[ int ] = getBlockElementIndexesFlatten( self.outputMesh )
                    l2Max: Any = 0
                    for BlockId in listBlockId:
                        dataset: vtkDataSet = vtkDataSet.SafeDownCast( self.outputMesh.GetDataSet( BlockId ) )
                        lToG: npt.NDArray[ Any ] = getArrayInObject( dataset, "localToGlobalMap", piece )
                        attributeArray = self.dicAttributesArray[ piece ][
                            lToG, attributeId, 0 ] - self.dicAttributesArray[ piece ][ lToG, attributeId, 1 ]
                        createAttribute( dataset,
                                         np.abs( attributeArray ),
                                         attributeDiffName,
                                         piece=piece,
                                         logger=self.logger )
                        if self.computeInfNorm:
                            l2 = np.linalg.norm( attributeArray, ord=np.inf )
                            if l2 > l2Max:
                                l2Max = l2
                    if self.computeInfNorm:
                        self.logger.info( f"The inf norm of { attributeDiffName } is { l2Max }." )

        return

    def getOutput( self: Self ) -> vtkMultiBlockDataSet | vtkDataSet:
        """Return the mesh with the computed diff as attributes for the wanted attributes.

        Returns:
            (vtkMultiBlockDataSet | vtkDataSet): The mesh with the computed attributes diff.
        """
        return self.outputMesh
