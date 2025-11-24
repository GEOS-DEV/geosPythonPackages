# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Union, Any
from geos.mesh.utils.arrayModifiers import fillAllPartialAttributes
from geos.processing.generic_processing_tools.AttributeMapping import AttributeMapping
from vtkmodules.vtkCommonDataModel import vtkMultiBlockDataSet, vtkDataSet


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, onPoints", [
    ( "fracture", "emptyFracture", { "collocatedNodes" }, True ),
    ( "multiblock", "emptyFracture", { "FAULT" }, False ),
    ( "multiblock", "emptymultiblock", { "FAULT" }, False ),
    ( "dataset", "emptymultiblock", { "FAULT" }, False ),
    ( "dataset", "emptydataset", { "FAULT" }, False ),
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

    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )
    attributeMappingFilter.applyFilter()


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, onPoints, error", [
    ( "dataset", "emptydataset", {}, False, "ValueError" ),
    ( "dataset", "emptydataset", { "Fault" }, False, "AttributeError" ),
    ( "dataset", "dataset", { "GLOBAL_IDS_CELLS" }, False, "AttributeError" ),
    ( "multiblock", "emptymultiblock", { "FAULT" }, False, "AttributeError" ),
    ( "dataset", "emptyFracture", { "FAULT" }, False, "ValueError" ),
] )
def test_AttributeMappingRaises(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
    onPoints: bool,
    error: str,
) -> None:
    """Test the fails of the filter."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )

    if error == "AttributeError":
        with pytest.raises( AttributeError ):
            attributeMappingFilter.applyFilter()
    elif error == "ValueError":
        with pytest.raises( ValueError ):
            attributeMappingFilter.applyFilter()
