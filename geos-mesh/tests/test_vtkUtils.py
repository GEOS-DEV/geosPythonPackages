# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest

from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkDataSet

from vtk import (  # type: ignore[import-untyped]
    VTK_CHAR, VTK_DOUBLE, VTK_FLOAT, VTK_INT, VTK_UNSIGNED_INT,
)

import geos.mesh.vtkUtils as vtkutils


@pytest.mark.parametrize( "onpoints, expected", [ ( True, {
    'GLOBAL_IDS_POINTS': 1
} ), ( False, {
    'CELL_MARKERS': 1,
    'PERM': 3,
    'PORO': 1,
    'FAULT': 1,
    'GLOBAL_IDS_CELLS': 1
} ) ] )
def test_getAttributesFromDataSet( vtkDataSetTest: vtkDataSet, onpoints: bool, expected: dict[ str, int ] ) -> None:
    """Test getAttributesFromDataSet function.

    Args:
        vtkDataSetTest (vtkDataSet): _description_
        onpoints (bool): _description_
        expected (dict[ str, int ]): _description_
    """
    attributes: dict[ str, int ] = vtkutils.getAttributesFromDataSet( object=vtkDataSetTest, onPoints=onpoints )
    assert attributes == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PORO", True, 0 ),
] )
def test_isAttributeInObjectDataSet( vtkDataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                     expected: bool ) -> None:
    """Test isAttributeFromDataSet function.

    Args:
        vtkDataSetTest (vtkDataSet): _description_
        attributeName (str): _description_
        onpoints (bool): _description_
        expected (bool): _description_
    """
    obtained: bool = vtkutils.isAttributeInObjectDataSet( object=vtkDataSetTest,
                                                          attributeName=attributeName,
                                                          onPoints=onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PORO", False, 1 ),
    ( "PERM", False, 3 ),
    ( "GLOBAL_IDS_POINTS", True, 1 ),
] )
def test_getNumberOfComponentsDataSet(
    vtkDataSetTest: vtkDataSet,
    attributeName: str,
    onpoints: bool,
    expected: int,
) -> None:
    """Test getNumberOfComponentsDataSet function.

    Args:
        vtkDataSetTest (vtkDataSet): _description_
        attributeName (str): _description_
        onpoints (bool): _description_
        expected (int): _description_
    """
    obtained: int = vtkutils.getNumberOfComponentsDataSet( vtkDataSetTest, attributeName, onpoints )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, onpoints, expected", [
    ( "PERM", False, ( "component1", "component2", "component3" ) ),
    ( "PORO", False, () ),
] )
def test_getComponentNamesDataSet( vtkDataSetTest: vtkDataSet, attributeName: str, onpoints: bool,
                                   expected: tuple[ str, ...] ) -> None:
    """Test getComponentNamesDataSet function.

    Args:
        vtkDataSetTest (vtkDataSet): _description_
        attributeName (str): _description_
        onpoints (bool): _description_
        expected (tuple[ str, ...]): _description_
    """
    obtained: tuple[ str, ...] = vtkutils.getComponentNamesDataSet( vtkDataSetTest, attributeName,
                                                                    onpoints )

    assert obtained == expected


@pytest.mark.parametrize(
    "attributeName, dataType, expectedDatatypeArray",
    [
        ( "test_double", VTK_DOUBLE, "vtkDoubleArray" ),
        ( "test_float", VTK_FLOAT, "vtkFloatArray" ),
        ( "test_int", VTK_INT, "vtkIntArray" ),
        ( "test_unsigned_int", VTK_UNSIGNED_INT, "vtkUnsignedIntArray" ),
        ( "test_char", VTK_CHAR, "vtkCharArray" ),
        # ("testFail", 4566, pytest.fail) #TODO
    ] )
def test_createEmptyAttribute(
    attributeName: str,
    dataType: int,
    expectedDatatypeArray: vtkDataArray,
) -> None:
    """Test createEmptyAttribute function.

    Args:
        attributeName (str): _description_
        dataType (int): _description_
        expectedDatatypeArray (vtkDataArray): _description_
    """
    componentNames: tuple[ str, str, str ] = ( "d1, d2, d3" )
    newAttr: vtkDataArray = vtkutils.createEmptyAttribute( attributeName, componentNames, dataType )

    assert newAttr.GetNumberOfComponents() == len( componentNames )
    assert newAttr.GetComponentName( 0 ) == componentNames[ 0 ]
    assert newAttr.GetComponentName( 1 ) == componentNames[ 1 ]
    assert newAttr.GetComponentName( 2 ) == componentNames[ 2 ]
    assert newAttr.IsA( str( expectedDatatypeArray ) )
