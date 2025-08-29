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

To use the filter
-----------------

.. code-block:: python

    from geos.mesh.doctor.filters.GenerateFractures import GenerateFractures

    # instantiate the filter
    generateFracturesFilter = GenerateFractures(
        mesh,
        fieldName="fracture_field",
        fieldValues="1,2",
        fracturesOutputDir="./fractures/",
        policy=1
    )

    # execute the filter
    success = generateFracturesFilter.applyFilter()

    # get the results
    splitMesh = generateFracturesFilter.getMesh()
    fractureMeshes = generateFracturesFilter.getFractureMeshes()

    # write all meshes
    generateFracturesFilter.writeMeshes("output/split_mesh.vtu", isDataModeBinary=True)

For standalone use without creating a filter instance
-----------------------------------------------------

.. code-block:: python

    from geos.mesh.doctor.filters.GenerateFractures import generateFractures

    # apply fracture generation directly
    splitMesh, fractureMeshes = generateFractures(
        mesh,
        outputPath="output/split_mesh.vtu",
        fieldName="fracture_field",
        fieldValues="1,2",
        fracturesOutputDir="./fractures/",
        policy=1,
        outputDataMode=0,
        fracturesDataMode=1
    )
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
        fieldName: str = None,
        fieldValues: str = None,
        fracturesOutputDir: str = None,
        policy: int = 1,
        outputDataMode: int = 0,
        fracturesDataMode: int = 1,
        useExternalLogger: bool = False,
    ) -> None:
        """Initialize the generate fractures filter.

        Args:
            mesh (vtkUnstructuredGrid): The input mesh to split.
            fieldName (str): Field name that defines fracture regions. Defaults to None.
            fieldValues (str): Comma-separated field values that identify fracture boundaries. Defaults to None.
            fracturesOutputDir (str): Output directory for fracture meshes. Defaults to None.
            policy (int): Fracture policy (0 for internal, 1 for boundary). Defaults to 1.
            outputDataMode (int): Data mode for main mesh (0 for ASCII, 1 for binary). Defaults to 0.
            fracturesDataMode (int): Data mode for fracture meshes (0 for ASCII, 1 for binary). Defaults to 1.
            useExternalLogger (bool): Whether to use external logger. Defaults to False.
        """
        super().__init__( mesh, loggerTitle, useExternalLogger )
        self.fieldName: str = fieldName
        self.fieldValues: str = fieldValues
        self.fracturesOutputDir: str = fracturesOutputDir
        self.policy: str = POLICIES[ policy ] if 0 <= policy <= 1 else POLICIES[ 1 ]
        self.outputDataMode: str = DATA_MODE[ outputDataMode ] if outputDataMode in [ 0, 1 ] else DATA_MODE[ 0 ]
        self.fracturesDataMode: str = ( DATA_MODE[ fracturesDataMode ]
                                        if fracturesDataMode in [ 0, 1 ] else DATA_MODE[ 1 ] )
        self.fractureMeshes: list[ vtkUnstructuredGrid ] = []
        self.allFracturesVtkOutput: list[ VtkOutput ] = []

    def applyFilter( self: Self ) -> bool:
        """Apply the fracture generation.

        Returns:
            bool: True if fractures generated successfully, False otherwise.
        """
        self.logger.info( f"Apply filter {self.logger.name}" )

        # Check for global IDs which are not allowed
        if has_array( self.mesh, [ "GLOBAL_IDS_POINTS", "GLOBAL_IDS_CELLS" ] ):
            self.logger.error(
                "The mesh cannot contain global ids for neither cells nor points."
                " The correct procedure is to split the mesh and then generate global ids for new split meshes." )
            return False

        # Validate required parameters
        parsedOptions = self._buildParsedOptions()
        if len( parsedOptions ) < 5:
            self.logger.error( "You must set all variables before trying to create fractures." )
            return False

        self.logger.info( f"Parsed options: {parsedOptions}" )

        # Convert options and split mesh
        options: Options = convert( parsedOptions )
        self.allFracturesVtkOutput = options.all_fractures_VtkOutput

        # Perform the fracture generation
        output_mesh, self.fractureMeshes = split_mesh_on_fractures( self.mesh, options )

        # Update the main mesh with the split result
        self.mesh = output_mesh

        self.logger.info( f"Generated {len(self.fractureMeshes)} fracture meshes." )
        self.logger.info( f"The filter {self.logger.name} succeeded." )
        return True

    def getAllGrids( self: Self ) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
        """Get both the split main mesh and fracture meshes.

        Returns:
            tuple[vtkUnstructuredGrid, list[vtkUnstructuredGrid]]: Split mesh and fracture meshes.
        """
        return ( self.mesh, self.fractureMeshes )

    def getFractureMeshes( self: Self ) -> list[ vtkUnstructuredGrid ]:
        """Get the generated fracture meshes.

        Returns:
            list[vtkUnstructuredGrid]: List of fracture meshes.
        """
        return self.fractureMeshes

    def setFieldName( self: Self, fieldName: str ) -> None:
        """Set the field name that defines fracture regions.

        Args:
            fieldName (str): Name of the field.
        """
        self.fieldName = fieldName

    def setFieldValues( self: Self, fieldValues: str ) -> None:
        """Set the field values that identify fracture boundaries.

        Args:
            fieldValues (str): Comma-separated field values.
        """
        self.fieldValues = fieldValues

    def setFracturesDataMode( self: Self, choice: int ) -> None:
        """Set the data mode for fracture mesh outputs.

        Args:
            choice (int): 0 for ASCII, 1 for binary.
        """
        if choice not in [ 0, 1 ]:
            self.logger.error( f"setFracturesDataMode: Please choose either 0 for {DATA_MODE[0]} "
                               f"or 1 for {DATA_MODE[1]}, not '{choice}'." )
        else:
            self.fracturesDataMode = DATA_MODE[ choice ]

    def setFracturesOutputDirectory( self: Self, directory: str ) -> None:
        """Set the output directory for fracture meshes.

        Args:
            directory (str): Directory path.
        """
        self.fracturesOutputDir = directory

    def setOutputDataMode( self: Self, choice: int ) -> None:
        """Set the data mode for the main mesh output.

        Args:
            choice (int): 0 for ASCII, 1 for binary.
        """
        if choice not in [ 0, 1 ]:
            self.logger.error(
                f"setOutputDataMode: Please choose either 0 for {DATA_MODE[0]} or 1 for {DATA_MODE[1]}, not '{choice}'."
            )
        else:
            self.outputDataMode = DATA_MODE[ choice ]

    def setPolicy( self: Self, choice: int ) -> None:
        """Set the fracture policy.

        Args:
            choice (int): 0 for field, 1 for internal surfaces.
        """
        if choice not in [ 0, 1 ]:
            self.logger.error(
                f"setPolicy: Please choose either 0 for {POLICIES[0]} or 1 for {POLICIES[1]}, not '{choice}'." )
        else:
            self.policy = convert_to_fracture_policy( POLICIES[ choice ] )

    def _buildParsedOptions( self: Self ) -> dict[ str, str ]:
        """Build parsed options to be used for an Options object."""
        parsedOptions: dict[ str, str ] = { "output": "./mesh.vtu", "data_mode": DATA_MODE[ 0 ] }
        parsedOptions[ POLICY ] = self.policy
        parsedOptions[ FRACTURES_DATA_MODE ] = self.fracturesDataMode

        if self.fieldName:
            parsedOptions[ FIELD_NAME ] = self.fieldName
        else:
            self.logger.error( "No field name provided. Please use setFieldName." )

        if self.fieldValues:
            parsedOptions[ FIELD_VALUES ] = self.fieldValues
        else:
            self.logger.error( "No field values provided. Please use setFieldValues." )

        if self.fracturesOutputDir:
            parsedOptions[ FRACTURES_OUTPUT_DIR ] = self.fracturesOutputDir
        else:
            self.logger.error( "No fracture output directory provided. Please use setFracturesOutputDirectory." )

        return parsedOptions

    def writeMeshes( self: Self, filepath: str, isDataModeBinary: bool = True, canOverwrite: bool = False ) -> None:
        """Write both the split main mesh and all fracture meshes.

        Args:
            filepath (str): Path for the main split mesh.
            isDataModeBinary (bool): Whether to use binary format for main mesh. Defaults to True.
            canOverwrite (bool): Whether to allow overwriting existing files. Defaults to False.
        """
        if self.mesh:
            write_mesh( self.mesh, VtkOutput( filepath, isDataModeBinary ), canOverwrite )
        else:
            self.logger.error( f"No output grid was built. Cannot output vtkUnstructuredGrid at {filepath}." )

        for i, fractureMesh in enumerate( self.fractureMeshes ):
            if i < len( self.allFracturesVtkOutput ):
                write_mesh( fractureMesh, self.allFracturesVtkOutput[ i ] )


