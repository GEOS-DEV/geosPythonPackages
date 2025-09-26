# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
from geos.utils.GeosOutputsConstants import (
    GeosDomainNameEnum,
)
import logging
from enum import Enum
from geos.utils.Logger import ( Logger, getLogger )
from typing_extensions import Self, Dict
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

loggerTitle: str =  "Geos Block Extractor Filter"


class GeosExtractDomain( vtkExtractBlock ):

    def __init__( self, **properties ):
        super().__init__( **properties )

        self.geosDomainType: Dict[ int, Enum ] = {
            0: GeosDomainNameEnum.VOLUME_DOMAIN_NAME,
            1: GeosDomainNameEnum.FAULT_DOMAIN_NAME,
            2: GeosDomainNameEnum.WELL_DOMAIN_NAME,
        }

    def AddIndex( self, domainType: int ) -> None:
        """Add the type of the domain to extract.

        The domain type to extract are:
            - Volumes -> block type = 0
            - Faults -> block type = 1
            - Wells -> block type = 2

        Args:
            domainType (int): Type of the domain to extract.

        """
        domainIndex: int = getBlockIndexFromName( self.geosDomainType[ domainType ] )
        return super().AddIndex( domainIndex )

class GeosBlockExtractor:

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

        self.extractFaults: bool = extractFaults
        self.extractWells: bool = extractWells

        self.extractedDomain: Dict[ int, vtkMultiBlockDataSet ] = {
            0: vtkMultiBlockDataSet(),
            1: vtkMultiBlockDataSet(),
            2: vtkMultiBlockDataSet(),
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

    def applyFilter( self: Self ) -> bool:
        """Extract the volume, the surface or the well domain block of the mesh from Geos.

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        extractBlock: GeosExtractDomain = GeosExtractDomain()
        extractBlock.SetInputData( self.geosMesh )
        extractBlock.AddIndex( 0 )
        extractBlock.Update()
        self.extractedDomain[ 0 ].DeepCopy( extractBlock.GetOutput() )
        if self.extractedDomain[ 0 ].GetNumberOfBlocks() == 0:
            self.logger.error( "The input mesh does not have volume to extract." )
            return False

        if self.extractFaults:
            extractBlock.RemoveAllIndices()
            extractBlock.AddIndex( 1 )
            extractBlock.Update()
            self.extractedDomain[ 1 ].DeepCopy( extractBlock.GetOutput() )
            if self.extractedDomain[ 1 ].GetNumberOfBlocks() == 0:
                self.logger.warning( "The input mesh does not have fault to extract." )

        if self.extractWells:
            extractBlock.RemoveAllIndices()
            extractBlock.AddIndex( 2 )
            extractBlock.Update()
            self.extractedDomain[ 2 ].DeepCopy( extractBlock.GetOutput() )
            if self.extractedDomain[ 2 ].GetNumberOfBlocks() == 0:
                self.logger.warning( "The input mesh does not have well to extract." )

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
        return self.extractedDomain[ domain ]

