# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
import copy
from collections.abc import MutableSet
from typing import Iterable, Optional

from typing_extensions import Iterator, Self

__doc__ = """ Defines connection set and connection set collection data
structures.
"""


class ConnectionSet:

    def __init__( self: Self, cellIdRef: int, connectedCellIds: dict[ int, bool ] ) -> None:
        """Define connection set data structure.

        A ConnectionSet stores information of connection between a reference
        cell and adjacent cells. Cell information relies on unique ids, and
        each connected cell is associated with a side according to connection
        face normal vector.

        Args:
            cellIdRef (int): reference cell id.
            connectedCellIds (int): map of connected cell ids with the side.
        """
        self.m_cellIdRef: int = cellIdRef
        self.m_connectedCellIds: dict[ int, bool ] = copy.deepcopy( connectedCellIds )

    def __repr__( self: Self ) -> str:
        """Get the string description of the FaceConnectionSet.

        Returns:
         str: string description of the FaceConnectionSet.
        """
        return f"{self.m_cellIdRef} - {set(self.m_connectedCellIds.keys())}"

    def __eq__( self: Self, other: object ) -> bool:
        """Equality operator.

        Equality means equality of cellIdRef and equality of connected cell ids.

        Args:
            other (object): another object.

        Returns:
            bool: True if FaceConnectionSet are equal, False otherwise.
        """
        if not isinstance( other, type( self ) ):
            return False

        connectedCellIds1 = set( self.m_connectedCellIds.keys() )
        connectedCellIds2 = set( other.m_connectedCellIds.keys() )
        if len( connectedCellIds1 ) != len( connectedCellIds2 ):
            return False
        return ( self.m_cellIdRef == other.m_cellIdRef ) and all(
            v1 == v2 for v1, v2 in zip( connectedCellIds1, connectedCellIds2 ) )

    def __hash__( self: Self ) -> int:
        """Define hash method.

        Returns:
            int: hash value.
        """
        return hash( ( self.m_cellIdRef, frozenset( self.m_connectedCellIds.keys() ) ) )

    def getCellIdRef( self: Self ) -> int:
        """Get the reference cell id.

        Returns:
            int: reference cell id.
        """
        return self.m_cellIdRef

    def setCellIdRef( self: Self, cellIdRef: int ) -> None:
        """Set the reference cell id.

        Args:
            cellIdRef (int): reference cell id.
        """
        self.m_cellIdRef = cellIdRef

    def getConnectedCellIds( self: Self ) -> dict[ int, bool ]:
        """Get connected cell ids.

        Returns:
            int: map of connected cell ids with side.
        """
        return self.m_connectedCellIds

    def setConnectedCellIds( self: Self, connectedCellIds: dict[ int, bool ] ) -> None:
        """Set the connected cell ids.

        Args:
            connectedCellIds (dict[int, bool]): map of connected cell ids with
                side.
        """
        self.m_connectedCellIds = copy.deepcopy( connectedCellIds )

    def addConnectedCells( self: Self, connectedCellsToAdd: dict[ int, bool ] ) -> None:
        """Add connected cells to the existing map of connected cells.

        The addConnectedCells() method adds element(s) to the dictionary if the
        cell Id is not in the dictionary. If the cell Id is in the dictionary,
        it updates the cell Id with the new side value.

        Args:
            connectedCellsToAdd (dict[int, bool]): connected cells to add.
        """
        self.m_connectedCellIds.update( connectedCellsToAdd )

    def copy( self: Self ) -> Self:
        """Create a deep copy of self.

        Returns:
            ConnectionSet: copy of ConnectionSet
        """
        return ConnectionSet( self.getCellIdRef(), self.getConnectedCellIds() )  # type: ignore  # noqa: F821


