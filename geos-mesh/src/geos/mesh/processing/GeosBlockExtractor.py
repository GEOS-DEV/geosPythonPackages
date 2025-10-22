# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
import logging
from dataclasses import dataclass
from typing_extensions import Self

from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.GeosOutputsConstants import ( GeosDomainNameEnum )
from geos.mesh.utils.multiblockHelpers import ( getBlockIndexFromName )

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from vtkmodules.vtkFiltersExtraction import vtkExtractBlock

__doc__ = """
GeosBlockExtractor is a vtk filter that allows to extract blocks from the ElementRegions from a GEOS output multiBlockDataset mesh.

The three ElementRegions are:
    0: CellElementRegion,
    1: SurfaceElementRegion,
    2: WellElementRegion,

.. Important::
    The input mesh must be an output of a GEOS simulation or contain blocks labeled with the same names.
    See more: https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/ElementRegions.html?_sm_au_=iVVT5rrr5fN00R8sQ0WpHK6H8sjL6#xml-element-elementregions

.. Note::
    CellElementRegion is automatically extracted, by defaults SurfaceElementRegion and SurfaceElementRegion are empty multiBlockDataSet.

To use the filter:

.. code-block:: python

    from geos.mesh.processing.GeosBlockExtractor import GeosBlockExtractor

    # Filter inputs.
    geosMesh: vtkMultiBlockDataSet
    # Optional inputs.
    extractSurface: bool # Defaults to False
    extractWell: bool # Defaults to False
    speHandler: bool # Defaults to False

    # Instantiate the filter
    filter: GeosBlockExtractor = GeosBlockExtractor( geosMesh, extractSurface, extractWell, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations
    filter.applyFilter()

    # Get the multiBlockDataSet with blocks of the extracted ElementRegions
    elementRegionId: int
    elementRegionExtracted: vtkMultiBlockDataSet = filter.getOutput( elementRegionId )
"""

loggerTitle: str = "Geos Block Extractor Filter"


class GeosExtractElementRegionsBlock( vtkExtractBlock ):

    def __init__( self: Self ) -> None:
        """Extract ElementRegions block from a GEOS output multiBlockDataset mesh."""
        super().__init__()

        self.geosElementRegionsName: dict[ int, str ] = {
            0: GeosDomainNameEnum.VOLUME_DOMAIN_NAME.value,
            1: GeosDomainNameEnum.FAULT_DOMAIN_NAME.value,
            2: GeosDomainNameEnum.WELL_DOMAIN_NAME.value,
        }

    def GetGeosElementRegionsName( self: Self, elementRegionId: int ) -> str:
        """Get the name of the GEOS ElementRegions from its index.

        Args:
            elementRegionId (int): The index of the GEOS ElementRegions.

        Returns:
            str: The name of the GEOS ElementRegions.
        """
        return self.geosElementRegionsName[ elementRegionId ]

    def AddGeosElementRegionsBlockIndex( self, elementRegionId: int ) -> None:
        """Add the index of the wanted GEOS ElementRegions to extract.

        The GEOS ElementRegions indexes are:
            0: CellElementRegion,
            1: SurfaceElementRegion,
            2: WellElementRegion,

        Args:
            elementRegionId (int): Index of the GEOS ElementRegions to extract.
        """
        elementRegionsBlockIndex: int = getBlockIndexFromName( self.GetInput(),
                                                               self.geosElementRegionsName[ elementRegionId ] )
        return super().AddIndex( elementRegionsBlockIndex )


