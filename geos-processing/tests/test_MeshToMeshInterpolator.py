# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Union, Any
import numpy as np

import sys
sys.path.insert(0,"/data/pau901/SIM_CS/users/jfranc/geosPythonPackages/geos-processing")

from geos.processing.generic_processing_tools.MeshToMeshInterpolator import MeshToMeshInterpolator
from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkIOXML import vtkXMLUnstructuredGridWriter
from geos.utils.pieceEnum import Piece

@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames", [
    ( "rank0", "extractAndMergeVolume", { "elementVolume" } ),]) 
def test_MeshToMeshInterpolator(
        dataSetTest: Any,
        meshFromName: str,
        meshToName: str,
        attributeNames: set[str]
):
    meshFrom: Union[ vtkDataSet,] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet,] = dataSetTest( meshToName )

    meshToMeshInterpolator = MeshToMeshInterpolator(meshFrom, meshTo, attributeNames )
    meshToMeshInterpolator.applyFilter()

    for attrib in attributeNames:
        a0 = vtk_to_numpy(meshFrom.GetCellData().GetArray(attrib))
        a1 = vtk_to_numpy(meshTo.GetCellData().GetArray(f"mapped_{attrib}"))
        assert np.linalg.norm(a0) == pytest.approx(np.linalg.norm(a1), rel=1e-2, abs=0)

    # output = meshToMeshInterpolator.getOutput()
    # w = vtkXMLUnstructuredGridWriter()
    # w.SetFileName(f"/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/tmp/test_crumbs/test.vtu")
    # w.SetInputData(output)
    # w.Update()
    # w.Write()

@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames,attributeRegionsName,regionIds", [
    ( "rank0WithAttr", "extractAndMergeVolume", { "elementVolume" }, "attributes", {4,5} ), ] )
def test_AttributeOnly_MeshToMeshInterpolator(
        dataSetTest: Any,
        meshFromName: str,
        meshToName: str,
        attributeNames: set[str],
        attributeRegionsName : str,
        regionIds : set[int] ):
    meshFrom: Union[ vtkDataSet,] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet,] = dataSetTest( meshToName )

    meshToMeshInterpolator = MeshToMeshInterpolator(meshFrom, meshTo, attributeNames )
    meshToMeshInterpolator.setCellRegionsIds(attributeRegionsName,regionIds)
    meshToMeshInterpolator.applyFilter()

    for attrib in attributeNames:
        a0 = vtk_to_numpy(meshFrom.GetCellData().GetArray(attrib))
        a1 = vtk_to_numpy(meshTo.GetCellData().GetArray(f"mapped_{attrib}"))
        mask   = np.zeros(meshFrom.GetNumberOfCells(), dtype=bool)
        attr   = vtk_to_numpy(meshFrom.GetCellData().GetArray(attributeRegionsName)).astype(np.int64)
        for rid in regionIds:
            mask |= (attr == rid)
        assert np.linalg.norm(a0[mask]) == pytest.approx(np.linalg.norm(a1), rel=1e-2, abs=0)

    # output = meshToMeshInterpolator.getOutput()
    # w = vtkXMLUnstructuredGridWriter()
    # w.SetFileName(f"/data/pau901/SIM_CS/04_WORKSPACE/USERS/jfranc/tmp/test_crumbs/testAttr.vtu")
    # w.SetInputData(output)
    # w.Update()
    # w.Write()

@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames", [
    ( "extractAndMergeFault", "extractAndMergeVolume", { "Texture Coordinates" } ), ] )
def test_ExpectedFailure_MeshToMeshInterpolator(
        dataSetTest: Any,
        meshFromName: str,
        meshToName: str,
        attributeNames: set[str]
):
    meshFrom: Union[ vtkDataSet,] = dataSetTest( meshFromName )
    meshTo: Union[ vtkDataSet,] = dataSetTest( meshToName )

    with pytest.raises(NotImplementedError):
        meshToMeshInterpolator = MeshToMeshInterpolator(meshFrom,meshTo, attributeNames )

