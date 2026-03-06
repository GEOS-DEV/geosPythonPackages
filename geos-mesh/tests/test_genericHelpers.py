# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
import numpy as np
import numpy.typing as npt

from typing import Iterator
from dataclasses import dataclass

from geos.mesh.utils.genericHelpers import ( getBoundsFromPointCoords, createVertices, createMultiCellMesh )

from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellArray, vtkCellTypes, VTK_HEXAHEDRON, VTK_QUAD,
                                            VTK_LINE )

# TODO: add case with various cell types
## mesh 3D
meshName3D: str = "hexaMesh"
coordPts3D: list[ list[ float ] ] = [ [ -1., 0., 0. ], [ 0., 0., 0. ], [ 0., 1., 0. ], [ -1., 1., 0. ], [ -1., 0., 1. ],
                                      [ 0., 0., 1. ], [ 0., 1., 1. ], [ -1., 1., 1. ], [ 1., 0., 0. ], [ 1., 1., 0. ],
                                      [ 1., 0., 1. ], [ 1., 1., 1. ], [ 2., 0., 0. ], [ 2., 1., 0. ], [ 2., 0., 1. ],
                                      [ 2., 1., 1. ] ]
cellsMesh3D: list[ tuple[ int, ...] ] = [ ( 0, 1, 2, 3, 4, 5, 6, 7 ), ( 1, 8, 9, 2, 5, 10, 11, 6 ),
                                          ( 8, 12, 13, 9, 10, 14, 15, 11 ) ]
coordCells3D: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ coordPts3D[ i ] for i in cellMesh3D ] ) for cellMesh3D in cellsMesh3D
]
list3DCellType: list[ int ] = [ VTK_HEXAHEDRON, VTK_HEXAHEDRON, VTK_HEXAHEDRON ]

## mesh 2D
meshName2D: str = "quadMesh"
coordPts2D: list[ list[ float ] ] = [ [ 0., 0., 0. ], [ 1., 0., 0. ], [ 1., 0., 1. ], [ 0., 0., 1. ], [ 2., 0., 0. ],
                                      [ 2., 0., 1. ], [ 3., 0., 0. ], [ 3., 0., 1. ] ]
cellsMesh2D: list[ tuple[ int, ...] ] = [ ( 0, 1, 2, 3 ), ( 1, 4, 5, 2 ), ( 4, 6, 7, 5 ) ]
coordCells2D: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ coordPts2D[ i ] for i in cellMesh2D ] ) for cellMesh2D in cellsMesh2D
]
list2DCellType: list[ int ] = [ VTK_QUAD, VTK_QUAD, VTK_QUAD ]

## mesh 1D
meshName1D: str = "lineMesh"
coordPts1D: list[ list[ float ] ] = [ [ 1., 0., 0. ], [ 1., 0., 1. ], [ 1.5, 0., 0. ], [ 1.5, 0., 1. ] ]
cellsMesh1D: list[ tuple[ int, ...] ] = [ ( 0, 1 ), ( 2, 3 ) ]
coordCells1D: list[ npt.NDArray[ np.float64 ] ] = [
    np.array( [ coordPts1D[ i ] for i in cellMesh1D ] ) for cellMesh1D in cellsMesh1D
]
list1DCellType: list[ int ] = [ VTK_LINE, VTK_LINE ]

