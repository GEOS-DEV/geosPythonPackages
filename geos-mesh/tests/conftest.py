# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest

import numpy as np
import numpy.typing as npt

from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader


@pytest.fixture
def array( request: str ) -> npt.NDArray:
    """Fixture to get reference array depending on request array name.

    Args:
        request (str): _description_

    Returns:
        npt.NDArray: _description_
    """
    reference_data = "data/data.npz"
    reference_data_path = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), reference_data )
    data = np.load( reference_data_path )

    return data[ request.param ]


@pytest.fixture( scope="function" )
def vtkDataSetTest() -> vtkDataSet:
    """Load vtk dataset to run the tests in test_vtkUtils.py.

    Returns:
        vtkDataSet: _description_
    """
    reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
    vtkFilename = "data/domain_res5_id.vtu"
    data_test_path = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
    # reader.SetFileName( "geos-mesh/tests/data/domain_res5_id.vtu" )
    reader.SetFileName( data_test_path )
    reader.Update()

    return reader.GetOutput()
