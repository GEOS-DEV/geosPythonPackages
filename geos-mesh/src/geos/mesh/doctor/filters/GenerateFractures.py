from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import vtkUnstructuredGrid
from geos.mesh.doctor.actions.generate_fractures import Options, split_mesh_on_fractures
from geos.mesh.doctor.filters.MeshDoctorFilterBase import MeshDoctorFilterBase
from geos.mesh.doctor.parsing.generate_fractures_parsing import convert, convert_to_fracture_policy
from geos.mesh.doctor.parsing.generate_fractures_parsing import ( __FIELD_NAME, __FIELD_VALUES, __FRACTURES_DATA_MODE,
                                                                  __FRACTURES_OUTPUT_DIR, __FRACTURES_DATA_MODE_VALUES,
                                                                  __POLICIES, __POLICY )
from geos.mesh.io.vtkIO import VtkOutput, write_mesh
from geos.mesh.utils.arrayHelpers import has_array

__doc__ = """
GenerateFractures module splits a vtkUnstructuredGrid along non-embedded fractures.
When a fracture plane is defined between two cells, the nodes of the shared face will be duplicated
to create a discontinuity. The filter generates both the split main mesh and separate fracture meshes.

To use the filter:

.. code-block:: python

    from geos.mesh.doctor.filters.GenerateFractures import GenerateFractures

    # instantiate the filter
    generateFracturesFilter = GenerateFractures(
        mesh,
        field_name="fracture_field",
        field_values="1,2",
        fractures_output_dir="./fractures/",
        policy=1
    )

    # execute the filter
    success = generateFracturesFilter.applyFilter()

    # get the results
    split_mesh = generateFracturesFilter.getMesh()
    fracture_meshes = generateFracturesFilter.getFractureMeshes()

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

loggerTitle: str = "Generate Fractures Filter"


class GenerateFractures( MeshDoctorFilterBase ):

    def __init__(
        self: Self,
        mesh: vtkUnstructuredGrid,
        field_name: str = None,
        field_values: str = None,
        fractures_output_dir: str = None,
        policy: int = 1,
        output_data_mode: int = 0,
        fractures_data_mode: int = 1,
        use_external_logger: bool = False,
    ) -> None:
        """Initialize the generate fractures filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to split
            field_name (str): Field name that defines fracture regions. Defaults to None.
            field_values (str): Comma-separated field values that identify fracture boundaries. Defaults to None.
            fractures_output_dir (str): Output directory for fracture meshes. Defaults to None.
            policy (int): Fracture policy (0 for internal, 1 for boundary). Defaults to 1.
            output_data_mode (int): Data mode for main mesh (0 for ASCII, 1 for binary). Defaults to 0.
            fractures_data_mode (int): Data mode for fracture meshes (0 for ASCII, 1 for binary). Defaults to 1.
            use_external_logger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, use_external_logger )
        self.field_name: str = field_name
        self.field_values: str = field_values
        self.fractures_output_dir: str = fractures_output_dir
        self.policy: str = POLICIES[ policy ] if 0 <= policy <= 1 else POLICIES[ 1 ]
        self.output_data_mode: str = DATA_MODE[ output_data_mode ] if output_data_mode in [ 0, 1 ] else DATA_MODE[ 0 ]
        self.fractures_data_mode: str = ( DATA_MODE[ fractures_data_mode ]
                                          if fractures_data_mode in [ 0, 1 ] else DATA_MODE[ 1 ] )

        # Results storage
        self.fracture_meshes: list[ vtkUnstructuredGrid ] = []
        self.all_fractures_vtk_output: list[ VtkOutput ] = []

    def setFieldName( self: Self, field_name: str ) -> None:
        """Set the field name that defines fracture regions.

        Args:
            field_name (str): Name of the field
        """
        self.field_name = field_name

    def setFieldValues( self: Self, field_values: str ) -> None:
        """Set the field values that identify fracture boundaries.

        Args:
            field_values (str): Comma-separated field values
        """
        self.field_values = field_values

    def setFracturesOutputDirectory( self: Self, directory: str ) -> None:
        """Set the output directory for fracture meshes.

        Args:
            directory (str): Directory path
        """
        self.fractures_output_dir = directory

    def setPolicy( self: Self, choice: int ) -> None:
        """Set the fracture policy.

        Args:
            choice (int): 0 for internal fractures, 1 for boundary fractures
        """
        if choice not in [ 0, 1 ]:
            self.logger.error(
                f"setPolicy: Please choose either 0 for {POLICIES[0]} or 1 for {POLICIES[1]}, not '{choice}'." )
        else:
            self.policy = convert_to_fracture_policy( POLICIES[ choice ] )

    def setOutputDataMode( self: Self, choice: int ) -> None:
        """Set the data mode for the main mesh output.

        Args:
            choice (int): 0 for ASCII, 1 for binary
        """
        if choice not in [ 0, 1 ]:
            self.logger.error(
                f"setOutputDataMode: Please choose either 0 for {DATA_MODE[0]} or 1 for {DATA_MODE[1]}, not '{choice}'."
            )
        else:
            self.output_data_mode = DATA_MODE[ choice ]

    def setFracturesDataMode( self: Self, choice: int ) -> None:
        """Set the data mode for fracture mesh outputs.

        Args:
            choice (int): 0 for ASCII, 1 for binary
        """
        if choice not in [ 0, 1 ]:
            self.logger.error( f"setFracturesDataMode: Please choose either 0 for {DATA_MODE[0]} "
                               f"or 1 for {DATA_MODE[1]}, not '{choice}'." )
        else:
            self.fractures_data_mode = DATA_MODE[ choice ]

    def applyFilter( self: Self ) -> bool:
        """Apply the fracture generation.

        Returns:
            bool: True if fractures generated successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        try:
            # Check for global IDs which are not allowed
            if has_array( self.mesh, [ "GLOBAL_IDS_POINTS", "GLOBAL_IDS_CELLS" ] ):
                self.logger.error(
                    "The mesh cannot contain global ids for neither cells nor points. "
                    "The correct procedure is to split the mesh and then generate global ids for new split meshes." )
                return False

            # Validate required parameters
            parsed_options = self._getParsedOptions()
            if len( parsed_options ) < 5:
                self.logger.error( "You must set all variables before trying to create fractures." )
                return False

            self.logger.info( f"Parsed options: {parsed_options}" )

            # Convert options and split mesh
            options: Options = convert( parsed_options )
            self.all_fractures_vtk_output = options.all_fractures_VtkOutput

            # Perform the fracture generation
            output_mesh, self.fracture_meshes = split_mesh_on_fractures( self.mesh, options )

            # Update the main mesh with the split result
            self.mesh = output_mesh

            self.logger.info( f"Generated {len(self.fracture_meshes)} fracture meshes" )
            self.logger.info( f"The filter {self.logger.name} succeeded" )
            return True

        except Exception as e:
            self.logger.error( f"Error in fracture generation: {e}" )
            self.logger.error( f"The filter {self.logger.name} failed" )
            return False

    def _getParsedOptions( self: Self ) -> dict[ str, str ]:
        """Get parsed options for fracture generation."""
        parsed_options: dict[ str, str ] = { "output": "./mesh.vtu", "data_mode": DATA_MODE[ 0 ] }
        parsed_options[ POLICY ] = self.policy
        parsed_options[ FRACTURES_DATA_MODE ] = self.fractures_data_mode

        if self.field_name:
            parsed_options[ FIELD_NAME ] = self.field_name
        else:
            self.logger.error( "No field name provided. Please use setFieldName." )

        if self.field_values:
            parsed_options[ FIELD_VALUES ] = self.field_values
        else:
            self.logger.error( "No field values provided. Please use setFieldValues." )

        if self.fractures_output_dir:
            parsed_options[ FRACTURES_OUTPUT_DIR ] = self.fractures_output_dir
        else:
            self.logger.error( "No fracture output directory provided. Please use setFracturesOutputDirectory." )

        return parsed_options

    def getFractureMeshes( self: Self ) -> list[ vtkUnstructuredGrid ]:
        """Get the generated fracture meshes.

        Returns:
            list[vtkUnstructuredGrid]: List of fracture meshes
        """
        return self.fracture_meshes

    def getAllGrids( self: Self ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
        """Get both the split main mesh and fracture meshes.

        Returns:
            tuple[vtkUnstructuredGrid, list[vtkUnstructuredGrid]]: Split mesh and fracture meshes
        """
        return ( self.mesh, self.fracture_meshes )

    def writeMeshes( self: Self, filepath: str, is_data_mode_binary: bool = True, canOverwrite: bool = False ) -> None:
        """Write both the split main mesh and all fracture meshes.

        Args:
            filepath (str): Path for the main split mesh
            is_data_mode_binary (bool): Whether to use binary format for main mesh. Defaults to True.
            canOverwrite (bool): Whether to allow overwriting existing files. Defaults to False.
        """
        if self.mesh:
            write_mesh( self.mesh, VtkOutput( filepath, is_data_mode_binary ), canOverwrite )
        else:
            self.logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )

        for i, fracture_mesh in enumerate( self.fracture_meshes ):
            if i < len( self.all_fractures_vtk_output ):
                write_mesh( fracture_mesh, self.all_fractures_vtk_output[ i ] )


# Main function for backward compatibility and standalone use
def generate_fractures(
    mesh: vtkUnstructuredGrid,
    field_name: str,
    field_values: str,
    fractures_output_dir: str,
    policy: int = 1,
    output_data_mode: int = 0,
    fractures_data_mode: int = 1,
    write_output: bool = False,
    output_path: str = "output/split_mesh.vtu",
) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    """Apply fracture generation to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh
        field_name (str): Field name that defines fracture regions
        field_values (str): Comma-separated field values that identify fracture boundaries
        fractures_output_dir (str): Output directory for fracture meshes
        policy (int): Fracture policy (0 for internal, 1 for boundary). Defaults to 1.
        output_data_mode (int): Data mode for main mesh (0 for ASCII, 1 for binary). Defaults to 0.
        fractures_data_mode (int): Data mode for fracture meshes (0 for ASCII, 1 for binary). Defaults to 1.
        write_output (bool): Whether to write output meshes to files. Defaults to False.
        output_path (str): Output file path if write_output is True.

    Returns:
        tuple[vtkUnstructuredGrid, list[vtkUnstructuredGrid]]:
            Split mesh and fracture meshes
    """
    filter_instance = GenerateFractures( mesh, field_name, field_values, fractures_output_dir, policy, output_data_mode,
                                         fractures_data_mode )
    success = filter_instance.applyFilter()

    if not success:
        raise RuntimeError( "Fracture generation failed" )

    if write_output:
        filter_instance.writeMeshes( output_path )

    return filter_instance.getAllGrids()


# Alias for backward compatibility
def processGenerateFractures(
    mesh: vtkUnstructuredGrid,
    field_name: str,
    field_values: str,
    fractures_output_dir: str,
    policy: int = 1,
) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    """Legacy function name for backward compatibility."""
    return generate_fractures( mesh, field_name, field_values, fractures_output_dir, policy )
