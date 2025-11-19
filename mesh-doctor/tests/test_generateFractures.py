from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pytest
from typing import Iterable, Iterator, Optional, Sequence, TypeAlias
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkQuad, VTK_HEXAHEDRON, VTK_POLYHEDRON, VTK_QUAD )
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from geos.mesh.utils.genericHelpers import toVtkIdList
from geos.mesh_doctor.actions.checkFractures import formatCollocatedNodes
from geos.mesh_doctor.actions.generateCube import buildRectilinearBlocksMesh, XYZ
from geos.mesh_doctor.actions.generateFractures import ( __splitMeshOnFractures, Options, FracturePolicy, Coordinates3D,
                                                         IDMapping )

BorderFacesNodesCoords: TypeAlias = tuple[ tuple[ Coordinates3D, ... ], ... ]
FaceNodesCoords: TypeAlias = tuple[ Coordinates3D, ... ]
IDMatrix: TypeAlias = Sequence[ Sequence[ int ] ]


@dataclass( frozen=True )
class TestResult:
    __test__ = False
    mainMeshNumPoints: int
    mainMeshNumCells: int
    fractureMeshNumPoints: int
    fractureMeshNumCells: int


@dataclass( frozen=True )
class TestCase:
    __test__ = False
    inputMesh: vtkUnstructuredGrid
    options: Options
    collocatedNodes: IDMatrix
    result: TestResult


def __buildTestCase( xs: tuple[ npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ], npt.NDArray[ np.float64 ] ],
                     attribute: Iterable[ int ],
                     fieldValues: Optional[ Iterable[ int ] ] = None,
                     policy: FracturePolicy = FracturePolicy.FIELD ) -> tuple[ vtkUnstructuredGrid, Options ]:
    """Builds a test case mesh and options for fracture generation testing."""
    xyz = XYZ( *xs )
    mesh: vtkUnstructuredGrid = buildRectilinearBlocksMesh( ( xyz, ) )

    ref = np.array( attribute, dtype=int )
    if policy == FracturePolicy.FIELD:
        assert len( ref ) == mesh.GetNumberOfCells()
    attr = numpy_to_vtk( ref )
    attr.SetName( "attribute" )
    mesh.GetCellData().AddArray( attr )

    fv = frozenset( attribute ) if fieldValues is None else frozenset( fieldValues )

    options = Options( policy=policy,
                       field="attribute",
                       fieldValuesCombined=fv,
                       fieldValuesPerFracture=[ fv ],
                       meshVtkOutput=None,
                       allFracturesVtkOutput=None )
    return mesh, options


# Utility class to generate the new indices of the newly created collocated nodes.
class Incrementor:

    def __init__( self, start: int ) -> None:
        """Initializes the incrementor with a starting value."""
        self.__val = start

    def next( self, num: int ) -> Iterable[ int ]:
        """Generates the next 'num' values in the incrementor sequence."""
        self.__val += num
        return range( self.__val - num, self.__val )


def __generateTestData() -> Iterator[ TestCase ]:
    """Generates test data for fracture generation tests."""
    twoNodes = np.arange( 2, dtype=float )
    threeNodes = np.arange( 3, dtype=float )
    fourNodes = np.arange( 4, dtype=float )

    # Split in 2
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 0, 1, 0, 1, 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=tuple( ( 1 + 3 * i, 27 + i ) for i in range( 9 ) ),
                    result=TestResult( 9 * 4, 8, 9, 4 ) )

    # Split in 3
    inc = Incrementor( 27 )
    collocatedNodes0: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 2 ) ),
                                   ( 7, *inc.next( 1 ) ), ( 1 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 1 ) ),
                                   ( 4 + 9, *inc.next( 2 ) ), ( 7 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                   ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 2 ) ), ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 2, 1, 0, 1, 2, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes0,
                    result=TestResult( 9 * 4 + 6, 8, 12, 6 ) )

    # Split in 8
    inc = Incrementor( 27 )
    collocatedNodes2: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 3 ) ),
                                   ( 5, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ), ( 0 + 9, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 3 ) ), ( 2 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 3 ) ),
                                   ( 4 + 9, *inc.next( 7 ) ), ( 5 + 9, *inc.next( 3 ) ), ( 6 + 9, *inc.next( 1 ) ),
                                   ( 7 + 9, *inc.next( 3 ) ), ( 8 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                   ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 3 ) ), ( 5 + 18, *inc.next( 1 ) ),
                                   ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), range( 8 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes2,
                    result=TestResult( 8 * 8, 8, 3 * 3 * 3 - 8, 12 ) )

    # Straight notch
    inc = Incrementor( 27 )
    collocatedNodes3: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, ), ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ),
                                   ( 1 + 18, *inc.next( 1 ) ), ( 4 + 18, ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 2, 2, 0, 1, 2, 2 ),
                                     fieldValues=( 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes3,
                    result=TestResult( 3 * 3 * 3 + 3, 8, 6, 2 ) )

    # L-shaped notch
    inc = Incrementor( 27 )
    collocatedNodes4: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ), ( 7 + 9, ), ( 19, *inc.next( 1 ) ), ( 22, ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 0, 1, 0, 1, 2, 2 ),
                                     fieldValues=( 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes4,
                    result=TestResult( 3 * 3 * 3 + 5, 8, 8, 3 ) )

    # 3x1x1 split
    inc = Incrementor( 2 * 2 * 4 )
    collocatedNodes5: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 2, *inc.next( 1 ) ), ( 5, *inc.next( 1 ) ),
                                   ( 6, *inc.next( 1 ) ), ( 1 + 8, *inc.next( 1 ) ), ( 2 + 8, *inc.next( 1 ) ),
                                   ( 5 + 8, *inc.next( 1 ) ), ( 6 + 8, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( fourNodes, twoNodes, twoNodes ), ( 0, 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes5,
                    result=TestResult( 6 * 4, 3, 2 * 4, 2 ) )

    # Discarded fracture element if no node duplication.
    collocatedNodes6: IDMatrix = ()
    mesh, options = __buildTestCase( ( threeNodes, fourNodes, fourNodes ), ( 0, ) * 8 + ( 1, 2 ) + ( 0, ) * 8,
                                     fieldValues=( 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes6,
                    result=TestResult( 3 * 4 * 4, 2 * 3 * 3, 0, 0 ) )

    # Fracture on a corner
    inc = Incrementor( 3 * 4 * 4 )
    collocatedNodes7: IDMatrix = ( ( 1 + 12, ), ( 4 + 12, ), ( 7 + 12, ), ( 1 + 12 * 2, *inc.next( 1 ) ),
                                   ( 4 + 12 * 2, *inc.next( 1 ) ), ( 7 + 12 * 2, ), ( 1 + 12 * 3, *inc.next( 1 ) ),
                                   ( 4 + 12 * 3, *inc.next( 1 ) ), ( 7 + 12 * 3, ) )
    mesh, options = __buildTestCase( ( threeNodes, fourNodes, fourNodes ),
                                     ( 0, ) * 6 + ( 1, 2, 1, 2, 0, 0, 1, 2, 1, 2, 0, 0 ),
                                     fieldValues=( 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes7,
                    result=TestResult( 3 * 4 * 4 + 4, 2 * 3 * 3, 9, 4 ) )

    # Generate mesh with 2 hexs, one being a standard hex, the other a 42 hex.
    inc = Incrementor( 3 * 2 * 2 )
    collocatedNodes8: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, twoNodes, twoNodes ), ( 0, 1 ) )
    polyhedronMesh = vtkUnstructuredGrid()
    polyhedronMesh.SetPoints( mesh.GetPoints() )
    polyhedronMesh.Allocate( 2 )
    polyhedronMesh.InsertNextCell( VTK_HEXAHEDRON, toVtkIdList( ( 1, 2, 5, 4, 7, 8, 10, 11 ) ) )
    poly = toVtkIdList( [ 6 ] + [ 4, 0, 1, 7, 6 ] + [ 4, 1, 4, 10, 7 ] + [ 4, 4, 3, 9, 10 ] + [ 4, 3, 0, 6, 9 ] +
                        [ 4, 6, 7, 10, 9 ] + [ 4, 1, 0, 3, 4 ] )
    polyhedronMesh.InsertNextCell( VTK_POLYHEDRON, poly )
    polyhedronMesh.GetCellData().AddArray( mesh.GetCellData().GetArray( "attribute" ) )

    yield TestCase( inputMesh=polyhedronMesh,
                    options=options,
                    collocatedNodes=collocatedNodes8,
                    result=TestResult( 4 * 4, 2, 4, 1 ) )

    # Split in 2 using the internal fracture description
    inc = Incrementor( 3 * 2 * 2 )
    collocatedNodes9: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
                                   ( 1 + 9, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, twoNodes, twoNodes ),
                                     attribute=( 0, 0, 0 ),
                                     fieldValues=( 0, ),
                                     policy=FracturePolicy.INTERNAL_SURFACES )
    mesh.InsertNextCell( VTK_QUAD, toVtkIdList( ( 1, 4, 7, 10 ) ) )  # Add a fracture on the fly
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes9,
                    result=TestResult( 4 * 4, 3, 4, 1 ) )


