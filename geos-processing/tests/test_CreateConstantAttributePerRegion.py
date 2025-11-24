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
    "meshType, newAttributeName, regionName, dictRegionValues, componentNames, componentNamesTest, valueNpType, error",
    [
        # Test the name of the new attribute (new on the mesh, one present on the other piece).
        ## For vtkDataSet.
        ( "dataset", "newAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32, "None" ),
        ( "dataset", "CellAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32, "None" ),
        ## For vtkMultiBlockDataSet.
        ( "multiblock", "newAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32, "None" ),
        ( "multiblock", "CellAttribute", "GLOBAL_IDS_POINTS", {}, (), (), np.float32, "None" ),
        ( "multiblock", "GLOBAL_IDS_CELLS", "GLOBAL_IDS_POINTS", {}, (), (), np.float32, "None" ),
        # Test if the region attribute is on cells or on points.
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.float32, "None" ),
        # Test the component name.
        ( "dataset", "newAttribute", "FAULT", {}, ( "X" ), (), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), ( "Component0", "Component1" ), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X" ), ( "Component0", "Component1" ), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X", "Y" ), ( "X", "Y" ), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, ( "X", "Y", "Z" ), ( "X", "Y" ), np.float32, "None" ),
        # Test the type of value.
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int8, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int16, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.int64, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint8, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint16, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.uint64, "None" ),
        ( "dataset", "newAttribute", "FAULT", {}, (), (), np.float64, "None" ),
        # Test index/value.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ]
        }, (), (), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
            101: [ 2 ]
        }, (), (), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ],
            101: [ 2 ],
            2: [ 3 ]
        }, (), (), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ]
        }, (), ( "Component0", "Component1" ), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
            101: [ 2, 2 ]
        }, (), ( "Component0", "Component1" ), np.float32, "None" ),
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ],
            101: [ 2, 2 ],
            2: [ 3, 3 ]
        }, (), ( "Component0", "Component1" ), np.float32, "None" ),
        # Test common error.
        ## Number of components.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1, 1 ]
        }, (), (), np.float32, "ValueError" ),  # Number of value inconsistent.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0, 0 ],
            100: [ 1, 1 ]
        }, (), (), np.float32, "ValueError" ),  # More values than components.
        ( "dataset", "newAttribute", "FAULT", {
            0: [ 0 ],
            100: [ 1 ]
        }, ( "X", "Y" ), ( "X", "Y" ), np.float32, "ValueError" ),  # More components than value.
        ## Attribute name.
        ( "dataset", "PERM", "FAULT", {}, (), (), np.float32, "ValueError" ),  # The attribute name already exist.
        ## Region attribute.
        ( "dataset", "newAttribute", "PERM", {}, (),
          (), np.float32, "AttributeError" ),  # Region attribute has too many components.
        ( "multiblock", "newAttribute", "FAULT", {}, (),
          (), np.float32, "AttributeError" ),  # Region attribute is partial.
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
    error: str,
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

    if error == "None":
        createConstantAttributePerRegionFilter.applyFilter()
    elif error == "AttributeError":
        with pytest.raises( AttributeError ):
            createConstantAttributePerRegionFilter.applyFilter()
    elif error == "ValueError":
        with pytest.raises( ValueError ):
            createConstantAttributePerRegionFilter.applyFilter()
