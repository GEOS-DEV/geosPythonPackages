# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
from typing import Union, Tuple, cast

import numpy as np
import numpy.typing as npt

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )

from geos.mesh.processing.FillPartialArrays import FillPartialArrays


@pytest.mark.parametrize( "onpoints, attributesList, value_test", [
    ( False, ( ( 0, "PORO", 1 ), ), np.nan ),
    ( True, ( ( 0, "PointAttribute", 3 ), ( 1, "collocated_nodes", 2 ) ), 2. ),
    ( False, ( ( 0, "CELL_MARKERS", 1 ), ( 0, "CellAttribute", 3 ), ( 0, "FAULT", 1 ), ( 0, "PERM", 3 ),
               ( 0, "PORO", 1 ) ), 2. ),
    ( False, ( ( 0, "PORO", 1 ), ), 2.0 ),
    ( True, ( ( 0, "PointAttribute", 3 ), ( 1, "collocated_nodes", 2 ) ), np.nan ),
    ( False, ( ( 0, "CELL_MARKERS", 1 ), ( 0, "CellAttribute", 3 ), ( 0, "FAULT", 1 ), ( 0, "PERM", 3 ),
               ( 0, "PORO", 1 ) ), np.nan ),
] )
def test_FillPartialArrays(
    dataSetTest: vtkMultiBlockDataSet,
    onpoints: bool,
    attributesList: Tuple[ Tuple[ int, str, int ], ...],
    value_test: float,
) -> None:
    """Test FillPartialArrays vtk filter."""
    vtkMultiBlockDataSetTestRef: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    vtkMultiBlockDataSetTest: vtkMultiBlockDataSet = dataSetTest( "multiblock" )
    attributesNameList: list[ str ] = [ attributesList[ i ][ 1 ] for i in range( len( attributesList ) ) ]

    filter: FillPartialArrays = FillPartialArrays()
    filter._SetAttributesNameList( attributesNameList )
    filter._SetValueToFill( value_test )
    filter.SetInputDataObject( vtkMultiBlockDataSetTest )
    filter.Update()

    nbBlock: int = vtkMultiBlockDataSetTestRef.GetNumberOfBlocks()
    for block_id in range( nbBlock ):
        datasetRef: vtkDataSet = cast( vtkDataSet, vtkMultiBlockDataSetTestRef.GetBlock( block_id ) )
        dataset: vtkDataSet = cast( vtkDataSet, filter.GetOutputDataObject( 0 ).GetBlock( block_id ) )
        expected_array: npt.NDArray[ np.float64 ]
        array: npt.NDArray[ np.float64 ]
        dataRef: Union[ vtkPointData, vtkCellData ]
        data: Union[ vtkPointData, vtkCellData ]
        nbElements: list[ int ]
        if onpoints:
            dataRef = datasetRef.GetPointData()
            data = dataset.GetPointData()
            nbElements = [ 212, 4092 ]
        else:
            dataRef = datasetRef.GetCellData()
            data = dataset.GetCellData()
            nbElements = [ 156, 1740 ]

        for inBlock, attribute, nbComponents in attributesList:
            array = vnp.vtk_to_numpy( data.GetArray( attribute ) )
            if block_id == inBlock:
                expected_array = vnp.vtk_to_numpy( dataRef.GetArray( attribute ) )
                assert ( array == expected_array ).all()
            else:
                expected_array = np.array( [ [ value_test for i in range( nbComponents ) ]
                                             for _ in range( nbElements[ inBlock ] ) ] )
                if np.isnan( value_test ):
                    assert np.all( np.isnan( array ) == np.isnan( expected_array ) )
                else:
                    assert ( array == expected_array ).all()
