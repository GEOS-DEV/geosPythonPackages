# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator, attr-defined"
import pytest
from typing import Union, Any

import pandas as pd  # type: ignore[import-untyped]
import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPolyData, vtkFieldData, vtkPointData,
                                            vtkCellData, vtkUnstructuredGrid )

from geos.mesh.utils import arrayHelpers
from geos.utils.pieceEnum import Piece


@pytest.mark.parametrize( "meshType, cellDimExpected", [
    ( "vtu3D", { 3 } ),
    ( "vtu2D", { 2 } ),
    ( "vtu1D", { 1 } ),
    ( "vtm", { 1, 2, 3 } ),
] )
def test_getCellDimension(
    internMeshTest: Any,
    meshType: str,
    cellDimExpected: set[ int ],
) -> None:
    """Test getting the different cells dimension in a mesh."""
    mesh: vtkUnstructuredGrid | vtkMultiBlockDataSet = internMeshTest( meshType )
    cellDimObtained: set[ int ] = arrayHelpers.getCellDimension( mesh )
    assert cellDimObtained == cellDimExpected


def test_getCellDimensionTypeError() -> None:
    """Test getCellDimension TypeError raises."""
    meshWrongType: vtkCellData = vtkCellData()
    with pytest.raises( TypeError ):
        arrayHelpers.getCellDimension( meshWrongType )


