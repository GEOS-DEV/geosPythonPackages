# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Jacques Franc
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
from typing import Union, Any
from vtkmodules.numpy_interface import dataset_adapter as dsa
from collections import Counter
import numpy as np

from geos.processing.generic_processing_tools.MeshToMeshInterpolator import MeshToMeshInterpolator
from vtkmodules.vtkCommonDataModel import vtkDataSet
from vtkmodules.util.numpy_support import vtk_to_numpy


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames", [
    ( "rank0", "extractAndMergeVolume", { "elementVolume" } ),
] )
def test_MeshToMeshInterpolator( dataSetTest: Any, meshFromName: str, meshToName: str,
                                 attributeNames: set[ str ] ) -> None:
    """Test MeshToMeshInterpolator basic."""
    meshFrom: Union[
        vtkDataSet,
    ] = dataSetTest( meshFromName )
    meshTo: Union[
        vtkDataSet,
    ] = dataSetTest( meshToName )

    meshToMeshInterpolator = MeshToMeshInterpolator( meshFrom, meshTo, attributeNames )
    meshToMeshInterpolator.applyFilter()

    for attrib in attributeNames:
        a0 = vtk_to_numpy( meshFrom.GetCellData().GetArray( attrib ) )
        a1 = vtk_to_numpy( meshTo.GetCellData().GetArray( f"mapped{attrib.capitalize()}" ) )
        assert np.linalg.norm( a0 ) == pytest.approx( np.linalg.norm( a1 ), rel=1e-2, abs=0 )


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames,attributeRegionsName,regionIds", [
    ( "rank0WithAttr", "mergeVolumeWithAttr", { "elementVolume" }, "attributes", { 4, 5 } ),
] )
def test_AttributeOnly_MeshToMeshInterpolator( dataSetTest: Any, meshFromName: str, meshToName: str,
                                               attributeNames: set[ str ], attributeRegionsName: str,
                                               regionIds: set[ int ] ) -> None:
    """Test MeshToMeshInterpolator with regions."""
    meshFrom: Union[
        vtkDataSet,
    ] = dataSetTest( meshFromName )
    meshTo: Union[
        vtkDataSet,
    ] = dataSetTest( meshToName )

    meshToMeshInterpolator = MeshToMeshInterpolator( meshFrom, meshTo, attributeNames )
    meshToMeshInterpolator.setCellRegionsIds( attributeRegionsName, regionIds )
    meshToMeshInterpolator.applyFilter()

    for attrib in attributeNames:
        a0 = vtk_to_numpy( meshFrom.GetCellData().GetArray( attrib ) )
        a1 = vtk_to_numpy( meshTo.GetCellData().GetArray( f"mapped{attrib.capitalize()}" ) )
        mask = np.zeros( meshFrom.GetNumberOfCells(), dtype=bool )
        attr = vtk_to_numpy( meshFrom.GetCellData().GetArray( attributeRegionsName ) ).astype( np.int64 )
        for rid in regionIds:
            mask |= ( attr == rid )
        assert np.linalg.norm( a0[ mask ] ) == pytest.approx( np.linalg.norm( a1 ), rel=1e-2, abs=0 )


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames", [
    ( "extractAndMergeFault", "extractAndMergeVolume", { "Texture Coordinates" } ),
] )
def test_ExpectedFailure_MeshToMeshInterpolator( dataSetTest: Any, meshFromName: str, meshToName: str,
                                                 attributeNames: set[ str ] ) -> None:
    """Test rejection of surfacic meshes as input."""
    meshFrom: Union[
        vtkDataSet,
    ] = dataSetTest( meshFromName )
    meshTo: Union[
        vtkDataSet,
    ] = dataSetTest( meshToName )

    with pytest.raises( NotImplementedError ):
        MeshToMeshInterpolator( meshFrom, meshTo, attributeNames )


@pytest.mark.parametrize( "meshFromName, meshToName, attributeNames", [
    ( "hasFault", "hasFault", { "elementVolume" } ),
] )
def test_ExtractNonVol_MeshToMeshInterpolator( dataSetTest: Any, meshFromName: str, meshToName: str,
                                               attributeNames: set[ str ] ) -> None:
    """Test rejection of surfacic meshes as input."""
    meshFrom: Union[
        vtkDataSet,
    ] = dataSetTest( meshFromName )
    meshTo: Union[
        vtkDataSet,
    ] = dataSetTest( meshToName )

    meshToMeshInterpolator = MeshToMeshInterpolator( meshFrom, meshTo, attributeNames )
    meshToMeshInterpolator.applyFilter()
    output = meshToMeshInterpolator.getOutput()

    counts = {}
    for i, m in enumerate( [ meshTo, output ] ):
        cell_types = dsa.WrapDataObject( m ).GetCellTypes()
        counts[ i ] = Counter( cell_types )

    assert ( counts[ 0 ] == counts[ 1 ] )
