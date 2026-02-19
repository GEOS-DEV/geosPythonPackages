# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
import numpy as np
import numpy.typing as npt
import pytest
from typing import Any

from geos.processing.pre_processing.CellTypeCounterEnhanced import CellTypeCounterEnhanced
from geos.mesh.model.CellTypeCounts import CellTypeCounts

from vtkmodules.vtkCommonDataModel import ( vtkUnstructuredGrid, vtkCellTypes, vtkCell, VTK_TRIANGLE, VTK_QUAD,
                                            VTK_TETRA, VTK_VERTEX, VTK_POLYHEDRON, VTK_POLYGON, VTK_PYRAMID,
                                            VTK_HEXAHEDRON, VTK_WEDGE )


@pytest.mark.parametrize(
    "meshName",
    [
        ( "extractAndMergeVolume" ),  # Tri mesh
        ( "extractAndMergeFault" ),  # Hex mesh
        ( "quads2_tris4" ),  # Quad and Tri mesh
        ( "hexs3_tets36_pyrs18" ),  # Hex, Tet and Pyr mesh
    ] )
def test_CellTypeCounterEnhancedRealCase(
    dataSetTest: Any,
    meshName: str,
) -> None:
    """Test of CellTypeCounterEnhanced filter."""
    mesh: vtkUnstructuredGrid = dataSetTest( meshName )
    cellTypeCounterEnhancedFilter: CellTypeCounterEnhanced = CellTypeCounterEnhanced( mesh )
    cellTypeCounterEnhancedFilter.applyFilter()
    countsObs: CellTypeCounts = cellTypeCounterEnhancedFilter.GetCellTypeCountsObject()

    assert countsObs is not None, "CellTypeCounts is undefined"
    assert countsObs.getTypeCount(
        VTK_VERTEX ) == mesh.GetNumberOfPoints(), f"Number of vertices should be { mesh.GetNumberOfPoints() }"

    # compute counts for each type of cell
    elementTypes: tuple[ int, ...] = ( VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE )
    counts: npt.NDArray[ np.int64 ] = np.zeros( len( elementTypes ), dtype=int )
    for i in range( mesh.GetNumberOfCells() ):
        cell: vtkCell = mesh.GetCell( i )
        index: int = elementTypes.index( cell.GetCellType() )
        counts[ index ] += 1
    # check cell type counts
    for i, elementType in enumerate( elementTypes ):
        assert int( countsObs.getTypeCount( elementType ) ) == counts[
            i ], f"The number of { vtkCellTypes.GetClassNameFromTypeId( elementType ) } should be { counts[ i ] }."

    nbPolygon: int = counts[ 0 ] + counts[ 1 ]
    nbPolyhedra: int = np.sum( counts[ 2: ], dtype=int )
    assert int( countsObs.getTypeCount( VTK_POLYGON ) ) == nbPolygon, f"The number of faces should be { nbPolygon }."
    assert int(
        countsObs.getTypeCount( VTK_POLYHEDRON ) ) == nbPolyhedra, f"The number of polyhedra should be { nbPolyhedra }."