@pytest.mark.parametrize( "TestCase", __generateTestData() )
def test_generateFracture( TestCase: TestCase ) -> None:
    """Tests the generation of fractures on a mesh according to various test cases."""
    mainMesh, fractureMeshes = __splitMeshOnFractures( TestCase.inputMesh, TestCase.options )
    fractureMesh: vtkUnstructuredGrid = fractureMeshes[ 0 ]
    assert mainMesh.GetNumberOfPoints() == TestCase.result.mainMeshNumPoints
    assert mainMesh.GetNumberOfCells() == TestCase.result.mainMeshNumCells
    assert fractureMesh.GetNumberOfPoints() == TestCase.result.fractureMeshNumPoints
    assert fractureMesh.GetNumberOfCells() == TestCase.result.fractureMeshNumCells

    res = formatCollocatedNodes( fractureMesh )
    assert res == TestCase.collocatedNodes
    assert len( res ) == TestCase.result.fractureMeshNumPoints


def addSimplifiedFieldForCells( mesh: vtkUnstructuredGrid, field_name: str, fieldDimension: int ) -> None:
    """Reduce functionality obtained from src.geos.mesh_doctor.actions.generateFractures.__add_fields.

    The goal is to add a cell data array with incrementing values.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        field_name (str): Name of the field to add to CellData
        fieldDimension (int): Number of components for the field.
    """
    data = mesh.GetCellData()
    n = mesh.GetNumberOfCells()
    array = np.ones( ( n, fieldDimension ), dtype=float )
    array = np.arange( 1, n * fieldDimension + 1 ).reshape( n, fieldDimension )
    vtkArray = numpy_to_vtk( array )
    vtkArray.SetName( field_name )
    data.AddArray( vtkArray )


def findBordersFacesRectilinearGrid( mesh: vtkUnstructuredGrid ) -> BorderFacesNodesCoords:
    """For a vtk rectilinear grid, gives the coordinates of each of its borders face nodes.

              6+--------+7
              /        /|
             /        / |
           4+--------+5 |
            |        |  |
            | 2+     |  +3
            |        | /
            |        |/
           0+--------+1

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.

    Returns:
        BorderFacesNodesCoords: For a rectilinear grid, returns a tuple of 6 faces nodeset.
    """
    meshBounds: tuple[ float, float, float, float, float, float ] = mesh.GetBounds()
    minBound: tuple[ float, ... ] = tuple( [ meshBounds[ i ] for i in range( len( meshBounds ) ) if i % 2 == 0 ] )
    maxBound: tuple[ float, ... ] = tuple( [ meshBounds[ i ] for i in range( len( meshBounds ) ) if i % 2 == 1 ] )
    center: Coordinates3D = mesh.GetCenter()
    faceDiag: Coordinates3D = ( ( maxBound[ 0 ] - minBound[ 0 ] ) / 2, ( maxBound[ 1 ] - minBound[ 1 ] ) / 2,
                                ( maxBound[ 2 ] - minBound[ 2 ] ) / 2 )
    node0: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node1: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node2: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node3: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node4: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node5: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node6: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node7: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    faces: BorderFacesNodesCoords = ( ( node0, node1, node3, node2 ), ( node4, node5, node7, node6 ),
                                    ( node0, node2, node6, node4 ), ( node1, node3, node7, node5 ),
                                    ( node0, node1, node5, node4 ), ( node2, node3, node7, node6 ) )
    return faces


def addQuad( mesh: vtkUnstructuredGrid, face: FaceNodesCoords ) -> None:
    """Adds a quad cell to each border of an unstructured mesh.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        face (FaceNodesCoords): Coordinates of the quad face to add.
    """
    pointsCoords = mesh.GetPoints().GetData()
    quad: vtkQuad = vtkQuad()
    idsAssociation: IDMapping = {}
    for i in range( mesh.GetNumberOfPoints() ):
        for j in range( len( face ) ):
            if pointsCoords.GetTuple( i ) == face[ j ]:
                idsAssociation[ i ] = j
                break
        if len( idsAssociation ) == 4:
            break

    for verticeId, quadCoordIndex in idsAssociation.items():
        quad.GetPoints().InsertNextPoint( face[ quadCoordIndex ] )
        quad.GetPointIds().SetId( quadCoordIndex, verticeId )

    mesh.InsertNextCell( quad.GetCellType(), quad.GetPointIds() )


