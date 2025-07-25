# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import os
from dataclasses import dataclass
import numpy as np
import numpy.typing as npt
import pytest
from typing import (
    Iterator, )

from geos.mesh.utils.genericHelpers import getBoundsFromPointCoords, createVertices, createMultiCellMesh

from vtkmodules.util.numpy_support import vtk_to_numpy

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellArray,
    vtkCellTypes,
    VTK_TETRA,
    VTK_HEXAHEDRON,
)

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
)

# TODO: add case whith various cell types

# inputs
data_root: str = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )
data_filename_all: tuple[ str, ...] = ( "tetra_mesh.csv", "hexa_mesh.csv" )
celltypes_all: tuple[ int ] = ( VTK_TETRA, VTK_HEXAHEDRON )
nbPtsCell_all: tuple[ int ] = ( 4, 8 )

# expected results if shared vertices
hexa_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0.0, 0.0, 0.5 ], [ 0.5, 0.0, 0.5 ], [ 0.5, 0.5, 0.5 ], [ 0.0, 0.5, 0.5 ], [ 0.0, 0.0, 1.0 ], [ 0.5, 0.0, 1.0 ],
      [ 0.5, 0.5, 1.0 ], [ 0.0, 0.5, 1.0 ], [ 1.0, 0.0, 0.5 ], [ 1.0, 0.5, 0.5 ], [ 1.0, 0.0, 1.0 ], [ 1.0, 0.5, 1.0 ],
      [ 0.0, 0.0, 0.0 ], [ 0.5, 0.0, 0.0 ], [ 0.5, 0.5, 0.0 ], [ 0.0, 0.5, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 0.5, 0.0 ],
      [ 0.5, 1.0, 0.5 ], [ 0.0, 1.0, 0.5 ], [ 0.5, 1.0, 1.0 ], [ 0.0, 1.0, 1.0 ], [ 1.0, 1.0, 0.5 ], [ 1.0, 1.0, 1.0 ],
      [ 0.5, 1.0, 0.0 ], [ 0.0, 1.0, 0.0 ], [ 1.0, 1.0, 0.0 ] ], np.float64 )
tetra_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0.0, 0.0, 0.0 ], [ 0.5, 0.0, 0.0 ], [ 0.0, 0.0, 0.5 ], [ 0.0, 0.5, 0.0 ], [ 0.5, 0.5, 0.0 ], [ 0.0, 0.5, 0.5 ],
      [ 0.0, 1.0, 0.0 ], [ 0.5, 0.0, 0.5 ], [ 1.0, 0.0, 0.0 ], [ 0.0, 0.0, 1.0 ] ], np.float64 )
points_out_all = ( tetra_points_out, hexa_points_out )

tetra_cellPtsIdsExp = [ ( 0, 1, 2, 3 ), ( 3, 4, 5, 6 ), ( 4, 1, 7, 8 ), ( 7, 2, 5, 9 ), ( 2, 5, 3, 1 ), ( 1, 5, 3, 4 ),
                        ( 1, 5, 4, 7 ), ( 7, 1, 5, 2 ) ]
hexa_cellPtsIdsExp = [ ( 0, 1, 2, 3, 4, 5, 6, 7 ), ( 1, 8, 9, 2, 5, 10, 11, 6 ), ( 12, 13, 14, 15, 0, 1, 2, 3 ),
                       ( 13, 16, 17, 14, 1, 8, 9, 2 ), ( 3, 2, 18, 19, 7, 6, 20, 21 ), ( 2, 9, 22, 18, 6, 11, 23, 20 ),
                       ( 15, 14, 24, 25, 3, 2, 18, 19 ), ( 14, 17, 26, 24, 2, 9, 22, 18 ) ]
cellPtsIdsExp_all = ( tetra_cellPtsIdsExp, hexa_cellPtsIdsExp )


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
    pointsExp: npt.NDArray[ np.float64 ]
    #: expected cell point ids
    cellPtsIdsExp: tuple[ tuple[ int ] ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for path, celltype, nbPtsCell, pointsExp0, cellPtsIdsExp0 in zip( data_filename_all,
                                                                      celltypes_all,
                                                                      nbPtsCell_all,
                                                                      points_out_all,
                                                                      cellPtsIdsExp_all,
                                                                      strict=True ):
        # all points coordinates
        ptsCoords: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, path ), dtype=float, delimiter=',' )
        # split array to get a list of coordinates per cell
        cellPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
            ptsCoords[ i:i + nbPtsCell ] for i in range( 0, ptsCoords.shape[ 0 ], nbPtsCell )
        ]
        nbCells: int = int( ptsCoords.shape[ 0 ] / nbPtsCell )
        cellTypes = nbCells * [ celltype ]
        for shared in ( False, True ):
            pointsExp: npt.NDArray[ np.float64 ] = pointsExp0 if shared else ptsCoords
            cellPtsIdsExp = cellPtsIdsExp0 if shared else [
                tuple( range( i * nbPtsCell, ( i + 1 ) * nbPtsCell, 1 ) ) for i in range( nbCells )
            ]
            yield TestCase( cellTypes, cellPtsCoords, shared, pointsExp, cellPtsIdsExp )


ids: list[ str ] = [
    os.path.splitext( name )[ 0 ] + f"_{shared}]" for name in data_filename_all for shared in ( False, True )
]


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
    nbPtsExp: int = test_case.pointsExp.shape[ 0 ]
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    assert np.array_equal( pointCoords, test_case.pointsExp ), "Points coordinates are wrong."
    assert cellPtsIds == test_case.cellPtsIdsExp, f"Cell point Ids are expected to be {test_case.cellPtsIdsExp}"


ids: list[ str ] = [
    os.path.splitext( name )[ 0 ] + f"_{shared}]" for name in data_filename_all for shared in ( False, True )
]


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
    nbPtsExp: int = test_case.pointsExp.shape[ 0 ]
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
        cellsOutObs: tuple[ int ] = tuple( [ ptIds.GetId( j ) for j in range( ptIds.GetNumberOfIds() ) ] )
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
