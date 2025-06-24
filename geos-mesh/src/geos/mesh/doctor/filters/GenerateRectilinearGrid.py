import numpy.typing as npt
from typing import Iterable, Sequence
from typing_extensions import Self
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.generate_global_ids import build_global_ids
from geos.mesh.doctor.actions.generate_cube import FieldInfo, add_fields, build_coordinates, build_rectilinear_grid
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

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
    generateRectilinearGridFilter.Update()
    mesh: vtkUnstructuredGrid = generateRectilinearGridFilter.GetOutputDataObject( 0 )

    # solution2, which is a method calling the 2 instructions above
    mesh: vtkUnstructuredGrid = generateRectilinearGridFilter.getRectilinearGrid()

    # finally, you can write the mesh at a specific destination with:
    generateRectilinearGridFilter.writeGrid( "output/filepath/of/your/grid.vtu" )
"""


class GenerateRectilinearGrid( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to generate a simple rectilinear grid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=0, nOutputPorts=1, outputType='vtkUnstructuredGrid' )
        self.m_generateCellsGlobalIds: bool = False
        self.m_generatePointsGlobalIds: bool = False
        self.m_coordsX: Sequence[ float ] = None
        self.m_coordsY: Sequence[ float ] = None
        self.m_coordsZ: Sequence[ float ] = None
        self.m_numberElementsX: Sequence[ int ] = None
        self.m_numberElementsY: Sequence[ int ] = None
        self.m_numberElementsZ: Sequence[ int ] = None
        self.m_fields: Iterable[ FieldInfo ] = list()
        self.m_logger = setup_logger

    def RequestData( self: Self, request: vtkInformation, inInfo: vtkInformationVector,
                     outInfo: vtkInformationVector ) -> int:
        opt = vtkUnstructuredGrid.GetData( outInfo )
        x: npt.NDArray = build_coordinates( self.m_coordsX, self.m_numberElementsX )
        y: npt.NDArray = build_coordinates( self.m_coordsY, self.m_numberElementsY )
        z: npt.NDArray = build_coordinates( self.m_coordsZ, self.m_numberElementsZ )
        output: vtkUnstructuredGrid = build_rectilinear_grid( x, y, z )
        output = add_fields( output, self.m_fields )
        build_global_ids( output, self.m_generateCellsGlobalIds, self.m_generatePointsGlobalIds )
        opt.ShallowCopy( output )
        return 1

    def SetLogger( self: Self, logger ) -> None:
        """Set the logger.

        Args:
            logger
        """
        self.m_logger = logger
        self.Modified()

    def getRectilinearGrid( self: Self ) -> vtkUnstructuredGrid:
        """Returns a rectilinear grid as a vtkUnstructuredGrid.

        Args:
            self (Self)

        Returns:
            vtkUnstructuredGrid
        """
        self.Update()  # triggers RequestData
        return self.GetOutputDataObject( 0 )

    def setCoordinates( self: Self, coordsX: Sequence[ float ], coordsY: Sequence[ float ],
                        coordsZ: Sequence[ float ] ) -> None:
        """Set the coordinates of the block you want to have in your grid by specifying the beginning and ending
        coordinates along the X, Y and Z axis.

        Args:
            self (Self)
            coordsX (Sequence[ float ])
            coordsY (Sequence[ float ])
            coordsZ (Sequence[ float ])
        """
        self.m_coordsX = coordsX
        self.m_coordsY = coordsY
        self.m_coordsZ = coordsZ
        self.Modified()

    def setGenerateCellsGlobalIds( self: Self, generate: bool ) -> None:
        """Set the generation of global cells ids to be True or False.

        Args:
            self (Self)
            generate (bool)
        """
        self.m_generateCellsGlobalIds = generate
        self.Modified()

    def setGeneratePointsGlobalIds( self: Self, generate: bool ) -> None:
        """Set the generation of global points ids to be True or False.

        Args:
            self (Self)
            generate (bool)
        """
        self.m_generatePointsGlobalIds = generate
        self.Modified()

    def setFields( self: Self, fields: Iterable[ FieldInfo ] ) -> None:
        """Specify the cells or points array to be added to the grid.

        Args:
            self (Self)
            fields (Iterable[ FieldInfo ])
        """
        self.m_fields = fields
        self.Modified()

    def setNumberElements( self: Self, numberElementsX: Sequence[ int ], numberElementsY: Sequence[ int ],
                           numberElementsZ: Sequence[ int ] ) -> None:
        """For each block that was defined in setCoordinates, specify the number of cells that they should contain.

        Args:
            self (Self)
            numberElementsX (Sequence[ int ])
            numberElementsY (Sequence[ int ])
            numberElementsZ (Sequence[ int ])
        """
        self.m_numberElementsX = numberElementsX
        self.m_numberElementsY = numberElementsY
        self.m_numberElementsZ = numberElementsZ
        self.Modified()

    def writeGrid( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of your rectilinear grid at the specified filepath.

        Args:
            filepath (str): /path/to/your/file.vtu
            is_data_mode_binary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        mesh: vtkUnstructuredGrid = self.getRectilinearGrid()
        if mesh:
            write_mesh( filepath, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
        else:
            self.m_logger.error( f"No rectilinear grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )
