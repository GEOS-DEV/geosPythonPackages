# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Any

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )

from geos.mesh.utils.multiblockHelpers import getBlockElementIndexesFlatten

from vtk import (  # type: ignore[import-untyped]
    VTK_UNSIGNED_CHAR, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_INT, VTK_UNSIGNED_LONG_LONG, VTK_CHAR, VTK_SIGNED_CHAR,
    VTK_SHORT, VTK_INT, VTK_LONG_LONG, VTK_ID_TYPE, VTK_FLOAT, VTK_DOUBLE,
)

# Information :
# https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/numpy_support.py
# https://github.com/Kitware/VTK/blob/master/Wrapping/Python/vtkmodules/util/vtkConstants.py
#     vtk array type       int   numpy type
# VTK_CHAR               = 2  = np.int8
# VTK_SIGNED_CHAR        = 15 = np.int8
# VTK_SHORT              = 4  = np.int16
# VTK_INT                = 6  = np.int32
# VTK_BIT                = 1  = np.uint8
# VTK_UNSIGNED_CHAR      = 3  = np.uint8
# VTK_UNSIGNED_SHORT     = 5  = np.uint16
# VTK_UNSIGNED_INT       = 7  = np.uint32
# VTK_UNSIGNED_LONG_LONG = 17 = np.uint64
# VTK_LONG               = 8  = LONG_TYPE_CODE ( int32 | int64 )
# VTK_UNSIGNED_LONG      = 9  = ULONG_TYPE_CODE ( uint32 | uint64 )
# VTK_FLOAT              = 10 = np.float32
# VTK_DOUBLE             = 11 = np.float64
# VTK_ID_TYPE            = 12 = ID_TYPE_CODE ( int32 | int64 )

#     vtk array type       int  IdType  numpy type
# VTK_LONG_LONG          = 16 = 2 = np.int64

from geos.mesh.utils import arrayModifiers


@pytest.mark.parametrize(
    "idBlock, attributeName, nbComponentsTest, componentNamesTest, onPoints, listValues, listValuesTest, vtkDataTypeTest",
    [
        # Test fill an attribute on point and on cell.
        ( 3, "PointAttribute", 3,
          ( "AX1", "AX2", "AX3" ), True, None, [ np.float64(
              np.nan ), np.float64( np.nan ), np.float64( np.nan ) ], VTK_DOUBLE ),
        ( 3, "CellAttribute", 3,
          ( "AX1", "AX2", "AX3" ), False, None, [ np.float64(
              np.nan ), np.float64( np.nan ), np.float64( np.nan ) ], VTK_DOUBLE ),
        # Test fill attributes with different number of component with or without component names.
        ( 3, "PORO", 1, (), False, None, [ np.float32( np.nan ) ], VTK_FLOAT ),
        ( 1, "collocated_nodes", 2, ( None, None ), True, None, [ np.int64( -1 ), np.int64( -1 ) ], VTK_ID_TYPE ),
        # Test fill an attribute with different type of value.
        ( 3, "FAULT", 1, (), False, None, [ np.int32( -1 ) ], VTK_INT ),
        ( 3, "FAULT", 1, (), False, [ 4 ], [ np.int32( 4 ) ], VTK_INT ),
        ( 3, "PORO", 1, (), False, [ 4 ], [ np.float32( 4 ) ], VTK_FLOAT ),
        ( 1, "collocated_nodes", 2, ( None, None ), True, [ 4, 4 ], [ np.int64( 4 ), np.int64( 4 ) ], VTK_ID_TYPE ),
        ( 3, "CellAttribute", 3, ( "AX1", "AX2", "AX3" ), False, [ 4, 4, 4 ],
          [ np.float64( 4 ), np.float64( 4 ), np.float64( 4 ) ], VTK_DOUBLE ),
    ] )
