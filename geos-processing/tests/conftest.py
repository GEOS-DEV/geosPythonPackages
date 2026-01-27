# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import pytest
from typing import Union, Any

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLGenericDataObjectReader


@pytest.fixture
def dataSetTest() -> Any:
    """Get a vtkObject from a file with the function _get_dataset().

    Returns:
        (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
    """

    def _get_dataset( datasetType: str ) -> Union[ vtkMultiBlockDataSet, vtkPolyData, vtkDataSet ]:
        """Get a vtkObject from a file.

        Args:
            datasetType (str): The type of vtk object wanted.

        Returns:
            (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
        """
        reader: vtkXMLGenericDataObjectReader = vtkXMLGenericDataObjectReader()
        if datasetType == "multiblock":
            vtkFilename = "data/displacedFault.vtm"
        elif datasetType == "emptymultiblock":
            vtkFilename = "data/displacedFaultempty.vtm"
        elif datasetType == "multiblockGeosOutput":
            # adapted from example GEOS/inputFiles/compositionalMultiphaseWell/simpleCo2InjTutorial_smoke.xml
            vtkFilename = "data/simpleReservoirViz_small_000478.vtm"
        elif datasetType == "fracture":
            vtkFilename = "data/fracture_res5_id.vtu"
        elif datasetType == "emptyFracture":
            vtkFilename = "data/fracture_res5_id_empty.vtu"
        elif datasetType == "dataset":
            vtkFilename = "data/domain_res5_id.vtu"
        elif datasetType == "emptydataset":
            vtkFilename = "data/domain_res5_id_empty.vtu"
        elif datasetType == "meshGeosExtractBlockTmp":
            vtkFilename = "data/meshGeosExtractBlockTmp.vtm"
        elif datasetType == "singlePhasePoromechanicsVTKOutput":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/singlePhasePoromechanicsVTKOutput.vtm"
        elif datasetType == "extractAndMergeVolume":
            vtkFilename = "data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeVolume.vtu"

        datapath: str = os.path.join( os.path.dirname( os.path.realpath( __file__ ) ), vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset
