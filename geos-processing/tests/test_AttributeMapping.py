# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Union, Any
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.processing.generic_processing_tools.AttributeMapping import AttributeMapping
from geos.processing.generic_processing_tools.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet
from geos.utils.pieceEnum import Piece


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, piece", [
    ( "extractAndMergeWell1", "extractAndMergeWell1", { "newAttribute" }, Piece.CELLS ),
    ( "extractAndMergeFaultVtp", "extractAndMergeVolume", { "deltaSlip" }, Piece.CELLS ),
    ( "extractAndMergeFault", "extractAndMergeVolume", { "deltaSlip" }, Piece.CELLS ),
    ( "extractAndMergeFault", "extractAndMergeVolume", { "Texture Coordinates" }, Piece.POINTS ),
    ( "extractAndMergeFault", "extractAndMergeVolumeWell1", { "Texture Coordinates" }, Piece.POINTS ),
    ( "extractAndMergeFaultVtp", "extractAndMergeVolumeWell1", { "Texture Coordinates" }, Piece.POINTS ),
    ( "extractAndMergeVolume", "extractAndMergeFaultVtp", { "averageStrain" }, Piece.CELLS ),
    ( "extractAndMergeVolume", "extractAndMergeFault", { "averageStrain" }, Piece.CELLS ),
    ( "extractAndMergeVolume", "extractAndMergeFault", { "totalDisplacement" }, Piece.POINTS ),
    ( "extractAndMergeVolume", "extractAndMergeFaultWell1", { "totalDisplacement" }, Piece.POINTS ),
    ( "extractAndMergeFaultWell1", "extractAndMergeVolume", { "Texture Coordinates" }, Piece.POINTS ),
    ( "extractAndMergeVolumeWell1", "extractAndMergeFault", { "totalDisplacement" }, Piece.POINTS ),
    ( "extractAndMergeVolumeWell1", "extractAndMergeFaultVtp", { "totalDisplacement" }, Piece.POINTS ),
] )
def test_AttributeMapping(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
    piece: Piece,
) -> None:
    """Test mapping an attribute between two meshes."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    if isinstance( meshFrom, vtkMultiBlockDataSet ):
        fillAllPartialAttributes( meshFrom )

    if meshFromName == meshToName:
        createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
            meshFrom, "blockIndex", {}, "newAttribute" )
        createConstantAttributePerRegionFilter.applyFilter()

    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, piece )
    attributeMappingFilter.applyFilter()


@pytest.mark.parametrize(
    "meshFromName, meshToName, attributeNames",
    [
        ( "extractAndMergeVolume", "extractAndMergeFault", { "Fault" } ),  # Attribute not in the mesh from
        ( "extractAndMergeVolume", "extractAndMergeFault", { "deltaPressure" } ),  # Attribute on both meshes
        ( "extractAndMergeVolumeWell1", "extractAndMergeFault", { "totalDisplacement"
                                                                 } ),  # Partial attribute in the mesh from
    ] )
def test_AttributeMappingRaisesAttributeError(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
) -> None:
    """Test the fails of the filter with attributes issues."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, Piece.CELLS )

    with pytest.raises( AttributeError ):
        attributeMappingFilter.applyFilter()


@pytest.mark.parametrize(
    "meshToName, attributeNames",
    [
        ( "extractAndMergeFault", {} ),  # No attribute to map
        ( "extractAndMergeWell1", { "mass" } ),  # Meshes with no common cells
    ] )
def test_AttributeMappingRaisesValueError(
    dataSetTest: Any,
    meshToName: str,
    attributeNames: set[ str ],
) -> None:
    """Test the fails of the filter with input value issue."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "extractAndMergeVolume" )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, Piece.CELLS )

    with pytest.raises( ValueError ):
        attributeMappingFilter.applyFilter()
