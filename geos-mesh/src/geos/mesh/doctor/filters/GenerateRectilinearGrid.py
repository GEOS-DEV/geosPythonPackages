import numpy.typing as npt
from typing import Iterable, Sequence
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.generate_global_ids import build_global_ids
from geos.mesh.doctor.actions.generate_cube import FieldInfo, add_fields, build_coordinates, build_rectilinear_grid
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorGeneratorBase

__doc__ = """
GenerateRectilinearGrid module is a vtk filter that allows to create a simple vtkUnstructuredGrid rectilinear grid.
GlobalIds for points and cells can be added.
You can create CellArray and PointArray of constant value = 1 and any dimension >= 1.

No filter input and one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.GenerateRectilinearGrid import GenerateRectilinearGrid

    # instanciate the filter
    generateRectilinearGridFilter: GenerateRectilinearGrid = GenerateRectilinearGrid()

    # set the coordinates of each block border for the X, Y and Z axis
    generateRectilinearGridFilter.setCoordinates( [ 0.0, 5.0, 10.0 ], [ 0.0, 5.0, 10.0 ], [ 0.0, 10.0 ] )

    # for each block defined, specify the number of cells that they should contain in the X, Y, Z axis
    generateRectilinearGridFilter.setNumberElements( [ 5, 5 ], [ 5, 5 ], [ 10 ] )

    # to add the GlobalIds for cells and points, set to True the generate global ids options
    generateRectilinearGridFilter.setGenerateCellsGlobalIds( True )
    generateRectilinearGridFilter.setGeneratePointsGlobalIds( True )

    # to create new arrays with a specific dimension, you can use the following commands
    cells_dim1 = FieldInfo( "cell1", 1, "CELLS" )  # array "cell1" of shape ( number of cells, 1 )
    cells_dim3 = FieldInfo( "cell3", 3, "CELLS" )  # array "cell3" of shape ( number of cells, 3 )
    points_dim1 = FieldInfo( "point1", 1, "POINTS" )  # array "point1" of shape ( number of points, 1 )
    points_dim3 = FieldInfo( "point3", 3, "POINTS" )  # array "point3" of shape ( number of points, 3 )
    generateRectilinearGridFilter.setFields( [ cells_dim1, cells_dim3, points_dim1, points_dim3 ] )

    # then, to obtain the constructed mesh out of all these operations, 2 solutions are available

    # solution1
    mesh: vtkUnstructuredGrid = generateRectilinearGridFilter.getGrid()

    # solution2, which calls the same method as above
    generateRectilinearGridFilter.Update()
    mesh: vtkUnstructuredGrid = generateRectilinearGridFilter.GetOutputDataObject( 0 )

    # finally, you can write the mesh at a specific destination with:
    generateRectilinearGridFilter.writeGrid("output/filepath/of/your/grid.vtu")
"""

loggerTitle: str = "Generate Rectilinear Grid"