@pytest.mark.skip( "Test to be fixed" )
def test_copyFieldsWhenSplittingMesh() -> None:
    """This test is designed to check the __copyFields method from generateFractures, that will be called when using __splitMeshOnFractures method from generateFractures."""
    # Generating the rectilinear grid and its quads on all borders
    x: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 1.0, 2.0 ] )
    y: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 1.0 ] )
    z: npt.NDArray[ np.float64 ] = np.array( [ 0.0, 1.0 ] )
    xyzs: XYZ = XYZ( x, y, z )
    mesh0: vtkUnstructuredGrid = buildRectilinearBlocksMesh( [ xyzs ] )
    assert mesh0.GetCells().GetNumberOfCells() == 2
    borderFaces0: BorderFacesNodesCoords = findBordersFacesRectilinearGrid( mesh0 )
    for face in borderFaces0:
        addQuad( mesh0, face )
    assert mesh0.GetCells().GetNumberOfCells() == 8
    # Create a quad cell to represent the fracture surface.
    fracture: FaceNodesCoords = ( ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 0.0, 1.0 ) )
    addQuad( mesh0, fracture )
    assert mesh0.GetCells().GetNumberOfCells() == 9
    # Add a "TestField" array
    assert mesh0.GetCellData().GetNumberOfArrays() == 0
    addSimplifiedFieldForCells( mesh0, "TestField", 1 )
    assert mesh0.GetCellData().GetNumberOfArrays() == 1
    assert mesh0.GetCellData().GetArrayName( 0 ) == "TestField"
    testFieldValues: list[ int ] = vtk_to_numpy( mesh0.GetCellData().GetArray( 0 ) ).tolist()
    assert testFieldValues == [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    # Split the mesh along the fracture surface which is number 9 on TestField
    options = Options( policy=FracturePolicy.INTERNAL_SURFACES,
                       field="TestField",
                       fieldValuesCombined=frozenset( map( int, [ "9" ] ) ),
                       fieldValuesPerFracture=[ frozenset( map( int, [ "9" ] ) ) ],
                       meshVtkOutput=None,
                       allFracturesVtkOutput=None )
    mainMesh, fractureMeshes = __splitMeshOnFractures( mesh0, options )
    fractureMesh: vtkUnstructuredGrid = fractureMeshes[ 0 ]
    assert mainMesh.GetCellData().GetNumberOfArrays() == 1
    assert fractureMesh.GetCellData().GetNumberOfArrays() == 1
    assert mainMesh.GetCellData().GetArrayName( 0 ) == "TestField"
    assert fractureMesh.GetCellData().GetArrayName( 0 ) == "TestField"
    #  Make sure that only 1 correct value is in "TestField" array for fractureMesh, 9 values for mainMesh
    fractureMeshValues: list[ int ] = vtk_to_numpy( fractureMesh.GetCellData().GetArray( 0 ) ).tolist()
    mainMeshValues: list[ int ] = vtk_to_numpy( mainMesh.GetCellData().GetArray( 0 ) ).tolist()
    assert fractureMeshValues == [ 9 ]  # The value for the fracture surface
    assert mainMeshValues == [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    # Test for invalid point field name
    addSimplifiedFieldForCells( mesh0, "GLOBAL_IDS_POINTS", 1 )
    with pytest.raises( ValueError ):
        mainMesh, fractureMeshes = __splitMeshOnFractures( mesh0, options )
    # Test for invalid cell field name
    mesh1: vtkUnstructuredGrid = buildRectilinearBlocksMesh( [ xyzs ] )
    borderFaces1: BorderFacesNodesCoords = findBordersFacesRectilinearGrid( mesh1 )
    for face in borderFaces1:
        addQuad( mesh1, face )
    addQuad( mesh1, fracture )
    addSimplifiedFieldForCells( mesh1, "TestField", 1 )
    addSimplifiedFieldForCells( mesh1, "GLOBAL_IDS_CELLS", 1 )
    assert mesh1.GetCellData().GetNumberOfArrays() == 2
    with pytest.raises( ValueError ):
        mainMesh, fractureMeshes = __splitMeshOnFractures( mesh1, options )
