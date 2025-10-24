# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay, Romain Baville
import logging
from dataclasses import dataclass
from typing_extensions import Self

from geos.utils.Logger import ( Logger, getLogger )
from geos.utils.GeosOutputsConstants import ( GeosDomainNameEnum )
from geos.mesh.utils.arrayHelpers import ( getCellDimension )
from geos.mesh.utils.multiblockHelpers import ( getBlockIndexFromName )

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet
from vtkmodules.vtkFiltersExtraction import vtkExtractBlock

__doc__ = """
GeosBlockExtractor is a vtk filter that allows to extract the domain (volume, fault and well) from a GEOS output multiBlockDataset mesh.

.. Important::
    The input mesh must be an output of a GEOS simulation or contain at least three blocks labeled with the same domain names:
        "CellElementRegion" for volume domain
        "SurfaceElementRegion" for fault domain
        "WellElementRegion" for well domain
        See more https://geosx-geosx.readthedocs-hosted.com/en/latest/docs/sphinx/datastructure/ElementRegions.html?_sm_au_=iVVT5rrr5fN00R8sQ0WpHK6H8sjL6#xml-element-elementregions

.. Note::
    Volume domain is automatically extracted, by defaults Fault and Well domains are empty multiBlockDataSet.

To use the filter:

.. code-block:: python

    from geos.mesh.processing.GeosBlockExtractor import GeosBlockExtractor

    # Filter inputs.
    geosMesh: vtkMultiBlockDataSet
    # Optional inputs.
    extractFault: bool # Defaults to False
    extractWell: bool # Defaults to False
    speHandler: bool # Defaults to False

    # Instantiate the filter
    filter: GeosBlockExtractor = GeosBlockExtractor( geosMesh, extractFault, extractWell, speHandler )

    # Set the handler of yours (only if speHandler is True).
    yourHandler: logging.Handler
    filter.setLoggerHandler( yourHandler )

    # Do calculations
    filter.applyFilter()

    # Get the multiBlockDataSet with blocks of the extracted domain.
    geosDomainExtracted: vtkMultiBlockDataSet
    geosDomainExtracted = filter.extractedGeosDomain.volume # For volume domain
    geosDomainExtracted = filter.extractedGeosDomain.fault # For fault domain
    geosDomainExtracted = filter.extractedGeosDomain.well # For well domain
"""

loggerTitle: str = "Geos Block Extractor Filter"


class GeosExtractDomainBlock( vtkExtractBlock ):

    def __init__( self: Self ) -> None:
        """Extract blocks from a GEOS output multiBlockDataset mesh."""

    def AddGeosDomainName( self: Self, geosDomainName: GeosDomainNameEnum ) -> None:
        """Add the index of the GEOS domain to extract from its name.

        Args:
            geosDomainName (GeosDomainNameEnum): Name of the GEOS domain to extract.
        """
        domainBlockIndex: int = getBlockIndexFromName( self.GetInput(), geosDomainName.value )
        return super().AddIndex( domainBlockIndex )


