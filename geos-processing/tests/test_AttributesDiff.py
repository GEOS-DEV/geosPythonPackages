# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
import numpy as np

from typing import Any
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet

from geos.processing.generic_processing_tools.AttributesDiff import AttributesDiff
from geos.mesh.utils.arrayHelpers import getArrayInObject
from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten
from geos.utils.pieceEnum import Piece


# TODO: Create meshes for test
@pytest.mark.skip( "Add data for test" )
@pytest.mark.parametrize( "mesh1Name, mesh2Name", [] )
def test_AttributesDiff(
    dataSetTest: Any,
    mesh1Name: str,
    mesh2Name: str,
) -> None:
    """Test the filter AttributesDiff."""
    mesh1: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( mesh1Name )
    mesh2: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( mesh2Name )

    AttributesDiffFilter: AttributesDiff = AttributesDiff()
    AttributesDiffFilter.setMeshes( [ mesh1, mesh2 ] )
    AttributesDiffFilter.logSharedAttributeInfo()
    dicAttributesToCompare: dict[ Piece, set[ str ] ] = {
        Piece.CELLS: { "elementCenter", "localToGlobalMap" },
        Piece.POINTS: { "localToGlobalMap" }
    }
    AttributesDiffFilter.setDicAttributesToCompare( dicAttributesToCompare )
    AttributesDiffFilter.applyFilter()
    mesh: vtkDataSet | vtkMultiBlockDataSet = mesh1.NewInstance()
    mesh.ShallowCopy( AttributesDiffFilter.getOutput() )
    dicAttributesDiffNames: dict[ Piece, set[ str ] ] = AttributesDiffFilter.getDicAttributesDiffNames()
    listFlattenIndexes = getBlockElementIndexesFlatten( mesh )
    for it in listFlattenIndexes:
        dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( it ) )  # type: ignore[union-attr]
        for piece, listDiffAttributesName in dicAttributesDiffNames.items():
            for diffAttributeName in listDiffAttributesName:
                test = getArrayInObject( dataset, diffAttributeName, piece )
                assert ( test == np.zeros( test.shape ) ).all()


# TODO: Implement a test for checking the log of the inf norm
