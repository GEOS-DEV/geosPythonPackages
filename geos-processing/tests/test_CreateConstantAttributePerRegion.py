# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Any
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet )

from geos.processing.generic_processing_tools.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion
import numpy as np


@pytest.mark.parametrize(
    "meshType, newAttributeName, regionName, dictRegionValues, componentNames, componentNamesTest, valueNpType",
    [
        # Test the name of the new attribute.
        ## For vtkDataSet.
        ( "dataset", "newAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32 ),
        ( "dataset", "CellAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32 ),
        ## For vtkMultiBlockDataSet.
        ( "multiblock", "newAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32 ),
        ( "multiblock", "CellAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32 ),
        ( "multiblock", "GLOBAL_IDS_CELLS", "GLOBAL_IDS_POINTS", {}, (), (), np.float32 ),
        # Test if the region attribute is on cells or on points.
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.float32 ),
        # Test the component name.
        ( "dataset", "newAttribute", "FAULT", {}, ( "X" ), (), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), ( "Component0", "Component1" ), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X" ), ( "Component0", "Component1" ), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X", "Y" ), ( "X", "Y" ), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X", "Y", "Z" ), ( "X", "Y" ), np.float32 ),
        # Test the type of value.
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int8 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int16 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int32 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int64 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint8 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint16 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint32 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint64 ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.float64 ),
        # Test index/value.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
        }, (), (), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
            101: [ 2 ],
        }, (), (), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
            101: [ 2 ],
            2: [ 3 ],
        }, (), (), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
        }, (), ( "Component0", "Component1" ), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
            101: [ 2, 2 ],
        }, (), ( "Component0", "Component1" ), np.float32 ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
            101: [ 2, 2 ],
            2: [ 3, 3 ],
        }, (), ( "Component0", "Component1" ), np.float32 ),
    ] )
def test_CreateConstantAttributePerRegion(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    meshType: str,
    newAttributeName: str,
    regionName: str,
    dictRegionValues: dict[ Any, Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    valueNpType: int,
) -> None:
    """Test CreateConstantAttributePerRegion."""
    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshType )
    nbComponents: int = len( componentNamesTest )
    if nbComponents == 0:  # If the attribute has one component, the component has no name.
        nbComponents += 1

    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        regionName,
        dictRegionValues,
        newAttributeName,
        valueNpType=valueNpType,
        nbComponents=nbComponents,
        componentNames=componentNames,
    )

    createConstantAttributePerRegionFilter.applyFilter()


@pytest.mark.parametrize(
    "meshType, newAttributeName, regionName, dictRegionValues, componentNames, componentNamesTest, valueNpType",
    [
        ( "dataset", "newAttribute", "PERM", {}, (), (), np.float32 ),  # Region attribute has too many components
        ( "multiblock", "newAttribute", "FAULT", {}, (), (), np.float32 ),  # Region attribute is partial.
    ] )
def test_CreateConstantAttributePerRegionRaisesAttributeError(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    meshType: str,
    newAttributeName: str,
    regionName: str,
    dictRegionValues: dict[ Any, Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    valueNpType: int,
) -> None:
    """Test tes fails of CreateConstantAttributePerRegion with attributes issues."""
    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshType )
    nbComponents: int = len( componentNamesTest )
    if nbComponents == 0:  # If the attribute has one component, the component has no name.
        nbComponents += 1

    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        regionName,
        dictRegionValues,
        newAttributeName,
        valueNpType=valueNpType,
        nbComponents=nbComponents,
        componentNames=componentNames,
    )

    with pytest.raises( AttributeError ):
        createConstantAttributePerRegionFilter.applyFilter()


@pytest.mark.parametrize(
    "meshType, newAttributeName, regionName, dictRegionValues, componentNames, componentNamesTest, valueNpType",
    [
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1, 1 ],
        }, (), (), np.float32 ),  # Number of value inconsistent.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
        }, (), (), np.float32 ),  # More values than components.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
        }, ( "X", "Y" ), ( "X", "Y" ), np.float32 ),  # More components than value.
        ( "dataset", "PERM", "FAULT", {}, (), (), np.float32 ),  # The attribute name already exist on the mesh on the same piece.
    ] )
def test_CreateConstantAttributePerRegionRaisesValueError(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    meshType: str,
    newAttributeName: str,
    regionName: str,
    dictRegionValues: dict[ Any, Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    valueNpType: int,
) -> None:
    """Test the fails of CreateConstantAttributePerRegion with inputs value issues."""
    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshType )
    nbComponents: int = len( componentNamesTest )
    if nbComponents == 0:  # If the attribute has one component, the component has no name.
        nbComponents += 1

    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        regionName,
        dictRegionValues,
        newAttributeName,
        valueNpType=valueNpType,
        nbComponents=nbComponents,
        componentNames=componentNames,
    )

    with pytest.raises( ValueError ):
        createConstantAttributePerRegionFilter.applyFilter()
