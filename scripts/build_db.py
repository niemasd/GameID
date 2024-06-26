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
CONSOLES = {'GB', 'GBA', 'GBC', 'GC', 'Genesis', 'N64', 'NeoGeoCD', 'PSP', 'PSX', 'PS2', 'Saturn', 'SegaCD', 'SNES'}

# get GameDB URL
def get_url(console):
    return 'https://github.com/niemasd/GameDB-%s/releases/latest/download/%s.data.tsv' % (console, console)

# iterate over rows of a GameDB data.tsv file
def iter_gamedb_data_tsv(console):
    for line in urlopen(get_url(console)).read().decode().splitlines():
        yield [v.strip() for v in line.split('\t')]

# load GameDB database
def load_gamedb(console):
    if console not in CONSOLES:
        print("Invalid console: %s" % console); exit(1)
    db = dict()
    for row_num, row in enumerate(iter_gamedb_data_tsv(console)):
        if row_num == 0:
            field2index = {v:i for i,v in enumerate(row)}
        else:
            db[row[field2index['ID']]] = {k:row[i] for k,i in field2index.items() if k != 'ID'}
    return db

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

    # merge GB/GBC
    print("Fixing GB and GBC databases...")
    db['GB_GBC'] = db['GB'] | db['GBC']; del db['GB']; del db['GBC']
    db['GB_GBC'] = {(v['internal_title'], int(v['global_checksum_expected'],0)):v for k,v in db['GB_GBC'].items()}

    # fix GC (only keep middle part of DOL-XXXX-XXX serial)
    print("Fixing GC database...")
    db['GC'] = {k.split('-')[1].strip():v for k,v in db['GC'].items()}

    # fix Genesis (delete spaces and dashes)
    print("Fixing Genesis database...")
    db['Genesis'] = {k.strip().split(' ')[0].replace('-','').replace(' ','').strip():v for k,v in db['Genesis'].items()}

    # fix N64 (only keep last 3 letters of middle part of NUS-NXXX-XXX serial)
    print("Fixing N64 database...")
    db['N64'] = {k.split('-')[1][1:]:v for k,v in db['N64'].items()}

    # fix Neo Geo CD: ID based on (UUID, disc label) tuples, with just disc label as a last resort
    print("Fixing NeoGeoCD database...")
    db['NeoGeoCD'] = {new_k:v for k,v in db['NeoGeoCD'].items() for new_k in [(v['uuid'],v['volume_ID']), v['volume_ID']] if new_k is not None}

    # fix PSX and PS2
    for console in ['PSX', 'PS2']:
        print("Fixing %s database..." % console)
        # replace '-' with '_' (most serials in ISO header are SXXX_XXXXX instead of SXXX-XXXXX)
        db[console] = {k.replace('-','_'):v for k,v in db[console].items()}

        # add Redump names as alternate keys (just in case serial isn't in root filenames or volume ID)
        for k in list(db[console].keys()):
            if 'redump_name' in db[console][k]:
                db[console][db[console][k]['redump_name']] = db[console][k]

        # preprocess PSX/PS2 serial beginnings for speed in GameID (sorted in decreasing order of frequency)
        counts = dict()
        for ID in db[console]:
            prefix = ID.split('_')[0].strip()
            if prefix not in counts:
                counts[prefix] = 0
            counts[prefix] += 1
        db['GAMEID'][console]['ID_PREFIXES'] = sorted(counts.keys(), key=lambda x: counts[x], reverse=True)

    # fix Saturn (delete spaces and dashes)
    print("Fixing Saturn database...")
    db['Saturn'] = {k.strip().split(' ')[0].replace('-','').replace(' ','').strip():v for k,v in db['Saturn'].items()}

    # fix SegaCD (delete spaces and dashes)
    print("Fixing SegaCD database...")
    db['SegaCD'] = {k.strip().replace('-','').replace(' ','').strip():v for k,v in db['SegaCD'].items()}

    # fix SNES: keys = (developer_ID, internal_title, rom_version, checksum) tuples
    print("Fixing SNES database...")
    db['SNES'] = {(int(v['developer_ID'],0), v['internal_title'], int(v['rom_version'],0), int(v['checksum'],0)):v for k,v in db['SNES'].items()}

    # dump GameID database
    print("Writing GameID database: %s" % argv[1])
    if argv[1].lower().endswith('.gz'):
        f = gopen(argv[1], 'wb', compresslevel=9)
    else:
        f = open(argv[1], 'wb')
    pdump(db, f); f.close()
