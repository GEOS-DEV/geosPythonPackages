# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
from typing import Optional, Union, cast

import numpy as np
import numpy.typing as npt
import pandas as pd  # type: ignore[import-untyped]
import pyvista as pv  # type: ignore[import-not-found]
import vtkmodules.util.numpy_support as vnp
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import (
    vtkPolyData,
)

import geos_posp.processing.vtkUtils as vtkUtils
from geos.utils.GeosOutputsConstants import GeosDomainNameEnum

__doc__ = r"""
This module contains utilities to process meshes using pyvista.

"""


def loadDataSet(
    reader: pv.PVDReader,
    timeStepIndexes: list[int],
    elevation: float,
    properties: tuple[str],
) -> tuple[dict[str, pd.DataFrame], npt.NDArray[np.float64]]:
    """Load the data using pyvista and extract properties from horizontal slice.

    Args:
        reader (pv.PVDReader): pyvista pvd reader
        timeStepIndexes (list[int]): list of time step indexes to load.
        elevation (float): elevation (m) of horizontal slice
        properties (tuple[str]): list of properties to extract

    Returns:
        tuple[dict[str, pd.DataFrame], npt.NDArray[np.float64]]: tuple containing
            a dictionnary with times as keys and dataframe with properties as
            values, and an array with cell center coordinates of the slice.

    """
    timeToPropertyMap: dict[str, pd.DataFrame] = {}
    surface: vtkPolyData
    timeValues: list[float] = reader.time_values
    for index in timeStepIndexes:
        assert index < len(timeValues), "Time step index is out of range."

        time: float = timeValues[index]
        reader.set_active_time_value(time)
        inputMesh: pv.Multiblock = reader.read()

        volMesh: Optional[Union[pv.MultiBlock, pv.UnstructuredGrid]] = getBlockByName(
            inputMesh, GeosDomainNameEnum.VOLUME_DOMAIN_NAME.value
        )
        assert volMesh is not None, "Volumic mesh was not found."

        # Merge volume block
        mergedMesh: pv.UnstructuredGrid
        if isinstance(volMesh, pv.MultiBlock):
            mergedMesh = volMesh.combine(merge_points=True)
        else:
            mergedMesh = volMesh

        assert mergedMesh is not None, "Merged mesh is undefined."

        # extract data
        surface = vtkUtils.extractSurfaceFromElevation(mergedMesh, elevation)
        # transfer point data to cell center
        surface = cast(vtkPolyData, vtkUtils.transferPointDataToCellData(surface))
        timeToPropertyMap[str(time)] = vtkUtils.getAttributeValuesAsDF(
            surface, properties
        )

    # get cell center coordinates
    assert surface is not None, "Surface are undefined."
    pointsCoords: vtkDataArray = vtkUtils.computeCellCenterCoordinates(surface)
    assert pointsCoords is not None, "Cell center are undefined."
    pointsCoordsNp: npt.NDArray[np.float64] = vnp.vtk_to_numpy(pointsCoords)
    return (timeToPropertyMap, pointsCoordsNp)


def getBlockByName(
    multiBlockMesh: Union[pv.MultiBlock, pv.UnstructuredGrid], blockName: str
) -> Optional[Union[pv.MultiBlock, pv.UnstructuredGrid]]:
    """Get a block in a multi block mesh from its name.

    Args:
        multiBlockMesh (Union[pv.MultiBlock, pv.UnstructuredGrid]): input mesh
        blockName (str): name of the block

    Returns:
        Optional[Union[pv.MultiBlock, pv.UnstructuredGrid]]: wanted block if it
            was found

    """
    if isinstance(multiBlockMesh, pv.UnstructuredGrid):
        return None

    mesh: Optional[Union[pv.MultiBlock, pv.UnstructuredGrid]]
    for i, mbMesh in enumerate(multiBlockMesh):
        # if one of the block of multiBlockMesh is the volumic mesh,
        # then save the mesh and break
        if multiBlockMesh.get_block_name(i) == blockName:
            mesh = mbMesh
            break
        # else look at its internal mesh(es)
        mesh = getBlockByName(mbMesh, blockName)
        # if mesh is not None, it is the searched one
        if mesh is not None:
            break
    return mesh
