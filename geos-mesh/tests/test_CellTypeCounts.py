# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
from dataclasses import dataclass
import pytest
from typing import (
    Iterator, )

from geos.mesh.model.CellTypeCounts import CellTypeCounts

from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID,
                                            VTK_HEXAHEDRON, VTK_WEDGE, VTK_VERTEX )

# inputs
nbVertex_all: tuple[ int ] = ( 3, 4, 5, 8, 10, 20 )
nbTri_all: tuple[ int ] = ( 1, 0, 3, 0, 0, 4 )
nbQuad_all: tuple[ int ] = ( 0, 1, 0, 6, 0, 3 )
nbTetra_all: tuple[ int ] = ( 0, 0, 1, 0, 4, 0 )
nbPyr_all: tuple[ int ] = ( 0, 0, 0, 0, 0, 4 )
nbWed_all: tuple[ int ] = ( 0, 0, 0, 0, 0, 2 )
nbHexa_all: tuple[ int ] = ( 0, 0, 0, 1, 0, 5 )


@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    nbVertex: tuple[ int ]
    nbTri: tuple[ int ]
    nbQuad: tuple[ int ]
    nbTetra: tuple[ int ]
    nbPyr: tuple[ int ]
    nbWed: tuple[ int ]
    nbHexa: tuple[ int ]


def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for nbVertex, nbTri, nbQuad, nbTetra, nbPyr, nbWed, nbHexa in zip( nbVertex_all,
                                                                       nbTri_all,
                                                                       nbQuad_all,
                                                                       nbTetra_all,
                                                                       nbPyr_all,
                                                                       nbWed_all,
                                                                       nbHexa_all,
                                                                       strict=True ):
        yield TestCase( nbVertex, nbTri, nbQuad, nbTetra, nbPyr, nbWed, nbHexa )


def __get_expected_counts(
    nbVertex: int,
    nbTri: int,
    nbQuad: int,
    nbTetra: int,
    nbPyr: int,
    nbWed: int,
    nbHexa: int,
) -> str:
    nbFaces: int = nbTri + nbQuad
    nbPolyhedre: int = nbTetra + nbPyr + nbHexa + nbWed
    countsExp: str = ""
    countsExp += "|                                   |              |\n"
    countsExp += "|               -                   |       -      |\n"
    countsExp += f"| **Total Number of Vertices**      | {int(nbVertex):12} |\n"
    countsExp += f"| **Total Number of Polygon**       | {int(nbFaces):12} |\n"
    countsExp += f"| **Total Number of Polyhedron**    | {int(nbPolyhedre):12} |\n"
    countsExp += f"| **Total Number of Cells**         | {int(nbPolyhedre+nbFaces):12} |\n"
    countsExp += "|               -                   |       -      |\n"
    for cellType, nb in zip( (
            VTK_TRIANGLE,
            VTK_QUAD,
    ), (
            nbTri,
            nbQuad,
    ), strict=True ):
        countsExp += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(nb):12} |\n"
    for cellType, nb in zip( ( VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON ), ( nbTetra, nbPyr, nbWed, nbHexa ),
                             strict=True ):
        countsExp += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(nb):12} |\n"
    return countsExp


