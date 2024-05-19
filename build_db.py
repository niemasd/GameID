#! /usr/bin/env python3
'''
Build a local game database using GameDB
'''

# imports
from gzip import open as gopen
from os.path import isdir, isfile
from pickle import dump as pdump
from sys import argv
from urllib.request import urlopen

# constants
CONSOLES = {'PSX', 'PS2'}

# get GameDB URL
def get_url(console):
    return 'https://github.com/niemasd/GameDB-%s/releases/latest/download/%s.data.tsv' % (console, console)

# iterate over rows of a GameDB data.tsv file
def iter_gamedb_data_tsv(console):
    for line in urlopen(get_url(console)).read().decode().splitlines():
        yield [v.strip() for v in line.split('\t')]

# get ID and title columns from header row of GameDB data.tsv file
def get_ID_title_columns(header_row):
    col_ID = None; col_title = None
    for i, v in enumerate(header_row):
        v_lower = v.strip().lower()
        if v_lower == 'id':
            col_ID = i
        elif v_lower == 'title':
            col_title = i
    if col_ID is None or col_title is None:
        print("Invalid GameDB data.tsv header row: %s" % header_row); exit(1)
    return col_ID, col_title

# load PSX or PS2 database
def load_gamedb_psx_ps2(console):
    db = dict()
    for row_num, row in enumerate(iter_gamedb_data_tsv(console)):
        if row_num == 0:
            col_ID, col_title = get_ID_title_columns(row); continue
        ID = row[col_ID]; title = row[col_title]
        db[ID.replace('-','_')] = title
    return db

# load GameDB
def load_gamedb(console):
    if console in {'PSX', 'PS2'}:
        return load_gamedb_psx_ps2(console)
    else:
        print("Invalid console: %s" % console); exit(1)

# main program
if __name__ == "__main__":
    # check user arguments
    if len(argv) != 2 or argv[1].strip().lower() in {'-h', '--help'}:
        print("USAGE: %s <output_GameID_db.pkl.gz>" % argv[0]); exit(1)
    if isfile(argv[1]) or isdir(argv[1]):
        print("Output file exists: %s" % argv[1]); exit(1)
    if not argv[1].lower().endswith('.pkl') and not argv[1].lower().endswith('.pkl.gz'):
        print("Invalid output file extension (must be .pkl or .pkl.gz): %s" % argv[1]); exit(1)

    # load GameDB databases
    db = {'GAMEID': dict()}
    for console in sorted(CONSOLES):
        print("Loading GameDB-%s..." % console)
        db[console] = load_gamedb(console) # load GameDB
        db['GAMEID'][console] = dict() # just in case I need to preprocess stuff for this console

    # preprocess PSX/PS2 serial beginnings for speed in GameID (sorted in decreasing order of frequency)
    for console in ['PSX', 'PS2']:
        counts = dict()
        for ID in db[console]:
            prefix = ID.split('_')[0].strip()
            if prefix not in counts:
                counts[prefix] = 0
            counts[prefix] += 1
        db['GAMEID'][console]['ID_PREFIXES'] = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

    # dump GameID database
    print("Writing GameID database: %s" % argv[1])
    if argv[1].lower().endswith('.gz'):
        f = gopen(argv[1], 'wb', compresslevel=9)
    else:
        f = open(argv[1], 'wb')
    pdump(db, f); f.close()