cellTypesAll = ( list3DCellType, list2DCellType, list1DCellType )
coordPtsAll = ( coordPts3D, coordPts2D, coordPts1D )
coordCellAll = ( coordCells3D, coordCells2D, coordCells1D )
cellsMeshAll = ( cellsMesh3D, cellsMesh2D, cellsMesh1D )
nbCellPtsAll = ( 8, 4, 2 )
meshNameAll = ( meshName3D, meshName2D, meshName1D )


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: cell types
    cellTypes: list[ int ]
    #: cell point coordinates
    cellPtsCoords: list[ npt.NDArray[ np.float64 ] ]
    #: share or unshare vertices
    share: bool
    #: expected points
    pointsExp: list[ list[ float ] ]
    #: expected cell point ids
    cellPtsIdsExp: list[ tuple[ int, ...] ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellTypes, cellPtsCoords, pointsExp0, cellPtsIdsExp0, nbCellPts in zip( cellTypesAll,
                                                                                coordCellAll,
                                                                                coordPtsAll,
                                                                                cellsMeshAll,
                                                                                nbCellPtsAll,
                                                                                strict=True ):
        ptsCoords: list[ list[ float ] ] = []
        for cell in cellPtsCoords:
            for pts in cell:
                ptsCoords.append( list( pts ) )
        for shared in ( True, False ):
            pointsExp = pointsExp0 if shared else ptsCoords
            cellPtsIdsExp = cellPtsIdsExp0 if shared else [
                tuple( range( i * nbCellPts, ( i + 1 ) * nbCellPts, 1 ) ) for i in range( len( cellTypes ) )
            ]
            yield TestCase( cellTypes, cellPtsCoords, shared, pointsExp, cellPtsIdsExp )


ids: list[ str ] = [ name + f"_{shared}]" for name in meshNameAll for shared in ( True, False ) ]


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_createVertices( test_case: TestCase ) -> None:
    """Test of createVertices method.

    Args:
        test_case (TestCase): test case
    """
    pointsOut: vtkPoints
    cellPtsIds: list[ tuple[ int, ...] ]
    pointsOut, cellPtsIds = createVertices( test_case.cellPtsCoords, test_case.share )
    assert pointsOut is not None, "Output points is undefined."
    assert cellPtsIds is not None, "Output cell point map is undefined."
    nbPtsExp: int = len( test_case.pointsExp )
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    assert np.array_equal( pointCoords, test_case.pointsExp ), "Points coordinates are wrong."
    assert cellPtsIds == test_case.cellPtsIdsExp, f"Cell point Ids are expected to be {test_case.cellPtsIdsExp}"


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_createMultiCellMesh( test_case: TestCase ) -> None:
    """Test of createMultiCellMesh method.

    Args:
        test_case (TestCase): test case
    """
    output: vtkUnstructuredGrid = createMultiCellMesh( test_case.cellTypes, test_case.cellPtsCoords, test_case.share )
    assert output is not None, "Output mesh is undefined."

    # tests on points
    pointsOut: vtkPoints = output.GetPoints()
    assert pointsOut is not None, "Output points is undefined."
    nbPtsExp: int = len( test_case.pointsExp )
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    assert np.array_equal( pointCoords, test_case.pointsExp ), "Points coordinates are wrong."

    # tests on cells
    cellsOut: vtkCellArray = output.GetCells()
    assert cellsOut is not None, "Cells from output mesh are undefined."
    nbCells: int = len( test_case.cellPtsCoords )
    assert cellsOut.GetNumberOfCells() == nbCells, f"Number of cells is expected to be {nbCells}."

    # check cell types
    types: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes( types )
    assert types is not None, "Cell types must be defined"
    typesArray: npt.NDArray[ np.int64 ] = vtk_to_numpy( types.GetCellTypesArray() )
    assert ( typesArray.size == 1 ) and ( typesArray[ 0 ] == test_case.cellTypes[ 0 ] ), "Cell types are wrong"

    for cellId in range( output.GetNumberOfCells() ):
        ptIds = vtkIdList()
        cellsOut.GetCellAtId( cellId, ptIds )
        cellsOutObs: tuple[ int, ...] = tuple( [ ptIds.GetId( j ) for j in range( ptIds.GetNumberOfIds() ) ] )
        nbCellPts: int = len( test_case.cellPtsIdsExp[ cellId ] )
        assert ptIds is not None, "Point ids must be defined"
        assert ptIds.GetNumberOfIds() == nbCellPts, f"Cells must be defined by {nbCellPts} points."
        assert cellsOutObs == test_case.cellPtsIdsExp[ cellId ], "Cell point ids are wrong."


def test_getBoundsFromPointCoords() -> None:
    """Test of getBoundsFromPointCoords method."""
    # input
    cellPtsCoord: list[ npt.NDArray[ np.float64 ] ] = [
        np.array( [ [ 5, 4, 3 ], [ 1, 8, 4 ], [ 2, 5, 7 ] ], dtype=float ),
        np.array( [ [ 1, 4, 6 ], [ 2, 7, 9 ], [ 4, 5, 6 ] ], dtype=float ),
        np.array( [ [ 3, 7, 8 ], [ 5, 7, 3 ], [ 4, 7, 3 ] ], dtype=float ),
        np.array( [ [ 1, 7, 2 ], [ 0, 1, 2 ], [ 2, 3, 7 ] ], dtype=float ),
    ]
    # expected output
    boundsExp: list[ float ] = [ 0., 5., 1., 8., 2., 9. ]
    boundsObs: list[ float ] = getBoundsFromPointCoords( cellPtsCoord )
    assert boundsExp == boundsObs, f"Expected bounds are {boundsExp}."
