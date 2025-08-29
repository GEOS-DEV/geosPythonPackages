import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.element_volumes import get_mesh_quality, get_mesh_volume, SUPPORTED_TYPES
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.element_volumes_parsing import logger_results

__doc__ = """
ElementVolumes module calculates the volumes of all elements in a vtkUnstructuredGrid.
The filter can identify elements with volume inferior to a specified threshold (usually 0.0), which typically indicate
mesh quality issues such as inverted elements or degenerate cells.

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.ElementVolumes import ElementVolumes

    # instantiate the filter
    elementVolumesFilter = ElementVolumes(mesh, minVolume=0.0, writeIsBelowVolume=True)

    # execute the filter
    success = elementVolumesFilter.applyFilter()

    # get problematic elements
    invalidVolumes = elementVolumesFilter.getInvalidVolumes()
    # returns the list of tuples (element index, volume)

    # get the processed mesh with volume information
    outputMesh = elementVolumesFilter.getMesh()

    # write the output mesh with volume information
    elementVolumesFilter.writeGrid("output/mesh_with_volumes.vtu")

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.ElementVolumes import elementVolumes

    # apply filter directly
    outputMesh, volumes, belowVolumes = elementVolumes(
        mesh,
        outputPath="output/mesh_with_volumes.vtu",
        minVolume=0.0,
        writeIsBelowVolume=True
    )
"""

loggerTitle: str = "Element Volumes Filter"


class ElementVolumes( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        minVolume: float = 0.0,
        writeIsBelowVolume: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the element volumes filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze.
            minVolume (float): Minimum volume threshold for elements. Defaults to 0.0.
            writeIsBelowVolume (bool): Whether to add new CellData array with values 0 or 1 if below the minimum volume.
                                       Defaults to False.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.minVolume: float = minVolume
        self.volumes: vtkDataArray = None
        self.belowVolumes: list[ tuple[ int, float ] ] = []
        self.writeIsBelowVolume: bool = writeIsBelowVolume

    def applyFilter( self: Self ) -> bool:
        """Apply the element volumes calculation.

        Returns:
            bool: True if calculation completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        volume: vtkDataArray = get_mesh_volume( self.mesh )
        if not volume:
            self.logger.error( "Volume computation failed." )
            return False

        quality: vtkDataArray = get_mesh_quality( self.mesh )
        if not quality:
            self.logger.error( "Quality computation failed." )
            return False

        volume = vtk_to_numpy( volume )
        quality = vtk_to_numpy( quality )
        self.belowVolumes = []
        for i, pack in enumerate( zip( volume, quality ) ):
            v, q = pack
            vol = q if self.mesh.GetCellType( i ) in SUPPORTED_TYPES else v
            if vol < self.minVolume:
                self.belowVolumes.append( ( i, float( vol ) ) )

        logger_results( self.logger, self.belowVolumes )

        if self.writeIsBelowVolume and self.belowVolumes:
            self._addBelowVolumeArray()

        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getBelowVolumes( self: Self ) -> list[ tuple[ int, float ] ]:
        """Get the list of volumes below the minimum threshold.

        Returns:
            list[ tuple[ int, float ] ]: List of tuples containing element index and volume.
        """
        return self.belowVolumes

    def getVolumes( self: Self ) -> vtkDataArray:
        """Get the computed volume array.

        Returns:
            vtkDataArray: The volume data array, or None if not computed yet.
        """
        return self.volumes

    def setWriteIsBelowVolume( self: Self, write: bool ) -> None:
        """Set whether to write elements below the volume threshold.

        Args:
            write (bool): True to enable writing, False to disable.
        """
        self.writeIsBelowVolume = write

    def _addBelowVolumeArray( self: Self ) -> None:
        """Add an array marking elements below the minimum volume threshold on the mesh."""
        self.logger.info( "Adding CellData array marking elements below the minimum volume threshold." )
        numCells = self.mesh.GetNumberOfCells()
        belowVolumeArray = np.zeros( numCells, dtype=np.int32 )
        belowVolumeArray[ [ i for i, _ in self.belowVolumes ] ] = 1

        vtkArray: vtkDataArray = numpy_to_vtk( belowVolumeArray )
        vtkArray.SetName( "BelowVolumeThresholdOf" + str( self.minVolume ) )
        self.mesh.GetCellData().AddArray( vtkArray )


# Main function for standalone use
def elementVolumes(
    mesh: vtkUnstructuredGrid,
    outputPath: str,
    minVolume: float = 0.0,
    writeIsBelowVolume: bool = False,
) -> tuple[ vtkUnstructuredGrid, npt.NDArray, list[ tuple[ int, float ] ] ]:
    """Apply element volumes calculation to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh to analyze.
        minVolume (float): Minimum volume threshold for elements. Defaults to 0.0.
        writeIsBelowVolume (bool): Whether to write elements below the volume threshold. Defaults to False.
        writeOutput (bool): Whether to write output mesh to file. Defaults to False.
        outputPath (str): Output file path if writeOutput is True.

    Returns:
        tuple[vtkUnstructuredGrid, npt.NDArray, list[ tuple[ int, float ] ]]:
            Processed mesh, array of volumes, list of volumes below the threshold.
    """
    filterInstance = ElementVolumes( mesh, minVolume, writeIsBelowVolume )
    success = filterInstance.applyFilter()

    if not success:
        raise RuntimeError( "Element volumes calculation failed." )

    if writeIsBelowVolume:
        filterInstance.writeGrid( outputPath )

    return (
        filterInstance.getMesh(),
        filterInstance.getVolumes(),
        filterInstance.getBelowVolumes(),
    )