class GeosBlockExtractor:

    @dataclass
    class ExtractedElementRegionsMesh:
        """The dataclass with the three GEOS ElementRegions mesh."""
        _cell: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _surface: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _well: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        @property
        def cell( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS CellElementRegion."""
            return self._cell

        @cell.setter
        def cell( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._cell.DeepCopy( multiBlockDataSet )

        @property
        def surface( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS SurfaceElementRegion."""
            return self._surface

        @surface.setter
        def surface( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._surface.DeepCopy( multiBlockDataSet )

        @property
        def well( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS WellElementRegion."""
            return self._well

        @well.setter
        def well( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._well.DeepCopy( multiBlockDataSet )

        def getExtractedElementRegions( self: Self, elementRegionId: int ) -> vtkMultiBlockDataSet:
            """Get the GEOS ElementRegions mesh extracted from its index.

            The GEOS ElementRegions indexes are:
                0: CellElementRegion,
                1: SurfaceElementRegion,
                2: WellElementRegion,

            Args:
                elementRegionId (int): Index of the GEOS ElementRegions to get.

            Returns:
                vtkMultiBlockDataSet: The mesh with the GEOS ElementRegions blocks.
            """
            if elementRegionId == 0:
                return self.cell
            elif elementRegionId == 1:
                return self.surface
            elif elementRegionId == 2:
                return self.well
            else:
                raise IndexError

        def setExtractedElementRegions( self: Self, elementRegionId: int,
                                        multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            """Set the mesh to the correct ElementRegions.

            Args:
                elementRegionId (int): Index of the GEOS ElementRegions.
                multiBlockDataSet (vtkMultiBlockDataSet): The mesh to set.
            """
            if elementRegionId == 0:
                self.cell = multiBlockDataSet
            elif elementRegionId == 1:
                self.surface = multiBlockDataSet
            elif elementRegionId == 2:
                self.well = multiBlockDataSet

    extractedElementRegions: ExtractedElementRegionsMesh

    def __init__(
        self: Self,
        geosMesh: vtkMultiBlockDataSet,
        extractSurface: bool = False,
        extractWell: bool = False,
        speHandler: bool = False,
    ) -> None:
        """Blocks from the ElementRegions from a GEOS output multiBlockDataset mesh.

        Args:
            geosMesh (vtkMultiBlockDataSet): The mesh from Geos.
            extractSurface (bool, Optional): True if SurfaceElementRegion needs to be extracted, False otherwise.
                Defaults to False.
            extractWell (bool, Optional): True if WellElementRegion needs to be extracted, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.geosMesh: vtkMultiBlockDataSet = geosMesh
        self.extractedElementRegions = self.ExtractedElementRegionsMesh()

        self.elementRegionsIdToExtract: list[ int ] = [ 0 ]
        if extractSurface:
            self.elementRegionsIdToExtract.append( 1 )
        if extractWell:
            self.elementRegionsIdToExtract.append( 2 )

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

    def applyFilter( self: Self ) -> bool:
        """Extract the volume, the surface or the well domain of the mesh from Geos.

        Returns:
            bool: True if calculation successfully ended, False otherwise.
        """
        extractElementRegions: GeosExtractElementRegionsBlock = GeosExtractElementRegionsBlock()
        extractElementRegions.SetInputData( self.geosMesh )

        for elementRegionId in self.elementRegionsIdToExtract:
            extractElementRegions.RemoveAllIndices()
            extractElementRegions.AddGeosElementRegionsBlockIndex( elementRegionId )
            extractElementRegions.Update()
            self.extractedElementRegions.setExtractedElementRegions( elementRegionId,
                                                                     extractElementRegions.GetOutput() )
            if self.extractedElementRegions.getExtractedElementRegions( elementRegionId ).GetNumberOfBlocks() == 0:
                self.logger.error(
                    f"The input mesh does not have { extractElementRegions.GetGeosElementRegionsName( elementRegionId ) } to extract."
                )
                return False

        return True

    def getOutput( self: Self, elementRegionId: int ) -> vtkMultiBlockDataSet:
        """Get the GEOS ElementRegions extracted from its index.

        The GEOS ElementRegions indexes are:
            0: CellElementRegion,
            1: SurfaceElementRegion,
            2: WellElementRegion,

        Args:
            elementRegionId (int): Index of the GEOS ElementRegions to get.

        Returns:
            vtkMultiBlockDataSet: The GEOS ElementRegions mesh extracted.
        """
        return self.extractedElementRegions.getExtractedElementRegions( elementRegionId )
