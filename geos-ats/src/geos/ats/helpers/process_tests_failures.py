#!/usr/bin/env python3
import sys
import os
import stat
import subprocess
import argparse
import platform
import shutil
import logging
import glob

logging.basicConfig( level=logging.INFO, format="%(levelname)s: %(message)s" )


def findFiles( folder, extension ):
    """
    Recursively find all files in `folder` that match a given extension.
    """
    # Build a pattern such as "*.py", "*.txt", etc.
    pattern = f"*{extension}"

    # Use glob with ** (recursive) to match all files under folder
    return glob.glob( os.path.join( folder, "**", pattern ), recursive=True )


def find_error_indices( lines, matchStrings ):
    """
    Returns a list of indices where all `matchStrings` appear in the line.
    """
    indices = []
    for idx, line in enumerate( lines ):
        if all( matchString in line for matchString in matchStrings ):
            indices.append( idx )
    return indices


def process_error_blocks( lines, indices, numTrailingLines ):
    """
    For each index in `indices`, collect the line itself plus a few trailing lines.
    Returns a list of match blocks (strings).
    """
    match_blocks = []
    for idx in indices:
        # Prepare the current match block
        match_block = []

        # Safely get the previous line if idx > 0
        if idx > 0:
            match_block.append( '  ' + lines[ idx - 1 ] )

        # Current line
        match_block.append( '  ' + lines[ idx ] )

        # Trailing lines
        for j in range( 1, numTrailingLines + 1 ):
            if idx + j >= len( lines ):
                match_block.append(
                    '  ***** No closing line. File truncated? Filters may not be properly applied! *****' )
                break
            match_block.append( '  ' + lines[ idx + j ] )

            # If we see a "stop" condition, break out of the trailing loop
            if '******************************************************************************' in lines[ idx + j ]:
                break

        # Convert match_block to a single string
        match_blocks.append( '\n'.join( match_block ) )

    return match_blocks


def parse_logs_and_filter_errors( directory, extension, exclusionStrings, numTrailingLines ):
    """
    Returns a list of indices where all `matchStrings` appear in the line.
    """
    # What strings to look for in order to flag a line/block for output
    errorStrings = [ 'Error:' ]

    unfilteredErrors = {}
    total_files_processed = 0
    files_with_excluded_errors = []

    for fileName in findFiles( directory, extension ):
        total_files_processed += 1
        errors = ''

        # Count how many blocks we matched and how many blocks we ended up including
        matched_block_count = 0
        included_block_count = 0

        with open( fileName ) as f:
            lines = f.readlines()

            # 1. Find the indices where the errorStrings are found
            indices = find_error_indices( lines, errorStrings )

            # 2. Extract the block of text associated with each error.
            matchBlock = process_error_blocks( lines, indices, numTrailingLines )

            for block in matchBlock:
                # if none of the exclusions appear in this block
                matched_block_count += 1
                if not any( excludeString in block for excludeString in exclusionStrings ):
                    # ... then add it to `errors`
                    included_block_count += 1
                    errors += block + "\n"

        # If at least 1 block was matched, and not all of them ended up in 'included_block_count'
        # it means at least one block was excluded.
        if matched_block_count > 0 and included_block_count < matched_block_count:
            files_with_excluded_errors.append( fileName )

        if errors:
            unfilteredErrors[ fileName ] = errors

    # --- Logging / Output ---
    logging.info( f"Total number of log files processed: {total_files_processed}\n" )

    # Unfiltered errors
    if unfilteredErrors:
        for fileName, errors in unfilteredErrors.items():
            logging.warning( f"Found unfiltered diff in: {fileName}" )
            logging.info( f"Details of diffs: {errors}" )
    else:
        logging.info( "No unfiltered differences were found.\n" )

    # Files that had at least one excluded block
    if files_with_excluded_errors:
        files_with_excluded_errors_basename = [ os.path.basename( f ) for f in files_with_excluded_errors ]

        excluded_files_text = "\n".join( files_with_excluded_errors_basename )
        logging.info( f"The following file(s) had at least one error block that was filtered:\n{excluded_files_text}" )


def main():

    DEFAULT_EXCLUSION_STRINGS = [
        'logLevel', 'NonlinearSolverParameters', 'has a child', 'different shapes', 'different types', 'differing types'
    ]

    parser = argparse.ArgumentParser( description='Process ats output to filter diffs.' )

    parser.add_argument( '-d',
                         '--directory',
                         type=str,
                         default='integratedTests',
                         help='directory to search recursively for files with specified extension' )

    parser.add_argument( '-ext', '--extension', type=str, default='.log', help='extension of files to filter' )

    parser.add_argument( '-tl',
                         '--numTrailingLines',
                         type=int,
                         default=5,
                         help='number of lines to include in block after match is found.' )

    parser.add_argument( '-e',
                         '--exclusionStrings',
                         type=str,
                         nargs="*",
                         default=[],
                         help='What stings to look for in order to exclude a block' )

    args, unknown_args = parser.parse_known_args()

    if unknown_args:
        print( "unknown arguments %s" % unknown_args )

    exclusionStrings = DEFAULT_EXCLUSION_STRINGS + args.exclusionStrings
    logging.info( f"exclusionStrings: {exclusionStrings}\n" )
    parse_logs_and_filter_errors( args.directory, args.extension, exclusionStrings, args.numTrailingLines )


if __name__ == '__main__':
    main()
