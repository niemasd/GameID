#! /usr/bin/env python3
'''
GameID: Identify a game using GameDB
'''

# standard imports
from gzip import open as gopen
from os.path import abspath, expanduser, getsize, isfile
from pickle import load as pload
from struct import unpack
from sys import stderr
import argparse

# useful constants
CONSOLES = {'GC', 'PSX', 'PS2'}
DEFAULT_BUFSIZE = 1000000
PSX_HEADER = b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'

# print an error message and exit
def error(message, exitcode=1):
    print(message, file=stderr); exit(exitcode)

# import gciso
try:
    from gciso import IsoFile as GCIsoFile
except:
    error("Unable to import gciso. Install with: pip install git+https://github.com/pfirsich/gciso.git")

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

# get file names in a disc image
def iso_get_fns(fn, console, only_root_dir=True, bufsize=DEFAULT_BUFSIZE):
    # check block_size and set things up
    size = getsize(fn)
    if (size % 2352) == 0:
        block_size = 2352
    elif (size % 2048) == 0:
        block_size = 2048
    else:
        error("Invalid disc image block size: %s" % fn)
    block_offset = 0 # most console disc images start at the beginning
    f = open(fn, 'rb', buffering=bufsize)

    # PSX raw image starts at 0x18: https://github.com/cebix/ff7tools/blob/21dd8e29c1f1599d7c776738b1df20f2e9c06de0/ff7/cd.py#L30-L40
    if console == 'PSX' and block_size == 2352:
        block_offset = 0x18

    # read PVD: https://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor
    f.seek(block_offset + (16 * block_size)); pvd = f.read(2048)

    # parse filenames: https://wiki.osdev.org/ISO_9660#Recursing_from_the_Root_Directory
    root_dir_lba = unpack('<I', pvd[156 +  2 : 156 +  6])[0]
    root_dir_len = unpack('<I', pvd[156 + 10 : 156 + 14])[0]
    to_explore = [('/', root_dir_lba, root_dir_len)]; files = list()
    while len(to_explore) != 0:
        curr_path, curr_lba, curr_len = to_explore.pop(); f.seek(block_offset + (curr_lba * block_size)); curr_data = f.read(curr_len); i = 0
        while i < len(curr_data):
            next_len = curr_data[i + 0]
            if next_len == 0:
                break
            next_ext_attr_rec_len = curr_data[i + 1]
            next_lba = unpack('<I', curr_data[i + 2 : i + 6])[0]
            next_data_len = unpack('<I', curr_data[i + 10 : i + 14])[0]
            next_rec_date_time = curr_data[i + 18 : i + 25]
            next_file_flags = curr_data[i + 25]
            next_file_unit_size = curr_data[i + 26]
            next_interleave_gap_size = curr_data[i + 27]
            next_vol_seq_num = unpack('<H', curr_data[i + 28 : i + 30])[0]
            next_name_len = curr_data[i + 32]
            next_name = curr_data[i + 33 : i + 33 + next_name_len]
            if next_name not in {b'\x00', b'\x01'}:
                try:
                    next_name = next_name.decode()
                    if next_name.endswith(';1'):
                        next_path = '%s%s' % (curr_path, next_name[:-2])
                    else:
                        next_path = '%s%s/' % (curr_path, next_name)
                    next_tup = (next_path, next_lba, next_len)
                    if not next_path.endswith('/'):
                        files.append(next_tup)
                    elif not only_root_dir:
                        #to_explore.append(next_tup) # doesn't work
                        raise NotImplementedError("Currently only supports root directory")
                except:
                    pass # skip trying to load filename that's not a valid string
            i += next_len
    return files

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
def identify_psx_ps2(fn, db, console, prefer_gamedb=False):
    if fn.lower().endswith('.cue'):
        fn = get_first_img_cue(fn)
    root_fns = [root_fn.lstrip('/') for root_fn, file_lba, file_len  in iso_get_fns(fn, console, only_root_dir=True)]
    for prefix in db['GAMEID'][console]['ID_PREFIXES']:
        for root_fn in root_fns:
            if root_fn.startswith(prefix):
                serial = root_fn.replace('.','').replace('-','_')
                if serial not in db[console] and len(serial) > len(prefix): # might have a different delimiter than '-' or '_' (e.g. DQ7 is 'SLUSP012.06)
                    serial = serial[:len(prefix)] + '_' + serial[len(prefix)+1:]
                if serial in db[console]:
                    out = db[console][serial]
                    out['ID'] = serial
                    return out
    error("%s game not found: %s\t%s" % (console, fn, root_fns))

# identify PSX game
def identify_psx(fn, db, prefer_gamedb=False):
    return identify_psx_ps2(fn, db, 'PSX', prefer_gamedb=prefer_gamedb)

# identify PS2 game
def identify_ps2(fn, db, prefer_gamedb=False):
    return identify_psx_ps2(fn, db, 'PS2', prefer_gamedb=prefer_gamedb)

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
