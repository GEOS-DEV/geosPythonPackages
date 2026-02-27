# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import pytest
import numpy as np
import numpy.typing as npt

from typing import Iterator
from dataclasses import dataclass

from geos.mesh.utils.genericHelpers import createSingleCellMesh

from vtkmodules.util.numpy_support import vtk_to_numpy
from vtkmodules.vtkCommonCore import vtkPoints, vtkIdList
from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellArray, vtkCellTypes, VTK_TRIANGLE, VTK_QUAD,
                                            VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID )

tetraCellType: int = VTK_TETRA
tetraPointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 0.0, 0.0, 1.0 ],
                                                           [ 0.0, 1.0, 0.0 ] ] )

hexaCellType: int = VTK_HEXAHEDRON
hexaPointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ],
                                                          [ 0.0, 1.0, 0.0 ], [ 0.0, 0.0, 1.0 ], [ 1.0, 0.0, 1.0 ],
                                                          [ 1.0, 1.0, 1.0 ], [ 0.0, 1.0, 1.0 ] ] )

pyramidCellType: int = VTK_PYRAMID
pyrPointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ],
                                                         [ 0.0, 1.0, 0.0 ], [ 0.5, 0.5, 1.0 ] ] )

triangleCellType: int = VTK_TRIANGLE
triPointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ] ] )

quadCellType: int = VTK_QUAD
quadPointsCoords: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ],
                                                          [ 0.0, 1.0, 0.0 ] ] )

pointsCoordsAll: tuple[ npt.NDArray[ np.float64 ], ...] = ( tetraPointsCoords, hexaPointsCoords, pyrPointsCoords,
                                                        triPointsCoords, quadPointsCoords )
cellTypesAll: tuple[ int, ...] = ( tetraCellType, hexaCellType, pyramidCellType, triangleCellType, quadCellType )


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: VTK cell type
    cellType: int
    #: cell point coordinates
    cellPoints: npt.NDArray[ np.float64 ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, cellPoints in zip( cellTypesAll, pointsCoordsAll, strict=True ):
        yield TestCase( cellType, cellPoints )


ids: list[ str ] = [ vtkCellTypes.GetClassNameFromTypeId( cellType ) for cellType in cellTypesAll ]


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_createSingleCellMesh( test_case: TestCase ) -> None:
    """Test of createSingleCellMesh method.

    Args:
        test_case (TestCase): test case
    """
    cellTypeName: str = vtkCellTypes.GetClassNameFromTypeId( test_case.cellType )
    output: vtkUnstructuredGrid = createSingleCellMesh( test_case.cellType, test_case.cellPoints )

    assert output is not None, "Output mesh is undefined."
    pointsOut: vtkPoints = output.GetPoints()
    nbPtsExp: int = len( test_case.cellPoints )
    assert pointsOut is not None, "Points from output mesh are undefined."
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    assert np.array_equal( pointCoords.ravel(), test_case.cellPoints.ravel() ), "Points coordinates are wrong."

    cellsOut: vtkCellArray = output.GetCells()
    assert cellsOut is not None, "Cells from output mesh are undefined."
    assert cellsOut.GetNumberOfCells() == 1, "Number of cells is expected to be 1."
    # check cell types
    types: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes( types )
    assert types is not None, "Cell types must be defined"
    typesArray: npt.NDArray[ np.int64 ] = vtk_to_numpy( types.GetCellTypesArray() )

    assert ( typesArray.size == 1 ) and ( typesArray[ 0 ] == test_case.cellType ), f"Cell must be {cellTypeName}"

    ptIds = vtkIdList()
    cellsOut.GetCellAtId( 0, ptIds )
    cellsOutObs: list[ int ] = [ ptIds.GetId( j ) for j in range( ptIds.GetNumberOfIds() ) ]

    assert ptIds is not None, "Point ids must be defined"
    assert ptIds.GetNumberOfIds() == nbPtsExp, f"Cells must be defined by {nbPtsExp} points."
    assert cellsOutObs == list( range( nbPtsExp ) ), "Cell point ids are wrong."
