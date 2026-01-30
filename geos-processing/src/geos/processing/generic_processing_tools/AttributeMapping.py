# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Raphaël Vinour, Martin Lemay, Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import logging
from typing_extensions import Self, Union
from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet
from geos.mesh.utils.arrayModifiers import transferAttributeWithElementMap
from geos.mesh.utils.arrayHelpers import ( computeElementMapping, getAttributeSet, isAttributeGlobal )
from geos.utils.Logger import ( getLogger, Logger, CountWarningHandler )
from geos.utils.pieceEnum import Piece

__doc__ = """
AttributeMapping is a vtk filter that transfers global attributes from a source mesh to a final mesh with same
point/cell coordinates. The final mesh is updated directly, without creation of a copy.

Input meshes can be vtkDataSet or vtkMultiBlockDataSet.

.. Warning::
    For one application of the filter, the attributes to transfer should all be located on the same piece
    (all on points or all on cells).

.. Note::
    For cell, the coordinates of the points in the cell are compared.
    If one of the two meshes is a surface and the other a volume,
    all the points of the surface must be points of the volume.

To use a logger handler of yours, set the variable 'speHandler' to True
and add it using the member function setLoggerHandler.

To use the filter:

.. code-block:: python

    import logging
    from geos.processing.generic_processing_tools.AttributeMapping import AttributeMapping

    # Filter inputs.
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ]
    attributeNames: set[ str ]
    # Optional inputs.
    piece: Piece  # defaults to Piece.CELLS
    speHandler: bool  # defaults to False

    # Instantiate the filter
    attributeMappingFilter: AttributeMapping = AttributeMapping(
        meshFrom,
        meshTo,
        attributeNames,
        piece,
        speHandler,
    )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    attributeMappingFilter.setLoggerHandler( yourHandler )

    # Do calculations.
    try:
        attributeMappingFilter.applyFilter()
    except( ValueError, AttributeError ) as e:
        attributeMappingFilter.logger.error( f"The filter { attributeMappingFilter.logger.name } failed due to: { e }" )
    except Exception as e:
        mess: str = f"The filter { attributeMappingFilter.logger.name } failed due to: { e }"
        attributeMappingFilter.logger.critical( mess, exc_info=True )
"""

loggerTitle: str = "Attribute Mapping"


class AttributeMapping:

    def __init__(
        self: Self,
        meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ],
        meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ],
        attributeNames: set[ str ],
        piece: Piece = Piece.CELLS,
        speHandler: bool = False,
    ) -> None:
        """Transfer global attributes from a source mesh to a final mesh.

        Mapping the piece of the attributes to transfer.

        Args:
            meshFrom (Union[vtkDataSet, vtkMultiBlockDataSet]): The source mesh with attributes to transfer.
            meshTo (Union[vtkDataSet, vtkMultiBlockDataSet]): The final mesh where to transfer attributes.
            attributeNames (set[str]): Names of the attributes to transfer.
            piece (Piece): The piece of the attribute.
                Defaults to Piece.CELLS.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshFrom
        self.meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = meshTo
        self.attributeNames: set[ str ] = attributeNames
        self.piece: Piece = piece

        # Element map
        self.ElementMap: dict[ int, npt.NDArray[ np.int64 ] ] = {}

        # Logger
        self.logger: Logger
        if not speHandler:
            self.logger = getLogger( loggerTitle, True )
        else:
            self.logger = logging.getLogger( loggerTitle )
            self.logger.setLevel( logging.INFO )
            self.logger.propagate = False

    def setLoggerHandler( self: Self, handler: logging.Handler ) -> None:
        """Set a specific handler for the filter logger.

        In this filter 4 log levels are use, .info, .error, .warning and .critical,
        be sure to have at least the same 4 levels.

        Args:
            handler (logging.Handler): The handler to add.
        """
        if len( self.logger.handlers ) == 0:
            self.logger.addHandler( handler )
        else:
            self.logger.warning( "The logger already has an handler, to use yours set the argument 'speHandler'"
                                 " to True during the filter initialization." )

    def getElementMap( self: Self ) -> dict[ int, npt.NDArray[ np.int64 ] ]:
        """Getter of the element mapping dictionary.

        If attribute to transfer are on points it will be a pointMap, else it will be a cellMap.

        Returns:
            self.elementMap (dict[int, npt.NDArray[np.int64]]): The element mapping dictionary.
        """
        return self.ElementMap

    def applyFilter( self: Self ) -> None:
        """Transfer global attributes from a source mesh to a final mesh.

        Mapping the piece of the attributes to transfer.

        Raises:
            ValueError: Errors with the input attributeNames or the input mesh.
            AttributeError: Errors with the attribute of the mesh.
        """
        self.logger.info( f"Apply filter { self.logger.name }." )
        # Add the handler to count warnings messages to the logger.
        self.counter: CountWarningHandler = CountWarningHandler()
        self.counter.setLevel( logging.INFO )
        self.logger.addHandler( self.counter )

        if len( self.attributeNames ) == 0:
            raise ValueError( "Please enter at least one attribute to transfer." )

        attributesInMeshFrom: set[ str ] = getAttributeSet( self.meshFrom, self.piece )
        wrongAttributeNames: set[ str ] = self.attributeNames.difference( attributesInMeshFrom )
        if len( wrongAttributeNames ) > 0:
            raise AttributeError( f"The attributes { wrongAttributeNames } are not present in the source mesh." )

        attributesInMeshTo: set[ str ] = getAttributeSet( self.meshTo, self.piece )
        attributesAlreadyInMeshTo: set[ str ] = self.attributeNames.intersection( attributesInMeshTo )
        if len( attributesAlreadyInMeshTo ) > 0:
            raise AttributeError(
                f"The attributes { attributesAlreadyInMeshTo } are already present in the final mesh." )

        if isinstance( self.meshFrom, vtkMultiBlockDataSet ):
            partialAttributes: list[ str ] = []
            for attributeName in self.attributeNames:
                if not isAttributeGlobal( self.meshFrom, attributeName, self.piece ):
                    partialAttributes.append( attributeName )

            if len( partialAttributes ) > 0:
                raise AttributeError(
                    f"All attributes to transfer must be global, { partialAttributes } are partials." )

        self.ElementMap = computeElementMapping( self.meshFrom, self.meshTo, self.piece )
        sharedElement: bool = False
        for key in self.ElementMap:
            if np.any( self.ElementMap[ key ] > -1 ):
                sharedElement = True

        if not sharedElement:
            raise ValueError( f"The two meshes do not have any shared { self.piece.value }." )

        for attributeName in self.attributeNames:
            transferAttributeWithElementMap( self.meshFrom, self.meshTo, self.ElementMap, attributeName, self.piece,
                                             self.logger )

        # Log the output message.
        self.logger.info(
            f"The attributes { self.attributeNames } have been transferred from the source mesh to the final mesh with a { self.piece.value } mapping.\n"
        )
        result: str = f"The filter { self.logger.name } succeeded"
        if self.counter.warningCount > 0:
            self.logger.warning( f"{ result } but { self.counter.warningCount } warnings have been logged." )
        else:
            self.logger.info( f"{ result }." )