class GeosBlockExtractor:

    @dataclass
    class ExtractedGeosDomain:
        """The dataclass with the three GEOS domain mesh."""
        _volume: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _fault: vtkMultiBlockDataSet = vtkMultiBlockDataSet()
        _well: vtkMultiBlockDataSet = vtkMultiBlockDataSet()

        @property
        def volume( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS CellElementRegion."""
            return self._volume

        @volume.setter
        def volume( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            cellDim: set[ int ] = getCellDimension( multiBlockDataSet )
            if len( cellDim ) == 1 and 3 in cellDim:
                self._volume.DeepCopy( multiBlockDataSet )
            else:
                raise TypeError( "The input mesh must be a volume mesh with cells dimension equal to 3." )

        @property
        def fault( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS SurfaceElementRegion."""
            return self._fault

        @fault.setter
        def fault( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            cellDim: set[ int ] = getCellDimension( multiBlockDataSet )
            if len( cellDim ) == 1 and 2 in cellDim:
                self._fault.DeepCopy( multiBlockDataSet )
            else:
                raise TypeError( "The input mesh must be a surface mesh with cells dimension equal to 2." )

        @property
        def well( self: Self ) -> vtkMultiBlockDataSet:
            """Get the mesh with the blocks of the GEOS WellElementRegion."""
            return self._well

        @well.setter
        def well( self: Self, multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            cellDim: set[ int ] = getCellDimension( multiBlockDataSet )
            if len( cellDim ) == 1 and 1 in cellDim:
                self._well.DeepCopy( multiBlockDataSet )
            else:
                raise TypeError( "The input mesh must be a segment mesh with cells dimension equal to 1." )

        def setExtractedDomain( self: Self, geosDomainName: GeosDomainNameEnum,
                                multiBlockDataSet: vtkMultiBlockDataSet ) -> None:
            """Set the mesh to the correct domain.

            Args:
                geosDomainName (GeosDomainNameEnum): Name of the GEOS domain.
                multiBlockDataSet (vtkMultiBlockDataSet): The mesh to set.
            """
            if geosDomainName.value == "CellElementRegion":
                self.volume = multiBlockDataSet
            elif geosDomainName.value == "SurfaceElementRegion":
                self.fault = multiBlockDataSet
            elif geosDomainName.value == "WellElementRegion":
                self.well = multiBlockDataSet
            else:
                raise ValueError(
                    f"The GEOS extractable domains are { GeosDomainNameEnum.VOLUME_DOMAIN_NAME.value }, { GeosDomainNameEnum.FAULT_DOMAIN_NAME.value } and { GeosDomainNameEnum.WELL_DOMAIN_NAME.value }."
                )

    extractedGeosDomain: ExtractedGeosDomain

    def __init__(
        self: Self,
        geosMesh: vtkMultiBlockDataSet,
        extractFault: bool = False,
        extractWell: bool = False,
        speHandler: bool = False,
    ) -> None:
        """Blocks from the ElementRegions from a GEOS output multiBlockDataset mesh.

        Args:
            geosMesh (vtkMultiBlockDataSet): The mesh from Geos.
            extractFault (bool, Optional): True if SurfaceElementRegion needs to be extracted, False otherwise.
                Defaults to False.
            extractWell (bool, Optional): True if WellElementRegion needs to be extracted, False otherwise.
                Defaults to False.
            speHandler (bool, optional): True to use a specific handler, False to use the internal handler.
                Defaults to False.
        """
        self.geosMesh: vtkMultiBlockDataSet = geosMesh
        self.extractedGeosDomain = self.ExtractedGeosDomain()

        self.domainToExtract: list[ GeosDomainNameEnum ] = [ GeosDomainNameEnum.VOLUME_DOMAIN_NAME ]
        if extractFault:
            self.domainToExtract.append( GeosDomainNameEnum.FAULT_DOMAIN_NAME )
        if extractWell:
            self.domainToExtract.append( GeosDomainNameEnum.WELL_DOMAIN_NAME )

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

    def applyFilter( self: Self ) -> None:
        """Extract the volume, the fault or the well domain of the mesh from GEOS."""
        self.logger.info( f"Apply filter { self.logger.name }." )

        try:
            extractGeosDomain: GeosExtractDomainBlock = GeosExtractDomainBlock()
            extractGeosDomain.SetInputData( self.geosMesh )

            for domain in self.domainToExtract:
                extractGeosDomain.RemoveAllIndices()
                extractGeosDomain.AddGeosDomainName( domain )
                extractGeosDomain.Update()
                self.extractedGeosDomain.setExtractedDomain( domain, extractGeosDomain.GetOutput() )

            self.logger.info( "The filter succeeded." )

        except ValueError as ve:
            self.logger.error( f"The filter failed.\n{ ve }." )
        except TypeError as te:
            self.logger.error( f"The filter failed.\n{ te }." )
