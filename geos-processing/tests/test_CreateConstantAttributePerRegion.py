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
    "meshType, regionName, dictRegionValues, componentNames, componentNamesTest, valueNpType",
    [
        # Test the piece of the region attribute.
        ## For vtkDataSet.
        ( "extractAndMergeVolume", "fractureMechSolver_totalDisplacement_dofIndex", {}, (),
          (), np.float32 ),  # on Points
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (),
          (), np.float32 ),  # on Cells
        ## For vtkMultiBlockDataSet
        ( "2Ranks", "fractureMechSolver_totalDisplacement_dofIndex", {}, (), (), np.float32 ),
        ( "2Ranks", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.float32 ),
        # Test the component name
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, ( "X" ),
          (), np.float32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (),
          ( "Component0", "Component1" ), np.float32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, ( "X" ),
          ( "Component0", "Component1" ), np.float32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, ( "X", "Y" ),
          ( "X", "Y" ), np.float32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, ( "X", "Y", "Z" ),
          ( "X", "Y" ), np.float32 ),
        # Test the type of value
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.int8 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.int16 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.int32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.int64 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.uint8 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.uint16 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.uint32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.uint64 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {}, (), (), np.float64 ),
        # Test index/value
        ## with only correct indexes
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {
            30: [ 0 ],
        }, (), (), np.float32 ),
        ( "extractAndMergeVolume", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex", {
            30: [ 0, 0 ],
        }, (), ( "Component0", "Component1" ), np.float32 ),
        ## with also incorrect indexes
        (
            "extractAndMergeVolume",
            "reservoirAndWellsSolver_singlePhaseVariables_dofIndex",
            {
                30: [ 0 ],
                0: [ 1 ],  # 0 is not an index of the region attribute
            },
            (),
            (),
            np.float32 ),
        (
            "extractAndMergeVolume",
            "reservoirAndWellsSolver_singlePhaseVariables_dofIndex",
            {
                30: [ 0, 0 ],
                0: [ 1, 1 ],  # 0 is not an index of the region attribute
            },
            (),
            ( "Component0", "Component1" ),
            np.float32 ),
    ] )
def test_CreateConstantAttributePerRegion(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    meshType: str,
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
        "newAttribute",
        valueNpType=valueNpType,
        nbComponents=nbComponents,
        componentNames=componentNames,
    )

    createConstantAttributePerRegionFilter.applyFilter()


@pytest.mark.parametrize(
    "meshType, newAttributeName, regionName",
    [
        ( "extractAndMergeVolume", "newAttribute", "averageStrain" ),  # Region attribute has too many components
        ( "geosOutput2Ranks", "newAttribute",
          "reservoirAndWellsSolver_singlePhaseVariables_dofIndex" ),  # Region attribute is partial
        ( "extractAndMergeVolume", "mass", "reservoirAndWellsSolver_singlePhaseVariables_dofIndex"
         ),  # The attribute name already exist in the mesh on the same piece
    ] )
def test_CreateConstantAttributePerRegionRaisesAttributeError(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    meshType: str,
    newAttributeName: str,
    regionName: str,
) -> None:
    """Test the fails of CreateConstantAttributePerRegion with attributes issues."""
    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshType )

    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        regionName,
        {},
        newAttributeName,
    )

    with pytest.raises( AttributeError ):
        createConstantAttributePerRegionFilter.applyFilter()


@pytest.mark.parametrize(
    "dictRegionValues, componentNames",
    [
        ( {
            30: [ 0 ],
            31: [ 1, 1 ],
        }, () ),  # Number of value inconsistent.
        ( {
            30: [ 0, 0 ],
        }, () ),  # More values than components.
        ( {
            30: [ 0 ],
        }, ( "X", "Y" ) ),  # More components than value.
    ] )
def test_CreateConstantAttributePerRegionRaisesValueError(
    dataSetTest: vtkDataSet,
    dictRegionValues: dict[ Any, Any ],
    componentNames: tuple[ str, ...],
) -> None:
    """Test the fails of CreateConstantAttributePerRegion with inputs value issues."""
    mesh: vtkDataSet = dataSetTest( 'extractAndMergeVolume' )
    nbComponents: int = len( componentNames )
    if nbComponents == 0:  # If the attribute has one component, the component has no name.
        nbComponents += 1

    createConstantAttributePerRegionFilter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion(
        mesh,
        "reservoirAndWellsSolver_singlePhaseVariables_dofIndex",
        dictRegionValues,
        "newAttribute",
        nbComponents=nbComponents,
        componentNames=componentNames,
    )

    with pytest.raises( ValueError ):
        createConstantAttributePerRegionFilter.applyFilter()