def test_fillPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
    idBlock: int,
    attributeName: str,
    nbComponentsTest: int,
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    listValues: Union[ list[ Any ], None ],
    listValuesTest: list[ Any ],
    vtkDataTypeTest: int,
) -> None:
    """Test filling a partial attribute from a multiblock with values."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    # Fill the attribute in the multiBlockDataSet.
    arrayModifiers.fillPartialAttributes( multiBlockDataSetTest, attributeName, onPoints=onPoints, listValues=listValues )

    # Get the dataSet where the attribute has been filled.
    dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( idBlock ) )

    # Get the filled attribute.
    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        nbElements = dataSet.GetNumberOfPoints()
        data = dataSet.GetPointData()
    else:
        nbElements = dataSet.GetNumberOfCells()
        data = dataSet.GetCellData()
    attributeFilled: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsFilled: int = attributeFilled.GetNumberOfComponents()
    assert nbComponentsFilled == nbComponentsTest
    if nbComponentsTest > 1:
        componentNamesFilled: tuple[ str, ...] = tuple(
            attributeFilled.GetComponentName( i ) for i in range( nbComponentsFilled ) )
        assert componentNamesFilled == componentNamesTest

    # Test values and their types.
    ## Create the constant array test from the value.
    npArrayTest: npt.NDArray[ Any ]
    if nbComponentsTest > 1:
        npArrayTest = np.array( [ listValuesTest for _ in range( nbElements ) ] )
    else:
        npArrayTest = np.array( [ listValuesTest[ 0 ] for _ in range( nbElements ) ] )

    npArrayFilled: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeFilled )
    assert npArrayFilled.dtype == npArrayTest.dtype
    if listValues is None and vtkDataTypeTest in ( VTK_FLOAT, VTK_DOUBLE ):
        assert np.isnan( npArrayFilled ).all()
    else:
        assert ( npArrayFilled == npArrayTest ).all()

    vtkDataTypeFilled: int = attributeFilled.GetDataType()
    assert vtkDataTypeFilled == vtkDataTypeTest


def test_fillPartialAttributesTypeError(
    dataSetTest: vtkDataSet,
) -> None:
    """Test the raises TypeError for the function fillPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.fillPartialAttributes( mesh, "PORO" )


def test_fillPartialAttributesValueError(
    dataSetTest: vtkMultiBlockDataSet,
) -> None:
    """Test the raises ValueError for the function fillPartialAttributes with to many values for the attribute."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( ValueError ):
        arrayModifiers.fillPartialAttributes( mesh, "PORO", listValues=[ 42, 42] )


@pytest.mark.parametrize( "attributeName", [
    ( "newAttribute" ),  # The attribute is not in the mesh
    ( "GLOBAL_IDS_CELLS" ),  # The attribute is already global
] )
def test_fillPartialAttributesAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
) -> None:
    """Test the raises AttributeError for the function fillPartialAttributes."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( AttributeError ):
        arrayModifiers.fillPartialAttributes( mesh, attributeName )


def test_FillAllPartialAttributes(
    dataSetTest: vtkMultiBlockDataSet,
) -> None:
    """Test to fill all the partial attributes of a vtkMultiBlockDataSet with a value."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    arrayModifiers.fillAllPartialAttributes( multiBlockDataSetTest )

    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTest )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( blockIndex ) )
        attributeExist: int
        for attributeNameOnPoint in [ "PointAttribute", "collocated_nodes" ]:
            attributeExist = dataSet.GetPointData().HasArray( attributeNameOnPoint )
            assert attributeExist == 1
        for attributeNameOnCell in [ "CELL_MARKERS", "CellAttribute", "FAULT", "PERM", "PORO" ]:
            attributeExist = dataSet.GetCellData().HasArray( attributeNameOnCell )
            assert attributeExist == 1


def test_fillAllPartialAttributesTypeError(
    dataSetTest: vtkDataSet,
) -> None:
    """Test the raises TypeError for the function fillAllPartialAttributes with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.fillAllPartialAttributes( mesh )


@pytest.mark.parametrize( "attributeName, dataType, expectedDatatypeArray", [
    ( "test_double", VTK_DOUBLE, "vtkDoubleArray" ),
    ( "test_float", VTK_FLOAT, "vtkFloatArray" ),
    ( "test_int", VTK_INT, "vtkIntArray" ),
    ( "test_unsigned_int", VTK_UNSIGNED_INT, "vtkUnsignedIntArray" ),
    ( "test_char", VTK_CHAR, "vtkCharArray" ),
] )
def test_createEmptyAttribute(
    attributeName: str,
    dataType: int,
    expectedDatatypeArray: vtkDataArray,
) -> None:
    """Test empty attribute creation."""
    componentNames: tuple[ str, str, str ] = ( "d1", "d2", "d3" )
    newAttr: vtkDataArray = arrayModifiers.createEmptyAttribute( attributeName, componentNames, dataType )

    assert newAttr.GetNumberOfComponents() == len( componentNames )
    for ax in range( 3 ):
        assert newAttr.GetComponentName( ax ) == componentNames[ ax ]
    assert newAttr.IsA( str( expectedDatatypeArray ) )


def test_createEmptyAttributeValueError() -> None:
    """Test the raises ValueError for the function createEmptyAttribute with a wrong vtkDataType."""
    with pytest.raises( ValueError ):
        newAttr: vtkDataArray = arrayModifiers.createEmptyAttribute( "newAttribute", (), 64 )


@pytest.mark.parametrize(
    "attributeName, onPoints",
    [
        # Test to create a new attribute on points and on cells.
        ( "newAttribute", False ),
        ( "newAttribute", True ),
        # Test to create a new attribute  when an attribute with the same name already exist on the opposite piece.
        ( "PORO", True ),  # Partial attribute on cells already exist.
        ( "GLOBAL_IDS_CELLS", True ),  # Global attribute on cells already exist.
    ] )
