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

import pytest


@pytest.fixture
def array(request: str) -> npt.NDArray:
    data = np.load("data/data.npz")

    return data[request.param]




@pytest.fixture(scope="function")
def vtkDataSetTest() -> vtkDataSet:
    reader: vtkXMLUnstructuredGridReader = vtkXMLUnstructuredGridReader()
    reader.SetFileName( "../../../GEOS/inputFiles/poromechanicsFractures/domain_res5_id.vtu" )
    reader.Update()
    
    return reader.GetOutput()



@pytest.fixture(scope="function")
def vtkdatasetWithComponentNames(vtkDataSetTest: vtkDataSet):
    attributeName1: str = "PERM"

    # return dataset
    if vtkDataSetTest.GetCellData().HasArray( attributeName1 ) == 1:
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 0, "component1" )
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 1, "component2" )
        vtkDataSetTest.GetCellData().GetArray( attributeName1 ).SetComponentName( 2, "component3" )

    return vtkDataSetTest

