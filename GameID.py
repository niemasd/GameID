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

# useful constants
CONSOLES = {'PSX'}
EXT_ISO = {'bin', 'iso'}
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
def identify_psx(fn, db):
    fn_lower = fn.lower(); fn_lower_strip = fn.lower().rstrip('.gz')
    if fn_lower_strip.endswith('.bin'):
        if fn_lower.endswith('.gz'):
            f = gopen(fn, 'rb')
        else:
            f = open(fn, 'rb')
        serial = f.read(0x0000ef06 + 11)[-11:].decode().replace('.','')
    else:
        raise NotImplementedError("TODO IMPLEMENT")
    if serial in db['PSX']:
        return db['PSX'][serial]

# identify game
def identify(fn, console, db):
    if console == 'PSX':
        return identify_psx(fn, db)
    else:
        error("Invalid console: %s" % console)

# main program logic
def main():
    args = parse_args()
    db = load_db(args.database)
    title = identify(args.input, args.console, db)
    if title is None:
        error("Game not found: %s" % args.input)
    print(title)

# run program
if __name__ == "__main__":
    main()