@pytest.mark.parametrize(
    "meshTypeFrom, meshTypeTo, piece",
    [
        ( "vtu1D", "vtu1D", Piece.CELLS ),  # 1D vtu -> 1D vtu onCells
        ( "vtu1D", "vtu1D", Piece.POINTS ),  # 1D vtu -> 1D vtu onPoints
        ( "vtu1D", "vtu2D", Piece.CELLS ),  # 1D vtu -> 2D vtu onCells
        ( "vtu1D", "vtu2D", Piece.POINTS ),  # 1D vtu -> 2D vtu onPoints
        ( "vtu1D", "vtu3D", Piece.CELLS ),  # 1D vtu -> 3D vtu onCells
        ( "vtu1D", "vtu3D", Piece.POINTS ),  # 1D vtu -> 3D vtu onPoints
        ( "vtu1D", "vtm", Piece.CELLS ),  # 1D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu1D", "vtm", Piece.POINTS ),  # 1D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints

        ( "vtu2D", "vtu2D", Piece.CELLS ),  # 2D vtu -> 2D vtu onCells
        ( "vtu2D", "vtu2D", Piece.POINTS ),  # 2D vtu -> 2D vtu onPoints
        ( "vtu2D", "vtu1D", Piece.CELLS ),  # 2D vtu -> 1D vtu onCells
        ( "vtu2D", "vtu1D", Piece.POINTS ),  # 2D vtu -> 1D vtu onPoints
        ( "vtu2D", "vtu3D", Piece.CELLS ),  # 2D vtu -> 3D vtu onCells
        ( "vtu2D", "vtu3D", Piece.POINTS ),  # 2D vtu -> 3D vtu onPoints
        ( "vtu2D", "vtm", Piece.CELLS ),  # 2D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu2D", "vtm", Piece.POINTS ),  # 2D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints

        ( "vtu3D", "vtu3D", Piece.CELLS ),  # 3D vtu -> 3D vtu onCells
        ( "vtu3D", "vtu3D", Piece.POINTS ),  # 3D vtu -> 3D vtu onPoints
        ( "vtu3D", "vtu1D", Piece.CELLS ),  # 3D vtu -> 1D vtu onCells
        ( "vtu3D", "vtu1D", Piece.POINTS ),  # 3D vtu -> 1D vtu onPoints
        ( "vtu3D", "vtu2D", Piece.CELLS ),  # 3D vtu -> 2D vtu onCells
        ( "vtu3D", "vtu2D", Piece.POINTS ),  # 3D vtu -> 2D vtu onPoints
        ( "vtu3D", "vtm", Piece.CELLS ),  # 3D vtu -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtu3D", "vtm", Piece.POINTS ),  # 3D vtu -> vtm( 1D, 2D & 3D vtu ) onPoints

        ( "vtm", "vtm", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> vtm( 1D, 2D & 3D vtu ) onCells
        ( "vtm", "vtm", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> vtm( 1D, 2D & 3D vtu ) onPoints
        ( "vtm", "vtu1D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 1D vtu onCells
        ( "vtm", "vtu1D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 1D vtu onPoints
        ( "vtm", "vtu2D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 2D vtu onCells
        ( "vtm", "vtu2D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 2D vtu onPoints
        ( "vtm", "vtu3D", Piece.CELLS ),  # vtm( 1D, 2D & 3D vtu ) -> 3D vtu onCells
        ( "vtm", "vtu3D", Piece.POINTS ),  # vtm( 1D, 2D & 3D vtu ) -> 3D vtu onPoints
    ] )
def test_computeElementMapping(
    internMeshTest: Any,
    getElementMap: dict[ int, npt.NDArray[ np.int64 ] ],
    meshTypeFrom: str,
    meshTypeTo: str,
    piece: Piece,
) -> None:
    """Test getting the map between two meshes element."""
    meshFrom: vtkMultiBlockDataSet | vtkUnstructuredGrid = internMeshTest( meshTypeFrom )
    meshTo: vtkMultiBlockDataSet | vtkUnstructuredGrid = internMeshTest( meshTypeTo )
    elementMapComputed: dict[ int,
                              npt.NDArray[ np.int64 ] ] = arrayHelpers.computeElementMapping( meshFrom, meshTo, piece )
    elementMapTest: dict[ int, npt.NDArray[ np.int64 ] ] = getElementMap( meshTypeFrom, meshTypeTo, piece )

    keysComputed: list[ int ] = list( elementMapComputed.keys() )
    keysTest: list[ int ] = list( elementMapTest.keys() )
    assert keysComputed == keysTest

    for key in keysTest:
        assert np.all( elementMapComputed[ key ] == elementMapTest[ key ] )


def test_computeElementMappingValueError() -> None:
    """Test computeElementMapping ValueError raises."""
    pieceWrongValue: Piece = Piece.BOTH
    with pytest.raises( ValueError ):
        arrayHelpers.computeElementMapping( vtkMultiBlockDataSet(), vtkMultiBlockDataSet(), pieceWrongValue )


@pytest.mark.parametrize( "meshName, piece, expected", [
    ( "geosOutput2Ranks", Piece.POINTS, { 'localToGlobalMap': 1, 'ghostRank': 1, 'totalDisplacement': 3, 'mass': 1, 'externalForce': 3, 'fractureMechSolver_totalDisplacement_dofIndex': 1    } ),
    ( "geosOutput2Ranks", Piece.CELLS, { 'rockPerm_permeability': 3, 'water_internalEnergy': 1, 'rock_bulkModulus': 1, 'water_dInternalEnergy': 1, 'rock_shearModulus': 1, 'water_density': 1, 'water_dViscosity': 1, 'water_dDensity': 1, 'water_viscosity': 1, 'rockPorosity_initialPorosity': 1, 'water_enthalpy': 1, 'rockPorosity_porosity': 1, 'water_dEnthalpy': 1, 'rock_density': 1, 'rockPorosity_referencePorosity': 1, 'rockPorosity_biotCoefficient': 1, 'rockPorosity_grainBulkModulus': 1, 'reservoirAndWellsSolver_singlePhaseVariables_dofIndex': 1, 'deltaPressure': 1, 'mass': 1, 'pressure': 1, 'ghostRank': 1, 'temperature': 1, 'localToGlobalMap': 1, 'averageStrain': 6, 'elementCenter': 3, 'averageStress': 6, 'elementVolume': 1, 'averagePlasticStrain': 6, 'reservoirAndWellsSolver_singlePhaseWellVars_dofIndex': 1, 'connectionRate': 1, 'fracturePorosity_referencePorosity': 1, 'fracturePorosity_initialPorosity': 1, 'fracturePorosity_porosity': 1, 'fracturePerm_permeability': 3, 'fractureMechSolver_traction_dofIndex': 1, 'massCreated': 1, 'hydraulicAperture': 1, 'elementArea': 1, 'traction': 3, 'slip': 1, 'elementAperture': 1, 'tangentVector1': 3, 'displacementJump': 3, 'normalVector': 3, 'fractureState': 1, 'tangentVector2': 3, 'deltaSlip': 2, 'tangentialTraction': 1 } ),
    ( "extractAndMergeVolume", Piece.POINTS, { 'externalForce': 3, 'fractureMechSolver_totalDisplacement_dofIndex': 1, 'ghostRank': 1, 'localToGlobalMap': 1, 'mass': 1, 'totalDisplacement': 3 } ),
    ( "extractAndMergeVolume", Piece.CELLS, { 'averagePlasticStrain': 6, 'averageStrain': 6, 'averageStress': 6, 'deltaPressure': 1, 'elementCenter': 3, 'elementVolume': 1, 'ghostRank': 1, 'localToGlobalMap': 1, 'mass': 1, 'pressure': 1, 'reservoirAndWellsSolver_singlePhaseVariables_dofIndex': 1, 'rockPorosity_initialPorosity': 1, 'temperature': 1, 'water_dDensity': 1, 'water_dEnthalpy': 1, 'water_dInternalEnergy': 1, 'water_dViscosity': 1, 'water_density': 1, 'water_enthalpy': 1, 'water_internalEnergy': 1, 'water_viscosity': 1, 'blockIndex': 1, 'bulkModulus': 1, 'porosityInitial': 1, 'permeability': 3, 'porosity': 1, 'density': 1, 'shearModulus': 1, 'bulkModulusGrains': 1, 'biotCoefficient': 1, 'stressEffectiveInitial': 6, 'shearModulusInitial': 1, 'bulkModulusInitial': 1 } ),
] )
def test_getAttributesWithNumberOfComponents( dataSetTest: Any, meshName: str, piece: Piece,
                                              expected: dict[ str, int ] ) -> None:
    """Test getting attribute list as dict from a mesh."""
    mesh: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshName )
    attributes: dict[ str, int ] = arrayHelpers.getAttributesWithNumberOfComponents( mesh, piece )

    assert attributes == expected


def test_getAttributesWithNumberOfComponentsValueError() -> None:
    """Test fails of the function getAttributesWithNumberOfComponents with a value error."""
    with pytest.raises( ValueError ):
        arrayHelpers.getAttributesWithNumberOfComponents( vtkPolyData(), Piece.BOTH )


def test_getAttributesWithNumberOfComponentsAttributeError() -> None:
    """Test fails of the function getAttributesWithNumberOfComponents with an attribute error."""
    mesh: vtkPolyData = vtkPolyData()
    mesh.GetCellData().AddArray( vtkDoubleArray() )
    with pytest.raises( AttributeError ):
        arrayHelpers.getAttributesWithNumberOfComponents( mesh, Piece.CELLS )


def test_getAttributesWithNumberOfComponentsTypeError() -> None:
    """Test fails of the function getAttributesWithNumberOfComponents with a type error."""
    with pytest.raises( TypeError ):
        arrayHelpers.getAttributesWithNumberOfComponents( vtkCellData(), Piece.CELLS )


@pytest.mark.parametrize( "meshName, attributeName, pieceTest", [
    ( "extractAndMergeVolume", "elementVolume", Piece.CELLS ),
    ( "extractAndMergeVolume", "externalForce", Piece.POINTS ),
    ( "extractAndMergeVolume", "NewAttribute", Piece.NONE ),
    ( "extractAndMergeVolume", "ghostRank", Piece.BOTH ),
    ( "extractAndMergeVolume", "TIME", Piece.FIELD ),
    ( "2Ranks", "elementVolume", Piece.CELLS ),
    ( "2Ranks", "externalForce", Piece.POINTS ),
    ( "2Ranks", "NewAttribute", Piece.NONE ),
    ( "2Ranks", "ghostRank", Piece.BOTH ),
    ( "2Ranks", "TIME", Piece.FIELD ),
] )
def test_getAttributePieceInfo(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
    pieceTest: Piece,
) -> None:
    """Test getting attribute piece information."""
    dataSet: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    pieceObtained = arrayHelpers.getAttributePieceInfo( dataSet, attributeName )
    assert pieceObtained == pieceTest


def test_getNumpyGlobalIdsArray( dataSetTest: vtkDataSet ) -> None:
    """Test the function getNumpyGlobalIdsArray."""
    dataset: vtkDataSet = dataSetTest( "dataset" )
    for piece in [ Piece.POINTS, Piece.CELLS ]:
        fieldData: vtkPointData | vtkCellData = dataset.GetPointData(
        ) if piece == Piece.POINTS else dataset.GetCellData()
        nbElements: int = fieldData.GetNumberOfTuples()
        npArrayExpected: npt.NDArray = np.array( list( range( nbElements ) ) )
        npArrayObtained: npt.NDArray = arrayHelpers.getNumpyGlobalIdsArray( fieldData )
        assert ( npArrayObtained == npArrayExpected ).all()


def test_getNumpyGlobalIdsArrayTypeError() -> None:
    """Test getNumpyGlobalIdsArray TypeError raises."""
    fieldData: vtkPolyData = vtkPolyData()
    with pytest.raises( TypeError ):
        arrayHelpers.getNumpyGlobalIdsArray( fieldData )


def test_getNumpyGlobalIdsArrayAttributeError() -> None:
    """Test getNumpyGlobalIdsArray AttributeError raises."""
    fieldData: vtkFieldData = vtkFieldData()
    with pytest.raises( AttributeError ):
        arrayHelpers.getNumpyGlobalIdsArray( fieldData )


@pytest.mark.parametrize( "meshName, piece, expectedAttributeSet", [
    ( "extractAndMergeVolume", Piece.POINTS, { 'totalDisplacement', 'fractureMechSolver_totalDisplacement_dofIndex', 'localToGlobalMap', 'externalForce', 'mass', 'ghostRank' } ),
    ( "extractAndMergeVolume", Piece.CELLS, { 'deltaPressure', 'averageStrain', 'water_dInternalEnergy', 'localToGlobalMap', 'blockIndex', 'bulkModulusInitial', 'averageStress', 'permeability', 'bulkModulusGrains', 'water_density', 'porosity', 'pressure', 'ghostRank', 'temperature', 'elementCenter', 'water_viscosity', 'stressEffectiveInitial', 'water_dViscosity', 'reservoirAndWellsSolver_singlePhaseVariables_dofIndex', 'averagePlasticStrain', 'biotCoefficient', 'water_internalEnergy', 'rockPorosity_initialPorosity', 'shearModulus', 'elementVolume', 'density', 'mass', 'porosityInitial', 'bulkModulus', 'water_dEnthalpy', 'shearModulusInitial', 'water_dDensity', 'water_enthalpy' } ),
    ( "geosOutput2Ranks", Piece.POINTS, { 'totalDisplacement', 'fractureMechSolver_totalDisplacement_dofIndex', 'localToGlobalMap', 'mass', 'externalForce', 'ghostRank' } ),
    ( "geosOutput2Ranks", Piece.CELLS, { 'averageStress', 'fractureMechSolver_traction_dofIndex', 'temperature', 'averagePlasticStrain', 'elementArea', 'rockPorosity_initialPorosity', 'tangentVector2', 'fracturePerm_permeability', 'fractureState', 'fracturePorosity_referencePorosity', 'ghostRank', 'rock_shearModulus', 'rockPorosity_biotCoefficient', 'rockPorosity_grainBulkModulus', 'pressure', 'traction', 'tangentialTraction', 'rock_bulkModulus', 'rockPerm_permeability', 'mass', 'tangentVector1', 'water_density', 'elementVolume', 'water_dInternalEnergy', 'connectionRate', 'normalVector', 'water_internalEnergy', 'displacementJump', 'fracturePorosity_initialPorosity', 'massCreated', 'elementCenter', 'water_dEnthalpy', 'deltaPressure', 'hydraulicAperture', 'elementAperture', 'averageStrain', 'water_dDensity', 'rock_density', 'reservoirAndWellsSolver_singlePhaseWellVars_dofIndex', 'reservoirAndWellsSolver_singlePhaseVariables_dofIndex', 'rockPorosity_porosity', 'water_viscosity', 'fracturePorosity_porosity', 'slip', 'localToGlobalMap', 'water_enthalpy', 'deltaSlip', 'water_dViscosity', 'rockPorosity_referencePorosity' } ),
] )
def test_getAttributeSet(
    dataSetTest: Any,
    meshName: str,
    piece: Piece,
    expectedAttributeSet: set[ str ],
) -> None:
    """Test getAttributeSet function."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    obtainedAttributeSet: set[ str ] = arrayHelpers.getAttributeSet( mesh, piece )
    assert obtainedAttributeSet == expectedAttributeSet


@pytest.mark.parametrize( "arrayName, sorted, piece, expectedNpArray", [
    ( "bulkModulus", False, Piece.CELLS, np.array( [ 7119047619.04762 for _ in range( 6000 ) ], dtype=np.float64 ) ),
    # ( "PORO", False, Piece.CELLS, np.array( [ 0.20000000298 for _ in range( 1740 ) ], dtype=np.float32 ) ),
    # ( "PointAttribute", False, Piece.POINTS, np.array( [ [ 12.4, 9.7, 10.5 ] for _ in range( 4092 ) ],
    #                                                    dtype=np.float64 ) ),
] )
def test_getNumpyArrayByName(
    dataSetTest: vtkDataSet,
    arrayName: str,
    sorted: bool,
    piece: Piece,
    expectedNpArray: npt.NDArray,
) -> None:
    """Test the function getNumpyGlobalIdsArray."""
    dataset: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    fieldData: vtkPointData | vtkCellData = dataset.GetPointData() if piece == Piece.POINTS else dataset.GetCellData()
    obtainedNpArray: npt.NDArray = arrayHelpers.getNumpyArrayByName( fieldData, arrayName, sorted )
    assert ( obtainedNpArray == expectedNpArray ).all()


def test_getNumpyArrayByNameAttributeError( dataSetTest: vtkDataSet ) -> None:
    """Test getNumpyArrayByName AttributeError raises."""
    dataset: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    fieldData: vtkCellData = dataset.GetCellData()
    with pytest.raises( AttributeError ):
        arrayHelpers.getNumpyArrayByName( fieldData, "Attribute" )


@pytest.mark.parametrize( "meshName, attributeName, listValues, piece, validValuesTest, invalidValuesTest", [
    ( "2Ranks", "localToGlobalMap", [ 0, 42, 7000 ], Piece.CELLS, [ 0, 42 ], [ 7000 ] ),
    ( "2Ranks", "localToGlobalMap", [ 0, 42, 8000 ], Piece.POINTS, [ 0, 42 ], [ 8000 ] ),
    ( "extractAndMergeVolume", "localToGlobalMap", [ 0, 42, 7000 ], Piece.CELLS, [ 0, 42 ], [ 7000 ] ),
    ( "extractAndMergeVolume", "localToGlobalMap", [ 0, 42, 8000 ], Piece.POINTS, [ 0, 42 ], [ 8000 ] ),
    ( "extractAndMergeVolume", "averagePlasticStrain", [ [ 0, 0, 0, 0, 0 ,0 ], [ 1, 1, 1, 1, 1, 1 ] ], Piece.CELLS, [ [ 0, 0, 0, 0, 0 ,0 ] ], [ [ 1, 1, 1, 1, 1, 1 ] ] ),
] )
def test_checkValidValuesInObject(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
    listValues: list[ Any ],
    piece: Piece,
    validValuesTest: list[ Any ],
    invalidValuesTest: list[ Any ],
) -> None:
    """Test the function checkValidValuesInObject."""
    mesh: vtkMultiBlockDataSet | vtkDataSet = dataSetTest( meshName )
    validValues: list[ Any ]
    invalidValues: list[ Any ]
    validValues, invalidValues = arrayHelpers.checkValidValuesInObject( mesh, attributeName, listValues, piece )
    assert validValues == validValuesTest
    assert invalidValues == invalidValuesTest


@pytest.mark.parametrize( "attributeName, piece", [
    ( "attributeName", Piece.CELLS ),  # The attribute is not on the mesh
    ( "ghostRank", Piece.POINTS ),  # The attribute is not global
] )
def test_checkValidValuesInObjectAttributeError(
    dataSetTest: vtkMultiBlockDataSet,
    attributeName: str,
    piece: str,
) -> None:
    """Test fails of checkValidValuesInObject with an attribute error."""
    mesh: vtkMultiBlockDataSet = dataSetTest( "geosOutput2Ranks" )
    with pytest.raises( AttributeError ):
        arrayHelpers.checkValidValuesInObject( mesh, attributeName, [], piece )


def test_checkValidValuesInObjectTypeError() -> None:
    """Test fails of checkValidValuesInObject with a type error."""
    with pytest.raises( TypeError ):
        arrayHelpers.checkValidValuesInObject( vtkCellData(), "AttributeName", [], Piece.CELLS )


@pytest.mark.parametrize( "meshName, attributeName, piece, expected", [
    ( "extractAndMergeVolume", "totalDisplacement", Piece.POINTS, True ),
    ( "extractAndMergeVolume", "Attribute", Piece.CELLS, False ),
    ( "extractAndMergeVolume", "pressure", Piece.CELLS, True ),
    ( "extractAndMergeVolume", "ghostRank", Piece.BOTH, True ),
    ( "extractAndMergeVolume", "TIME", Piece.FIELD, True ),
    ( "geosOutput2Ranks", "totalDisplacement", Piece.POINTS, True ),
    ( "geosOutput2Ranks", "Attribute", Piece.CELLS, False ),
    ( "geosOutput2Ranks", "pressure", Piece.CELLS, True ),
    ( "geosOutput2Ranks", "ghostRank", Piece.BOTH, True ),
    ( "geosOutput2Ranks", "TIME", Piece.FIELD, True ),
] )
def test_isAttributeInObject(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
    piece: Piece,
    expected: bool,
) -> None:
    """Test the function isAttributeInObject."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    assert arrayHelpers.isAttributeInObject( mesh, attributeName, piece ) == expected


def test_isAttributeInObjectTypeError() -> None:
    """Test isAttributeInObject TypeError raises."""
    mesh: vtkCellData = vtkCellData()
    with pytest.raises( TypeError ):
        arrayHelpers.isAttributeInObject( mesh, "Attribute", Piece.CELLS )


@pytest.mark.parametrize( "meshName, attributeName, piece, expected", [
    ( "2Ranks", "pressure", Piece.CELLS, True ),
    ( "2Ranks", "totalDisplacement", Piece.POINTS, True ),
    ( "geosOutput2Ranks", "ghostRank", Piece.CELLS, True ),
    ( "geosOutput2Ranks", "ghostRank", Piece.POINTS, False ),
] )
def test_isAttributeGlobal(
    dataSetTest: vtkMultiBlockDataSet,
    meshName: str,
    attributeName: str,
    piece: Piece,
    expected: bool,
) -> None:
    """Test if the attribute is global or partial."""
    multiBlockDataset: vtkMultiBlockDataSet = dataSetTest( meshName )
    obtained: bool = arrayHelpers.isAttributeGlobal( multiBlockDataset, attributeName, piece )
    assert obtained == expected


@pytest.mark.parametrize( "attributeName, piece, expected", [
    ( "externalForce", Piece.POINTS, np.array( [ [0, 0, 0 ] for _ in range( 7381 ) ], dtype=np.int64 ) ),
    ( "biotCoefficient", Piece.CELLS, np.array( [ 1 for _ in range( 6000 ) ], dtype=np.int64 ) ),
    ( "TIME", Piece.FIELD, np.array( [ 30000000. ], dtype=np.float64 ) ),
] )
def test_getArrayInObject(
    dataSetTest: vtkDataSet,
    attributeName: str,
    piece: Piece,
    expected: npt.NDArray[ Any ], ) -> None:
    """Test getting numpy array of an attribute from dataset."""
    vtkDataSetTest: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    obtained: npt.NDArray[ Any ] = arrayHelpers.getArrayInObject( vtkDataSetTest, attributeName, piece )

    assert ( obtained == expected ).all()


@pytest.mark.parametrize( "meshName, attributeName, piece, expectedVtkType", [
    ( "extractAndMergeVolume", "ghostRank", Piece.CELLS, 6 ),
    ( "extractAndMergeVolume", "localToGlobalMap", Piece.CELLS, 16 ),
    ( "extractAndMergeVolume", "averagePlasticStrain", Piece.CELLS, 11 ),
    ( "extractAndMergeVolume", "ghostRank", Piece.POINTS, 6 ),
    ( "extractAndMergeVolume", "localToGlobalMap", Piece.POINTS, 16 ),
    ( "extractAndMergeVolume", "totalDisplacement", Piece.POINTS, 11 ),
    ( "extractAndMergeFault", "Normals", Piece.CELLS, 10 ),
    ( "extractAndMergeFault", "Texture Coordinates", Piece.POINTS, 10 ),
    ( "2Ranks", "ghostRank", Piece.CELLS, 6 ),
    ( "2Ranks", "localToGlobalMap", Piece.CELLS, 16 ),
    ( "2Ranks", "averagePlasticStrain", Piece.CELLS, 11 ),
    ( "2Ranks", "ghostRank", Piece.POINTS, 6 ),
    ( "2Ranks", "localToGlobalMap", Piece.POINTS, 16 ),
    ( "2Ranks", "totalDisplacement", Piece.POINTS, 11 ),
] )
def test_getVtkArrayTypeInObject(
    dataSetTest: Any,
    meshName: str,
    attributeName: str,
    piece: Piece,
    expectedVtkType: int,
) -> None:
    """Test the function getVtkArrayTypeInObject."""
    mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
    obtainedVtkType: int = arrayHelpers.getVtkArrayTypeInObject( mesh, attributeName, piece )

    assert obtainedVtkType == expectedVtkType


def test_getVtkArrayTypeInObjectAttributeError( dataSetTest: Any ) -> None:
    """Test fails of the function getVtkArrayTypeInObject with an attribute error."""
    mesh: vtkDataSet = dataSetTest( "extractAndMergeVolume" )
    with pytest.raises( AttributeError ):
        arrayHelpers.getVtkArrayTypeInObject( mesh, "attributeName", Piece.CELLS )


def test_getVtkArrayTypeInObjectTypeError() -> None:
    """Test fails of the function getVtkArrayTypeInObject with a type error."""
    with pytest.raises( TypeError ):
        arrayHelpers.getVtkArrayTypeInObject( vtkCellData(), "PORO", Piece.CELLS )


# @pytest.mark.parametrize( "arrayExpected, piece", [
#     ( "PORO", Piece.CELLS ),
#     ( "PointAttribute", Piece.POINTS ),
# ],
#                           indirect=[ "arrayExpected" ] )
# def test_getVtkArrayInObject( request: pytest.FixtureRequest, arrayExpected: npt.NDArray[ np.float64 ],
#                               dataSetTest: vtkDataSet, piece: Piece ) -> None:
#     """Test getting Vtk Array from a dataset."""
#     vtkDataSetTest: vtkDataSet = dataSetTest( "dataset" )
#     params = request.node.callspec.params
#     attributeName: str = params[ 'arrayExpected' ]

#     obtained: vtkDoubleArray = arrayHelpers.getVtkArrayInObject( vtkDataSetTest, attributeName, piece )
#     obtained_as_np: npt.NDArray[ np.float64 ] = vnp.vtk_to_numpy( obtained )

#     assert ( obtained_as_np == arrayExpected ).all()


# @pytest.mark.parametrize( "meshName, attributeName, piece, expected", [
#     ( "dataset", "PORO", Piece.CELLS, 1 ),
#     ( "dataset", "PERM", Piece.CELLS, 3 ),
#     ( "dataset", "PointAttribute", Piece.POINTS, 3 ),
#     ( "multiblock", "PORO", Piece.CELLS, 1 ),
#     ( "multiblock", "PERM", Piece.CELLS, 3 ),
#     ( "multiblock", "PointAttribute", Piece.POINTS, 3 ),
# ] )
# def test_getNumberOfComponents(
#     dataSetTest: Any,
#     meshName: str,
#     attributeName: str,
#     piece: Piece,
#     expected: int,
# ) -> None:
#     """Test getting the number of components of an attribute from a multiblock."""
#     mesh: vtkDataSet | vtkMultiBlockDataSet = dataSetTest( meshName )
#     assert arrayHelpers.getNumberOfComponents( mesh, attributeName, piece ) == expected


# def test_getNumberOfComponentsTypeError() -> None:
#     """Test getNumberOfComponents fails with a type error."""
#     meshWrongType: vtkCellData = vtkCellData()
#     with pytest.raises( TypeError ):
#         arrayHelpers.getNumberOfComponents( meshWrongType, "PORO", Piece.CELLS )


# def test_getNumberOfComponentsAttributeError( dataSetTest: Any, ) -> None:
#     """Test getNumberOfComponents fails with an attribute error."""
#     mesh: vtkDataSet = dataSetTest( "dataset" )
#     with pytest.raises( AttributeError ):
#         arrayHelpers.getNumberOfComponents( mesh, "attributeName", Piece.POINTS )


# def test_getNumberOfComponentsValueError( dataSetTest: Any, ) -> None:
#     """Test getNumberOfComponents fails with a value error."""
#     mesh: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
#     with pytest.raises( ValueError ):
#         arrayHelpers.getNumberOfComponents( mesh, "ghostRank", Piece.BOTH )


# @pytest.mark.parametrize( "meshName, attributeName, piece, expected", [
#     ( "dataset", "PERM", Piece.CELLS, ( "AX1", "AX2", "AX3" ) ),
#     ( "dataset", "PORO", Piece.CELLS, () ),
#     ( "multiblock", "PERM", Piece.CELLS, ( "AX1", "AX2", "AX3" ) ),
#     ( "multiblock", "PORO", Piece.CELLS, () ),
# ] )
# def test_getComponentNames( dataSetTest: Any, meshName: str, attributeName: str, piece: Piece,
#                             expected: tuple[ str, ...] ) -> None:
#     """Test getting the component names of an attribute from a mesh."""
#     vtkDataSetTest: Any = dataSetTest( meshName )
#     obtained: tuple[ str, ...] = arrayHelpers.getComponentNames( vtkDataSetTest, attributeName, piece )
#     assert obtained == expected


# def test_getComponentNamesTypeError() -> None:
#     """Test getting the component names fails with a type error."""
#     meshWrongType: vtkFieldData = vtkFieldData()
#     with pytest.raises( TypeError ):
#         arrayHelpers.getComponentNames( meshWrongType, "PORO", Piece.CELLS )


# def test_getComponentNamesAttributeError( dataSetTest: Any, ) -> None:
#     """Test getting the component names fails with an attribute error."""
#     mesh: vtkDataSet = dataSetTest( "dataset" )
#     with pytest.raises( AttributeError ):
#         arrayHelpers.getComponentNames( mesh, "attributeName", Piece.POINTS )


# def test_getComponentNamesValueError( dataSetTest: Any, ) -> None:
#     """Test getting the component names fails with a value error."""
#     mesh: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
#     with pytest.raises( ValueError ):
#         arrayHelpers.getComponentNames( mesh, "ghostRank", Piece.BOTH )


# @pytest.mark.parametrize( "attributeNames, piece, expected_columns", [
#     ( ( "collocated_nodes", ), Piece.POINTS, ( "collocated_nodes_0", "collocated_nodes_1" ) ),
# ] )
# def test_getAttributeValuesAsDF( dataSetTest: vtkPolyData, attributeNames: tuple[ str, ...], piece: Piece,
#                                  expected_columns: tuple[ str, ...] ) -> None:
#     """Test getting an attribute from a polydata as a dataframe."""
#     polydataset: vtkPolyData = vtkPolyData.SafeDownCast( dataSetTest( "polydata" ) )
#     data: pd.DataFrame = arrayHelpers.getAttributeValuesAsDF( polydataset, attributeNames, piece )

#     obtained_columns = data.columns.values.tolist()
#     assert obtained_columns == list( expected_columns )


# @pytest.mark.parametrize(
#     "attributeNames, expected",
#     [
#         ( [ "CellAttribute" ], True ),  # Attribute on cells
#         ( [ "PointAttribute" ], True ),  # Attribute on points
#         ( [ "attribute" ], False ),  # "attribute" is not on the mesh
#         ( [ "CellAttribute", "attribute" ], True ),  # "attribute" is not on the mesh
#     ] )
# def test_hasArray( dataSetTest: vtkDataSet, attributeNames: list[ str ], expected: bool ) -> None:
#     """Test the function hasArray."""
#     mesh: vtkDataSet = dataSetTest( "dataset" )
#     assert arrayHelpers.hasArray( mesh, attributeNames ) == expected


# def test_computeCellCenterCoordinates( dataSetTest: vtkMultiBlockDataSet ) -> None:
#     """Test the function computeCellCenterCoordinates."""
#     mesh: vtkMultiBlockDataSet = dataSetTest( "multiblockGeosOutput" )
#     dataset: vtkDataSet = vtkDataSet.SafeDownCast( mesh.GetDataSet( 5 ) )
#     expected: npt.NDArray = vnp.vtk_to_numpy( dataset.GetCellData().GetArray( "elementCenter" ) )
#     obtained: npt.NDArray = vnp.vtk_to_numpy( arrayHelpers.computeCellCenterCoordinates( dataset ) )
#     assert ( obtained == expected ).all()
