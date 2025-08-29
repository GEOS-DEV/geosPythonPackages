from dataclasses import dataclass
import uuid
from vtkmodules.vtkCommonCore import vtkDataArray
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
    element_volumes: list[ tuple[ int, float ] ]


SUPPORTED_TYPES = [ VTK_HEXAHEDRON, VTK_TETRA ]


def get_mesh_quality( mesh: vtkUnstructuredGrid ) -> vtkDataArray:
    """Get the quality of the mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.

    Returns:
        vtkDataArray: The array containing the quality of each cell.
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
        setup_logger.warning(
            "Your \"pyvtk\" version does not bring pyramid nor wedge support with vtkMeshQuality. Using the fallback solution."
        )
    mq.SetInputData( mesh )
    mq.Update()

    return mq.GetOutput().GetCellData().GetArray( "Quality" )  # Name is imposed by vtk.


def get_mesh_volume( mesh: vtkUnstructuredGrid ) -> vtkDataArray:
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

    volume_array_name: str = "__MESH_DOCTOR_VOLUME-" + str( uuid.uuid4() )  # Making the name unique
    cs.SetVolumeArrayName( volume_array_name )
    cs.SetInputData( mesh )
    cs.Update()

    return cs.GetOutput().GetCellData().GetArray( volume_array_name )


def mesh_action( mesh: vtkUnstructuredGrid, options: Options ) -> Result:
    volume: vtkDataArray = get_mesh_volume( mesh )
    if not volume:
        setup_logger.error( "Volume computation failed." )
        raise RuntimeError( "Volume computation failed." )

    quality: vtkDataArray = get_mesh_quality( mesh )
    if not quality:
        setup_logger.error( "Quality computation failed." )
        raise RuntimeError( "Quality computation failed." )

    volume = vtk_to_numpy( volume )
    quality = vtk_to_numpy( quality )
    small_volumes: list[ tuple[ int, float ] ] = []
    for i, pack in enumerate( zip( volume, quality ) ):
        v, q = pack
        vol = q if mesh.GetCellType( i ) in SUPPORTED_TYPES else v
        if vol < options.min_volume:
            small_volumes.append( ( i, float( vol ) ) )
    return Result( element_volumes=small_volumes )


def action( vtk_input_file: str, options: Options ) -> Result:
    mesh: vtkUnstructuredGrid = read_unstructured_grid( vtk_input_file )
    return mesh_action( mesh, options )
