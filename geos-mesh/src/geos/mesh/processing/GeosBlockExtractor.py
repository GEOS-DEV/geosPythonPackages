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
GeosBlockExtractor is a vtk filter that allows to extract from an output Geos multiBlockDataSet
all the blocks in a multiBlockDataSet of a Geos domain with its index.

There is tree domains:
    0: all the blocks referring to volume,
    1: all the blocks referring to faults,
    2: all the blocks referring to wells,

.. Important::
    The input mesh must be an output of a Geos simulation.

.. Note::
    The volume domain is automatically extracted, by defaults the fault and well domain are empty multiBlockDataSet.

To use the filter:

.. code-block:: python

    from geos.mesh.processing.GeosBlockExtractor import GeosBlockExtractor

    # Filter inputs.
    geosMesh: vtkMultiBlockDataSet
    # Optional inputs.
    extractFaults: bool # Defaults to False
    extractWells: bool # Defaults to False
    speHandler: bool # Defaults to False

    # Instantiate the filter
    blockExtractor: GeosBlockExtractor = GeosBlockExtractor( geosMesh, extractFaults, extractWells, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations
    filter.applyFilter()

    # Get the mesh of the wanted extracted domain
    domainId: int
    domainExtracted: vtkMultiBlockDataSet = filter.getOutput( domainId )
"""

loggerTitle: str = "Geos Block Extractor Filter"


class GeosExtractDomain( vtkExtractBlock ):

    def __init__( self: Self ) -> None:
        """Extract domain (volume, fault, well) from geos output."""
        super().__init__()

        self.geosDomainName: dict[ int, str ] = {
            0: GeosDomainNameEnum.VOLUME_DOMAIN_NAME.value,
            1: GeosDomainNameEnum.FAULT_DOMAIN_NAME.value,
            2: GeosDomainNameEnum.WELL_DOMAIN_NAME.value,
        }

    def GetGeosDomainName( self: Self, domainId: int ) -> str:
        """Get the name from the Geos domain index.

        Args:
            domainId (int): The index of the Geos domain.

        Returns:
            str: The name of the Geos domain.
        """
        return self.geosDomainName[ domainId ]

    def AddGeosDomainIndex( self, domainId: int ) -> None:
        """Add the index of the wanted Geos domain block to extract.

        The domain type to extract are:
            - Volumes -> domain index = 0
            - Faults -> domain index = 1
            - Wells -> domain index = 2

        Args:
            domainId (int): Index of the Geos domain to extract.
        """
        blockIndex: int = getBlockIndexFromName( self.GetInput(), self.geosDomainName[ domainId ] )
        return super().AddIndex( blockIndex )


class GeosBlockExtractor:

    @dataclass
    class ExtractDomain:
        """The dataclass with the three Geos domains (volume, fault, well)."""
        _volume: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _fault: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _well: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        @property
        def volume( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh corresponding to the Geos volume domain."""
            return self._volume

        @volume.setter
        def volume( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._volume.DeepCopy( multiBlockDataSet )

        @property
        def fault( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh corresponding to the Geos fault domain."""
            return self._fault

        @fault.setter
        def fault( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._fault.DeepCopy( multiBlockDataSet )

        @property
        def well( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh corresponding to the Geos well domain."""
            return self._well

        @well.setter
        def well( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._well.DeepCopy( multiBlockDataSet )

        def getExtractDomain( self: Self, domainId: int ) -> vtkMultiBlockDataSet:
            """Get the mesh for the correct domain.

            Args:
                domainId (int): The index of the Geos domain to get.

            Returns:
                vtkMultiBlockDataSet: The mesh with the Geos domain.
            """
            if domainId == 0:
                return self.volume
            elif domainId == 1:
                return self.fault
            elif domainId == 2:
                return self.well
            else:
                raise IndexError

        def setExtractDomain( self: Self, domainId: int, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            """Set the mesh to the correct domain.

            Args:
                domainId (int): The index of the Geos domain.
                multiBlockDataSet (vtkMultiBlockDataSet): The mesh to set.
            """
            if domainId == 0:
                self.volume = multiBlockDataSet
            elif domainId == 1:
                self.fault = multiBlockDataSet
            elif domainId == 2:
                self.well = multiBlockDataSet

    extractDomain: ExtractDomain = ExtractDomain()

    def __init__(
        self: Self,
        geosMesh: vtkMultiBlockDataSet,
        extractFaults: bool = False,
        extractWells: bool = False,
        speHandler: bool = False,
    ) -> None:
        """Extract the volume, the surface or the well domain block of the mesh from Geos.

        Args:
            geosMesh (vtkMultiBlockDataSet): The mesh from Geos.
            extractFaults (bool, Optional): True if the mesh contains Faults to extract, False otherwise.
                Defaults to False.
            extractWells (bool, Optional): True if the mesh contains wells to extract, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.geosMesh: vtkMultiBlockDataSet = geosMesh

        self.domainIdToExtract: list[ int ] = [ 0 ]
        if extractFaults:
            self.domainIdToExtract.append( 1 )
        if extractWells:
            self.domainIdToExtract.append( 2 )

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
        extractBlock: GeosExtractDomain = GeosExtractDomain()
        extractBlock.SetInputData( self.geosMesh )

        for domainId in self.domainIdToExtract:
            extractBlock.RemoveAllIndices()
            extractBlock.AddGeosDomainIndex( domainId )
            extractBlock.Update()
            self.extractDomain.setExtractDomain( domainId, extractBlock.GetOutput() )
            if self.extractDomain.getExtractDomain( domainId ).GetNumberOfBlocks() == 0:
                self.logger.error(
                    f"The input mesh does not have { extractBlock.GetGeosDomainName( domainId ) } to extract." )
                return False

        return True

    def getOutput( self: Self, domainId: int ) -> vtkMultiBlockDataSet:
        """Get the Geos domain extracted.

        The domain extracted are:
            - Volumes -> domain index = 0
            - Faults -> domain index = 1
            - Wells -> domain index = 2

        Args:
            domainId (int): The index of the Geos domain to get.

        Returns:
            vtkMultiBlockDataSet: The Geos domain extracted.
        """
        return self.extractDomain.getExtractDomain( domainId )
