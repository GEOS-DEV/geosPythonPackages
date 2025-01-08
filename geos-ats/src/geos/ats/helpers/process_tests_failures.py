#!/usr/bin/env python3
# Python script to
import sys
import os
import stat
import subprocess
import argparse
import platform
import shutil
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# fines all files recursively from
def findFiles(folder, extension):
    for root, folders, files in os.walk(folder):
        for filename in folders + files:
            if (extension in filename):
                yield os.path.join(root, filename)

def parse_logs_and_filter_errors( directory, extension, exclusionStrings, numTrailingLines ):
    # What strings to look for in order to flag a line/block for output
    matchStrings = ['Error:']

    filteredErrors = {}

    # What stings to look for in order to exclude a block
    for fileName in findFiles(directory, extension):
        errors = ''

        with open(fileName) as f:
            lines = f.readlines()

            for i in range(0, len(lines)):
                line = lines[i]
                if all(matchString in line for matchString in matchStrings):
                    matchBlock = []
                    matchBlock.append('  ' + lines[i - 1])
                    matchBlock.append('  ' + line)

                    for j in range(1, numTrailingLines + 1):
                        if i + j >= len(lines):
                            matchBlock.append('  ***** No closing line. file truncated? Filters may not be properly applied! *****')
                            break
                        matchBlock.append('  ' + lines[i + j])
                    
                    matchBlock = '\n'.join(matchBlock)     

                    if ('******************************************************************************'
                            in lines[i + j]):
                        break
                    
                    i += j

            if not any(excludeString in matchBlock for excludeString in exclusionStrings):
                errors += matchBlock

        if errors:
            filteredErrors[fileName] = errors

    if filteredErrors:
       for fileName, errors in filteredErrors.items():
           logging.warning(f"Found unfiltered diff in: {fileName}")
           logging.info(f"Details of diffs: {errors}")
    else:
        logging.info("No unfiltered differences were found.")

def main():

    DEFAULT_EXCLUSION_STRINGS = ['logLevel', 'NonlinearSolverParameters', 'has a child', 'different shapes', 'different types', 'differing types']

    parser = argparse.ArgumentParser(description='Process ats output to filter diffs.')
    
    parser.add_argument('-d',
                        '--directory',
                        type=str,
                        default='integratedTests',
                        help='directory to search recursively for files with specified extension')
                        
    parser.add_argument('-ext', '--extension', type=str, default='.log', help='extension of files to filter')

    parser.add_argument('-tl',
                        '--numTrailingLines',
                        type=int,
                        default=5,
                        help='number of lines to include in block after match is found.')
    
    parser.add_argument('-e',
                        '--exclusionStrings',
                        type=str,
                        nargs="*",
                        default=[],
                        help='What stings to look for in order to exclude a block')

    args, unknown_args = parser.parse_known_args()
    
    if unknown_args:
        print("unknown arguments %s" % unknown_args)
    
    exclusionStrings = DEFAULT_EXCLUSION_LIST + args.exclusionStrings 
    parse_logs_and_filter_errors( args.directory, args.extension,  exclusionStrings, args.numTrailingLines )    

if __name__ == '__main__':
    main()
