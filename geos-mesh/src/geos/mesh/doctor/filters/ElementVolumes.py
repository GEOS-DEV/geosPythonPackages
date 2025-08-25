import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from vtkmodules.vtkFiltersVerdict import vtkCellSizeFilter
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase

__doc__ = """
ElementVolumes module calculates the volumes of all elements in a vtkUnstructuredGrid.
The filter can identify elements with negative or zero volumes, which typically indicate mesh quality issues
such as inverted elements or degenerate cells.

To use the filter:

.. code-block:: python

    from geos.mesh.doctor.filters.ElementVolumes import ElementVolumes

    # instantiate the filter
    elementVolumesFilter = ElementVolumes(mesh, return_negative_zero_volumes=True)

    # execute the filter
    success = elementVolumesFilter.applyFilter()

    # get problematic elements (if enabled)
    negative_zero_volumes = elementVolumesFilter.getNegativeZeroVolumes()
    # returns numpy array with shape (n, 2) where first column is element index, second is volume

    # get the processed mesh with volume information
    output_mesh = elementVolumesFilter.getMesh()

    # write the output mesh with volume information
    elementVolumesFilter.writeGrid("output/mesh_with_volumes.vtu")
"""

loggerTitle: str = "Element Volumes Filter"


class ElementVolumes( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        return_negative_zero_volumes: bool = False,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the element volumes filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to analyze
            return_negative_zero_volumes (bool): Whether to report negative/zero volume elements. Defaults to False.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.return_negative_zero_volumes: bool = return_negative_zero_volumes
        self.volumes: vtkDataArray = None

    def setReturnNegativeZeroVolumes( self: Self, return_negative_zero_volumes: bool ) -> None:
        """Set whether to report negative and zero volume elements.

        Args:
            return_negative_zero_volumes (bool): True to enable reporting, False to disable
        """
        self.return_negative_zero_volumes = return_negative_zero_volumes

    def applyFilter( self: Self ) -> bool:
        """Apply the element volumes calculation.

        Returns:
            bool: True if calculation completed successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Use VTK's cell size filter to compute volumes
            cellSize = vtkCellSizeFilter()
            cellSize.ComputeAreaOff()
            cellSize.ComputeLengthOff()
            cellSize.ComputeSumOff()
            cellSize.ComputeVertexCountOff()
            cellSize.ComputeVolumeOn()

            volume_array_name: str = "MESH_DOCTOR_VOLUME"
            cellSize.SetVolumeArrayName( volume_array_name )
            cellSize.SetInputData( self.mesh )
            cellSize.Update()

            # Get the computed volumes
            self.volumes = cellSize.GetOutput().GetCellData().GetArray( volume_array_name )

            # Add the volume array to our mesh
            self.mesh.GetCellData().AddArray( self.volumes )

            if self.return_negative_zero_volumes:
                negative_zero_volumes = self.getNegativeZeroVolumes()
                self.logger.info( f"Found {len(negative_zero_volumes)} elements with zero or negative volume" )
                if len( negative_zero_volumes ) > 0:
                    self.logger.info( "Element indices and volumes with zero or negative values:" )
                    for idx, vol in negative_zero_volumes:
                        self.logger.info( f"  Element {idx}: volume = {vol}" )

            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in element volumes calculation: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def getNegativeZeroVolumes( self: Self ) -> npt.NDArray:
        """Returns a numpy array of all the negative and zero volumes.

        Returns:
            npt.NDArray: Array with shape (n, 2) where first column is element index, second is volume
        """
        if self.volumes is None:
            return np.array( [] ).reshape( 0, 2 )

        volumes_np: npt.NDArray = vtk_to_numpy( self.volumes )
        indices = np.where( volumes_np <= 0 )[ 0 ]
        return np.column_stack( ( indices, volumes_np[ indices ] ) )

    def getVolumes( self: Self ) -> vtkDataArray:
        """Get the computed volume array.

        Returns:
            vtkDataArray: The volume data array, or None if not computed yet
        """
        return self.volumes


# Main function for backward compatibility and standalone use
def element_volumes(
    mesh: vtkUnstructuredGrid,
    return_negative_zero_volumes: bool = False,
    write_output: bool = False,
    output_path: str = "output/mesh_with_volumes.vtu",
) -> tuple[ vtkUnstructuredGrid, npt.NDArray ]:
    """Apply element volumes calculation to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        return_negative_zero_volumes (bool): Whether to report negative/zero volume elements. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, npt.NDArray]:
            Processed mesh, array of negative/zero volume elements
    """
    filter_instance = ElementVolumes( mesh, return_negative_zero_volumes )
    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Element volumes calculation failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return (
        filter_instance.getMesh(),
        filter_instance.getNegativeZeroVolumes(),
    )


# Alias for backward compatibility
def processElementVolumes(
    mesh: vtkUnstructuredGrid,
    return_negative_zero_volumes: bool = False,
) -> tuple[ vtkUnstructuredGrid, npt.NDArray ]:
    """Legacy function name for backward compatibility."""
    return element_volumes( mesh, return_negative_zero_volumes )
