#! /usr/bin/env python3
'''
GameID: Identify a game using GameDB
'''

# standard imports
from gzip import open as gopen
from os.path import abspath, expanduser, isfile
from pickle import load as pload
from sys import stderr
import argparse

# useful constants
CONSOLES = {'PSX', 'PS2'}
START_LEN = { # search for ID in first START_LEN[console] bytes of image data (currently just PSX and PS2)
    'PSX': 1000000,
    'PS2': 1000000,
}

# print an error message and exit
def error(message, exitcode=1):
    print(message, file=stderr); exit(exitcode)

# throw an error if a file doesn't exist
def check_exists(fn):
    if not isfile(fn):
        error("File not found: %s" % fn)

# throw an error for unsupported consoles
def check_console(console):
    if console not in CONSOLES:
        error("Invalid console: %s\nOptions: %s" % (console, ', '.join(sorted(CONSOLES))))

# get path of first image file from CUE
def get_first_img_cue(fn):
    try:
        img_fn = [l.split('"')[1].strip() for l in open(fn) if l.strip().lower().startswith('file')][0]
    except:
        error("Invalid CUE file: %s" % fn)
    return '%s/%s' % ('/'.join(abspath(expanduser(fn)).split('/')[:-1]), img_fn)

# parse user arguments
def parse_args():
    # run argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True, type=str, help="Input Game File")
    parser.add_argument('-c', '--console', required=True, type=str, help="Console (options: %s)" % ', '.join(sorted(CONSOLES)))
    parser.add_argument('-d', '--database', required=True, type=str, help="GameID Database (db.pkl.gz)")
    args = parser.parse_args()

    # check console
    check_console(args.console)

    # check input game file
    args.input = abspath(expanduser(args.input))
    check_exists(args.input)

    # check input database file
    args.database = abspath(expanduser(args.database))
    check_exists(args.database)

    # all good, so return args
    return args

# load GameID database
def load_db(fn):
    if fn.lower().endswith('.gz'):
        f = gopen(fn, 'rb')
    else:
        f = open(fn, 'rb')
    db = pload(f); f.close()
    return db

# identify PSX/PS2 game
def identify_psx_ps2(fn, console, db):
    if fn.lower().endswith('.cue'):
        fn = get_first_img_cue(fn)
    if fn.lower().endswith('.gz'):
        f = gopen(fn, 'rb')
    else:
        f = open(fn, 'rb', buffering=START_LEN[console])
    data = f.read(START_LEN[console]); offset = None; prefixes = db['GAMEID'][console]['ID_PREFIXES']
    for prefix in prefixes:
        if offset is not None:
            break
        for i, v in enumerate(data):
            if offset is not None:
                break
            found = True
            for j, c in enumerate(prefix):
                if data[i+j] != ord(c):
                    found = False; break
            if found:
                offset = i; break
    if offset is not None:
        serial = ''; i = offset-1
        while len(serial) < 10:
            i += 1
            if chr(data[i]) == '.':
                continue
            serial += chr(data[i])
        if serial in db[console]:
            return db[console][serial]

# identify game
def identify(fn, console, db):
    check_console(console)
    if console in {'PSX', 'PS2'}:
        return identify_psx_ps2(fn, console, db)
    else:
        raise RuntimeError("Shouldn't reach this")

# main program logic
def main():
    args = parse_args()
    db = load_db(args.database)
    title = identify(args.input, args.console, db)
    if title is None:
        error("%s game not found: %s" % (args.console, args.input))
    print(title)

# run program
if __name__ == "__main__":
    main()