def test_createConstantAttributeMultiBlock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test creation of constant attribute in multiblock dataset."""
    multiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    values: list[ float ] = [ np.nan ]
    arrayModifiers.createConstantAttributeMultiBlock( multiBlockDataSetTest, values, attributeName, onPoints=onPoints )

    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetTest )
    for blockIndex in elementaryBlockIndexes:
        dataSet: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTest.GetDataSet( blockIndex ) )
        data: Union[ vtkPointData, vtkCellData ]
        data = dataSet.GetPointData() if onPoints else dataSet.GetCellData()

        attributeWellCreated: int = data.HasArray( attributeName )
        assert attributeWellCreated == 1


def test_createConstantAttributeMultiBlockRaiseTypeError(
    dataSetTest: vtkDataSet,
) -> None:
    """Test the raises TypeError for the function createConstantAttributeMultiBlock with a wrong mesh type."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.createConstantAttributeMultiBlock( mesh, [ np.int32( 42 ) ], "newAttribute" )


def test_createConstantAttributeMultiBlockRaiseAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
) -> None:
    """Test the raises AttributeError for the function createConstantAttributeMultiBlock with a wrong attributeName."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( AttributeError ):
        arrayModifiers.createConstantAttributeMultiBlock( mesh, [ np.int32( 42 ) ], "PORO" )


@pytest.mark.parametrize(
    "listValues, componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, attributeName",
    [
        # Test attribute names.
        ## Test with an attributeName already existing on opposite piece.
        ( [ np.float64( 42 ) ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "CellAttribute" ),
        ( [ np.float64( 42 ) ], (), (), False, VTK_DOUBLE, VTK_DOUBLE, "PointAttribute" ),
        ## Test with a new attributeName on cells and on points.
        ( [ np.float32( 42 ) ], (), (), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ) ], (), (), False, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the number of components and their names.
        ( [ np.float32( 42 ) ], ( "X" ), (), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y" ),
          ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], ( "X", "Y", "Z" ),
          ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        ( [ np.float32( 42 ), np.float32( 42 ) ], (),
          ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( [ np.int8( 42 ) ], (), (), True, None, VTK_SIGNED_CHAR, "newAttribute" ),
        ( [ np.int8( 42 ) ], (), (), True, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "newAttribute" ),
        ( [ np.int16( 42 ) ], (), (), True, None, VTK_SHORT, "newAttribute" ),
        ( [ np.int16( 42 ) ], (), (), True, VTK_SHORT, VTK_SHORT, "newAttribute" ),
        ( [ np.int32( 42 ) ], (), (), True, None, VTK_INT, "newAttribute" ),
        ( [ np.int32( 42 ) ], (), (), True, VTK_INT, VTK_INT, "newAttribute" ),
        ( [ np.int64( 42 ) ], (), (), True, None, VTK_LONG_LONG, "newAttribute" ),
        ( [ np.int64( 42 ) ], (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( [ np.uint8( 42 ) ], (), (), True, None, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( [ np.uint8( 42 ) ], (), (), True, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "newAttribute" ),
        ( [ np.uint16( 42 ) ], (), (), True, None, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( [ np.uint16( 42 ) ], (), (), True, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "newAttribute" ),
        ( [ np.uint32( 42 ) ], (), (), True, None, VTK_UNSIGNED_INT, "newAttribute" ),
        ( [ np.uint32( 42 ) ], (), (), True, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "newAttribute" ),
        ( [ np.uint64( 42 ) ], (), (), True, None, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( [ np.uint64( 42 ) ], (), (), True, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "newAttribute" ),
        ( [ np.float32( 42 ) ], (), (), True, None, VTK_FLOAT, "newAttribute" ),
        ( [ np.float64( 42 ) ], (), (), True, None, VTK_DOUBLE, "newAttribute" ),
        ( [ np.float64( 42 ) ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
        ## With python scalar type.
        ( [ 42 ], (), (), True, None, VTK_LONG_LONG, "newAttribute" ),
        ( [ 42 ], (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "newAttribute" ),
        ( [ 42. ], (), (), True, None, VTK_DOUBLE, "newAttribute" ),
        ( [ 42. ], (), (), True, VTK_DOUBLE, VTK_DOUBLE, "newAttribute" ),
    ] )
def test_createConstantAttributeDataSet(
    dataSetTest: vtkDataSet,
    listValues: list[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    vtkDataType: Union[ int, Any ],
    vtkDataTypeTest: int,
    attributeName: str,
) -> None:
    """Test constant attribute creation in dataset."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )

    # Create the new constant attribute in the dataSet.
    arrayModifiers.createConstantAttributeDataSet( dataSet, listValues, attributeName, componentNames, onPoints, vtkDataType )

    # Get the created attribute.
    data: Union[ vtkPointData, vtkCellData ]
    nbElements: int
    if onPoints:
        data = dataSet.GetPointData()
        nbElements = dataSet.GetNumberOfPoints()
    else:
        data = dataSet.GetCellData()
        nbElements = dataSet.GetNumberOfCells()
    attributeCreated: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsTest: int = len( listValues )
    nbComponentsCreated: int = attributeCreated.GetNumberOfComponents()
    assert nbComponentsCreated == nbComponentsTest
    if nbComponentsTest > 1:
        componentNamesCreated: tuple[ str, ...] = tuple(
            attributeCreated.GetComponentName( i ) for i in range( nbComponentsCreated ) )
        assert componentNamesCreated, componentNamesTest

    # Test values and their types.
    ## Create the constant array test from values in the list values.
    npArrayTest: npt.NDArray[ Any ]
    if len( listValues ) > 1:
        npArrayTest = np.array( [ listValues for _ in range( nbElements ) ] )
    else:
        npArrayTest = np.array( [ listValues[ 0 ] for _ in range( nbElements ) ] )

    npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCreated )
    assert npArrayCreated.dtype == npArrayTest.dtype
    assert ( npArrayCreated == npArrayTest ).all()

    vtkDataTypeCreated: int = attributeCreated.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize( "listValues, vtkDataType", [
    ( [ np.int32( 42 ), np.int64( 42 ) ], VTK_DOUBLE ),  # All the values in the listValues are not the same
    ( [ np.int32( 42 ) ], VTK_DOUBLE ),  # The type of the value is not coherent with the vtkDataType
] )
def test_createConstantAttributeDataSetRaiseTypeError(
    dataSetTest: vtkDataSet,
    listValues: list[ Any ],
    vtkDataType: int,
) -> None:
    """Test the raises TypeError for the function createConstantAttributeDataSet."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.createConstantAttributeDataSet( mesh, listValues, "newAttribute", vtkDataType=vtkDataType )


def test_createConstantAttributeDataSetRaiseValueError(
    dataSetTest: vtkDataSet,
) -> None:
    """Test the raises ValueError for the function createConstantAttributeDataSet with a wrong vtkDataType."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( ValueError ):
        arrayModifiers.createConstantAttributeDataSet( mesh, [ np.int32( 42 ) ], "newAttribute", vtkDataType=64 )


