from typing import Any, Self
import unittest
import os
import argparse
import numpy as np
import random
import string
from geos.hdf5_wrapper import hdf5_wrapper


def random_string( N: int ) -> str:
    """Generate random string.

    Args:
        N (int): int

    Returns:
        _type_: str
    """
    return ''.join( random.choices( string.ascii_uppercase + string.ascii_lowercase + string.digits, k=N ) )


def build_test_dict( depth: int = 0, max_depth: int = 3 ) -> dict[ str, Any ]:
    """Build test dictionnary.

    Args:
        depth (int, optional): depth. Defaults to 0.
        max_depth (int, optional): maximum depth. Defaults to 3.

    Returns:
        dict[str, Any]: test dictionnary.
    """
    r = [ np.random.randint( 2, 20 ) for x in range( 5 ) ]
    test = {
        'int': np.random.randint( -1000000, 1000000 ),
        'float': np.random.random(),
        '1d_array': np.random.randn( r[ 0 ] ),
        '3d_array': np.random.randn( r[ 1 ], r[ 2 ], r[ 3 ] ),
        'string': random_string( 10 ),
        'string_array': np.array( [ random_string( x + 10 ) for x in range( r[ 4 ] ) ] )
    }
    if ( depth < max_depth ):
        test[ 'child_a' ] = build_test_dict( depth + 1, max_depth )
        test[ 'child_b' ] = build_test_dict( depth + 1, max_depth )
        test[ 'child_c' ] = build_test_dict( depth + 1, max_depth )

    return test


# Test the unit manager definitions
class Testhdf5_wrapper( unittest.TestCase ):

    @classmethod
    def setUpClass( cls ) -> None:
        """Set the tests up."""
        cls.test_dir = 'wrapper_tests'  # type: ignore[attr-defined]
        os.makedirs( cls.test_dir, exist_ok=True )  # type: ignore[attr-defined]
        cls.test_dict = build_test_dict()  # type: ignore[attr-defined]

    def compare_wrapper_dict( self, x: dict[ str, Any ], y: dict[ str, Any ] ) -> None:
        """Compare dictionnary wrapper.

        Args:
            x (dict[str, Any]): first dict
            y (dict[str, Any]): second dict

        Raises:
            Exception: Key in dictionnary
        """
        kx = x.keys()
        ky = y.keys()

        for k in kx:
            if k not in ky:
                raise Exception( 'y key not in x object (%s)' % ( k ) )

        for k in ky:
            if k not in kx:
                raise Exception( 'x key not in y object (%s)' % ( k ) )

            vx, vy = x[ k ], y[ k ]
            tx, ty = type( vx ), type( vy )
            if ( ( tx != ty )
                 and not ( isinstance( vx, ( dict, hdf5_wrapper ) ) and isinstance( vy, ( dict, hdf5_wrapper ) ) ) ):
                self.assertTrue( np.issubdtype( tx, ty ) )  # type: ignore[unreachable]

            if isinstance( vx, ( dict, hdf5_wrapper ) ):
                self.compare_wrapper_dict( vx, vy )
            else:
                if isinstance( vx, np.ndarray ):  # type: ignore[unreachable]
                    self.assertTrue( np.shape( vx ) == np.shape( vy ) )
                    self.assertTrue( ( vx == vy ).all() )
                else:
                    self.assertTrue( vx == vy )

    def test_a_insert_write( self: Self ) -> None:
        """Test insert."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_insert.hdf5' ), mode='w' )  # type: ignore[attr-defined]
        data.insert( self.test_dict )  # type: ignore[attr-defined]

    def test_b_manual_write( self: Self ) -> None:
        """Test manual write."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_manual.hdf5' ), mode='w' )  # type: ignore[attr-defined]
        for k, v in self.test_dict.items():  # type: ignore[attr-defined]
            data[ k ] = v

    def test_c_link_write( self: Self ) -> None:
        """Test of link."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_linked.hdf5' ), mode='w' )  # type: ignore[attr-defined]
        for k, v in self.test_dict.items():  # type: ignore[attr-defined]
            if ( 'child' in k ):
                child_path = os.path.join( self.test_dir, 'test_%s.hdf5' % ( k ) )  # type: ignore[attr-defined]
                data_child = hdf5_wrapper( child_path, mode='w' )
                data_child.insert( v )
                data.link( k, child_path )
            else:
                data[ k ] = v

    def test_d_compare_wrapper( self: Self ) -> None:
        """Test of compare_wrapper."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_insert.hdf5' ) )  # type: ignore[attr-defined]
        self.compare_wrapper_dict( self.test_dict, data )  # type: ignore[attr-defined]

    def test_e_compare_wrapper_copy( self: Self ) -> None:
        """Test of compare_wrapper."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_insert.hdf5' ) )  # type: ignore[attr-defined]
        tmp = data.copy()
        self.compare_wrapper_dict( self.test_dict, tmp )  # type: ignore[attr-defined]

    def test_f_compare_wrapper( self: Self ) -> None:
        """Test of compare_wrapper."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_manual.hdf5' ) )  # type: ignore[attr-defined]
        self.compare_wrapper_dict( self.test_dict, data )  # type: ignore[attr-defined]

    def test_g_compare_wrapper( self: Self ) -> None:
        """Test of compare_wrapper."""
        data = hdf5_wrapper( os.path.join( self.test_dir, 'test_linked.hdf5' ) )  # type: ignore[attr-defined]
        self.compare_wrapper_dict( self.test_dict, data )  # type: ignore[attr-defined]


def main() -> None:
    """Entry point for the geosx_xml_tools unit tests.

    Args:
        -v/--verbose (int): Output verbosity
    """
    # Parse the user arguments
    parser = argparse.ArgumentParser()
    parser.add_argument( '-v', '--verbose', type=int, help='Verbosity level', default=2 )
    args = parser.parse_args()

    # Unit manager tests
    suite = unittest.TestLoader().loadTestsFromTestCase( Testhdf5_wrapper )
    unittest.TextTestRunner( verbosity=args.verbose ).run( suite )


if __name__ == "__main__":
    main()
