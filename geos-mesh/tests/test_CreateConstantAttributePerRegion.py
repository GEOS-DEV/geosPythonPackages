# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
# mypy: disable-error-code="operator"
import pytest
import os
from typing import Union, Tuple, cast, Any

import numpy as np
import numpy.typing as npt
from geos.utils.Logger import *

import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonDataModel import ( vtkDataSet, vtkMultiBlockDataSet, vtkPointData, vtkCellData )
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridReader, vtkXMLMultiBlockDataReader

from geos.mesh.processing.CreateConstantAttributePerRegion import CreateConstantAttributePerRegion

datasetType: str = "dataset"

reader: Union[ vtkXMLMultiBlockDataReader, vtkXMLUnstructuredGridReader ]
if datasetType == "multiblock":
    reader = vtkXMLMultiBlockDataReader()
    vtkFilename = "data/displacedFault.vtm"
elif datasetType == "dataset":
    reader = vtkXMLUnstructuredGridReader()
    vtkFilename = "data/domain_res5_id.vtu"
elif datasetType == "polydata":
    reader = vtkXMLUnstructuredGridReader()
    vtkFilename = "data/surface.vtu"

datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
reader.SetFileName( datapath )
reader.Update()

input_mesh: Union[vtkMultiBlockDataSet, vtkDataSet] = reader.GetOutput()
regionName: str = "PORO"
newAttributeName: str = "Test"
dictRegion: dict[Any, Any] = {}
valueType: int = 11
use_color = True

    # instantiate the filter
filter: CreateConstantAttributePerRegion = CreateConstantAttributePerRegion( regionName,
                                                                             newAttributeName,
                                                                             dictRegion,
                                                                             valueType,
                                                                             use_color, )
ch = logging.StreamHandler()
ch.setFormatter( CustomLoggerFormatter( use_color ) )
filter.setLoggerHandler( ch )
    # Set the mesh
filter.SetInputDataObject( input_mesh )
    # Do calculations
filter.Update()

    # get output object
output: Union[vtkMultiBlockDataSet, vtkDataSet] = filter.GetOutputDataObject( 0 )