@pytest.mark.parametrize(
    "componentNames, componentNamesTest, onPoints, vtkDataType, vtkDataTypeTest, valueType, attributeName",
    [
        # Test attribute names.
        ## Test with an attributeName already existing on opposite piece.
        ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64", "CellAttribute" ),
        ( (), (), False, VTK_DOUBLE, VTK_DOUBLE, "float64", "PointAttribute" ),
        ## Test with a new attributeName on cells and on points.
        ( (), (), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), (), False, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        # Test the number of components and their names.
        ( ( "X" ), (), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( ( "X", "Y" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( ( "X", "Y", "Z" ), ( "X", "Y" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), ( "Component0", "Component1" ), True, VTK_FLOAT, VTK_FLOAT, "float32", "newAttribute" ),
        # Test the type of the values.
        ## With numpy scalar type.
        ( (), (), True, None, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
        ( (), (), True, VTK_SIGNED_CHAR, VTK_SIGNED_CHAR, "int8", "newAttribute" ),
        ( (), (), True, None, VTK_SHORT, "int16", "newAttribute" ),
        ( (), (), True, VTK_SHORT, VTK_SHORT, "int16", "newAttribute" ),
        ( (), (), True, None, VTK_INT, "int32", "newAttribute" ),
        ( (), (), True, VTK_INT, VTK_INT, "int32", "newAttribute" ),
        ( (), (), True, None, VTK_LONG_LONG, "int64", "newAttribute" ),
        ( (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int64", "newAttribute" ),
        ( (), (), True, None, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
        ( (), (), True, VTK_UNSIGNED_CHAR, VTK_UNSIGNED_CHAR, "uint8", "newAttribute" ),
        ( (), (), True, None, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
        ( (), (), True, VTK_UNSIGNED_SHORT, VTK_UNSIGNED_SHORT, "uint16", "newAttribute" ),
        ( (), (), True, None, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
        ( (), (), True, VTK_UNSIGNED_INT, VTK_UNSIGNED_INT, "uint32", "newAttribute" ),
        ( (), (), True, None, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
        ( (), (), True, VTK_UNSIGNED_LONG_LONG, VTK_UNSIGNED_LONG_LONG, "uint64", "newAttribute" ),
        ( (), (), True, None, VTK_FLOAT, "float32", "newAttribute" ),
        ( (), (), True, None, VTK_DOUBLE, "float64", "newAttribute" ),
        ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float64", "newAttribute" ),
        ## With python scalar type.
        ( (), (), True, None, VTK_LONG_LONG, "int", "newAttribute" ),
        ( (), (), True, VTK_LONG_LONG, VTK_LONG_LONG, "int", "newAttribute" ),
        ( (), (), True, None, VTK_DOUBLE, "float", "newAttribute" ),
        ( (), (), True, VTK_DOUBLE, VTK_DOUBLE, "float", "newAttribute" ),
    ] )
def test_createAttribute(
    dataSetTest: vtkDataSet,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    componentNames: tuple[ str, ...],
    componentNamesTest: tuple[ str, ...],
    onPoints: bool,
    vtkDataType: int,
    vtkDataTypeTest: int,
    valueType: str,
    attributeName: str,
) -> None:
    """Test creation of dataset in dataset from given array."""
    dataSet: vtkDataSet = dataSetTest( "dataset" )

    # Get a array with random values of a given type.
    nbElements: int = dataSet.GetNumberOfPoints() if onPoints else dataSet.GetNumberOfCells()
    nbComponentsTest: int = 1 if len( componentNamesTest ) == 0 else len( componentNamesTest )
    npArrayTest: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( nbComponentsTest, nbElements, valueType )

    # Create the new attribute in the dataSet.
    arrayModifiers.createAttribute( dataSet, npArrayTest, attributeName, componentNames, onPoints, vtkDataType )

    # Get the created attribute.
    data: Union[ vtkPointData, vtkCellData ]
    data = dataSet.GetPointData() if onPoints else dataSet.GetCellData()
    attributeCreated: vtkDataArray = data.GetArray( attributeName )

    # Test the number of components and their names if multiple.
    nbComponentsCreated: int = attributeCreated.GetNumberOfComponents()
    assert nbComponentsCreated == nbComponentsTest
    if nbComponentsTest > 1:
        componentsNamesCreated: tuple[ str, ...] = tuple(
            attributeCreated.GetComponentName( i ) for i in range( nbComponentsCreated ) )
        assert componentsNamesCreated == componentNamesTest

    # Test values and their types.
    npArrayCreated: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCreated )
    assert npArrayCreated.dtype == npArrayTest.dtype
    assert ( npArrayCreated == npArrayTest ).all()

    vtkDataTypeCreated: int = attributeCreated.GetDataType()
    assert vtkDataTypeCreated == vtkDataTypeTest


@pytest.mark.parametrize( "meshName, arrayType", [
    ( "multiblock", "float64" ),  # The input mesh has the wrong type
    ( "dataset", "int32" ),  # The input array has the wrong type (should be float64)
] )
def test_createAttributeRaiseTypeError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    meshName: str,
    arrayType: str,
) -> None:
    """Test the raises TypeError for the function createAttribute."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshName )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1, arrayType )
    attributeName: str = "NewAttribute"
    with pytest.raises( TypeError ):
        arrayModifiers.createAttribute( mesh, npArray, attributeName, vtkDataType=VTK_DOUBLE )


@pytest.mark.parametrize( "vtkDataType, nbElements", [
    ( 64, 1740 ),  # The vtkDataType does not exist
    ( VTK_DOUBLE, 1741 ),  # The number of element of the array is wrong
] )
def test_createAttributeRaiseValueError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
    vtkDataType: int,
    nbElements: int,
) -> None:
    """Test the raises ValueError for the function createAttribute."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "dataset" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, nbElements, "float64" )
    with pytest.raises( ValueError ):
        arrayModifiers.createAttribute( mesh, npArray, "newAttribute", vtkDataType=vtkDataType )


def test_createAttributeRaiseAttributeError(
    dataSetTest: Any,
    getArrayWithSpeTypeValue: npt.NDArray[ Any ],
) -> None:
    """Test the raises AttributeError for the function createAttribute with a wrong attribute name."""
    mesh: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( "dataset" )
    npArray: npt.NDArray[ Any ] = getArrayWithSpeTypeValue( 1, 1740, "float64" )
    with pytest.raises( AttributeError ):
        arrayModifiers.createAttribute( mesh, npArray, "PORO" )


@pytest.mark.parametrize(
    "attributeNameFrom, attributeNameTo, onPoints",
    [
        # Test with global attributes.
        ( "GLOBAL_IDS_POINTS", "GLOBAL_IDS_POINTS_To", True ),
        ( "GLOBAL_IDS_CELLS", 'GLOBAL_IDS_CELLS_To', False ),
        # Test with partial attributes.
        ( "CellAttribute", "CellAttributeTo", False ),
        ( "PointAttribute", "PointAttributeTo", True ),
    ] )
def test_copyAttribute(
    dataSetTest: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool,
) -> None:
    """Test copy of cell attribute from one multiblock to another."""
    multiBlockDataSetFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    multiBlockDataSetTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )

    # Copy the attribute from the multiBlockDataSetFrom to the multiBlockDataSetTo.
    arrayModifiers.copyAttribute( multiBlockDataSetFrom, multiBlockDataSetTo, attributeNameFrom, attributeNameTo, onPoints )

    # Parse the two multiBlockDataSet and test if the attribute has been copied.
    elementaryBlockIndexes: list[ int ] = getBlockElementIndexesFlatten( multiBlockDataSetFrom )
    for blockIndex in elementaryBlockIndexes:
        dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetFrom.GetDataSet( blockIndex ) )
        dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( multiBlockDataSetTo.GetDataSet( blockIndex ) )
        dataFrom: Union[ vtkPointData, vtkCellData ]
        dataTo: Union[ vtkPointData, vtkCellData ]
        if onPoints:
            dataFrom = dataSetFrom.GetPointData()
            dataTo = dataSetTo.GetPointData()
        else:
            dataFrom = dataSetFrom.GetCellData()
            dataTo = dataSetTo.GetCellData()

        attributeExistTest: int = dataFrom.HasArray( attributeNameFrom )
        attributeExistCopied: int = dataTo.HasArray( attributeNameTo )
        assert attributeExistCopied == attributeExistTest


@pytest.mark.parametrize( "meshNameFrom, meshNameTo", [
    ( "dataset", "emptydataset" ),
    ( "dataset", "emptymultiblock" ),
    ( "multiblock", "emptydataset" ),
] )
def test_copyAttributeTypeError(
    dataSetTest: Any,
    meshNameFrom: str,
    meshNameTo: str,
) -> None:
    """Test the raises TypeError for the function copyAttribute."""
    meshFrom: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshNameFrom )
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshNameTo )
    with pytest.raises( TypeError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, "PORO", "PORO" )


def test_copyAttributeValueError(
    dataSetTest: vtkMultiBlockDataSet,
) -> None:
    """Test the raises ValueError for the function copyAttribute with two meshes with different block architecture."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "meshGeosExtractBlockTmp" )
    meshTo: vtkMultiBlockDataSet = dataSetTest( "emptymultiblock" )
    with pytest.raises( ValueError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, "PORO", "PORO" )


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo", [
    ( "PORO", "PORO" ),  # An attribute PORO is already present in the mesh to
    ( "newAttribute", "newAttribute" ),  # newAttribute is not in the mesh from
] )
def test_copyAttributeAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
) -> None:
    """Test the raises AttributeError for the function copyAttribute."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    meshTo: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    with pytest.raises( AttributeError ):
        arrayModifiers.copyAttribute( meshFrom, meshTo, attributeNameFrom, attributeNameTo )


@pytest.mark.parametrize( "attributeNameFrom, attributeNameTo, onPoints", [
    ( "CellAttribute", "CellAttributeTo", False ),
    ( "PointAttribute", "PointAttributeTo", True ),
] )
def test_copyAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeNameFrom: str,
    attributeNameTo: str,
    onPoints: bool,
) -> None:
    """Test copy of an attribute from one dataset to another."""
    dataSetFrom: vtkDataSet = dataSetTest( "dataset" )
    dataSetTo: vtkDataSet = dataSetTest( "emptydataset" )

    # Copy the attribute from the dataSetFrom to the dataSetTo.
    arrayModifiers.copyAttributeDataSet( dataSetFrom, dataSetTo, attributeNameFrom, attributeNameTo, onPoints )

    # Get the tested attribute and its copy.
    dataFrom: Union[ vtkPointData, vtkCellData ]
    dataTo: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        dataFrom = dataSetFrom.GetPointData()
        dataTo = dataSetTo.GetPointData()
    else:
        dataFrom = dataSetFrom.GetCellData()
        dataTo = dataSetTo.GetCellData()
    attributeTest: vtkDataArray = dataFrom.GetArray( attributeNameFrom )
    attributeCopied: vtkDataArray = dataTo.GetArray( attributeNameTo )

    # Test the number of components and their names if multiple.
    nbComponentsTest: int = attributeTest.GetNumberOfComponents()
    nbComponentsCopied: int = attributeCopied.GetNumberOfComponents()
    assert nbComponentsCopied == nbComponentsTest
    if nbComponentsTest > 1:
        componentsNamesTest: tuple[ str, ...] = tuple(
            attributeTest.GetComponentName( i ) for i in range( nbComponentsTest ) )
        componentsNamesCopied: tuple[ str, ...] = tuple(
            attributeCopied.GetComponentName( i ) for i in range( nbComponentsCopied ) )
        assert componentsNamesCopied == componentsNamesTest

    # Test values and their types.
    npArrayTest: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeTest )
    npArrayCopied: npt.NDArray[ Any ] = vnp.vtk_to_numpy( attributeCopied )
    assert npArrayCopied.dtype == npArrayTest.dtype
    assert ( npArrayCopied == npArrayTest ).all()

    vtkDataTypeTest: int = attributeTest.GetDataType()
    vtkDataTypeCopied: int = attributeCopied.GetDataType()
    assert vtkDataTypeCopied == vtkDataTypeTest


def test_copyAttributeDataSetTypeError(
    dataSetTest: Any,
) -> None:
    """Test the raises TypeError for the function copyAttributeDataSet with a mesh from with a wrong type."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    meshTo: vtkDataSet = dataSetTest( "emptydataset" )
    with pytest.raises( TypeError ):
        arrayModifiers.copyAttributeDataSet( meshFrom, meshTo, "PORO", "PORO" )


def test_copyAttributeDataSetAttributeError(
    dataSetTest: vtkDataSet,
) -> None:
    """Test the raises AttributeError for the function copyAttributeDataSet with an attributeNameFrom not in the mesh From."""
    meshFrom: vtkDataSet = dataSetTest( "dataset" )
    meshTo: vtkDataSet = dataSetTest( "emptydataset" )
    with pytest.raises( AttributeError ):
        arrayModifiers.copyAttributeDataSet( meshFrom, meshTo, "newAttribute", "newAttribute" )


@pytest.mark.parametrize( "isMeshFrom, meshToName", [
    ( True, "emptymultiblock" ),  # The mesh to is not a vtkDataSet.
    ( False, "emptyFracture" ),  # The mesh from is not a mesh.
] )
def test_transferAttributeToDataSetWithElementMapTypeError(
    dataSetTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    isMeshFrom: bool,
    meshToName: str,
) -> None:
    """Test the raises TypeError for the function transferAttributeToDataSetWithElementMap."""
    meshFrom: Union[ bool, vtkMultiBlockDataSet ]
    if isMeshFrom:
        meshFrom = dataSetTest( "multiblock" )
    else:
        meshFrom = False
    meshTo: Union[ vtkDataSet, vtkMultiBlockDataSet ] = dataSetTest( meshToName )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "multiblock", meshToName, False )
    with pytest.raises( TypeError ):
        arrayModifiers.transferAttributeToDataSetWithElementMap( meshFrom, meshTo, elementMap, "FAULT", False )


@pytest.mark.parametrize( "attributeName", [
    ( "PORO" ),  # The attribute is partial.
    ( "newAttribute" ),  # The attribute is not in the mesh from.
] )
def test_transferAttributeToDataSetWithElementMapAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    attributeName: str,
) -> None:
    """Test the raises AttributeError for the function transferAttributeToDataSetWithElementMap."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    meshTo: vtkMultiBlockDataSet = dataSetTest( "emptyFracture" )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "multiblock", "emptyFracture", False )
    with pytest.raises( AttributeError ):
        arrayModifiers.transferAttributeToDataSetWithElementMap( meshFrom, meshTo, elementMap, attributeName, False )


@pytest.mark.parametrize( "meshToNameTransfer, meshToNameMap, flatIdDataSetTo", [
    ( "emptyFracture", "emptymultiblock", 0 ),  # The map is wrong.
    ( "emptyFracture", "emptyFracture", 1 ),  # The flatIdDataSetTo is wrong.
] )
def test_transferAttributeToDataSetWithElementMapValueError(
    dataSetTest: vtkDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshToNameTransfer: str,
    meshToNameMap: str,
    flatIdDataSetTo: int,
) -> None:
    """Test the raises ValueError for the function transferAttributeToDataSetWithElementMap."""
    meshFrom: vtkDataSet = dataSetTest( "dataset" )
    meshTo: vtkDataSet = dataSetTest( meshToNameTransfer )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "dataset", meshToNameMap, False )
    with pytest.raises( ValueError ):
        arrayModifiers.transferAttributeToDataSetWithElementMap( meshFrom, meshTo, elementMap, "FAULT", False, flatIdDataSetTo=flatIdDataSetTo )


@pytest.mark.parametrize( "meshFromName, meshToName, attributeName, onPoints, defaultValueTest", [
    ( "fracture", "emptyFracture", "collocated_nodes", True, [ -1, -1 ] ),
    ( "multiblock", "emptyFracture", "FAULT", False, -1 ),
    ( "multiblock", "emptymultiblock", "FAULT", False, -1 ),
    ( "dataset", "emptymultiblock", "FAULT", False, -1 ),
    ( "dataset", "emptydataset", "FAULT", False, -1 ),
] )
def test_transferAttributeWithElementMap(
    dataSetTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshFromName: str,
    meshToName: str,
    attributeName: str,
    onPoints: bool,
    defaultValueTest: Any,
) -> None:
    """Test to transfer attributes from the source mesh to the final mesh using a map of points/cells."""
    meshFrom: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshFromName )
    if isinstance( meshFrom, vtkMultiBlockDataSet ):
        arrayModifiers.fillAllPartialAttributes( meshFrom )

    meshTo: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( meshToName )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshFromName, meshToName, onPoints )

    arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, attributeName, onPoints )

    for flatIdDataSetTo in elementMap:
        dataTo: Union[ vtkPointData, vtkCellData ]
        if isinstance( meshTo, vtkDataSet ):
            dataTo = meshTo.GetPointData() if onPoints else meshTo.GetCellData()
        elif isinstance( meshTo, vtkMultiBlockDataSet ):
            dataSetTo: vtkDataSet = vtkDataSet.SafeDownCast( meshTo.GetDataSet( flatIdDataSetTo ) )
            dataTo = dataSetTo.GetPointData() if onPoints else dataSetTo.GetCellData()

        arrayTo: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataTo.GetArray( attributeName ) )
        for idElementTo in range( len( arrayTo ) ):
            idElementFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 1 ] )
            if idElementFrom == -1:
                assert arrayTo[ idElementTo ] == defaultValueTest

            else:
                dataFrom: Union[ vtkPointData, vtkCellData ]
                if isinstance( meshFrom, vtkDataSet ):
                    dataFrom = meshFrom.GetPointData() if onPoints else meshFrom.GetCellData()
                elif isinstance( meshFrom, vtkMultiBlockDataSet ):
                    flatIdDataSetFrom: int = int( elementMap[ flatIdDataSetTo ][ idElementTo ][ 0 ] )
                    dataSetFrom: vtkDataSet = vtkDataSet.SafeDownCast( meshFrom.GetDataSet( flatIdDataSetFrom ) )
                    dataFrom = dataSetFrom.GetPointData() if onPoints else dataSetFrom.GetCellData()

                arrayFrom: npt.NDArray[ Any ] = vnp.vtk_to_numpy( dataFrom.GetArray( attributeName ) )
                assert np.all( arrayTo[ idElementTo ] == arrayFrom[ idElementFrom ] )


