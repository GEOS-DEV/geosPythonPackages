# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
from geos.utils.GeosOutputsConstants import (
    GeosDomainNameEnum, )
import logging
from dataclasses import dataclass
from geos.utils.Logger import ( Logger, getLogger )
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from vtkmodules.vtkFiltersExtraction import vtkExtractBlock

from geos.mesh.utils.multiblockHelpers import (
    getBlockIndexFromName, )

__doc__ = """
GeosBlockExtractor module is a vtk filter that allows to extract in a vtkMultiblockDataSet
all the block of a domain of the output mesh of geos. The volume blocks are extracted by defaults.

There is tree domains:
    0 is all the blocks with volume mesh,
    1 is all the blocks referring to faults,
    2 is all the blocks referring to wells,

The input mesh must be an output of Geos

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
    blockExtractor :GeosBlockExtractor = GeosBlockExtractor( geosMesh, extractFaults, extractWells, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations
    filter.applyFilter()

    # Get the mesh with the wanted extracted domain
    domain: int
    domainExtracted: vtkMultiBlockDataSet = filter.getOutput( domain )
"""

loggerTitle: str = "Geos Block Extractor Filter"


class GeosExtractDomain( vtkExtractBlock ):

    def __init__( self: Self ) -> None:
        """Extract Bock (volume, surface, well) from geos output."""
        super().__init__()

        self.geosDomainName: dict[ int, str ] = {
            0: GeosDomainNameEnum.VOLUME_DOMAIN_NAME,
            1: GeosDomainNameEnum.FAULT_DOMAIN_NAME,
            2: GeosDomainNameEnum.WELL_DOMAIN_NAME,
        }

    def GetGeosDomainName( self: Self, domainId: int ) -> str:
        return self.geosDomainName[ domainId ]

    def AddGeosDomainIndex( self, domainId: int ) -> None:
        """Add the index of the Geos domain to extract.

        The domain type to extract are:
            - Volumes -> domain index = 0
            - Faults -> domain index = 1
            - Wells -> domain index = 2

        Args:
            domainId (int): Index of the Geos domain to extract.

        """
        domainIndex: int = getBlockIndexFromName( self.geosDomainName[ domainId ] )
        return super().AddIndex( domainIndex )


class GeosBlockExtractor:

    @dataclass
    class ExtractDomain:

        _volume: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _fault: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _well: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        @property
        def volume( self: Self ) -> vtkMultiBlockDataSet:
            return self._volume

        @volume.setter
        def volume( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._volume.DeepCopy( multiBlockDataSet )

        @property
        def fault( self: Self ) -> vtkMultiBlockDataSet:
            return self._fault

        @fault.setter
        def fault( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._fault.DeepCopy( multiBlockDataSet )

        @property
        def well( self: Self ) -> vtkMultiBlockDataSet:
            return self._well

        @well.setter
        def well( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            self._well.DeepCopy( multiBlockDataSet )

        def getExtractDomain( self: Self, domain: int ) -> vtkMultiBlockDataSet:
            if domain == 0:
                return self.volume
            elif domain == 1:
                return self.fault
            elif domain == 2:
                return self.well
            else:
                raise IndexError

        def setExtractDomain( self: Self, domain: int, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            if domain == 0:
                self.volume = multiBlockDataSet
            elif domain == 1:
                self.fault = multiBlockDataSet
            elif domain == 2:
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

        self.domainToExtract: list[ int ] = [ 0 ]
        if extractFaults:
            self.domainToExtract.append( 1 )
        if extractWells:
            self.domainToExtract.append( 2 )

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
        """Extract the volume, the surface or the well domain block of the mesh from Geos.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        extractBlock: GeosExtractDomain = GeosExtractDomain()
        extractBlock.SetInputData( self.geosMesh )

        for domain in self.domainToExtract:
            extractBlock.RemoveAllIndices()
            extractBlock.AddIndex( domain )
            extractBlock.Update()
            self.extractDomain.setExtractDomain( domain, extractBlock.GetOutput() )
            if self.extractDomain.getExtractDomain( domain ).GetNumberOfBlocks() == 0:
                self.logger.error( f"The input mesh does not have { extractBlock.GetGeosDomainName( domain ) } to extract." )
                return False

        return True

    def getOutput( self: Self, domain: int ) -> vtkMultiBlockDataSet:
        """Get the domain extracted.

        The domain extracted are:
            - Volumes -> domain = 0
            - Faults -> domain = 1
            - Wells -> domain = 2

        Args:
            domain (int): The domain to get.

        Returns:
            vtkMultiBlockDataSet: The domain block extracted.
        """
        return self.extractDomain.getExtractDomain( domain )
