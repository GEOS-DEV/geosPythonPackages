from dataclasses import dataclass
import numpy
import pytest
from typing import Iterable, Iterator, Sequence
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkQuad, VTK_HEXAHEDRON, VTK_POLYHEDRON, VTK_QUAD )
from vtkmodules.util.numpy_support import numpy_to_vtk, vtk_to_numpy
from geos.mesh.doctor.actions.checkFractures import formatCollocatedNodes
from geos.mesh.doctor.actions.generateCube import buildRectilinearBlocksMesh, XYZ
from geos.mesh.doctor.actions.generateFractures import ( __splitMeshOnFractures, Options, FracturePolicy, Coordinates3D,
                                                         IDMapping )
from geos.mesh.utils.genericHelpers import toVtkIdList

FaceNodesCoords = tuple[ tuple[ float ] ]
IDMatrix = Sequence[ Sequence[ int ] ]


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


def __buildTestCase( xs: tuple[ numpy.ndarray, numpy.ndarray, numpy.ndarray ],
                     attribute: Iterable[ int ],
                     fieldValues: Iterable[ int ] = None,
                     policy: FracturePolicy = FracturePolicy.FIELD ):
    xyz = XYZ( *xs )

    mesh: vtkUnstructuredGrid = buildRectilinearBlocksMesh( ( xyz, ) )

    ref = numpy.array( attribute, dtype=int )
    if policy == FracturePolicy.FIELD:
        assert len( ref ) == mesh.GetNumberOfCells()
    attr = numpy_to_vtk( ref )
    attr.SetName( "attribute" )
    mesh.GetCellData().AddArray( attr )

    if fieldValues is None:
        fv = frozenset( attribute )
    else:
        fv = frozenset( fieldValues )

    options = Options( policy=policy,
                       field="attribute",
                       fieldValuesCombined=fv,
                       fieldValuesPerFracture=[ fv ],
                       meshVtkOutput=None,
                       allFracturesVtkOutput=None )
    return mesh, options


# Utility class to generate the new indices of the newly created collocated nodes.
class Incrementor:

    def __init__( self, start ):
        self.__val = start

    def next( self, num: int ) -> Iterable[ int ]:
        self.__val += num
        return range( self.__val - num, self.__val )


