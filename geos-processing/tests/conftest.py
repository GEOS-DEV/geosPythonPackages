# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Paloma Martinez, Romain Baville
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from pathlib import Path
from typing import Any

from vtkmodules.vtkCommonDataModel import vtkDataSet, vtkMultiBlockDataSet, vtkPolyData
from vtkmodules.vtkIOXML import vtkXMLGenericDataObjectReader


@pytest.fixture
def dataSetTest() -> Any:
    """Get a vtkObject from a file with the function _get_dataset().

    Returns:
        (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
    """

    def _get_dataset( datasetType: str ) -> vtkMultiBlockDataSet | vtkPolyData | vtkDataSet:
        """Get a vtkObject from a file.

        Args:
            datasetType (str): The type of vtk object wanted.

        Returns:
            (vtkMultiBlockDataSet, vtkPolyData, vtkDataSet): The vtk object.
        """
        reader: vtkXMLGenericDataObjectReader = vtkXMLGenericDataObjectReader()
        # Meshes from the GEOS integrated test singlePhasePoromechanics_FaultModel_well_seq from geos-mesh
        if datasetType == "2Ranks":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/cellElementRegion2Ranks.vtm"
        elif datasetType == "4Ranks":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/cellElementRegion4Ranks.vtm"
        elif datasetType == "geosOutput2Ranks":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/geosOutput2Ranks.vtm"
        elif datasetType == "extractAndMergeVolume":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeVolume.vtu"
        elif datasetType == "extractAndMergeFault":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFault.vtu"
        elif datasetType == "extractAndMergeFaultVtp":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFault.vtp"
        elif datasetType == "extractAndMergeWell1":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeWell1.vtu"
        elif datasetType == "extractAndMergeVolumeWell1":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeVolumeWell1.vtm"
        elif datasetType == "extractAndMergeFaultWell1":
            vtkFilename = "geos-mesh/tests/data/singlePhasePoromechanics_FaultModel_well_seq/extractAndMergeFaultWell1.vtm"
        # Small useful meshes
        elif datasetType == "quads2_tris4":
            vtkFilename = "geos-processing/tests/data/quads2_tris4.vtu"
        elif datasetType == "hexs3_tets36_pyrs18":
            vtkFilename = "geos-processing/tests/data/hexs3_tets36_pyrs18.vtu"
        elif datasetType == "meshtet1":
            vtkFilename = "geos-processing/tests/data/mesh1.vtu"
        elif datasetType == "meshtet1b":
            vtkFilename = "geos-processing/tests/data/mesh1b.vtu"

        datapath: str = str( Path( __file__ ).parent.parent.parent / vtkFilename )
        reader.SetFileName( datapath )
        reader.Update()

        return reader.GetOutput()

    return _get_dataset