def test_CellTypeCounts_init() -> None:
    """Test of CellTypeCounts .

    Args:
        test_case (TestCase): test case
    """
    counts: CellTypeCounts = CellTypeCounts()
    assert counts.getTypeCount( VTK_VERTEX ) == 0, "Number of vertices must be 0"
    assert counts.getTypeCount( VTK_TRIANGLE ) == 0, "Number of triangles must be 0"
    assert counts.getTypeCount( VTK_QUAD ) == 0, "Number of quads must be 0"
    assert counts.getTypeCount( VTK_TETRA ) == 0, "Number of tetrahedra must be 0"
    assert counts.getTypeCount( VTK_PYRAMID ) == 0, "Number of pyramids must be 0"
    assert counts.getTypeCount( VTK_WEDGE ) == 0, "Number of wedges must be 0"
    assert counts.getTypeCount( VTK_HEXAHEDRON ) == 0, "Number of hexahedra must be 0"


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_CellTypeCounts_addType( test_case: TestCase ) -> None:
    """Test of CellTypeCounts .

    Args:
        test_case (TestCase): test case
    """
    counts: CellTypeCounts = CellTypeCounts()
    for _ in range( test_case.nbVertex ):
        counts.addType( VTK_VERTEX )
    for _ in range( test_case.nbTri ):
        counts.addType( VTK_TRIANGLE )
    for _ in range( test_case.nbQuad ):
        counts.addType( VTK_QUAD )
    for _ in range( test_case.nbTetra ):
        counts.addType( VTK_TETRA )
    for _ in range( test_case.nbPyr ):
        counts.addType( VTK_PYRAMID )
    for _ in range( test_case.nbWed ):
        counts.addType( VTK_WEDGE )
    for _ in range( test_case.nbHexa ):
        counts.addType( VTK_HEXAHEDRON )

    assert counts.getTypeCount( VTK_VERTEX ) == test_case.nbVertex, f"Number of vertices must be {test_case.nbVertex}"
    assert counts.getTypeCount( VTK_TRIANGLE ) == test_case.nbTri, f"Number of triangles must be {test_case.nbTri}"
    assert counts.getTypeCount( VTK_QUAD ) == test_case.nbQuad, f"Number of quads must be {test_case.nbQuad}"
    assert counts.getTypeCount( VTK_TETRA ) == test_case.nbTetra, f"Number of tetrahedra must be {test_case.nbTetra}"
    assert counts.getTypeCount( VTK_PYRAMID ) == test_case.nbPyr, f"Number of pyramids must be {test_case.nbPyr}"
    assert counts.getTypeCount( VTK_WEDGE ) == test_case.nbWed, f"Number of wedges must be {test_case.nbWed}"
    assert counts.getTypeCount( VTK_HEXAHEDRON ) == test_case.nbHexa, f"Number of hexahedra must be {test_case.nbHexa}"


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_CellTypeCounts_setCount( test_case: TestCase ) -> None:
    """Test of CellTypeCounts .

    Args:
        test_case (TestCase): test case
    """
    counts: CellTypeCounts = CellTypeCounts()
    counts.setTypeCount( VTK_VERTEX, test_case.nbVertex )
    counts.setTypeCount( VTK_TRIANGLE, test_case.nbTri )
    counts.setTypeCount( VTK_QUAD, test_case.nbQuad )
    counts.setTypeCount( VTK_TETRA, test_case.nbTetra )
    counts.setTypeCount( VTK_PYRAMID, test_case.nbPyr )
    counts.setTypeCount( VTK_WEDGE, test_case.nbWed )
    counts.setTypeCount( VTK_HEXAHEDRON, test_case.nbHexa )

    assert counts.getTypeCount( VTK_VERTEX ) == test_case.nbVertex, f"Number of vertices must be {test_case.nbVertex}"
    assert counts.getTypeCount( VTK_TRIANGLE ) == test_case.nbTri, f"Number of triangles must be {test_case.nbTri}"
    assert counts.getTypeCount( VTK_QUAD ) == test_case.nbQuad, f"Number of quads must be {test_case.nbQuad}"
    assert counts.getTypeCount( VTK_TETRA ) == test_case.nbTetra, f"Number of tetrahedra must be {test_case.nbTetra}"
    assert counts.getTypeCount( VTK_PYRAMID ) == test_case.nbPyr, f"Number of pyramids must be {test_case.nbPyr}"
    assert counts.getTypeCount( VTK_WEDGE ) == test_case.nbWed, f"Number of wedges must be {test_case.nbWed}"
    assert counts.getTypeCount( VTK_HEXAHEDRON ) == test_case.nbHexa, f"Number of hexahedra must be {test_case.nbHexa}"


