from configparser import ConfigParser
import argparse
import os


def log_check( fname ):
    log = ConfigParser()
    log.read( os.path.expanduser( fname ) )

    Nfail = 0
    status_fail = [ 'timedout', 'halted', 'lsferror', 'failed' ]
    overall_status = 'PASSED'
    fail_names = []

    print( '=======================' )
    print( 'Integrated test results' )
    print( '=======================' )
    for status_code, tests in log[ 'Results' ].items():
        tmp = tests.split( ';' )
        N = len( tmp )
        print( f'{status_code}: {N}' )
        if status_code in status_fail:
            Nfail += Nfail
            fail_names.extend( tmp )

    if Nfail:
        overall_status = 'FAILED'
        print( '=======================' )
        print( 'Test failures' )
        print( '=======================' )
        for name in fail_names:
            print( name )

    print( '=======================' )
    print( f'Overall status: {overall_status}' )
    print( '=======================' )


def main():
    parser = argparse.ArgumentParser( description="GEOS ATS Test Log Check" )
    parser.add_argument( "log_file", type=str, help="Path to the log file" )
    args = parser.parse_args()
    log_check( args.log_file )


if __name__ == '__main__':
    main()
