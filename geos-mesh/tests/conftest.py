# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union
import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader, vtkXMLMultiBlockDataReader


@pytest.fixture
def arrayExpected( request: pytest.FixtureRequest ) -> npt.NDArray[ np.float64 ]:
    reference_data = "data/data.npz"
    reference_data_path = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), reference_data )
    data = np.load( reference_data_path )

    return data[ request.param ]


@pytest.fixture
def arrayTest( request: pytest.FixtureRequest ) -> npt.NDArray[ np.float64 ]:
    np.random.seed( 42 )
    array: npt.NDArray[ np.float64 ] = np.random.rand(
        request.param,
        3,
    )
    return array

@pytest.fixture
def getArrayWithSpeTypeValue() -> npt.NDArray[ any ]:
    def _getarray( nb_component: int, nb_elements: int, valueType: str ) :
        if valueType == "int32":
            if nb_component == 1:
                return np.array( [ np.int32( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int32( 1000 * np.random.random() ) for _ in range( nb_component ) ] for _ in range( nb_elements ) ] )


        elif valueType == "int64":
            if nb_component == 1:
                return np.array( [ np.int64( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.int64( 1000 * np.random.random() ) for _ in range( nb_component ) ] for _ in range( nb_elements ) ] )
    
        elif valueType == "float32":
            if nb_component == 1:
                return np.array( [ np.float32( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.float32( 1000 * np.random.random() ) for _ in range( nb_component ) ] for _ in range( nb_elements ) ] )

        elif valueType == "float64":
            if nb_component == 1:
                return np.array( [ np.float64( 1000 * np.random.random() ) for _ in range( nb_elements ) ] )
            else:
                return np.array( [ [ np.float64( 1000 * np.random.random() ) for _ in range( nb_component ) ] for _ in range( nb_elements ) ] )

    return _getarray


@pytest.fixture
def dataSetTest() -> Union[ vtkMultiBlockDataSet, vtkPolyData, vtkDataSet ]:

    def _get_dataset( datasetType: str ):
        if datasetType == "multiblock":
            reader = reader = vtkXMLMultiBlockDataReader()
            vtkFilename = "data/displacedFault.vtm"
        elif datasetType == "emptymultiblock":
            reader = reader = vtkXMLMultiBlockDataReader()
            vtkFilename = "data/displacedFaultempty.vtm"
        elif datasetType == "dataset":
            reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/domain_res5_id.vtu"
        elif datasetType == "emptydataset":
            reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/domain_res5_id_empty.vtu"
        elif datasetType == "polydata":
            reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/surface.vtu"
        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset