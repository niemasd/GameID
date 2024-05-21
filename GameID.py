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
CONSOLES = {'GC', 'PSX', 'PS2'}
START_LEN = { # search for ID in first START_LEN[console] bytes of image data (currently just PSX)
    'PSX': 1000000,
}

# print an error message and exit
def error(message, exitcode=1):
    print(message, file=stderr); exit(exitcode)

# import gciso
try:
    from gciso import IsoFile as GCIsoFile
except:
    error("Unable to import gciso. Install with: pip install git+https://github.com/pfirsich/gciso.git")

# import pycdlib
try:
    from pycdlib import PyCdlib
except:
    error("Unable to import pycdlib. Install with: pip install pycdlib")

# check if a file exists and throw an error if it doesn't
def check_exists(fn):
    if not isfile(fn):
        error("File not found: %s" % fn)

# check if a file doesn't exist and throw an error if it does
def check_not_exists(fn):
    if isfile(fn):
        error("File exists: %s" % fn)

# open an output text file for writing (automatically handle gzip)
def open_text_output(fn):
    if fn == 'stdout':
        from sys import stdout as f_out
    elif fn.strip().lower().endswith('.gz'):
        f_out = gopen(fn, 'wt', compresslevel=9)
    else:
        f_out = open(fn, 'w')
    return f_out

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
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File")
    parser.add_argument('--delimiter', required=False, type=str, default='\t', help="Delimiter")
    parser.add_argument('--prefer_gamedb', action="store_true", help="Prefer Metadata in GameDB (rather than metadata loaded from game)")
    args = parser.parse_args()

    # check console
    check_console(args.console)

    # check input game file
    args.input = abspath(expanduser(args.input))
    check_exists(args.input)

    # check input database file
    args.database = abspath(expanduser(args.database))
    check_exists(args.database)

    # check output file
    if args.output != 'stdout':
        check_not_exists(args.output)

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

# identify PSX game
def identify_psx(fn, db, prefer_gamedb=False):
    if fn.lower().endswith('.cue'):
        fn = get_first_img_cue(fn)
    if fn.lower().endswith('.gz'):
        f = gopen(fn, 'rb')
    else:
        f = open(fn, 'rb', buffering=START_LEN['PSX'])
    data = f.read(START_LEN['PSX']); offset = None; prefixes = db['GAMEID']['PSX']['ID_PREFIXES']
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
            if found and chr(data[i+len(prefix)]) in {'_','-'}:
                offset = i; break
    if offset is not None:
        serial = ''; i = offset-1
        while len(serial) < 10:
            i += 1; c = chr(data[i])
            if c == '.':
                continue
            elif c == '-':
                c = '_'
            serial += c
        if serial in db['PSX']:
            out = db['PSX'][serial]
            out['ID'] = serial
            return out

# identify PS2 game
def identify_ps2(fn, db, prefer_gamedb=False):
    iso = PyCdlib(); iso.open(fn); root_fns = [child.file_identifier().decode().strip() for child in iso.list_children(iso_path='/')]
    for prefix in db['GAMEID']['PS2']['ID_PREFIXES']: # prioritize higher-frequency prefixes (just in case; should still be super fast)
        for fn in root_fns:
            if fn.upper().startswith(prefix):
                serial = fn.replace('.','')[:10].replace('-','_')
                if serial in db['PS2']:
                    out = db['PS2'][serial]
                    out['ID'] = serial
                    return out

# identify GC game
def identify_gc(fn, db, prefer_gamedb=False):
    iso = GCIsoFile(fn)
    serial = iso.gameCode.decode()
    if serial in db['GC']:
        out = db['GC'][serial]
        out['ID'] = serial
        if not prefer_gamedb: # https://gciso.readthedocs.io/en/latest/#gciso.IsoFile
            out['maker_code'] = iso.makerCode.decode()
            out['disk_ID'] = iso.diskId
            out['version'] = iso.version
            out['title'] = iso.gameName.decode()
            out['dol_offset'] = iso.dolOffset
            out['dol_size'] = iso.dolSize
            out['fst_offset'] = iso.fstOffset
            out['fst_size'] = iso.fstSize
            out['max_fst_size'] = iso.maxFstSize
            out['num_fst_entries'] = iso.numFstEntries
            out['string_table_offset'] = iso.stringTableOffset
            out['apploader_date'] = iso.apploaderDate.decode().replace('/','-')
            out['apploader_entry_point'] = iso.apploaderEntryPoint
            out['apploader_code_size'] = iso.apploaderCodeSize
            out['apploader_trailer_size'] = iso.apploaderTrailerSize
        return out

# dictionary storing all identify functions
IDENTIFY = {
    'GC':  identify_gc,
    'PSX': identify_psx,
    'PS2': identify_ps2,
}

# main program logic
def main():
    args = parse_args()
    db = load_db(args.database)
    meta = IDENTIFY[args.console](args.input, db, prefer_gamedb=args.prefer_gamedb)
    if meta is None:
        error("%s game not found: %s" % (args.console, args.input))
    f_out = open_text_output(args.output)
    print('\n'.join('%s%s%s' % (k,args.delimiter,v) for k,v in meta.items()), file=f_out)
    f_out.close()

# run program
if __name__ == "__main__":
    main()
