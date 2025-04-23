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

from geos.mesh.processing.helpers import createMultiCellMesh
from geos.mesh.processing.MergeColocatedPoints import MergeColocatedPoints

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
    #: input mesh
    mesh: vtkUnstructuredGrid
    #: expected points
    pointsExp: npt.NDArray[ np.float64 ]
    #: expected cell point ids
    cellPtsIdsExp: tuple[ tuple[ int ] ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for path, celltype, nbPtsCell, pointsExp, cellPtsIdsExp in zip( data_filename_all,
                                                                    celltypes_all,
                                                                    nbPtsCell_all,
                                                                    points_out_all,
                                                                    cellPtsIdsExp_all,
                                                                    strict=True ):
        # all points coordinates
        ptsCoords: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, path ), dtype=float, delimiter=',' )
        # split array to get a list of coordinates per cell
        cellPtsCoords = [ ptsCoords[ i:i + nbPtsCell ] for i in range( 0, ptsCoords.shape[ 0 ], nbPtsCell ) ]
        nbCells: int = int( ptsCoords.shape[ 0 ] / nbPtsCell )
        cellTypes = nbCells * [ celltype ]
        mesh: vtkUnstructuredGrid = createMultiCellMesh( cellTypes, cellPtsCoords, False )
        assert mesh is not None, "Input mesh is undefined."
        yield TestCase( mesh, pointsExp, cellPtsIdsExp )


ids: list[ str ] = [ os.path.splitext( name )[ 0 ] for name in data_filename_all ]


@pytest.mark.parametrize( "test_case", __generate_test_data(), ids=ids )
def test_mergeColocatedPoints( test_case: TestCase ) -> None:
    """Test of MergeColocatedPoints filter..

    Args:
        test_case (TestCase): test case
    """
    filter = MergeColocatedPoints()
    filter.SetInputDataObject( 0, test_case.mesh )
    filter.Update()
    output: vtkUnstructuredGrid = filter.GetOutputDataObject( 0 )
    # tests on points
    pointsOut: vtkPoints = output.GetPoints()
    assert pointsOut is not None, "Output points is undefined."
    nbPtsExp: int = test_case.pointsExp.shape[ 0 ]
    assert pointsOut.GetNumberOfPoints() == nbPtsExp, f"Number of points is expected to be {nbPtsExp}."
    pointCoords: npt.NDArray[ np.float64 ] = vtk_to_numpy( pointsOut.GetData() )
    print( "Points coords Obs: ", pointCoords.tolist() )
    assert np.array_equal( pointCoords, test_case.pointsExp ), "Points coordinates are wrong."

    # tests on cells
    cellsOut: vtkCellArray = output.GetCells()
    assert cellsOut is not None, "Cells from output mesh are undefined."
    nbCells: int = test_case.mesh.GetNumberOfCells()
    assert cellsOut.GetNumberOfCells() == nbCells, f"Number of cells is expected to be {nbCells}."

    # check cell types
    typesInput: vtkCellTypes = vtkCellTypes()
    test_case.mesh.GetCellTypes( typesInput )
    assert typesInput is not None, "Input cell types must be defined"
    typesOutput: vtkCellTypes = vtkCellTypes()
    output.GetCellTypes( typesOutput )
    assert typesOutput is not None, "Output cell types must be defined"
    typesArrayInput: npt.NDArray[ np.int64 ] = vtk_to_numpy( typesInput.GetCellTypesArray() )
    typesArrayOutput: npt.NDArray[ np.int64 ] = vtk_to_numpy( typesOutput.GetCellTypesArray() )
    assert np.array_equal( typesArrayInput, typesArrayOutput ), "Cell types are wrong"

    for cellId in range( output.GetNumberOfCells() ):
        ptIds = vtkIdList()
        cellsOut.GetCellAtId( cellId, ptIds )
        cellsOutObs: tuple[ int ] = tuple( [ ptIds.GetId( j ) for j in range( ptIds.GetNumberOfIds() ) ] )
        print( "cellsOutObs: ", cellsOutObs )
        nbCellPts: int = len( test_case.cellPtsIdsExp[ cellId ] )
        assert ptIds is not None, "Point ids must be defined"
        assert ptIds.GetNumberOfIds() == nbCellPts, f"Cells must be defined by {nbCellPts} points."
        assert cellsOutObs == test_case.cellPtsIdsExp[ cellId ], "Cell point ids are wrong."
