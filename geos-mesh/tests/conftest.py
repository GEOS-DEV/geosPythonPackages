# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file

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
    data = np.load( "data/data.npz" )

    return data[ request.param ]


@pytest.fixture( scope="function" )
def vtkDataSetTest() -> vtkDataSet:
    """Load vtk dataset to run the tests in test_vtkUtils.py.

    Returns:
        vtkDataSet: _description_
    """
    reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
    reader.SetFileName( "../../../GEOS/inputFiles/poromechanicsFractures/domain_res5_id.vtu" )
    reader.Update()

    return reader.GetOutput()


@pytest.fixture( scope="function" )
def vtkdatasetWithComponentNames( vtkDataSetTest: vtkDataSet ) -> vtkDataSet:
    """Set names for existing vtk dataset for test purpose.

    Args:
        vtkDataSetTest (vtkDataSet): _description_

    Returns:
        _type_: _description_
    """
    attributeName1: str = "PERM"

    # return dataset
    if vtkDataSetTest.GetCellData().HasArray( attributeName1 ) == 1:
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 0, "component1" )
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 1, "component2" )
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 2, "component3" )

    return vtkDataSetTest
