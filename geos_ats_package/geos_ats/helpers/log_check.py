from configparser import ConfigParser
import argparse
import os
from typing import Iterable


def log_check( fname: str, ignored: Iterable[ str ] ) -> None:
    """
    Check logs produced by geos_ats

    Args:
        fname (str): Path to geos_ats log
        ignored (list): List of test name failures to ignore
    """
    log = ConfigParser()
    log.read( os.path.expanduser( fname ) )

    Nignore = 0
    ignore_names = []
    Nfail = 0
    status_fail = [ 'timedout', 'halted', 'lsferror', 'failed' ]
    overall_status = 'PASSED'
    fail_names = []

    print( '=======================' )
    print( 'Integrated test results' )
    print( '=======================' )
    for status_code, tests in log[ 'Results' ].items():
        if tests:
            tmp = tests.split( ';' )
            tmp_a = [ x for x in tmp if x not in ignored ]
            tmp_b = [ x for x in tmp if x in ignored ]
            Na = len( tmp_a )
            Nb = len( tmp_b )

            if status_code in status_fail:
                if Nb:
                    print( f'{status_code}: {Na} ({Nb} ignored)' )
                else:
                    print( f'{status_code}: {Na}' )
                Nfail += Na
                fail_names.extend( tmp_a )
                Nignore += Nb
                ignore_names.extend( tmp_b )
            else:
                print( f'{status_code}: {Na+Nb}' )
        else:
            print( f'{status_code}: 0' )

    if Nignore:
        print( '=======================' )
        print( 'Ignored tests' )
        print( '=======================' )
        for name in sorted( ignore_names, key=lambda v: v.lower() ):
            print( name )

    if Nfail:
        overall_status = 'FAILED'
        print( '=======================' )
        print( 'Test failures' )
        print( '=======================' )
        for name in sorted( fail_names, key=lambda v: v.lower() ):
            print( name )

    print( '=======================' )
    print( f'Overall status: {overall_status}' )
    print( '=======================' )


def main():
    parser = argparse.ArgumentParser( description="GEOS ATS Test Log Check" )
    parser.add_argument( "log_file", type=str, help="Path to the log file" )
    parser.add_argument( "-i",
                         "--ignore-fail",
                         nargs='+',
                         default=[],
                         action="extend",
                         help='Ignore specific tests when evaluating success' )
    args = parser.parse_args()
    log_check( args.log_file, args.ignore_check )


if __name__ == '__main__':
    main()
