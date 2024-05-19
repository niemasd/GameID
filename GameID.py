#! /usr/bin/env python3
'''
GameID: Identify a game using GameDB
'''

# standard imports
from os.path import isfile
from sys import stderr
import argparse

# import pycdlib
try:
    from pycdlib import PyCdlib
except:
    print("Unable to import pycdlib. Install with: pip install pycdlib", file=stderr); exit(1)

# useful constants
EXT_ISO = {'bin', 'cue', 'iso'}
EXT_ALL = EXT_ISO # union all EXT_* sets

# print an error message and exit
def error(message, exitcode=1):
    print(message, file=stderr); exit(exitcode)

# throw an error if a file doesn't exist
def check_exists(fn):
    if not isfile(fn):
        error("File not found: %s" % fn)

# throw an error for unsupported file extensions
def check_extension(fn):
    ext = fn.split('.')[-1].strip().lower()
    if ext not in EXT_ALL:
        error("%s files are not supported (yet): %s" % (ext, fn))

# parse user arguments
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True, type=str, help="Input Game File")
    args = parser.parse_args()
    check_exists(args.input)
    check_extension(args.input)
    return args

# main program logic
def main():
    args = parse_args()

# run program
if __name__ == "__main__":
    main()