def test_transferAttributeWithElementMapTypeError(
    dataSetTest: vtkMultiBlockDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
) -> None:
    """Test the raises TypeError for the function transferAttributeWithElementMap with the mesh to with a wrong type."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    meshTo: bool = False
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "multiblock", "emptymultiblock", False )
    with pytest.raises( TypeError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, "FAULT", False )


def test_transferAttributeWithElementMapAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
) -> None:
    """Test the raises AttributeError for the function transferAttributeWithElementMap with an attribute already in the mesh to."""
    meshFrom: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    meshTo: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    elementMap: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( "multiblock", "emptymultiblock", False )
    with pytest.raises( AttributeError ):
        arrayModifiers.transferAttributeWithElementMap( meshFrom, meshTo, elementMap, "FAULT", False )


@pytest.mark.parametrize( "attributeName, onPoints", [
    ( "CellAttribute", False ),
    ( "PointAttribute", True ),
] )
def test_renameAttributeMultiblock(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test renaming attribute in a multiblock dataset."""
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute(
        vtkMultiBlockDataSetTest,
        attributeName,
        newAttributeName,
        onPoints,
    )
    block: vtkDataSet = vtkDataSet.SafeDownCast( vtkMultiBlockDataSetTest.GetDataSet( 1 ) )
    data: Union[ vtkPointData, vtkCellData ]
    if onPoints:
        data = block.GetPointData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1

    else:
        data = block.GetCellData()
        assert data.HasArray( attributeName ) == 0
        assert data.HasArray( newAttributeName ) == 1


