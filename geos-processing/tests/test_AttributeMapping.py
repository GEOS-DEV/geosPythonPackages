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


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, onPoints", [
    ( "dataset", "emptydataset", { "Fault" }, False ),  # Attribute not in the mesh from
    ( "dataset", "dataset", { "GLOBAL_IDS_CELLS" }, False ),  # Attribute on both meshes
    ( "multiblock", "emptymultiblock", { "FAULT" }, False ),  # Partial attribute in the mesh from
] )
def test_AttributeMappingRaisesAttributeError(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
    onPoints: bool,
) -> None:
    """Test the fails of the filter with attributes issues."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )

    with pytest.raises( AttributeError ):
        attributeMappingFilter.applyFilter()


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames, onPoints", [
    ( "dataset", "emptydataset", {}, False ),  # no attribute to map
    ( "dataset", "emptyFracture", { "FAULT" }, False ),  # meshes with same type but different cells dimension
] )
def test_AttributeMappingRaisesValueError(
    dataSetTest: Any,
    meshFromName: str,
    meshToName: str,
    attributeNames: set[ str ],
    onPoints: bool,
) -> None:
    """Test the fails of the filter with input value issue."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    attributeMappingFilter: AttributeMapping = AttributeMapping( meshFrom, meshTo, attributeNames, onPoints )

    with pytest.raises( ValueError ):
        attributeMappingFilter.applyFilter()