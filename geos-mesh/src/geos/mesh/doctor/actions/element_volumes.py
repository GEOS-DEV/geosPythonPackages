from dataclasses import dataclass
from typing import List, Tuple
import uuid
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid, VTK_HEXAHEDRON, VTK_PYRAMID, VTK_TETRA, VTK_WEDGE
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter, vtkMeshQuality
from vtkmodules.util.numpy_support import vtk_to_numpy
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import read_unstructured_grid


@dataclass( frozen=True )
class Options:
    min_volume: float


@dataclass( frozen=True )
class Result:
    element_volumes: List[ Tuple[ int, float ] ]


def mesh_action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    cs = vtkCellSizeFilter()

    cs.ComputeAreaOff()
    cs.ComputeLengthOff()
    cs.ComputeSumOff()
    cs.ComputeVertexCountOff()
    cs.ComputeVolumeOn()
    volume_array_name = "__MESH_DOCTOR_VOLUME-" + str( uuid.uuid4() )  # Making the name unique
    cs.SetVolumeArrayName( volume_array_name )

    cs.SetInputData( mesh )
    cs.Update()

    mq = vtkMeshQuality()
    SUPPORTED_TYPES = [ VTK_HEXAHEDRON, VTK_TETRA ]

    mq.SetTetQualityMeasureToVolume()
    mq.SetHexQualityMeasureToVolume()
    if hasattr( mq, "SetPyramidQualityMeasureToVolume" ):  # This feature is quite recent
        mq.SetPyramidQualityMeasureToVolume()
        SUPPORTED_TYPES.append( VTK_PYRAMID )
        mq.SetWedgeQualityMeasureToVolume()
        SUPPORTED_TYPES.append( VTK_WEDGE )
    else:
        setup_logger.warning(
            "Your \"pyvtk\" version does not bring pyramid nor wedge support with vtkMeshQuality. Using the fallback solution."
        )

    mq.SetInputData( mesh )
    mq.Update()

    volume = cs.GetOutput().GetCellData().GetArray( volume_array_name )
    quality = mq.GetOutput().GetCellData().GetArray( "Quality" )  # Name is imposed by vtk.

    assert volume is not None
    assert quality is not None
    volume = vtk_to_numpy( volume )
    quality = vtk_to_numpy( quality )
    small_volumes: List[ Tuple[ int, float ] ] = []
    for i, pack in enumerate( zip( volume, quality ) ):
        v, q = pack
        vol = q if mesh.GetCellType( i ) in SUPPORTED_TYPES else v
        if vol < options.min_volume:
            small_volumes.append( ( i, float( vol ) ) )
    return Result( element_volumes=small_volumes )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = read_unstructured_grid( vtk_input_file )
    return mesh_action( mesh, options )
