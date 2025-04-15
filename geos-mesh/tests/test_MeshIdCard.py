# SPDX-FileContributor: Martin Lemay
# SPDX-License-Identifier: Apache 2.0
# ruff: noqa: E402 # disable Module level import not at top of file
from dataclasses import dataclass
import pytest
from typing import (
    Iterator,
)

from geos.mesh.model.MeshIdCard import MeshIdCard

from vtkmodules.vtkCommonDataModel import (
    vtkCellTypes,
    VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE, VTK_VERTEX, VTK_LINE
)


# inputs
nbVertex_all: tuple[int] = (3, 4, 5, 8, 10, 20)
nbEdges_all: tuple[int]  = (3, 4, 6, 8, 12, 30)
nbTri_all: tuple[int]    = (1, 0, 3, 0,  0,  4)
nbQuad_all: tuple[int]   = (0, 1, 0, 6,  0,  3)
nbTetra_all: tuple[int]  = (0, 0, 1, 0,  4,  0)
nbPyr_all: tuple[int]    = (0, 0, 0, 0,  0,  4)
nbWed_all: tuple[int]    = (0, 0, 0, 0,  0,  2)
nbHexa_all: tuple[int]   = (0, 0, 0, 1,  0,  5)

@dataclass( frozen=True )
class TestCase:
    """Test case."""
    __test__ = False
    nbVertex: tuple[int]
    nbEdges: tuple[int]
    nbTri: tuple[int]
    nbQuad: tuple[int]
    nbTetra: tuple[int]
    nbPyr: tuple[int]
    nbWed: tuple[int]
    nbHexa: tuple[int]

def __generate_test_data() -> Iterator[ TestCase ]:
    """Generate test cases.

    Yields:
        Iterator[ TestCase ]: iterator on test cases
    """
    for nbVertex, nbEdges, nbTri, nbQuad, nbTetra, nbPyr, nbWed, nbHexa  in zip(
        nbVertex_all, nbEdges_all, nbTri_all, nbQuad_all, nbTetra_all, nbPyr_all, nbWed_all, nbHexa_all,
        strict=True):
        yield TestCase( nbVertex, nbEdges, nbTri, nbQuad, nbTetra, nbPyr, nbWed, nbHexa )

def __get_expected_card(nbVertex: int, nbEdges: int, nbTri: int, nbQuad: int, nbTetra: int, nbPyr: int, nbWed: int, nbHexa: int,) ->str:
    nbFaces: int = nbTri + nbQuad
    nbPolyhedre: int = nbTetra + nbPyr + nbHexa + nbWed
    cardExp: str = ""
    cardExp +=  "|                                   |              |\n"
    cardExp +=  "|               -                   |       -      |\n"
    cardExp += f"| **Total Number of Vertices**      | {int(nbVertex):12} |\n"
    cardExp += f"| **Total Number of Edges**         | {int(nbEdges):12} |\n"
    cardExp += f"| **Total Number of Faces**         | {int(nbFaces):12} |\n"
    cardExp += f"| **Total Number of Polyhedron**    | {int(nbPolyhedre):12} |\n"
    cardExp += f"| **Total Number of Cells**         | {int(nbPolyhedre+nbFaces):12} |\n"
    cardExp +=  "|               -                   |       -      |\n"
    for cellType, nb in zip((VTK_TRIANGLE, VTK_QUAD, ), (nbTri, nbQuad,), strict=True):
        cardExp += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(nb):12} |\n"
    for cellType, nb in zip((VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON), (nbTetra, nbPyr, nbWed, nbHexa), strict=True):
        cardExp += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(nb):12} |\n"
    return cardExp

def test_MeshIdCard_init( ) ->None:
    """Test of MeshIdCard .

    Args:
        test_case (TestCase): test case
    """
    card: MeshIdCard = MeshIdCard()
    assert card.getTypeCount(VTK_VERTEX) == 0, "Number of vertices must be 0"
    assert card.getTypeCount(VTK_LINE) == 0, "Number of edges must be 0"
    assert card.getTypeCount(VTK_TRIANGLE) == 0, "Number of triangles must be 0"
    assert card.getTypeCount(VTK_QUAD) == 0, "Number of quads must be 0"
    assert card.getTypeCount(VTK_TETRA) == 0, "Number of tetrahedra must be 0"
    assert card.getTypeCount(VTK_PYRAMID) == 0, "Number of pyramids must be 0"
    assert card.getTypeCount(VTK_WEDGE) == 0, "Number of wedges must be 0"
    assert card.getTypeCount(VTK_HEXAHEDRON) == 0, "Number of hexahedra must be 0"

