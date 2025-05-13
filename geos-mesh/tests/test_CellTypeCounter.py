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

from geos.mesh.vtk.helpers import createSingleCellMesh, createMultiCellMesh
from geos.mesh.stats.CellTypeCounter import CellTypeCounter
from geos.mesh.model.CellTypeCounts import CellTypeCounts

from vtkmodules.vtkCommonDataModel import (
    vtkUnstructuredGrid,
    vtkCellTypes,
    vtkCell,
    VTK_TRIANGLE,
    VTK_QUAD,
    VTK_TETRA,
    VTK_VERTEX,
    VTK_POLYHEDRON,
    VTK_POLYGON,
    VTK_PYRAMID,
    VTK_HEXAHEDRON,
    VTK_WEDGE,
)

#from vtkmodules.vtkFiltersSources import vtkCubeSource

data_root: str = os.path.join( os.path.dirname( os.path.abspath( __file__ ) ), "data" )

filename_all: tuple[ str, ...] = ( "triangle_cell.csv", "quad_cell.csv", "tetra_cell.csv", "pyramid_cell.csv",
                                   "hexa_cell.csv" )
cellType_all: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON )

filename_all2: tuple[ str, ...] = ( "tetra_mesh.csv", "hexa_mesh.csv" )
cellType_all2: tuple[ int, ...] = ( VTK_TETRA, VTK_HEXAHEDRON )
nbPtsCell_all2: tuple[ int ] = ( 4, 8 )


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    #: mesh
    mesh: vtkUnstructuredGrid


def __generate_test_data_single_cell() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, filename in zip( cellType_all, filename_all, strict=True ):
        ptsCoord: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, filename ),
                                                          dtype=float,
                                                          delimiter=',' )
        mesh: vtkUnstructuredGrid = createSingleCellMesh( cellType, ptsCoord )
        yield TestCase( mesh )


ids: list[ str ] = [ vtkCellTypes.GetClassNameFromTypeId( cellType ) for cellType in cellType_all ]


@pytest.mark.parametrize( "test_case", __generate_test_data_single_cell(), ids=ids )
def test_CellTypeCounter_single( test_case: TestCase ) -> None:
    """Test of CellTypeCounter filter.

    Args:
        test_case (TestCase): test case
    """
    filter: CellTypeCounter = CellTypeCounter()
    filter.SetInputDataObject( test_case.mesh )
    filter.Update()
    countsObs: CellTypeCounts = filter.GetCellTypeCountsObject()
    assert countsObs is not None, "CellTypeCounts is undefined"

    assert countsObs.getTypeCount( VTK_VERTEX ) == test_case.mesh.GetNumberOfPoints(
    ), f"Number of vertices should be {test_case.mesh.GetNumberOfPoints()}"

    # compute counts for each type of cell
    elementTypes: tuple[ int ] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE )
    counts: npt.NDArray[ np.int64 ] = np.zeros( len( elementTypes ) )
    for i in range( test_case.mesh.GetNumberOfCells() ):
        cell: vtkCell = test_case.mesh.GetCell( i )
        index: int = elementTypes.index( cell.GetCellType() )
        counts[ index ] += 1
    # check cell type counts
    for i, elementType in enumerate( elementTypes ):
        assert int(
            countsObs.getTypeCount( elementType )
        ) == counts[ i ], f"The number of {vtkCellTypes.GetClassNameFromTypeId(elementType)} should be {counts[i]}."

    nbPolygon: int = counts[ 0 ] + counts[ 1 ]
    nbPolyhedra: int = np.sum( counts[ 2: ] )
    assert int( countsObs.getTypeCount( VTK_POLYGON ) ) == nbPolygon, f"The number of faces should be {nbPolygon}."
    assert int(
        countsObs.getTypeCount( VTK_POLYHEDRON ) ) == nbPolyhedra, f"The number of polyhedra should be {nbPolyhedra}."


def __generate_test_data_multi_cell() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for cellType, filename, nbPtsCell in zip( cellType_all2, filename_all2, nbPtsCell_all2, strict=True ):
        ptsCoords: npt.NDArray[ np.float64 ] = np.loadtxt( os.path.join( data_root, filename ),
                                                           dtype=float,
                                                           delimiter=',' )
        # split array to get a list of coordinates per cell
        cellPtsCoords: list[ npt.NDArray[ np.float64 ] ] = [
            ptsCoords[ i:i + nbPtsCell ] for i in range( 0, ptsCoords.shape[ 0 ], nbPtsCell )
        ]
        nbCells: int = int( ptsCoords.shape[ 0 ] / nbPtsCell )
        cellTypes = nbCells * [ cellType ]
        mesh: vtkUnstructuredGrid = createMultiCellMesh( cellTypes, cellPtsCoords, True )
        yield TestCase( mesh )


ids2: list[ str ] = [ os.path.splitext( name )[ 0 ] for name in filename_all2 ]


@pytest.mark.parametrize( "test_case", __generate_test_data_multi_cell(), ids=ids2 )
def test_CellTypeCounter_multi( test_case: TestCase ) -> None:
    """Test of CellTypeCounter filter.

    Args:
        test_case (TestCase): test case
    """
    filter: CellTypeCounter = CellTypeCounter()
    filter.SetInputDataObject( test_case.mesh )
    filter.Update()
    countsObs: CellTypeCounts = filter.GetCellTypeCountsObject()
    assert countsObs is not None, "CellTypeCounts is undefined"

    assert countsObs.getTypeCount( VTK_VERTEX ) == test_case.mesh.GetNumberOfPoints(
    ), f"Number of vertices should be {test_case.mesh.GetNumberOfPoints()}"

    # compute counts for each type of cell
    elementTypes: tuple[ int ] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE )
    counts: npt.NDArray[ np.int64 ] = np.zeros( len( elementTypes ), dtype=int )
    for i in range( test_case.mesh.GetNumberOfCells() ):
        cell: vtkCell = test_case.mesh.GetCell( i )
        index: int = elementTypes.index( cell.GetCellType() )
        counts[ index ] += 1
    # check cell type counts
    for i, elementType in enumerate( elementTypes ):
        assert int(
            countsObs.getTypeCount( elementType )
        ) == counts[ i ], f"The number of {vtkCellTypes.GetClassNameFromTypeId(elementType)} should be {counts[i]}."

    nbPolygon: int = counts[ 0 ] + counts[ 1 ]
    nbPolyhedra: int = np.sum( counts[ 2: ] )
    assert int( countsObs.getTypeCount( VTK_POLYGON ) ) == nbPolygon, f"The number of faces should be {nbPolygon}."
    assert int(
        countsObs.getTypeCount( VTK_POLYHEDRON ) ) == nbPolyhedra, f"The number of polyhedra should be {nbPolyhedra}."
