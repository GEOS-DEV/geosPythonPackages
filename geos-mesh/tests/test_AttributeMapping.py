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
    ( "fracture", "emptyFracture", set( [ "collocated_nodes" ] ), True ),
    ( "multiblock", "emptyFracture", set( [ "FAULT" ] ), False ),
    ( "multiblock", "emptymultiblock", set( [ "FAULT" ] ), False ),
    ( "dataset", "emptymultiblock", set( [ "FAULT" ] ), False ),
    ( "dataset", "emptydataset", set( [ "FAULT" ] ), False ),
] )
def test_AttributeMapping(
        dataSetTest: Any,
        meshFromName: str,
        meshToName: str,
        attributeNames: set[ str ],
        onPoints: bool,
) -> None:
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    if isinstance( meshFrom, vtkMultiBlockDataSet ):
        fillAllPartialAttributes( meshFrom )
    
    filter = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )
    assert filter.applyFilter()
