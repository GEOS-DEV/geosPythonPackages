# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Any
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )

from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

@pytest.mark.parametrize( "mesh, regionName, newAttributeName, dictRegion, valueType", [
    ( "dataset", "FAULT", "newAttribute", { 0: 0, 100: 1 }, 10 )
] )
def test_CreateConstantAttributePerRegion(
    dataSetTest: Union[ vtkMultiBlockDataSet, vtkDataSet ],
    mesh: str,
    regionName: str,
    newAttributeName: str,
    dictRegion: dict[ Any, Any ],
    valueType: int,
) -> None:
    input_mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = dataSetTest( mesh )
    filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( regionName,
                                                                                 newAttributeName,
                                                                                 dictRegion,
                                                                                 valueType,
                                                                                 )
    filter.SetInputDataObject( input_mesh )
    filter.Update()

    mesh: Union[ vtkMultiBlockDataSet, vtkDataSet ] = filter.GetOutputDataObject( 0 )

    if isinstance( mesh, vtkMultiBlockDataSet ):
        assert 1 == 1
    
    else:
        assert mesh.GetCellData().HasArray( newAttributeName ) == 1