class ConnectionSetCollection( MutableSet ):

    def __init__( self: Self ) -> None:
        """Define a collection of ConnectionSet.

        Because ConnectionSet relies on cell unique id, the collection imposes
        uniqueness of reference cell id.
        """
        self._items: set[ ConnectionSet ] = set()

    def __contains__( self: Self, item: object ) -> bool:
        """Redefine contains method.

        Args:
            item (object): object to test

        Returns:
            bool: True if the object is in the collection, False otherwise.
        """
        if not isinstance( item, ConnectionSet ):
            return False
        return any( obj.getCellIdRef() == item.getCellIdRef() for obj in self._items )

    def __iter__( self: Self ) -> Iterator[ ConnectionSet ]:
        """Iterator on the collection.

        Returns:
            Iterator[ConnectionSet]: Iterator of ConnectionSet.
        """
        return iter( self._items )

    def __len__( self: Self ) -> int:
        """Get the number of elements of the collection.

        Returns:
            int: number of elements
        """
        return len( self._items )

    def containsEqual( self: Self, item: ConnectionSet ) -> bool:
        """Test if a ConnectionSet is present in the collection.

        Both th reference cell id and connected cell dictionnary must match the input
        ConnectionSet.

        Args:
            item (ConnectionSet): ConnectionSet to add.
        """
        connectionSet: Optional[ ConnectionSet ] = self.get( item.getCellIdRef() )
        return ( connectionSet is not None ) and ( connectionSet == item )

    def containsCellIdRef( self: Self, cellIdRef: int ) -> bool:
        """Test if a ConnectionSet with cellIdRef is present in the collection.

        Args:
            cellIdRef (int): reference cell id

        Returns:
            bool: True if a ConnectionSet is present, False otherwise.
        """
        connectionSet: Optional[ ConnectionSet ] = self.get( cellIdRef )
        return connectionSet is not None

    def add( self: Self, item: ConnectionSet ) -> None:
        """Add a ConnectionSet to the collection.

        Args:
            item (ConnectionSet): ConnectionSet to add.
        """
        assert item not in self, f"ConnectionSet {item} is already in the collection."
        self._items.add( item.copy() )

    def addMultiple( self: Self, items: Iterable[ ConnectionSet ] ) -> None:
        """Add an iterable of ConnectionSet to the collection.

        Args:
            items (Iterable[ConnectionSet]): list of ConnectionSet to add.
        """
        for item in items:
            self.add( item )

    def replace( self: Self, item: ConnectionSet ) -> None:
        """Replace a ConnectionSet if another one with the same cellIdRef exists.

        Args:
            item (ConnectionSet): ConnectionSet to add.
        """
        self.discardCellIdRef( item.getCellIdRef() )
        self.add( item )

    def update( self: Self, item: ConnectionSet ) -> None:
        """Update or add a ConnectionSet to the collection.

        Args:
            item (ConnectionSet): ConnectionSet
        """
        connectionSet: Optional[ ConnectionSet ] = self.get( item.getCellIdRef() )
        if connectionSet is None:
            self.add( item )
        else:
            connectionSet.addConnectedCells( item.getConnectedCellIds() )

    def get( self: Self, cellIdRef: int ) -> Optional[ ConnectionSet ]:
        """Get ConnectionSet from reference cell id.

        Args:
            cellIdRef (int): reference cell id

        Returns:
            Optional[ConnectionSet]: ConnectionSet with cellIdRef.
        """
        for connectionSet in self._items:
            if connectionSet.getCellIdRef() == cellIdRef:
                return connectionSet
        return None

    def discard( self: Self, item: ConnectionSet ) -> None:
        """Remove a ConnectionSet to the collection.

        ConnectionSet is removed if both reference cell id and connected cell dictionnary
        match an element of the collection.

        Args:
            item (ConnectionSet): ConnectionSet to remove.
        """
        self._items.discard( item )

    def discardCellIdRef( self: Self, cellIdRef: int ) -> None:
        """Remove a ConnectionSet to the collection using the reference cell id.

        Args:
            cellIdRef (int): reference cell id to remove.
        """
        item: Optional[ ConnectionSet ] = self.get( cellIdRef )
        if item is not None:
            self.discard( item )

    def __repr__( self: Self ) -> str:
        """Representation of ConnectionSetCollection.

        Returns:
            str: representation.
        """
        return f"{self.__class__.__name__}({list(self._items)})"

    def getReversedConnectionSetCollection( self: Self ) -> Self:
        """Get the set of reversed connection set.

        Returns:
            ConnectionSetCollection: reversed collection of ConnectionSet
        """
        connectionSetCollection: ConnectionSetCollection = ConnectionSetCollection()
        for face2VolumeCS in self._items:
            for cellId, side in face2VolumeCS.getConnectedCellIds().items():
                newConnectionSet: ConnectionSet = ConnectionSet( cellId, { face2VolumeCS.getCellIdRef(): side } )
                connectionSetCollection.update( newConnectionSet )
        return connectionSetCollection  # type: ignore  # noqa: F821
