import os.path
import textwrap
from geos.mesh_doctor.parsing.cliParsing import setupLogger
from geos.mesh.io.vtkIO import VtkOutput

__OUTPUT_FILE = "output"
__OUTPUT_BINARY_MODE = "data-mode"
__OUTPUT_BINARY_MODE_VALUES = "binary", "ascii"
__OUTPUT_BINARY_MODE_DEFAULT = __OUTPUT_BINARY_MODE_VALUES[ 0 ]


def getVtkOutputHelp():
    msg = \
    f"""{__OUTPUT_FILE} [string]: The vtk output file destination.
    {__OUTPUT_BINARY_MODE} [string]: For ".vtu" output format, the data mode can be {" or ".join(__OUTPUT_BINARY_MODE_VALUES)}. Defaults to {__OUTPUT_BINARY_MODE_DEFAULT}."""
    return textwrap.dedent( msg )


def __buildArg( prefix, main ):
    return "-".join( filter( None, ( prefix, main ) ) )


def fillVtkOutputSubparser( parser, prefix="" ) -> None:
    parser.add_argument( '--' + __buildArg( prefix, __OUTPUT_FILE ),
                         type=str,
                         required=True,
                         help=f"[string]: The vtk output file destination." )
    parser.add_argument(
        '--' + __buildArg( prefix, __OUTPUT_BINARY_MODE ),
        type=str,
        metavar=", ".join( __OUTPUT_BINARY_MODE_VALUES ),
        default=__OUTPUT_BINARY_MODE_DEFAULT,
        help=
        f"""[string]: For ".vtu" output format, the data mode can be {" or ".join(__OUTPUT_BINARY_MODE_VALUES)}. Defaults to {__OUTPUT_BINARY_MODE_DEFAULT}."""
    )


def convert( parsedOptions, prefix="" ) -> VtkOutput:
    outputKey = __buildArg( prefix, __OUTPUT_FILE ).replace( "-", "_" )
    binaryModeKey = __buildArg( prefix, __OUTPUT_BINARY_MODE ).replace( "-", "_" )
    output = parsedOptions[ outputKey ]
    if parsedOptions[ binaryModeKey ] and os.path.splitext( output )[ -1 ] == ".vtk":
        setupLogger.info( "VTK data mode will be ignored for legacy file format \"vtk\"." )
    isDataModeBinary: bool = parsedOptions[ binaryModeKey ] == __OUTPUT_BINARY_MODE_DEFAULT
    return VtkOutput( output=output, isDataModeBinary=isDataModeBinary )
