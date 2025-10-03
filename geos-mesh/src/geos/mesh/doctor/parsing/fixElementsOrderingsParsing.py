import random
from vtkmodules.vtkCommonDataModel import (
    VTK_HEXAGONAL_PRISM,
    VTK_HEXAHEDRON,
    VTK_PENTAGONAL_PRISM,
    VTK_PYRAMID,
    VTK_TETRA,
    VTK_VOXEL,
    VTK_WEDGE,
)
from geos.mesh.doctor.actions.fixElementsOrderings import Options, Result
from geos.mesh.doctor.parsing import vtkOutputParsing, FIX_ELEMENTS_ORDERINGS
from geos.mesh.doctor.parsing.cliParsing import setupLogger

__CELL_TYPE_MAPPING = {
    "Hexahedron": VTK_HEXAHEDRON,
    "Prism5": VTK_PENTAGONAL_PRISM,
    "Prism6": VTK_HEXAGONAL_PRISM,
    "Pyramid": VTK_PYRAMID,
    "Tetrahedron": VTK_TETRA,
    "Voxel": VTK_VOXEL,
    "Wedge": VTK_WEDGE,
}

__CELL_TYPE_SUPPORT_SIZE = {
    VTK_HEXAHEDRON: 8,
    VTK_PENTAGONAL_PRISM: 10,
    VTK_HEXAGONAL_PRISM: 12,
    VTK_PYRAMID: 5,
    VTK_TETRA: 4,
    VTK_VOXEL: 8,
    VTK_WEDGE: 6,
}


def fillSubparser( subparsers ) -> None:
    p = subparsers.add_parser( FIX_ELEMENTS_ORDERINGS, help="Reorders the support nodes for the given cell types." )
    for key, vtkKey in __CELL_TYPE_MAPPING.items():
        tmp = list( range( __CELL_TYPE_SUPPORT_SIZE[ vtkKey ] ) )
        random.Random( 4 ).shuffle( tmp )
        p.add_argument( '--' + key,
                        type=str,
                        metavar=",".join( map( str, tmp ) ),
                        default=None,
                        required=False,
                        help=f"[list of integers]: node permutation for \"{key}\"." )
    vtkOutputParsing.fillVtkOutputSubparser( p )


def convert( parsedOptions ) -> Options:
    """
    From the parsed cli options, return the converted options for self intersecting elements check.
    :param parsedOptions: Parsed cli options.
    :return: Options instance.
    """
    cellTypeToOrdering = {}
    for key, vtkKey in __CELL_TYPE_MAPPING.items():
        rawMapping = parsedOptions[ key ]
        if rawMapping:
            tmp = tuple( map( int, rawMapping.split( "," ) ) )
            if not set( tmp ) == set( range( __CELL_TYPE_SUPPORT_SIZE[ vtkKey ] ) ):
                errMsg = f"Permutation {rawMapping} for type {key} is not valid."
                setupLogger.error( errMsg )
                raise ValueError( errMsg )
            cellTypeToOrdering[ vtkKey ] = tmp
    vtkOutput = vtkOutputParsing.convert( parsedOptions )
    return Options( vtkOutput=vtkOutput, cellTypeToOrdering=cellTypeToOrdering )


def displayResults( options: Options, result: Result ):
    if result.output:
        setupLogger.info( f"New mesh was written to file '{result.output}'" )
        if result.unchangedCellTypes:
            setupLogger.info(
                f"Those vtk types were not reordered: [{', '.join(map(str, result.unchangedCellTypes))}]." )
        else:
            setupLogger.info( "All the cells of the mesh were reordered." )
    else:
        setupLogger.info( "No output file was written." )