@pytest.mark.parametrize( "attributeName, onPoints", [ ( "CellAttribute", False ), ( "PointAttribute", True ) ] )
def test_renameAttributeDataSet(
    dataSetTest: vtkDataSet,
    attributeName: str,
    onPoints: bool,
) -> None:
    """Test renaming an attribute in a dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
    newAttributeName: str = "new" + attributeName
    arrayModifiers.renameAttribute( object=vtkDataSetTest,
                                    attributeName=attributeName,
                                    newAttributeName=newAttributeName,
                                    onPoints=onPoints )
    if onPoints:
        assert vtkDataSetTest.GetPointData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetPointData().HasArray( newAttributeName ) == 1

    else:
        assert vtkDataSetTest.GetCellData().HasArray( attributeName ) == 0
        assert vtkDataSetTest.GetCellData().HasArray( newAttributeName ) == 1


def test_renameAttributeTypeError() -> None:
    """Test the raises TypeError for the function renameAttribute with the mesh to with a wrong type."""
    with pytest.raises( TypeError ):
        arrayModifiers.renameAttribute( False, "PORO", "newName", False )


@pytest.mark.parametrize( "attributeName, newName", [
    ( "newName", "newName" ),  # The attribute is not in the mesh.
    ( "PORO", "PORO" ),  # The new name is already an attribute in the mesh.
] )
def test_renameAttributeAttributeError(
    dataSetTest: vtkDataSet,
    attributeName: str,
    newName: str,
) -> None:
    """Test the raises AttributeError for the function renameAttribute."""
    mesh: vtkDataSet = dataSetTest( "dataset" )
    with pytest.raises( AttributeError ):
        arrayModifiers.renameAttribute( mesh, attributeName, newName, False )