def __generateTestData() -> Iterator[ TestCase ]:
    twoNodes = numpy.arange( 2, dtype=float )
    threeNodes = numpy.arange( 3, dtype=float )
    fourNodes = numpy.arange( 4, dtype=float )

    # Split in 2
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 0, 1, 0, 1, 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=tuple( map( lambda i: ( 1 + 3 * i, 27 + i ), range( 9 ) ) ),
                    result=TestResult( 9 * 4, 8, 9, 4 ) )

    # Split in 3
    inc = Incrementor( 27 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 2 ) ),
                                  ( 7, *inc.next( 1 ) ), ( 1 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 1 ) ),
                                  ( 4 + 9, *inc.next( 2 ) ), ( 7 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                  ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 2 ) ), ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 2, 1, 0, 1, 2, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 9 * 4 + 6, 8, 12, 6 ) )

    # Split in 8
    inc = Incrementor( 27 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 3, *inc.next( 1 ) ), ( 4, *inc.next( 3 ) ),
                                  ( 5, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ), ( 0 + 9, *inc.next( 1 ) ),
                                  ( 1 + 9, *inc.next( 3 ) ), ( 2 + 9, *inc.next( 1 ) ), ( 3 + 9, *inc.next( 3 ) ),
                                  ( 4 + 9, *inc.next( 7 ) ), ( 5 + 9, *inc.next( 3 ) ), ( 6 + 9, *inc.next( 1 ) ),
                                  ( 7 + 9, *inc.next( 3 ) ), ( 8 + 9, *inc.next( 1 ) ), ( 1 + 18, *inc.next( 1 ) ),
                                  ( 3 + 18, *inc.next( 1 ) ), ( 4 + 18, *inc.next( 3 ) ), ( 5 + 18, *inc.next( 1 ) ),
                                  ( 7 + 18, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), range( 8 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 8 * 8, 8, 3 * 3 * 3 - 8, 12 ) )

    # Straight notch
    inc = Incrementor( 27 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, ), ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ),
                                  ( 1 + 18, *inc.next( 1 ) ), ( 4 + 18, ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 2, 2, 0, 1, 2, 2 ),
                                     fieldValues=( 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 3 * 3 * 3 + 3, 8, 6, 2 ) )

    # L-shaped notch
    inc = Incrementor( 27 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 4, *inc.next( 1 ) ), ( 7, *inc.next( 1 ) ),
                                  ( 1 + 9, *inc.next( 1 ) ), ( 4 + 9, ), ( 7 + 9, ), ( 19, *inc.next( 1 ) ), ( 22, ) )
    mesh, options = __buildTestCase( ( threeNodes, threeNodes, threeNodes ), ( 0, 1, 0, 1, 0, 1, 2, 2 ),
                                     fieldValues=( 0, 1 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 3 * 3 * 3 + 5, 8, 8, 3 ) )

    # 3x1x1 split
    inc = Incrementor( 2 * 2 * 4 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 2, *inc.next( 1 ) ), ( 5, *inc.next( 1 ) ),
                                  ( 6, *inc.next( 1 ) ), ( 1 + 8, *inc.next( 1 ) ), ( 2 + 8, *inc.next( 1 ) ),
                                  ( 5 + 8, *inc.next( 1 ) ), ( 6 + 8, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( fourNodes, twoNodes, twoNodes ), ( 0, 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 6 * 4, 3, 2 * 4, 2 ) )

    # Discarded fracture element if no node duplication.
    collocatedNodes: IDMatrix = tuple()
    mesh, options = __buildTestCase( ( threeNodes, fourNodes, fourNodes ), ( 0, ) * 8 + ( 1, 2 ) + ( 0, ) * 8,
                                     fieldValues=( 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 3 * 4 * 4, 2 * 3 * 3, 0, 0 ) )

    # Fracture on a corner
    inc = Incrementor( 3 * 4 * 4 )
    collocatedNodes: IDMatrix = ( ( 1 + 12, ), ( 4 + 12, ), ( 7 + 12, ), ( 1 + 12 * 2, *inc.next( 1 ) ),
                                  ( 4 + 12 * 2, *inc.next( 1 ) ), ( 7 + 12 * 2, ), ( 1 + 12 * 3, *inc.next( 1 ) ),
                                  ( 4 + 12 * 3, *inc.next( 1 ) ), ( 7 + 12 * 3, ) )
    mesh, options = __buildTestCase( ( threeNodes, fourNodes, fourNodes ),
                                     ( 0, ) * 6 + ( 1, 2, 1, 2, 0, 0, 1, 2, 1, 2, 0, 0 ),
                                     fieldValues=( 1, 2 ) )
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 3 * 4 * 4 + 4, 2 * 3 * 3, 9, 4 ) )

    # Generate mesh with 2 hexs, one being a standard hex, the other a 42 hex.
    inc = Incrementor( 3 * 2 * 2 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
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
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 4 * 4, 2, 4, 1 ) )

    # Split in 2 using the internal fracture description
    inc = Incrementor( 3 * 2 * 2 )
    collocatedNodes: IDMatrix = ( ( 1, *inc.next( 1 ) ), ( 1 + 3, *inc.next( 1 ) ), ( 1 + 6, *inc.next( 1 ) ),
                                  ( 1 + 9, *inc.next( 1 ) ) )
    mesh, options = __buildTestCase( ( threeNodes, twoNodes, twoNodes ),
                                     attribute=( 0, 0, 0 ),
                                     fieldValues=( 0, ),
                                     policy=FracturePolicy.INTERNAL_SURFACES )
    mesh.InsertNextCell( VTK_QUAD, toVtkIdList( ( 1, 4, 7, 10 ) ) )  # Add a fracture on the fly
    yield TestCase( inputMesh=mesh,
                    options=options,
                    collocatedNodes=collocatedNodes,
                    result=TestResult( 4 * 4, 3, 4, 1 ) )


@pytest.mark.parametrize( "test_case", __generateTestData() )
def test_generate_fracture( test_case: TestCase ):
    mainMesh, fractureMeshes = __splitMeshOnFractures( test_case.inputMesh, test_case.options )
    fractureMesh: vtkUnstructuredGrid = fractureMeshes[ 0 ]
    assert mainMesh.GetNumberOfPoints() == test_case.result.mainMeshNumPoints
    assert mainMesh.GetNumberOfCells() == test_case.result.mainMeshNumCells
    assert fractureMesh.GetNumberOfPoints() == test_case.result.fractureMeshNumPoints
    assert fractureMesh.GetNumberOfCells() == test_case.result.fractureMeshNumCells

    res = formatCollocatedNodes( fractureMesh )
    assert res == test_case.collocatedNodes
    assert len( res ) == test_case.result.fractureMeshNumPoints


def addSimplifiedFieldForCells( mesh: vtkUnstructuredGrid, field_name: str, fieldDimension: int ):
    """Reduce functionality obtained from src.geos.mesh.doctor.actions.generateFractures.__add_fields
    where the goal is to add a cell data array with incrementing values.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
        field_name (str): Name of the field to add to CellData
        fieldDimension (int): Number of components for the field.
    """
    data = mesh.GetCellData()
    n = mesh.GetNumberOfCells()
    array = numpy.ones( ( n, fieldDimension ), dtype=float )
    array = numpy.arange( 1, n * fieldDimension + 1 ).reshape( n, fieldDimension )
    vtkArray = numpy_to_vtk( array )
    vtkArray.SetName( field_name )
    data.AddArray( vtkArray )


