# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Antoine Mazuyer, Martin Lemay
import numpy as np
import numpy.typing as npt
from typing_extensions import Self
from vtkmodules.vtkCommonDataModel import ( vtkCellTypes, VTK_TRIANGLE, VTK_QUAD, VTK_TETRA, VTK_VERTEX, VTK_POLYHEDRON,
                                            VTK_POLYGON, VTK_PYRAMID, VTK_HEXAHEDRON, VTK_WEDGE,
                                            VTK_NUMBER_OF_CELL_TYPES )

__doc__ = """
CellTypeCounts stores the number of elements of each type.
"""


class CellTypeCounts():

    def __init__( self: Self ) -> None:
        """CellTypeCounts stores the number of cells of each type."""
        self._counts: npt.NDArray[ np.int64 ] = np.zeros( VTK_NUMBER_OF_CELL_TYPES, dtype=float )

    def __str__( self: Self ) -> str:
        """Overload __str__ method.

        Returns:
            str: counts as string.
        """
        return self.print()

    def __add__( self: Self, other: Self ) -> Self:
        """Addition operator.

        CellTypeCounts addition consists in suming counts.

        Args:
            other (Self): other CellTypeCounts object

        Returns:
            Self: new CellTypeCounts object
        """
        assert isinstance( other, CellTypeCounts ), "Other object must be a CellTypeCounts."
        newCounts: CellTypeCounts = CellTypeCounts()
        newCounts._counts = self._counts + other._counts
        return newCounts

    def getCounts( self: Self ) -> npt.NDArray[ np.int64 ]:
        """Get all counts.

        Returns:
            npt.NDArray[ np.int64 ]: counts
        """
        return self._counts

    def addType( self: Self, cellType: int ) -> None:
        """Increment the number of cell of input type.

        Args:
            cellType (int): cell type
        """
        self._counts[ cellType ] += 1
        self._updateGeneralCounts( cellType, 1 )

    def setTypeCount( self: Self, cellType: int, count: int ) -> None:
        """Set the number of cells of input type.

        Args:
            cellType (int): cell type
            count (int): number of cells
        """
        prevCount = self._counts[ cellType ]
        self._counts[ cellType ] = count
        self._updateGeneralCounts( cellType, count - prevCount )

    def getTypeCount( self: Self, cellType: int ) -> int:
        """Get the number of cells of input type.

        Args:
            cellType (int): cell type

        Returns:
            int: number of cells
        """
        return int( self._counts[ cellType ] )

    def reset(self: Self) ->None:
        """Reset counts."""
        self._counts = np.zeros( VTK_NUMBER_OF_CELL_TYPES, dtype=float )

    def _updateGeneralCounts( self: Self, cellType: int, count: int ) -> None:
        """Update generic type counters.

        Args:
            cellType (int): cell type
            count (int): count increment
        """
        if ( cellType != VTK_POLYGON ) and ( vtkCellTypes.GetDimension( cellType ) == 2 ):
            self._counts[ VTK_POLYGON ] += count
        if ( cellType != VTK_POLYHEDRON ) and ( vtkCellTypes.GetDimension( cellType ) == 3 ):
            self._counts[ VTK_POLYHEDRON ] += count

    def print( self: Self ) -> str:
        """Print counts string.

        Returns:
            str: counts string.
        """
        card: str = ""
        card += "|                                   |              |\n"
        card += "|               -                   |       -      |\n"
        card += f"| **Total Number of Vertices**      | {int(self._counts[VTK_VERTEX]):12} |\n"
        card += f"| **Total Number of Polygon**       | {int(self._counts[VTK_POLYGON]):12} |\n"
        card += f"| **Total Number of Polyhedron**    | {int(self._counts[VTK_POLYHEDRON]):12} |\n"
        card += f"| **Total Number of Cells**         | {int(self._counts[VTK_POLYHEDRON]+self._counts[VTK_POLYGON]):12} |\n"
        card += "|               -                   |       -      |\n"
        for cellType in ( VTK_TRIANGLE, VTK_QUAD ):
            card += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(self._counts[cellType]):12} |\n"
        for cellType in ( VTK_TETRA, VTK_PYRAMID, VTK_WEDGE, VTK_HEXAHEDRON ):
            card += f"| **Total Number of {vtkCellTypes.GetClassNameFromTypeId(cellType):<13}** | {int(self._counts[cellType]):12} |\n"
        return card
