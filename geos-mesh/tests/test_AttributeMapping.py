# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest

from typing import Union, Any
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.mesh.processing.AttributeMapping import AttributeMapping

from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, onPoints", [
    ( "fracture", "emptyFracture", ( [ "collocated_nodes" ] ), True ),
    ( "multiblock", "emptyFracture", ( [ "FAULT" ] ), False ),
    ( "multiblock", "emptymultiblock", ( [ "FAULT" ] ), False ),
    ( "dataset", "emptymultiblock", ( [ "FAULT" ] ), False ),
    ( "dataset", "emptydataset", ( [ "FAULT" ] ), False ),
] )
def test_AttributeMapping(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
    onPoints: bool,
) -> None:
    """Test mapping an attribute between two meshes."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    if isinstance( meshFrom, vtkMultiBlockDataSet ):
        fillAllPartialAttributes( meshFrom )

    filter = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )
    assert filter.applyFilter()
