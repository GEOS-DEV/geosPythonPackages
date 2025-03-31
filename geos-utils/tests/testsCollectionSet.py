# SPDX-License-Identifier: Apache-2.0
# # SPDX-FileCopyrightText: Copyright 2023-2024 TotalEnergies.
# SPDX-FileContributor: Martin Lemay
# ruff: noqa: E402 # disable Module level import not at top of file
import os
import sys
import unittest

from typing_extensions import Self

from geos.utils.ConnectionSet import (
    ConnectionSet,
    ConnectionSetCollection,
)

faceId1: int = 1
faceId2: int = 2
faceId3: int = 10
cellIdSide1: dict[ int, bool ] = { 3: True, 4: False, 5: True }
cellIdSide2: dict[ int, bool ] = { 6: True, 7: False, 4: True }
cellIdSide3: dict[ int, bool ] = { 3: True, 6: False, 5: True }


class TestsConnectionSet( unittest.TestCase ):

    def test_ConnectionSetInit( self: Self ) -> None:
        """Test ConnectionSet instanciation."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        self.assertEqual( cs1.getCellIdRef(), faceId1 )
        self.assertEqual( cs1.getConnectedCellIds(), cellIdSide1 )

    def test_ConnectionSetEqual( self: Self ) -> None:
        """Test ConnectionSet equality."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide1 )
        cs3: ConnectionSet = ConnectionSet( faceId1, cellIdSide2 )

        self.assertEqual( cs1, cs1 )
        self.assertNotEqual( cs1, cs2 )
        self.assertNotEqual( cs1, cs3 )

    def test_ConnectionSetSetFaceId( self: Self ) -> None:
        """Test ConnectionSet SetFaceId method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs1.setCellIdRef( faceId2 )
        self.assertEqual( cs1.getCellIdRef(), faceId2 )

    def test_ConnectionSetSetConnectedCellIds( self: Self ) -> None:
        """Test ConnectionSet SetConnectedCellIds method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs1.setConnectedCellIds( cellIdSide2 )
        self.assertEqual( cs1.getConnectedCellIds(), cellIdSide2 )

    def test_ConnectionSetCopy( self: Self ) -> None:
        """Test ConnectionSet copy method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = cs1.copy()
        self.assertFalse( cs1 is cs2 )
        self.assertEqual( cs1, cs2 )

    def test_ConnectionSetAddConnectedCellIds( self: Self ) -> None:
        """Test ConnectionSet AddConnectedCellIds method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        expected: dict[ int, bool ] = { 3: True, 4: True, 5: True, 6: True, 7: False }
        cs1.addConnectedCells( cellIdSide2 )
        self.assertEqual( cs1.getConnectedCellIds(), expected )

    def test_ConnectionSetCollectionInit( self: Self ) -> None:
        """Test ConnectionSetCollection instanciation and add method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        self.assertEqual( len( csc ), 2 )

    def test_ConnectionSetCollectionAddMultiple( self: Self ) -> None:
        """Test ConnectionSetCollection addMultiple method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.addMultiple( ( cs1, cs2 ) )

        self.assertEqual( len( csc ), 2 )

    def test_ConnectionSetContains( self: Self ) -> None:
        """Test ConnectionSetCollection __contains__ method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs3: ConnectionSet = ConnectionSet( faceId3, cellIdSide1 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        self.assertTrue( cs1 in csc )
        self.assertTrue( cs2 in csc )
        self.assertTrue( cs3 not in csc )

    def test_ConnectionSetContainsCellIdRef( self: Self ) -> None:
        """Test ConnectionSetCollection containsCellIdRef method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        self.assertTrue( csc.containsCellIdRef( faceId1 ) )
        self.assertTrue( csc.containsCellIdRef( faceId2 ) )
        self.assertFalse( csc.containsCellIdRef( faceId3 ) )

    def test_ConnectionSetContainsEqual( self: Self ) -> None:
        """Test ConnectionSetCollection containsEqual method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs3: ConnectionSet = ConnectionSet( faceId1, cellIdSide3 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        self.assertTrue( csc.containsEqual( cs1 ) )
        csc.replace( cs3 )

        self.assertTrue( not csc.containsEqual( cs1 ) )
        self.assertTrue( csc.containsEqual( cs3 ) )

    def test_ConnectionSetReplace( self: Self ) -> None:
        """Test ConnectionSetCollection replace method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs3: ConnectionSet = ConnectionSet( faceId1, cellIdSide3 )

        print( cs1 )
        print( cs2 )
        print( cs3 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )
        print( csc )
        csc.replace( cs3 )
        print( csc )
        self.assertTrue( not csc.containsEqual( cs1 ) )
        self.assertTrue( cs2 in csc )
        self.assertTrue( cs3 in csc )

    def test_ConnectionSetGet( self: Self ) -> None:
        """Test ConnectionSetCollection get method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        self.assertEqual( csc.get( faceId1 ), cs1 )
        self.assertTrue( csc.get( faceId3 ) is None )

    def test_ConnectionSetDiscard( self: Self ) -> None:
        """Test ConnectionSetCollection discard method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        csc.discard( cs1 )

        self.assertTrue( cs1 not in csc )
        self.assertTrue( cs2 in csc )

    def test_ConnectionSetDiscardFaceId( self: Self ) -> None:
        """Test ConnectionSetCollection discardFaceId method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        csc.discardCellIdRef( faceId1 )

        self.assertTrue( cs1 not in csc )
        self.assertTrue( cs2 in csc )

    def test_ConnectionSetUpdate( self: Self ) -> None:
        """Test ConnectionSetCollection update method."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs3: ConnectionSet = ConnectionSet( faceId3, cellIdSide3 )
        cs4: ConnectionSet = ConnectionSet( faceId2, cellIdSide3 )

        # expected cs2 + cs4
        cs5: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs5.addConnectedCells( cellIdSide3 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )

        csc.update( cs3 )
        csc.update( cs4 )

        self.assertTrue( cs1 in csc )
        self.assertTrue( cs3 in csc )
        self.assertTrue( cs5 in csc )

    def tests_GetReversedConnectionSetCollection( self: Self ) -> None:
        """Test ConnectionSetCollection getReversedConnectionSetCollection."""
        cs1: ConnectionSet = ConnectionSet( faceId1, cellIdSide1 )
        cs2: ConnectionSet = ConnectionSet( faceId2, cellIdSide2 )
        cs3: ConnectionSet = ConnectionSet( faceId3, cellIdSide3 )
        cs4: ConnectionSet = ConnectionSet( faceId2, cellIdSide3 )

        csc: ConnectionSetCollection = ConnectionSetCollection()
        csc.add( cs1 )
        csc.add( cs2 )
        csc.update( cs3 )
        csc.update( cs4 )

        print( csc )
        # expected results
        cs21: ConnectionSet = ConnectionSet( 3, { faceId1: True, faceId2: True, faceId3: True } )
        cs22: ConnectionSet = ConnectionSet( 4, { faceId1: False, faceId2: True } )
        cs23: ConnectionSet = ConnectionSet( 5, { faceId1: True, faceId3: True } )
        cs24: ConnectionSet = ConnectionSet( 6, { faceId2: True, faceId3: False } )
        cs25: ConnectionSet = ConnectionSet( 7, { faceId2: False } )
        expected: ConnectionSetCollection = ConnectionSetCollection()
        expected.addMultiple( ( cs21, cs22, cs23, cs24, cs25 ) )

        obtained: ConnectionSetCollection = csc.getReversedConnectionSetCollection()
        self.assertEqual( obtained, expected )
