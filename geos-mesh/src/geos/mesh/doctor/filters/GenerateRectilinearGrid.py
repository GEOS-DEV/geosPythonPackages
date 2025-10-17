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

To use the filter
-----------------

.. code-block:: python

    from filters.GenerateRectilinearGrid import GenerateRectilinearGrid

    # instantiate the filter
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

    # execute the filter
    success = elementVolumesFilter.applyFilter()

    # get the generated mesh
    outputMesh = generateRectilinearGridFilter.getGrid()

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from filters.GenerateRectilinearGrid import generateRectilinearGrid, FieldInfo

    # generate grid directly
    outputMesh = generateRectilinearGrid(
        coordsX=[0.0, 5.0, 10.0],
        coordsY=[0.0, 5.0, 10.0],
        coordsZ=[0.0, 10.0],
        numberElementsX=[5, 5],
        numberElementsY=[5, 5],
        numberElementsZ=[10],
        outputPath="output/rectilinear_grid.vtu",
        fields=[FieldInfo("cell1", 1, "CELLS")],
        generateCellsGlobalIds=True,
        generatePointsGlobalIds=True
    )
"""

loggerTitle: str = "Generate Rectilinear Grid"


class GenerateRectilinearGrid( MeshDoctorGeneratorBase ):

    def __init__(
        self: Self,
        generateCellsGlobalIds: bool = False,
        generatePointsGlobalIds: bool = False,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the rectilinear grid generator.

        Args:
            generateCellsGlobalIds (bool): Whether to generate global cell IDs. Defaults to False.
            generatePointsGlobalIds (bool): Whether to generate global point IDs. Defaults to False.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( loggerTitle, useExternalLogger )
        self.generateCellsGlobalIds: bool = generateCellsGlobalIds
        self.generatePointsGlobalIds: bool = generatePointsGlobalIds
        self.coordsX: Sequence[ float ] = None
        self.coordsY: Sequence[ float ] = None
        self.coordsZ: Sequence[ float ] = None
        self.numberElementsX: Sequence[ int ] = None
        self.numberElementsY: Sequence[ int ] = None
        self.numberElementsZ: Sequence[ int ] = None
        self.number_elements_z: Sequence[ int ] = None
        self.fields: Iterable[ FieldInfo ] = list()

    def applyFilter( self: Self ) -> bool:
        """Generate the rectilinear grid.

        Returns:
            bool: True if grid generated successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Validate inputs
            required_fields = [
                self.coordsX, self.coordsY, self.coordsZ, self.numberElementsX, self.numberElementsY,
                self.numberElementsZ
            ]
            if any( field is None for field in required_fields ):
                self.logger.error( "Coordinates and number of elements must be set before generating grid." )
                return False

            # Build coordinates
            x: npt.NDArray = build_coordinates( self.coordsX, self.numberElementsX )
            y: npt.NDArray = build_coordinates( self.coordsY, self.numberElementsY )
            z: npt.NDArray = build_coordinates( self.coordsZ, self.numberElementsZ )

            # Build the rectilinear grid
            self.mesh = build_rectilinear_grid( x, y, z )

            # Add fields if specified
            if self.fields:
                self.mesh = add_fields( self.mesh, self.fields )

            # Add global IDs if requested
            build_global_ids( self.mesh, self.generateCellsGlobalIds, self.generatePointsGlobalIds )

            self.logger.info( f"Generated rectilinear grid with {self.mesh.GetNumberOfPoints()} points "
                              f"and {self.mesh.GetNumberOfCells()} cells." )
            self.logger.info( f"The filter {self.logger.name} succeeded." )
            return True

        except Exception as e:
            self.logger.error( f"Error in rectilinear grid generation: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed." )
            return False

    def setCoordinates(
        self: Self,
        coordsX: Sequence[ float ],
        coordsY: Sequence[ float ],
        coordsZ: Sequence[ float ],
    ) -> None:
        """Set the coordinates of the block boundaries for the grid along X, Y and Z axis.

        Args:
            coordsX (Sequence[float]): Block boundary coordinates along X axis.
            coordsY (Sequence[float]): Block boundary coordinates along Y axis.
            coordsZ (Sequence[float]): Block boundary coordinates along Z axis.
        """
        self.coordsX = coordsX
        self.coordsY = coordsY
        self.coordsZ = coordsZ

    def setFields( self: Self, fields: Iterable[ FieldInfo ] ) -> None:
        """Set the fields (arrays) to be added to the grid.

        Args:
            fields (Iterable[FieldInfo]): Field information for arrays to create.
        """
        self.fields = fields

    def setGenerateCellsGlobalIds( self: Self, generate: bool ) -> None:
        """Set whether to generate global cell IDs.

        Args:
            generate (bool): True to generate global cell IDs, False otherwise.
        """
        self.generateCellsGlobalIds = generate

    def setGeneratePointsGlobalIds( self: Self, generate: bool ) -> None:
        """Set whether to generate global point IDs.

        Args:
            generate (bool): True to generate global point IDs, False otherwise.
        """
        self.generatePointsGlobalIds = generate

    def setNumberElements(
        self: Self,
        numberElementsX: Sequence[ int ],
        numberElementsY: Sequence[ int ],
        numberElementsZ: Sequence[ int ],
    ) -> None:
        """Set the number of elements for each block along X, Y and Z axis.

        Args:
            numberElementsX (Sequence[int]): Number of elements per block along X axis.
            numberElementsY (Sequence[int]): Number of elements per block along Y axis.
            numberElementsZ (Sequence[int]): Number of elements per block along Z axis.
        """
        self.numberElementsX = numberElementsX
        self.numberElementsY = numberElementsY
        self.numberElementsZ = numberElementsZ


# Main function for standalone use
def generateRectilinearGrid(
    coordsX: Sequence[ float ],
    coordsY: Sequence[ float ],
    coordsZ: Sequence[ float ],
    numberElementsX: Sequence[ int ],
    numberElementsY: Sequence[ int ],
    numberElementsZ: Sequence[ int ],
    outputPath: str,
    fields: Iterable[ FieldInfo ] = None,
    generateCellsGlobalIds: bool = False,
    generatePointsGlobalIds: bool = False,
) -> vtkUnstructuredGrid:
    """Generate a rectilinear grid mesh.

    Args:
        coordsX (Sequence[float]): Block boundary coordinates along X axis.
        coordsY (Sequence[float]): Block boundary coordinates along Y axis.
        coordsZ (Sequence[float]): Block boundary coordinates along Z axis.
        numberElementsX (Sequence[int]): Number of elements per block along X axis.
        numberElementsY (Sequence[int]): Number of elements per block along Y axis.
        numberElementsZ (Sequence[int]): Number of elements per block along Z axis.
        outputPath (str): Output file path if write_output is True.
        fields (Iterable[FieldInfo]): Field information for arrays to create. Defaults to None.
        generateCellsGlobalIds (bool): Whether to generate global cell IDs. Defaults to False.
        generatePointsGlobalIds (bool): Whether to generate global point IDs. Defaults to False.

    Returns:
        vtkUnstructuredGrid: The generated mesh.
    """
    filterInstance = GenerateRectilinearGrid( generateCellsGlobalIds, generatePointsGlobalIds )
    filterInstance.setCoordinates( coordsX, coordsY, coordsZ )
    filterInstance.setNumberElements( numberElementsX, numberElementsY, numberElementsZ )

    if fields:
        filterInstance.setFields( fields )

    success = filterInstance.applyFilter()
    if not success:
        raise RuntimeError( "Rectilinear grid generation failed." )

    filterInstance.writeGrid( outputPath )

    return filterInstance.getMesh()