# Main function for standalone use
def generateFractures(
    mesh: vtkUnstructuredGrid,
    outputPath: str,
    fieldName: str,
    fieldValues: str,
    fracturesOutputDir: str,
    policy: int = 1,
    outputDataMode: int = 0,
    fracturesDataMode: int = 1
) -> tuple[ vtkUnstructuredGrid, list[ vtkUnstructuredGrid ] ]:
    """Apply fracture generation to a mesh.

    Args:
        mesh (vtkUnstructuredGrid): The input mesh.
        outputPath (str): Output file path if write_output is True.
        fieldName (str): Field name that defines fracture regions.
        fieldValues (str): Comma-separated field values that identify fracture boundaries.
        fracturesOutputDir (str): Output directory for fracture meshes.
        policy (int): Fracture policy (0 for internal, 1 for boundary). Defaults to 1.
        outputDataMode (int): Data mode for main mesh (0 for ASCII, 1 for binary). Defaults to 0.
        fracturesDataMode (int): Data mode for fracture meshes (0 for ASCII, 1 for binary). Defaults to 1.

    Returns:
        tuple[vtkUnstructuredGrid, list[vtkUnstructuredGrid]]:
            Split mesh and fracture meshes.
    """
    filterInstance = GenerateFractures( mesh, fieldName, fieldValues, fracturesOutputDir, policy, outputDataMode,
                                        fracturesDataMode )
    success = filterInstance.applyFilter()

    if not success:
        raise RuntimeError( "Fracture generation failed." )

    filterInstance.writeMeshes( outputPath )

    return filterInstance.getAllGrids()