class GenerateRectilinearGrid( MeshDoctorGeneratorBase ):

    def __init__(
        self: Self,
        generate_cells_global_ids: bool = False,
        generate_points_global_ids: bool = False,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the rectilinear grid generator.

        Args:
            generate_cells_global_ids (bool): Whether to generate global cell IDs. Defaults to False.
            generate_points_global_ids (bool): Whether to generate global point IDs. Defaults to False.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( loggerTitle, use_external_logger )
        self.generate_cells_global_ids: bool = generate_cells_global_ids
        self.generate_points_global_ids: bool = generate_points_global_ids
        self.coords_x: Sequence[ float ] = None
        self.coords_y: Sequence[ float ] = None
        self.coords_z: Sequence[ float ] = None
        self.number_elements_x: Sequence[ int ] = None
        self.number_elements_y: Sequence[ int ] = None
        self.number_elements_z: Sequence[ int ] = None
        self.fields: Iterable[ FieldInfo ] = list()

    def setCoordinates(
        self: Self,
        coords_x: Sequence[ float ],
        coords_y: Sequence[ float ],
        coords_z: Sequence[ float ],
    ) -> None:
        """Set the coordinates of the block boundaries for the grid along X, Y and Z axis.

        Args:
            coords_x (Sequence[float]): Block boundary coordinates along X axis
            coords_y (Sequence[float]): Block boundary coordinates along Y axis
            coords_z (Sequence[float]): Block boundary coordinates along Z axis
        """
        self.coords_x = coords_x
        self.coords_y = coords_y
        self.coords_z = coords_z

    def setNumberElements(
        self: Self,
        number_elements_x: Sequence[ int ],
        number_elements_y: Sequence[ int ],
        number_elements_z: Sequence[ int ],
    ) -> None:
        """Set the number of elements for each block along X, Y and Z axis.

        Args:
            number_elements_x (Sequence[int]): Number of elements per block along X axis
            number_elements_y (Sequence[int]): Number of elements per block along Y axis
            number_elements_z (Sequence[int]): Number of elements per block along Z axis
        """
        self.number_elements_x = number_elements_x
        self.number_elements_y = number_elements_y
        self.number_elements_z = number_elements_z

    def setGenerateCellsGlobalIds( self: Self, generate: bool ) -> None:
        """Set whether to generate global cell IDs.

        Args:
            generate (bool): True to generate global cell IDs, False otherwise
        """
        self.generate_cells_global_ids = generate

    def setGeneratePointsGlobalIds( self: Self, generate: bool ) -> None:
        """Set whether to generate global point IDs.

        Args:
            generate (bool): True to generate global point IDs, False otherwise
        """
        self.generate_points_global_ids = generate

    def setFields( self: Self, fields: Iterable[ FieldInfo ] ) -> None:
        """Set the fields (arrays) to be added to the grid.

        Args:
            fields (Iterable[FieldInfo]): Field information for arrays to create
        """
        self.fields = fields

    def applyFilter( self: Self ) -> bool:
        """Generate the rectilinear grid.

        Returns:
            bool: True if grid generated successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Validate inputs
            required_fields = [
                self.coords_x, self.coords_y, self.coords_z, self.number_elements_x, self.number_elements_y,
                self.number_elements_z
            ]
            if any( field is None for field in required_fields ):
                self.logger.error( "Coordinates and number of elements must be set before generating grid" )
                return False

            # Build coordinates
            x: npt.NDArray = build_coordinates( self.coords_x, self.number_elements_x )
            y: npt.NDArray = build_coordinates( self.coords_y, self.number_elements_y )
            z: npt.NDArray = build_coordinates( self.coords_z, self.number_elements_z )

            # Build the rectilinear grid
            self.mesh = build_rectilinear_grid( x, y, z )

            # Add fields if specified
            if self.fields:
                self.mesh = add_fields( self.mesh, self.fields )

            # Add global IDs if requested
            build_global_ids( self.mesh, self.generate_cells_global_ids, self.generate_points_global_ids )

            self.logger.info( f"Generated rectilinear grid with {self.mesh.GetNumberOfPoints()} points "
                              f"and {self.mesh.GetNumberOfCells()} cells" )
            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in rectilinear grid generation: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False


# Main function for backward compatibility and standalone use
def generate_rectilinear_grid(
    coords_x: Sequence[ float ],
    coords_y: Sequence[ float ],
    coords_z: Sequence[ float ],
    number_elements_x: Sequence[ int ],
    number_elements_y: Sequence[ int ],
    number_elements_z: Sequence[ int ],
    fields: Iterable[ FieldInfo ] = None,
    generate_cells_global_ids: bool = False,
    generate_points_global_ids: bool = False,
    write_output: bool = False,
    output_path: str = "output/rectilinear_grid.vtu",
) -> vtkUnstructuredGrid:
    """Generate a rectilinear grid mesh.

    Args:
        coords_x (Sequence[float]): Block boundary coordinates along X axis
        coords_y (Sequence[float]): Block boundary coordinates along Y axis
        coords_z (Sequence[float]): Block boundary coordinates along Z axis
        number_elements_x (Sequence[int]): Number of elements per block along X axis
        number_elements_y (Sequence[int]): Number of elements per block along Y axis
        number_elements_z (Sequence[int]): Number of elements per block along Z axis
        fields (Iterable[FieldInfo]): Field information for arrays to create. Defaults to None.
        generate_cells_global_ids (bool): Whether to generate global cell IDs. Defaults to False.
        generate_points_global_ids (bool): Whether to generate global point IDs. Defaults to False.
        write_output (bool): Whether to write output mesh to file. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        vtkUnstructuredGrid: The generated mesh
    """
    filter_instance = GenerateRectilinearGrid( generate_cells_global_ids, generate_points_global_ids )
    filter_instance.setCoordinates( coords_x, coords_y, coords_z )
    filter_instance.setNumberElements( number_elements_x, number_elements_y, number_elements_z )

    if fields:
        filter_instance.setFields( fields )

    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Rectilinear grid generation failed" )

    if write_output:
        filter_instance.writeGrid( output_path )

    return filter_instance.getMesh()
