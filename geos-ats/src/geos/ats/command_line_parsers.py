import argparse
import os

action_options = {
    "run": "execute the test cases that previously did not pass.",
    "rerun": "ignore the status from previous runs, and rerun the tests.",
    "continue": "continue running, ignoring tests that have either passed or failed",
    "list": "list the test cases.",
    "commands": "display the command line of each test step.",
    "reset": "Removes Failed status from any test case.",
    "clean": "remove files generated by the test cases.",
    "veryclean": "does a clean plus removes non testcase created files (TestLog, results, ...)",
    "check": "skip the action steps and just run the check steps.",
    "rebaseline": "rebaseline the testcases from a previous run.",
    "rebaselinefailed": "rebaseline only failed testcases from a previous run.",
    "report": "generate a text or html report, see config for the reporting options.",
    "pack_baselines": "Pack baselines into archive",
    "upload_baselines": "Upload baselines to bucket",
    "download_baselines": "Download baselines from bucket",
}

check_options = {
    "all": "run all checks",
    "none": "no additional checking",
    "stopcheck": "check the stop time and stop cycle",
    "curvecheck": "check the ultra curves",
    "restartcheck": "check the restart file",
}

verbose_options = {
    "debug": "Show detailed log information",
    "info": "Show typical log information",
    "warnings": "Show warnings only",
    "errors": "Show errors only",
}


def build_command_line_parser():
    parser = argparse.ArgumentParser( description="Runs GEOS integrated tests" )

    parser.add_argument( "geos_bin_dir", type=str, help="GEOS binary directory." )

    parser.add_argument( "ats_target", type=str, help="ats file" )

    parser.add_argument( "-w", "--workingDir", type=str, help="Root working directory" )

    parser.add_argument( "-b", "--baselineDir", type=str, help="Root baseline directory" )

    parser.add_argument( "-y", "--yaml", type=str, help="Path to YAML config file", default='' )

    parser.add_argument( "--baselineArchiveName", type=str, help="Baseline archive name", default='' )
    parser.add_argument( "--baselineCacheDirectory", type=str, help="Baseline cache directory", default='' )

    parser.add_argument( "-d",
                         "--delete-old-baselines",
                         action="store_true",
                         default=False,
                         help="Automatically delete old baselines" )

    parser.add_argument( "-u",
                         "--update-baselines",
                         action="store_true",
                         default=False,
                         help="Force baseline file update" )

    action_names = ','.join( action_options.keys() )
    parser.add_argument( "-a", "--action", type=str, default="run", help=f"Test actions options ({action_names})" )

    check_names = ','.join( check_options.keys() )
    parser.add_argument( "-c", "--check", type=str, default="all", help=f"Test check options ({check_names})" )

    verbosity_names = ','.join( verbose_options.keys() )
    parser.add_argument( "-v",
                         "--verbose",
                         type=str,
                         default="info",
                         help=f"Log verbosity options ({verbosity_names})" )

    parser.add_argument( "-r",
                         "--restartCheckOverrides",
                         nargs='+',
                         action='append',
                         help='Restart check parameter override (name value)',
                         default=[] )

    parser.add_argument(
        "--salloc",
        default=True,
        help="Used by the chaosM machine to first allocate nodes with salloc, before running the tests" )

    parser.add_argument(
        "--sallocoptions",
        type=str,
        default="",
        help="Used to override all command-line options for salloc. No other options with be used or added." )

    parser.add_argument( "--ats", nargs='+', default=[], action="append", help="pass arguments to ats" )

    parser.add_argument( "--machine", default=None, help="name of the machine" )

    parser.add_argument( "--machine-dir", default=None, help="Search path for machine definitions" )

    parser.add_argument( "-l", "--logs", type=str, default=None )

    parser.add_argument( "-f", "--allow-failed-tests", default=False, action='store_true' )

    parser.add_argument(
        "--failIfTestsFail",
        action="store_true",
        default=False,
        help="geos_ats normally exits with 0. This will cause it to exit with an error code if there was a failed test."
    )

    parser.add_argument( "-n", "-N", "--numNodes", type=int, default="2" )

    return parser


def parse_command_line_arguments( args ):
    parser = build_command_line_parser()
    options, unkown_args = parser.parse_known_args()
    exit_flag = False

    # Check action, check, verbosity items
    check = options.check
    if check not in check_options:
        print( f"Selected check option ({check}) not recognized" )
        exit_flag = True

    action = options.action
    if action not in action_options:
        print( f"Selected action option ({action}) not recognized" )
        exit_flag = True

    if exit_flag:
        for option_type, details in ( 'action', action_options ), ( 'check', check_options ):
            print( f'\nAvailable {option_type} options:' )
            for k, v in details.items():
                print( f'    {k}:  {v}' )

    verbose = options.verbose
    if verbose not in verbose_options:
        print( f"Selected verbose option ({verbose}) not recognized" )
        exit_flag = True

    # Paths
    if not options.workingDir:
        options.workingDir = os.path.basename( options.ats_target )

    if not options.baselineDir:
        options.baselineDir = options.workingDir

    if exit_flag:
        quit()

    return options