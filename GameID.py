#! /usr/bin/env python3
'''
GameID: Identify a game using GameDB
'''

# standard imports
from gzip import open as gopen
from os.path import isfile
from pickle import load as pload
from sys import stderr
import argparse

# import pycdlib
try:
    from pycdlib import PyCdlib
except:
    print("Unable to import pycdlib. Install with: pip install pycdlib", file=stderr); exit(1)

# useful constants
CONSOLES = {'PSX'}
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
    parser.add_argument('-c', '--console', required=True, type=str, help="Console (options: %s)" % ', '.join(sorted(CONSOLES)))
    parser.add_argument('-d', '--database', required=True, type=str, help="GameID Database (db.pkl.gz)")
    args = parser.parse_args()
    check_exists(args.input)
    check_extension(args.input)
    return args

# load GameID database
def load_db(fn):
    if fn.lower().endswith('.gz'):
        f = gopen(fn, 'rb')
    else:
        f = open(fn, 'rb')
    db = pload(f); f.close()
    return db

# identify PSX game
def identify_psx(fn):
    return "TODO"

# identify game
def identify(fn, console):
    if console == 'PSX':
        return identify_psx(fn)
    else:
        error("Invalid console: %s" % console)

# main program logic
def main():
    args = parse_args()
    db = load_db(args.database)

# run program
if __name__ == "__main__":
    main()
