from typing_extensions import Self
from vtkmodules.vtkCommonCore import vtkInformation, vtkInformationVector
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.generate_fractures import Options, split_mesh_on_fractures
from geos.mesh.doctor.filters.MeshDoctorBase import MeshDoctorBase
from geos.mesh.doctor.parsing.generate_fractures_parsing import convert, convert_to_fracture_policy
from geos.mesh.doctor.parsing.generate_fractures_parsing import ( __FIELD_NAME, __FIELD_VALUES, __FRACTURES_DATA_MODE,
                                                                  __FRACTURES_OUTPUT_DIR, __FRACTURES_DATA_MODE_VALUES,
                                                                  __POLICIES, __POLICY )
from geos.mesh.io.vtkIO import VtkOutput, write_mesh
from geos.mesh.utils.arrayHelpers import has_array

__doc__ = """
GenerateFractures module is a vtk filter that splits a vtkUnstructuredGrid along non-embedded fractures.
When a fracture plane is defined between two cells, the nodes of the shared face will be duplicated
to create a discontinuity. The filter generates both the split main mesh and separate fracture meshes.

One filter input is vtkUnstructuredGrid, two filter outputs which are vtkUnstructuredGrid.

To use the filter:

.. code-block:: python

    from filters.GenerateFractures import GenerateFractures

    # instantiate the filter
    generateFracturesFilter: GenerateFractures = GenerateFractures()

    # set the field name that defines fracture regions
    generateFracturesFilter.setFieldName("fracture_field")

    # set the field values that identify fracture boundaries
    generateFracturesFilter.setFieldValues("1,2")  # comma-separated values

    # set fracture policy (0 for internal fractures, 1 for boundary fractures)
    generateFracturesFilter.setPolicy(1)

    # set output directory for fracture meshes
    generateFracturesFilter.setFracturesOutputDirectory("./fractures/")

    # optionally set data mode (0 for ASCII, 1 for binary)
    generateFracturesFilter.setOutputDataMode(1)
    generateFracturesFilter.setFracturesDataMode(1)

    # set input mesh
    generateFracturesFilter.SetInputData(mesh)

    # execute the filter
    generateFracturesFilter.Update()

    # get the split mesh and fracture meshes
    split_mesh, fracture_meshes = generateFracturesFilter.getAllGrids()

    # write all meshes
    generateFracturesFilter.writeMeshes("output/split_mesh.vtu", is_data_mode_binary=True)
"""

FIELD_NAME = __FIELD_NAME
FIELD_VALUES = __FIELD_VALUES
FRACTURES_DATA_MODE = __FRACTURES_DATA_MODE
DATA_MODE = __FRACTURES_DATA_MODE_VALUES
FRACTURES_OUTPUT_DIR = __FRACTURES_OUTPUT_DIR
POLICIES = __POLICIES
POLICY = __POLICY