@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_CellTypeCounts_add( test_case: TestCase ) -> None:
    """Test of CellTypeCounts .

    Args:
        test_case (TestCase): test case
    """
    counts1: CellTypeCounts = CellTypeCounts()
    counts1.setTypeCount( VTK_VERTEX, test_case.nbVertex )
    counts1.setTypeCount( VTK_TRIANGLE, test_case.nbTri )
    counts1.setTypeCount( VTK_QUAD, test_case.nbQuad )
    counts1.setTypeCount( VTK_TETRA, test_case.nbTetra )
    counts1.setTypeCount( VTK_PYRAMID, test_case.nbPyr )
    counts1.setTypeCount( VTK_WEDGE, test_case.nbWed )
    counts1.setTypeCount( VTK_HEXAHEDRON, test_case.nbHexa )

    counts2: CellTypeCounts = CellTypeCounts()
    counts2.setTypeCount( VTK_VERTEX, test_case.nbVertex )
    counts2.setTypeCount( VTK_TRIANGLE, test_case.nbTri )
    counts2.setTypeCount( VTK_QUAD, test_case.nbQuad )
    counts2.setTypeCount( VTK_TETRA, test_case.nbTetra )
    counts2.setTypeCount( VTK_PYRAMID, test_case.nbPyr )
    counts2.setTypeCount( VTK_WEDGE, test_case.nbWed )
    counts2.setTypeCount( VTK_HEXAHEDRON, test_case.nbHexa )

    newcounts: CellTypeCounts = counts1 + counts2
    assert newcounts.getTypeCount( VTK_VERTEX ) == int(
        2 * test_case.nbVertex ), f"Number of vertices must be {int(2 * test_case.nbVertex)}"
    assert newcounts.getTypeCount( VTK_TRIANGLE ) == int(
        2 * test_case.nbTri ), f"Number of triangles must be {int(2 * test_case.nbTri)}"
    assert newcounts.getTypeCount( VTK_QUAD ) == int(
        2 * test_case.nbQuad ), f"Number of quads must be {int(2 * test_case.nbQuad)}"
    assert newcounts.getTypeCount( VTK_TETRA ) == int(
        2 * test_case.nbTetra ), f"Number of tetrahedra must be {int(2 * test_case.nbTetra)}"
    assert newcounts.getTypeCount( VTK_PYRAMID ) == int(
        2 * test_case.nbPyr ), f"Number of pyramids must be {int(2 * test_case.nbPyr)}"
    assert newcounts.getTypeCount( VTK_WEDGE ) == int(
        2 * test_case.nbWed ), f"Number of wedges must be {int(2 * test_case.nbWed)}"
    assert newcounts.getTypeCount( VTK_HEXAHEDRON ) == int(
        2 * test_case.nbHexa ), f"Number of hexahedra must be {int(2 * test_case.nbHexa)}"


#cpt = 0
@pytest.mark.parametrize( "test_case", __generate_test_data() )
def test_CellTypeCounts_print( test_case: TestCase ) -> None:
    """Test of CellTypeCounts .

    Args:
        test_case (TestCase): test case
    """
    counts: CellTypeCounts = CellTypeCounts()
    counts.setTypeCount( VTK_VERTEX, test_case.nbVertex )
    counts.setTypeCount( VTK_TRIANGLE, test_case.nbTri )
    counts.setTypeCount( VTK_QUAD, test_case.nbQuad )
    counts.setTypeCount( VTK_TETRA, test_case.nbTetra )
    counts.setTypeCount( VTK_PYRAMID, test_case.nbPyr )
    counts.setTypeCount( VTK_WEDGE, test_case.nbWed )
    counts.setTypeCount( VTK_HEXAHEDRON, test_case.nbHexa )
    line: str = counts.print()
    lineExp: str = __get_expected_counts( test_case.nbVertex, test_case.nbTri, test_case.nbQuad, test_case.nbTetra,
                                          test_case.nbPyr, test_case.nbWed, test_case.nbHexa )
    # global cpt
    # with open(f"meshIdcounts_{cpt}.txt", 'w') as fout:
    #     fout.write(line)
    #     fout.write("------------------------------------------------------------\n")
    #     fout.write(lineExp)
    # cpt += 1
    assert line == lineExp, "Output counts string differs from expected value."