@pytest.mark.parametrize( "test_case", __generate_test_data())
def test_MeshIdCard_add( test_case: TestCase ) ->None:
    """Test of MeshIdCard .

    Args:
        test_case (TestCase): test case
    """
    card: MeshIdCard = MeshIdCard()
    for _ in range(test_case.nbVertex):
        card.add(VTK_VERTEX)
    for _ in range(test_case.nbEdges):
        card.add(VTK_LINE)
    for _ in range(test_case.nbTri):
        card.add(VTK_TRIANGLE)
    for _ in range(test_case.nbQuad):
        card.add(VTK_QUAD)
    for _ in range(test_case.nbTetra):
        card.add(VTK_TETRA)
    for _ in range(test_case.nbPyr):
        card.add(VTK_PYRAMID)
    for _ in range(test_case.nbWed):
        card.add(VTK_WEDGE)
    for _ in range(test_case.nbHexa):
        card.add(VTK_HEXAHEDRON)

    assert card.getTypeCount(VTK_VERTEX) == test_case.nbVertex, f"Number of vertices must be {test_case.nbVertex}"
    assert card.getTypeCount(VTK_LINE) == test_case.nbEdges, f"Number of edges must be {test_case.nbEdges}"
    assert card.getTypeCount(VTK_TRIANGLE) == test_case.nbTri, f"Number of triangles must be {test_case.nbTri}"
    assert card.getTypeCount(VTK_QUAD) == test_case.nbQuad, f"Number of quads must be {test_case.nbQuad}"
    assert card.getTypeCount(VTK_TETRA) == test_case.nbTetra, f"Number of tetrahedra must be {test_case.nbTetra}"
    assert card.getTypeCount(VTK_PYRAMID) == test_case.nbPyr, f"Number of pyramids must be {test_case.nbPyr}"
    assert card.getTypeCount(VTK_WEDGE) == test_case.nbWed, f"Number of wedges must be {test_case.nbWed}"
    assert card.getTypeCount(VTK_HEXAHEDRON) == test_case.nbHexa, f"Number of hexahedra must be {test_case.nbHexa}"


@pytest.mark.parametrize( "test_case", __generate_test_data())
def test_MeshIdCard_setCount( test_case: TestCase ) ->None:
    """Test of MeshIdCard .

    Args:
        test_case (TestCase): test case
    """
    card: MeshIdCard = MeshIdCard()
    card.setTypeCount(VTK_VERTEX, test_case.nbVertex)
    card.setTypeCount(VTK_LINE, test_case.nbEdges)
    card.setTypeCount(VTK_TRIANGLE, test_case.nbTri)
    card.setTypeCount(VTK_QUAD, test_case.nbQuad)
    card.setTypeCount(VTK_TETRA, test_case.nbTetra)
    card.setTypeCount(VTK_PYRAMID, test_case.nbPyr)
    card.setTypeCount(VTK_WEDGE, test_case.nbWed)
    card.setTypeCount(VTK_HEXAHEDRON, test_case.nbHexa)

    assert card.getTypeCount(VTK_VERTEX) == test_case.nbVertex, f"Number of vertices must be {test_case.nbVertex}"
    assert card.getTypeCount(VTK_LINE) == test_case.nbEdges, f"Number of edges must be {test_case.nbEdges}"
    assert card.getTypeCount(VTK_TRIANGLE) == test_case.nbTri, f"Number of triangles must be {test_case.nbTri}"
    assert card.getTypeCount(VTK_QUAD) == test_case.nbQuad, f"Number of quads must be {test_case.nbQuad}"
    assert card.getTypeCount(VTK_TETRA) == test_case.nbTetra, f"Number of tetrahedra must be {test_case.nbTetra}"
    assert card.getTypeCount(VTK_PYRAMID) == test_case.nbPyr, f"Number of pyramids must be {test_case.nbPyr}"
    assert card.getTypeCount(VTK_WEDGE) == test_case.nbWed, f"Number of wedges must be {test_case.nbWed}"
    assert card.getTypeCount(VTK_HEXAHEDRON) == test_case.nbHexa, f"Number of hexahedra must be {test_case.nbHexa}"

#cpt = 0
@pytest.mark.parametrize( "test_case", __generate_test_data())
def test_MeshIdCard_print( test_case: TestCase ) ->None:
    """Test of MeshIdCard .

    Args:
        test_case (TestCase): test case
    """
    card: MeshIdCard = MeshIdCard()
    card.setTypeCount(VTK_VERTEX, test_case.nbVertex)
    card.setTypeCount(VTK_LINE, test_case.nbEdges)
    card.setTypeCount(VTK_TRIANGLE, test_case.nbTri)
    card.setTypeCount(VTK_QUAD, test_case.nbQuad)
    card.setTypeCount(VTK_TETRA, test_case.nbTetra)
    card.setTypeCount(VTK_PYRAMID, test_case.nbPyr)
    card.setTypeCount(VTK_WEDGE, test_case.nbWed)
    card.setTypeCount(VTK_HEXAHEDRON, test_case.nbHexa)
    line: str = card.print()
    lineExp: str = __get_expected_card(test_case.nbVertex, test_case.nbEdges, test_case.nbTri, test_case.nbQuad, test_case.nbTetra, test_case.nbPyr, test_case.nbWed, test_case.nbHexa)
    # global cpt
    # with open(f"meshIdCard_{cpt}.txt", 'w') as fout:
    #     fout.write(line)
    #     fout.write("------------------------------------------------------------\n")
    #     fout.write(lineExp)
    # cpt += 1
    assert line == lineExp, "Output card string differs from expected value."
