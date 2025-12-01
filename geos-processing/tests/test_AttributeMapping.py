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
    assert attributeMappingFilter.applyFilter()