def findBordersFacesRectilinearGrid( mesh: vtkUnstructuredGrid ) -> tuple[ FaceNodesCoords ]:
    """
              6+--------+7
              /        /|
             /        / |
           4+--------+5 |
            |        |  |
            | 2+     |  +3
            |        | /
            |        |/
           0+--------+1

    For a vtk rectilinear grid, gives the coordinates of each of its borders face nodes.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.

    Returns:
        tuple[QuadCoords]: For a rectilinear grid, returns a tuple of 6 elements.
    """
    meshBounds: tuple[ float ] = mesh.GetBounds()
    minBound: Coordinates3D = [ meshBounds[ i ] for i in range( len( meshBounds ) ) if i % 2 == 0 ]
    maxBound: Coordinates3D = [ meshBounds[ i ] for i in range( len( meshBounds ) ) if i % 2 == 1 ]
    center: Coordinates3D = mesh.GetCenter()
    faceDiag: tuple[ float ] = ( ( maxBound[ 0 ] - minBound[ 0 ] ) / 2, ( maxBound[ 1 ] - minBound[ 1 ] ) / 2,
                                 ( maxBound[ 2 ] - minBound[ 2 ] ) / 2 )
    node0: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node1: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node2: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node3: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] - faceDiag[ 2 ] )
    node4: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node5: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] - faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node6: Coordinates3D = ( center[ 0 ] - faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    node7: Coordinates3D = ( center[ 0 ] + faceDiag[ 0 ], center[ 1 ] + faceDiag[ 1 ], center[ 2 ] + faceDiag[ 2 ] )
    faces: tuple[ FaceNodesCoords ] = ( ( node0, node1, node3, node2 ), ( node4, node5, node7, node6 ),
                                        ( node0, node2, node6, node4 ), ( node1, node3, node7, node5 ),
                                        ( node0, node1, node5, node4 ), ( node2, node3, node7, node6 ) )
    return faces


def addQuad( mesh: vtkUnstructuredGrid, face: FaceNodesCoords ):
    """Adds a quad cell to each border of an unstructured mesh.

    Args:
        mesh (vtkUnstructuredGrid): Unstructured mesh.
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
def test_copyFieldsWhenSplittingMesh():
    """This test is designed to check the __copyFields method from generate_fractures,
    that will be called when using __splitMeshOnFractures method from generate_fractures.
    """
    # Generating the rectilinear grid and its quads on all borders
    x: numpy.array = numpy.array( [ 0, 1, 2 ] )
    y: numpy.array = numpy.array( [ 0, 1 ] )
    z: numpy.array = numpy.array( [ 0, 1 ] )
    xyzs: XYZ = XYZ( x, y, z )
    mesh: vtkUnstructuredGrid = buildRectilinearBlocksMesh( [ xyzs ] )
    assert mesh.GetCells().GetNumberOfCells() == 2
    borderFaces: tuple[ FaceNodesCoords ] = findBordersFacesRectilinearGrid( mesh )
    for face in borderFaces:
        addQuad( mesh, face )
    assert mesh.GetCells().GetNumberOfCells() == 8
    # Create a quad cell to represent the fracture surface.
    fracture: FaceNodesCoords = ( ( 1.0, 0.0, 0.0 ), ( 1.0, 1.0, 0.0 ), ( 1.0, 1.0, 1.0 ), ( 1.0, 0.0, 1.0 ) )
    addQuad( mesh, fracture )
    assert mesh.GetCells().GetNumberOfCells() == 9
    # Add a "TestField" array
    assert mesh.GetCellData().GetNumberOfArrays() == 0
    addSimplifiedFieldForCells( mesh, "TestField", 1 )
    assert mesh.GetCellData().GetNumberOfArrays() == 1
    assert mesh.GetCellData().GetArrayName( 0 ) == "TestField"
    testFieldValues: list[ int ] = vtk_to_numpy( mesh.GetCellData().GetArray( 0 ) ).tolist()
    assert testFieldValues == [ 1, 2, 3, 4, 5, 6, 7, 8, 9 ]
    # Split the mesh along the fracture surface which is number 9 on TestField
    options = Options( policy=FracturePolicy.INTERNAL_SURFACES,
                       field="TestField",
                       fieldValuesCombined=frozenset( map( int, [ "9" ] ) ),
                       fieldValuesPerFracture=[ frozenset( map( int, [ "9" ] ) ) ],
                       meshVtkOutput=None,
                       allFracturesVtkOutput=None )
    mainMesh, fractureMeshes = __splitMeshOnFractures( mesh, options )
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
    addSimplifiedFieldForCells( mesh, "GLOBAL_IDS_POINTS", 1 )
    with pytest.raises( ValueError ) as pytestWrappedError:
        mainMesh, fractureMeshes = __splitMeshOnFractures( mesh, options )
    assert pytestWrappedError.type == ValueError
    # Test for invalid cell field name
    mesh: vtkUnstructuredGrid = buildRectilinearBlocksMesh( [ xyzs ] )
    borderFaces: tuple[ FaceNodesCoords ] = findBordersFacesRectilinearGrid( mesh )
    for face in borderFaces:
        addQuad( mesh, face )
    addQuad( mesh, fracture )
    addSimplifiedFieldForCells( mesh, "TestField", 1 )
    addSimplifiedFieldForCells( mesh, "GLOBAL_IDS_CELLS", 1 )
    assert mesh.GetCellData().GetNumberOfArrays() == 2
    with pytest.raises( ValueError ) as pytestWrappedError:
        mainMesh, fractureMeshes = __splitMeshOnFractures( mesh, options )
    assert pytestWrappedError.type == ValueError