class GenerateFractures( MeshDoctorBase ):

    def __init__( self: Self ) -> None:
        """Vtk filter to generate a simple rectilinear grid.

        Output mesh is vtkUnstructuredGrid.
        """
        super().__init__( nInputPorts=1,
                          nOutputPorts=2,
                          inputType='vtkUnstructuredGrid',
                          outputType='vtkUnstructuredGrid' )
        self.m_policy: str = POLICIES[ 1 ]
        self.m_field_name: str = None
        self.m_field_values: str = None
        self.m_fractures_output_dir: str = None
        self.m_output_modes_binary: str = { "mesh": DATA_MODE[ 0 ], "fractures": DATA_MODE[ 1 ] }
        self.m_mesh_VtkOutput: VtkOutput = None
        self.m_all_fractures_VtkOutput: list[ VtkOutput ] = None

    def RequestData( self: Self, request: vtkInformation, inInfoVec: list[ vtkInformationVector ],
                     outInfo: list[ vtkInformationVector ] ) -> int:
        input_mesh = vtkUnstructuredGrid.GetData( inInfoVec[ 0 ] )
        if has_array( input_mesh, [ "GLOBAL_IDS_POINTS", "GLOBAL_IDS_CELLS" ] ):
            err_msg: str = ( "The mesh cannot contain global ids for neither cells nor points. The correct procedure " +
                             " is to split the mesh and then generate global ids for new split meshes." )
            self.m_logger.error( err_msg )
            return 0

        parsed_options: dict[ str, str ] = self.getParsedOptions()
        self.m_logger.critical( f"Parsed_options:\n{parsed_options}" )
        if len( parsed_options ) < 5:
            self.m_logger.error( "You must set all variables before trying to create fractures." )
            return 0

        options: Options = convert( parsed_options )
        self.m_all_fractures_VtkOutput = options.all_fractures_VtkOutput
        output_mesh, fracture_meshes = split_mesh_on_fractures( input_mesh, options )
        opt = vtkUnstructuredGrid.GetData( outInfo, 0 )
        opt.ShallowCopy( output_mesh )

        nbr_faults: int = len( fracture_meshes )
        self.SetNumberOfOutputPorts( 1 + nbr_faults )  # one output port for splitted mesh, the rest for every fault
        for i in range( nbr_faults ):
            opt_fault = vtkUnstructuredGrid.GetData( outInfo, i + 1 )
            opt_fault.ShallowCopy( fracture_meshes[ i ] )

        return 1

    def getAllGrids( self: Self ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
        """Returns the vtkUnstructuredGrid with volumes.

        Args:
            self (Self)

        Returns:
            vtkUnstructuredGrid
        """
        self.Update()  # triggers RequestData
        splitted_grid: vtkUnstructuredGrid = self.GetOutputDataObject( 0 )
        nbrOutputPorts: int = self.GetNumberOfOutputPorts()
        fracture_meshes: list[ vtkUnstructuredGrid ] = list()
        for i in range( 1, nbrOutputPorts ):
            fracture_meshes.append( self.GetOutputDataObject( i ) )
        return ( splitted_grid, fracture_meshes )

    def getParsedOptions( self: Self ) -> dict[ str, str ]:
        parsed_options: dict[ str, str ] = { "output": "./mesh.vtu", "data_mode": DATA_MODE[ 0 ] }
        parsed_options[ POLICY ] = self.m_policy
        parsed_options[ FRACTURES_DATA_MODE ] = self.m_output_modes_binary[ "fractures" ]
        if self.m_field_name:
            parsed_options[ FIELD_NAME ] = self.m_field_name
        else:
            self.m_logger.error( "No field name provided. Please use setFieldName." )
        if self.m_field_values:
            parsed_options[ FIELD_VALUES ] = self.m_field_values
        else:
            self.m_logger.error( "No field values provided. Please use setFieldValues." )
        if self.m_fractures_output_dir:
            parsed_options[ FRACTURES_OUTPUT_DIR ] = self.m_fractures_output_dir
        else:
            self.m_logger.error( "No fracture output directory provided. Please use setFracturesOutputDirectory." )
        return parsed_options

    def setFieldName( self: Self, field_name: str ) -> None:
        self.m_field_name = field_name
        self.Modified()

    def setFieldValues( self: Self, field_values: str ) -> None:
        self.m_field_values = field_values
        self.Modified()

    def setFracturesDataMode( self: Self, choice: int ) -> None:
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setFracturesDataMode: Please choose either 0 for {DATA_MODE[ 0 ]} or 1 for",
                                 f" {DATA_MODE[ 1 ]}, not '{choice}'." )
        else:
            self.m_output_modes_binary[ "fractures" ] = DATA_MODE[ choice ]
            self.Modified()

    def setFracturesOutputDirectory( self: Self, directory: str ) -> None:
        self.m_fractures_output_dir = directory
        self.Modified()

    def setOutputDataMode( self: Self, choice: int ) -> None:
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setOutputDataMode: Please choose either 0 for {DATA_MODE[ 0 ]} or 1 for",
                                 f" {DATA_MODE[ 1 ]}, not '{choice}'." )
        else:
            self.m_output_modes_binary[ "mesh" ] = DATA_MODE[ choice ]
            self.Modified()

    def setPolicy( self: Self, choice: int ) -> None:
        if choice not in [ 0, 1 ]:
            self.m_logger.error( f"setPolicy: Please choose either 0 for {POLICIES[ 0 ]} or 1 for {POLICIES[ 1 ]},"
                                 f" not '{choice}'." )
        else:
            self.m_policy = convert_to_fracture_policy( POLICIES[ choice ] )
            self.Modified()

    def writeMeshes( self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        splitted_grid, fracture_meshes = self.getAllGrids()
        if splitted_grid:
            write_mesh( splitted_grid, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
        else:
            self.m_logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )

        for i, fracture_mesh in enumerate( fracture_meshes ):
            write_mesh( fracture_mesh, self.m_all_fractures_VtkOutput[ i ] )
