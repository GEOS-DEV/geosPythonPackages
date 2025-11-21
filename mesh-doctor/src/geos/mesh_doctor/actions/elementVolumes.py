# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Thomas Gazolla, Alexandre Benedicto
from dataclasses import dataclass
import uuid
import numpy as np
from numpy.typing import NDArray
from vtkmodules.vtkCommonCore import vtkDoubleArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_HEXAHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_WEDGE
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter, vtkMeshQuality
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import readUnstructuredGrid


@dataclass( frozen=True )
class Options:
    minVolume: float


@dataclass( frozen=True )
class Result:
    elementVolumes: list[ tuple[ int, float ] ]


SUPPORTED_TYPES = [ VTK_HEXAHEDRON, VTK_TETRA ]


def getMeshQuality( mesh: vtkUnstructuredGrid ) -> vtkDoubleArray:
    """Get the quality of the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.

    Returns:
        vtkDoubleArray: The array containing the quality of each cell.
    """
    mq = vtkMeshQuality()
    mq.SetTetQualityMeasureToVolume()
    mq.SetHexQualityMeasureToVolume()
    if hasattr( mq, "SetPyramidQualityMeasureToVolume" ):  # This feature is quite recent
        mq.SetPyramidQualityMeasureToVolume()
        SUPPORTED_TYPES.append( VTK_PYRAMID )
        mq.SetWedgeQualityMeasureToVolume()
        SUPPORTED_TYPES.append( VTK_WEDGE )
    else:
        setupLogger.warning( "Your \"pyvtk\" version does not bring pyramid nor wedge support with vtkMeshQuality."
                             " Using the fallback solution." )
    mq.SetInputData( mesh )
    mq.Update()

    return mq.GetOutput().GetCellData().GetArray( "Quality" )  # Name is imposed by vtk.


def getMeshVolume( mesh: vtkUnstructuredGrid ) -> vtkDoubleArray:
    """Get the volume of the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.

    Returns:
        vtkDataArray: The array containing the volume of each cell.
    """
    cs = vtkCellSizeFilter()
    cs.ComputeAreaOff()
    cs.ComputeLengthOff()
    cs.ComputeSumOff()
    cs.ComputeVertexCountOff()
    cs.ComputeVolumeOn()

    volumeArrayName: str = "__MESH_DOCTOR_VOLUME-" + str( uuid.uuid4() )  # Making the name unique
    cs.SetVolumeArrayName( volumeArrayName )
    cs.SetInputData( mesh )
    cs.Update()

    return cs.GetOutput().GetCellData().GetArray( volumeArrayName )


def meshAction( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    """Performs the supported elements check on a vtkUnstructuredGrid.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        options (Options): The options for processing.

    Returns:
        Result: The result of the supported elements check.
    """
    volume: vtkDoubleArray = getMeshVolume( mesh )
    if not volume:
        setupLogger.error( "Volume computation failed." )
        raise RuntimeError( "Volume computation failed." )

    quality: vtkDoubleArray = getMeshQuality( mesh )
    if not quality:
        setupLogger.error( "Quality computation failed." )
        raise RuntimeError( "Quality computation failed." )

    volumeArray: NDArray[ np.floating ] = vtk_to_numpy( volume )
    qualityArray: NDArray[ np.floating ] = vtk_to_numpy( quality )
    smallVolumes: list[ tuple[ int, float ] ] = []
    for i, pack in enumerate( zip( volumeArray, qualityArray ) ):
        v, q = pack
        vol = q if mesh.GetCellType( i ) in SUPPORTED_TYPES else v
        if vol < options.minVolume:
            smallVolumes.append( ( i, float( vol ) ) )
    return Result( elementVolumes=smallVolumes )


def action( vtuInputFile: str, options: Options ) -> Result:
    """Reads a vtu file and performs the element volumes check on it.

    Args:
        vtuInputFile (str): The path to the input VTU file.
        options (Options): The options for processing.

    Returns:
        Result: The result of the element volumes check.
    """
    mesh: vtkUnstructuredGrid = readUnstructuredGrid( vtuInputFile )
    return meshAction( mesh, options )
