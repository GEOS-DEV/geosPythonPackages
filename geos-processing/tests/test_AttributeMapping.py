# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Union, Any
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.processing.generic_processing_tools.AttributeMapping import AttributeMapping
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet
from geos.utils.pieceEnum import Piece


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, piece", [
    ( "fracture", "emptyFracture", { "collocatedNodes" }, Piece.POINTS ),
    ( "multiblock", "emptyFracture", { "FAULT" }, Piece.CELLS ),
    ( "multiblock", "emptymultiblock", { "FAULT" }, Piece.CELLS ),
    ( "dataset", "emptymultiblock", { "FAULT" }, Piece.CELLS ),
    ( "dataset", "emptydataset", { "FAULT" }, Piece.CELLS ),
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

    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, piece )
    attributeMappingFilter.applyFilter()


@pytest.mark.parametrize(
    "meshFromName, meshToName, attributeNames",
    [
        ( "dataset", "emptydataset", { "Fault" } ),  # Attribute not in the mesh from
        ( "dataset", "dataset", { "GLOBAL_IDS_CELLS" } ),  # Attribute on both meshes
        ( "multiblock", "emptymultiblock", { "FAULT" } ),  # Partial attribute in the mesh from
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
        ( "emptydataset", {} ),  # No attribute to map
        ( "multiblockGeosOutput", { "FAULT" } ),  # Meshes with no common cells
    ] )
def test_AttributeMappingRaisesValueError(
    dataSetTest: Any,
    meshToName: str,
    attributeNames: set[ str ],
) -> None:
    """Test the fails of the filter with input value issue."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "dataset" )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, Piece.CELLS )

    with pytest.raises( ValueError ):
        attributeMappingFilter.applyFilter()
