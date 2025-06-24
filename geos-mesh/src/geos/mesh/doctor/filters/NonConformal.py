import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.util.numpy_support import numpy_to_vtk
from vtkmodules.util.vtkAlgorithm import VTKPythonAlgorithmBase
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector, vtkDataArray
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.non_conformal import Options, find_non_conformal_cells
from geos.mesh.doctor.parsing.cli_parsing import setup_logger
from geos.mesh.io.vtkIO import VtkOutput, write_mesh

__doc__ = """
NonConformal module is a vtk filter that ... of a vtkUnstructuredGrid.

One filter input is vtkUnstructuredGrid, one filter output which is vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.NonConformal import NonConformal

    # instanciate the filter
    nonConformalFilter: NonConformal = NonConformal()

"""


class NonConformal( VTKPythonAlgorithmBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to ... of a vtkUnstructuredGrid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1, nOutputPorts=1, inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_angle_tolerance: float = 10.0
        self.m_face_tolerance: float = 0.0
        self.m_point_tolerance: float = 0.0
        self.m_non_conformal_cells: list[ tuple[ int, int ] ] = list()
        self.m_paintNonConformalCells: int = 0
        self.m_logger = setup_logger

    def FillInputPortInformation( self: Self, port: int, info: vtkInformation ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            port (int): input port
            info (vtkInformationVector): info

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        if port == 0:
            info.Set( self.INPUT_REQUIRED_DATA_TYPE(), "vtkUnstructuredGrid" )
        return 1

    def RequestInformation(
        self: Self,
        request: vtkInformation,  # noqa: F841
        inInfoVec: list[ vtkInformationVector ],  # noqa: F841
        outInfoVec: vtkInformationVector,
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestInformation.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        executive = self.GetExecutive()  # noqa: F841
        outInfo = outInfoVec.GetInformationObject( 0 )  # noqa: F841
        return 1

    def RequestData(
        self: Self,
        request: vtkInformation,
        inInfoVec: list[ vtkInformationVector ],
        outInfo: vtkInformationVector
    ) -> int:
        """Inherited from VTKPythonAlgorithmBase::RequestData.

        Args:
            request (vtkInformation): request
            inInfoVec (list[vtkInformationVector]): input objects
            outInfoVec (vtkInformationVector): output objects

        Returns:
            int: 1 if calculation successfully ended, 0 otherwise.
        """
        input_mesh: vtkUnstructuredGrid = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
        output = vtkUnstructuredGrid.GetData( outInfo )

        options = Options( self.m_angle_tolerance, self.m_point_tolerance, self.m_face_tolerance )
        non_conformal_cells = find_non_conformal_cells( input_mesh, options )
        self.m_non_conformal_cells = non_conformal_cells

        non_conformal_cells_extended = [ cell_id for pair in non_conformal_cells for cell_id in pair ]
        unique_non_conformal_cells = frozenset( non_conformal_cells_extended )
        self.m_logger.info( f"You have {len( unique_non_conformal_cells )} non conformal cells.\n" +
                            f"{', '.join( map( str, sorted( non_conformal_cells_extended ) ) )}" )

        output_mesh: vtkUnstructuredGrid = input_mesh.NewInstance()
        output_mesh.CopyStructure( input_mesh )
        output_mesh.CopyAttributes( input_mesh )

        if self.m_paintNonConformalCells:
            arrayNC: npt.NDArray = np.zeros( ( output_mesh.GetNumberOfCells(), 1 ), dtype=int )
            arrayNC[ unique_non_conformal_cells ] = 1
            vtkArrayNC: vtkDataArray = numpy_to_vtk( arrayNC )
            vtkArrayNC.SetName( "IsNonConformal" )
            output_mesh.GetCellData().AddArray( vtkArrayNC )

        output.ShallowCopy( output_mesh )

        return 1

    def SetLogger( self: Self, logger ) -> None:
        """Set the logger.

        Args:
            logger
        """
        self.m_logger = logger
        self.Modified()

    def getGrid( self: Self ) -> vtkUnstructuredGrid:
        """Returns the vtkUnstructuredGrid with volumes.

        Args:
            self (Self)

        Returns:
            vtkUnstructuredGrid
        """
        self.Update()  # triggers RequestData
        return self.GetOutputDataObject( 0 )

    def getAngleTolerance( self: Self ) -> float:
        """Returns the angle tolerance.

        Args:
            self (Self)

        Returns:
            float
        """
        return self.m_angle_tolerance

    def getfaceTolerance( self: Self ) -> float:
        """Returns the face tolerance.

        Args:
            self (Self)

        Returns:
            float
        """
        return self.m_face_tolerance

    def getPointTolerance( self: Self ) -> float:
        """Returns the point tolerance.

        Args:
            self (Self)

        Returns:
            float
        """
        return self.m_point_tolerance

    def setPaintNonConformalCells( self: Self, choice: int ) -> None:
        """Set 0 or 1 to choose if you want to create a new "IsNonConformal" array in your output data.

        Args:
            self (Self)
            choice (int): 0 or 1
        """
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setPaintNonConformalCells: Please choose either 0 or 1 not '{choice}'." )
        else:
            self.m_paintNonConformalCells = choice
            self.Modified()

    def setAngleTolerance( self: Self, tolerance: float ) -> None:
        """Set the angle tolerance parameter in degree.

        Args:
            self (Self)
            tolerance (float)
        """
        self.m_angle_tolerance = tolerance
        self.Modified()

    def setFaceTolerance( self: Self, tolerance: float ) -> None:
        """Set the face tolerance parameter.

        Args:
            self (Self)
            tolerance (float)
        """
        self.m_face_tolerance = tolerance
        self.Modified()

    def setPointTolerance( self: Self, tolerance: float ) -> None:
        """Set the point tolerance parameter.

        Args:
            self (Self)
            tolerance (float)
        """
        self.m_point_tolerance = tolerance
        self.Modified()

    def writeGrid( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        """Writes a .vtu file of the vtkUnstructuredGrid at the specified filepath with volumes.

        Args:
            filepath (str): /path/to/your/file.vtu
            is_data_mode_binary (bool, optional): Writes the file in binary format or ascii. Defaults to True.
            canOverwrite (bool, optional): Allows or not to overwrite if the filepath already leads to an existing file.
                                           Defaults to False.
        """
        mesh: vtkUnstructuredGrid = self.getGrid()
        if mesh:
            write_mesh( filepath, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
        else:
            self.m_logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )
