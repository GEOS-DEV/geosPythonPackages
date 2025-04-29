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

from geos.mesh.vtk.helpers import createSingleCellMesh
from geos.mesh.processing.SplitMesh import SplitMesh

from vtkmodules.util.numpy_support import vtk_to_numpy

from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellArray, vtkCellData, vtkCellTypes, VTK_TRIANGLE,
                                            VTK_QUAD, VTK_TETRA, VTK_HEXAHEDRON, VTK_PYRAMID )

from vtkmodules.vtkCommonCore import (
    vtkPoints,
    vtkIdList,
    vtkDataArray,
)
#from vtkmodules.vtkFiltersSources import vtkCubeSource

data_root: str = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )

###############################################################
#                  create single tetra mesh                   #
###############################################################
tetra_cell_type: int = VTK_TETRA
tetra_path = "tetra_cell.csv"

# expected results
tetra_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0., 0., 0. ], [ 1., 0., 0. ], [ 0., 0., 1. ], [ 0., 1., 0. ], [ 0.5, 0., 0. ], [ 0.5, 0., 0.5 ],
      [ 0., 0., 0.5 ], [ 0., 0.5, 0. ], [ 0., 0.5, 0.5 ], [ 0.5, 0.5, 0. ] ], np.float64 )
tetra_cells_out: list[ list[ int ] ] = [ [ 0, 4, 6, 7 ], [ 7, 9, 8, 3 ], [ 9, 4, 5, 1 ], [ 5, 6, 8, 2 ], [ 6, 8, 7, 4 ],
                                         [ 4, 8, 7, 9 ], [ 4, 8, 9, 5 ], [ 5, 4, 8, 6 ] ]

###############################################################
#                  create single hexa mesh                    #
###############################################################
hexa_cell_type: int = VTK_HEXAHEDRON
hexa_path = "hexa_cell.csv"

# expected results
hexa_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ], [ 0.0, 1.0, 0.0 ], [ 0.0, 0.0, 1.0 ], [ 1.0, 0.0, 1.0 ],
      [ 1.0, 1.0, 1.0 ], [ 0.0, 1.0, 1.0 ], [ 0.5, 0.0, 0.0 ], [ 0.0, 0.5, 0.0 ], [ 0.0, 0.0, 0.5 ], [ 1.0, 0.5, 0.0 ],
      [ 1.0, 0.0, 0.5 ], [ 0.5, 1.0, 0.0 ], [ 1.0, 1.0, 0.5 ], [ 0.0, 1.0, 0.5 ], [ 0.5, 0.0, 1.0 ], [ 0.0, 0.5, 1.0 ],
      [ 1.0, 0.5, 1.0 ], [ 0.5, 1.0, 1.0 ], [ 0.5, 0.5, 0.0 ], [ 0.5, 0.0, 0.5 ], [ 0.0, 0.5, 0.5 ], [ 1.0, 0.5, 0.5 ],
      [ 0.5, 1.0, 0.5 ], [ 0.5, 0.5, 1.0 ], [ 0.5, 0.5, 0.5 ] ], np.float64 )
hexa_cells_out: list[ list[ int ] ] = [ [ 10, 21, 26, 22, 4, 16, 25, 17 ], [ 21, 12, 23, 26, 16, 5, 18, 25 ],
                                        [ 0, 8, 20, 9, 10, 21, 26, 22 ], [ 8, 1, 11, 20, 21, 12, 23, 26 ],
                                        [ 22, 26, 24, 15, 17, 25, 19, 7 ], [ 26, 23, 14, 24, 25, 18, 6, 19 ],
                                        [ 9, 20, 13, 3, 22, 26, 24, 15 ], [ 20, 11, 2, 13, 26, 23, 14, 24 ] ]

###############################################################
#                 create single pyramid mesh                  #
###############################################################
pyramid_cell_type: int = VTK_PYRAMID
pyramid_path = "pyramid_cell.csv"

