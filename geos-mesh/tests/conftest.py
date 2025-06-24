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
def dataSetTest() -> Union[ vtkMultiBlockDataSet, vtkPolyData, vtkDataSet ]:

    def _get_dataset( datasetType: str ):
        if datasetType == "multiblock":
            reader = reader = vtkXMLMultiBlockDataReader()
            vtkFilename = "data/displacedFault.vtm"
        elif datasetType == "dataset":
            reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/domain_res5_id.vtu"
        elif datasetType == "polydata":
            reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
            vtkFilename = "data/surface.vtu"
        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset