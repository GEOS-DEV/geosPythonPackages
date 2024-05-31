from configparser import ConfigParser
import argparse
import os
import yaml
import socket
from typing import Iterable


def check_yaml( yaml_file: str ) -> Iterable[ str ]:
    """
    Check the integrated test yaml file for tests to ignore

    Args:
        yaml_file (str): Integrated test yaml file

    Returns:
        list: List of tests to ignore
    """
    hostname = socket.gethostname()
    ignored_tests = []
    with open( yaml_file ) as f:
        test_options = yaml.safe_load( f )
        allow_fail = test_options.get( 'allow_fail', {} )
        for k, v in allow_fail.items():
            if ( k in hostname ) or ( k == 'all' ):
                if v:
                    ignored_tests.extend( [ x.strip() for x in v.split( ',' ) ] )

    return ignored_tests


def log_check( fname: str, yaml_file: str, ignored: Iterable[ str ] ) -> None:
    """
    Check logs produced by geos_ats

    Args:
        fname (str): Path to geos_ats log
        yaml_file (str): Integrated test yaml file
        ignored (list): List of test name failures to ignore
    """
    log = ConfigParser()
    log.read( os.path.expanduser( fname ) )

    if yaml_file:
        yaml_file = os.path.expanduser( yaml_file )
        if os.path.isfile( yaml_file ):
            ignored.extend( check_yaml( yaml_file ) )

    Nignore = 0
    ignore_names = []
    Nfail = 0
    Nfailrun = 0
    status_fail = [ 'timedout', 'halted', 'lsferror', 'failed', 'failrun' ]
    overall_status = 'PASSED'
    fail_names = []
    failrun_names = []

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
                Nignore += Nb
                ignore_names.extend( tmp_b )
                if ( status_code == 'failrun' ):
                    Nfailrun += Na
                    failrun_names.extend( tmp_a )
                else:
                    Nfail += Na
                    fail_names.extend( tmp_a )

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

    if Nfailrun:
        overall_status = 'FAIL RUN'
        print( '=======================' )
        print( 'Run failures' )
        print( '=======================' )
        for name in sorted( failrun_names, key=lambda v: v.lower() ):
            print( name )

    print( '=======================' )
    print( f'Overall status: {overall_status}' )
    print( '=======================' )


def main():
    parser = argparse.ArgumentParser( description="GEOS ATS Test Log Check" )
    parser.add_argument( "log_file", type=str, help="Path to the log file" )
    parser.add_argument( "-y", "--yaml-file", type=str, help="Integrated test yaml file", default='' )
    parser.add_argument( "-i",
                         "--ignore-fail",
                         nargs='+',
                         default=[],
                         action="extend",
                         help='Ignore specific tests when evaluating success' )
    args = parser.parse_args()
    log_check( args.log_file, args.yaml_file, args.ignore_fail )


if __name__ == '__main__':
    main()