# expected results
pyramid_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ], [ 0.0, 1.0, 0.0 ], [ 0.5, 0.5, 1.0 ], [ 0.5, 0.0, 0.0 ],
      [ 0.0, 0.5, 0.0 ], [ 0.25, 0.25, 0.5 ], [ 1.0, 0.5, 0.0 ], [ 0.75, 0.25, 0.5 ], [ 0.5, 1.0, 0.0 ],
      [ 0.75, 0.75, 0.5 ], [ 0.25, 0.75, 0.5 ], [ 0.5, 0.5, 0.0 ] ], np.float64 )
pyramid_cells_out: list[ list[ int ] ] = [ [ 5, 1, 8, 13, 9 ], [ 13, 8, 2, 10, 11 ], [ 3, 6, 13, 10, 12 ],
                                           [ 6, 0, 5, 13, 7 ], [ 12, 7, 9, 11, 4 ], [ 11, 9, 7, 12, 13 ],
                                           [ 7, 9, 5, 13 ], [ 9, 11, 8, 13 ], [ 11, 12, 10, 13 ], [ 12, 7, 6, 13 ] ]

###############################################################
#                create single triangle mesh                  #
###############################################################
triangle_cell_type: int = VTK_TRIANGLE
triangle_path = "triangle_cell.csv"

# expected results
triangle_points_out: npt.NDArray[ np.float64 ] = np.array( [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 0.0, 1.0, 0.0 ],
                                                             [ 0.5, 0.0, 0.0 ], [ 0.5, 0.5, 0.0 ], [ 0.0, 0.5, 0.0 ] ],
                                                           np.float64 )
triangle_cells_out: list[ list[ int ] ] = [ [ 0, 3, 5 ], [ 3, 1, 4 ], [ 5, 4, 2 ], [ 3, 4, 5 ] ]

###############################################################
#                   create single quad mesh                   #
###############################################################
quad_cell_type: int = VTK_QUAD
quad_path = "quad_cell.csv"

# expected results
quad_points_out: npt.NDArray[ np.float64 ] = np.array(
    [ [ 0.0, 0.0, 0.0 ], [ 1.0, 0.0, 0.0 ], [ 1.0, 1.0, 0.0 ], [ 0.0, 1.0, 0.0 ], [ 0.5, 0.0, 0.0 ], [ 1.0, 0.5, 0.0 ],
      [ 0.5, 1.0, 0.0 ], [ 0.0, 0.5, 0.0 ], [ 0.5, 0.5, 0.0 ] ], np.float64 )
quad_cells_out: list[ list[ int ] ] = [ [ 0, 4, 8, 7 ], [ 4, 1, 5, 8 ], [ 8, 5, 2, 6 ], [ 7, 8, 6, 3 ] ]

###############################################################
#                   create multi cell mesh                    #
###############################################################
# TODO: add tests cases composed of multi-cell meshes of various types

data_filename_all = ( tetra_path, hexa_path, pyramid_path, triangle_path, quad_path )
cell_types_all = ( tetra_cell_type, hexa_cell_type, pyramid_cell_type, triangle_cell_type, quad_cell_type )
points_out_all = ( tetra_points_out, hexa_points_out, pyramid_points_out, triangle_points_out, quad_points_out )
cells_out_all = ( tetra_cells_out, hexa_cells_out, pyramid_cells_out, triangle_cells_out, quad_cells_out )


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: VTK cell type
    cellType: int
    #: mesh
    mesh: vtkUnstructuredGrid
    #: expected new point coordinates
    pointsExp: npt.NDArray[ np.float64 ]
    #: expected new cell point ids
    cellsExp: list[ int ]


def __generate_split_mesh_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, data_path, pointsExp, cellsExp in zip( cell_types_all,
                                                         data_filename_all,
                                                         points_out_all,
                                                         cells_out_all,
                                                         strict=True ):
        ptsCoord: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, data_path ),
                                                          dtype=float,
                                                          delimiter=',' )
        mesh: vtkUnstructuredGrid = createSingleCellMesh( cellType, ptsCoord )
        yield TestCase( cellType, mesh, pointsExp, cellsExp )


ids = [ vtkCellTypes.GetClassNameFromTypeId( cellType ) for cellType in cell_types_all ]


@pytest.mark.parametrize( "test_case", __generate_split_mesh_test_data(), ids=ids )
def test_single_cell_split( test_case: TestCase ) -> None:
    """Test of SplitMesh filter with meshes composed of a single cell.

    Args:
        test_case (TestCase): test case
    """
    cellTypeName: str = vtkCellTypes.GetClassNameFromTypeId( test_case.cellType )
    filter: SplitMesh = SplitMesh()
    filter.SetInputDataObject( test_case.mesh )
    filter.Update()
    output: vtkUnstructuredGrid = filter.GetOutputDataObject( 0 )
    assert output is not None, "Output mesh is undefined."
    pointsOut: vtkPoints = output.GetPoints()
    assert pointsOut is not None, "Points from output mesh are undefined."
    assert pointsOut.GetNumberOfPoints(
    ) == test_case.pointsExp.shape[ 0 ], f"Number of points is expected to be {test_case.pointsExp.shape[0]}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    print( "Points coords: ", cellTypeName, pointCoords.tolist() )
    assert np.array_equal( pointCoords.ravel(), test_case.pointsExp.ravel() ), "Points coordinates mesh are wrong."

    cellsOut: vtkCellArray = output.GetCells()
    typesArray0: npt.NDArray[ np.int64 ] = vtk_to_numpy( output.GetDistinctCellTypesArray() )
    print( "typesArray0", cellTypeName, typesArray0 )

    assert cellsOut is not None, "Cells from output mesh are undefined."
    assert cellsOut.GetNumberOfCells() == len(
        test_case.cellsExp ), f"Number of cells is expected to be {len(test_case.cellsExp)}."
    # check cell types
    types: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes( types )
    assert types is not None, "Cell types must be defined"
    typesArray: npt.NDArray[ np.int64 ] = vtk_to_numpy( types.GetCellTypesArray() )

    print( "typesArray", cellTypeName, typesArray )
    assert ( typesArray.size == 1 ) and ( typesArray[ 0 ] == test_case.cellType ), f"All cells must be {cellTypeName}"

    for i in range( cellsOut.GetNumberOfCells() ):
        ptIds = vtkIdList()
        cellsOut.GetCellAtId( i, ptIds )
        cellsOutObs: list[ int ] = [ ptIds.GetId( j ) for j in range( ptIds.GetNumberOfIds() ) ]
        nbPtsExp: int = len( test_case.cellsExp[ i ] )
        print( "cell type", cellTypeName, i, vtkCellTypes.GetClassNameFromTypeId( types.GetCellType( i ) ) )
        print( "cellsOutObs: ", cellTypeName, i, cellsOutObs )
        assert ptIds is not None, "Point ids must be defined"
        assert ptIds.GetNumberOfIds() == nbPtsExp, f"Cells must be defined by {nbPtsExp} points."
        assert cellsOutObs == test_case.cellsExp[ i ], "Cell point ids are wrong."

    # test originalId array was created
    cellData: vtkCellData = output.GetCellData()
    assert cellData is not None, "Cell data should be defined."
    array: vtkDataArray = cellData.GetArray( "OriginalID" )
    assert array is not None, "OriginalID array should be defined."

    # test other arrays were transferred
    cellDataInput: vtkCellData = test_case.mesh.GetCellData()
    assert cellDataInput is not None, "Cell data from input mesh should be defined."
    nbArrayInput: int = cellDataInput.GetNumberOfArrays()
    nbArraySplited: int = cellData.GetNumberOfArrays()
    assert nbArraySplited == nbArrayInput + 1, f"Number of arrays should be {nbArrayInput + 1}"

    #assert False
