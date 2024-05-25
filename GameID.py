#! /usr/bin/env python3
'''
GameID: Identify a game using GameDB
'''

# standard imports
from datetime import datetime
from gzip import decompress as gdecompress
from gzip import open as gopen
from os.path import abspath, expanduser, getsize, isfile
from pickle import loads as ploads
from struct import unpack
from sys import stderr
import sys
import argparse

# useful constants
VERSION = '1.0.4'
DB_URL = 'https://github.com/niemasd/GameID/raw/main/db.pkl.gz'
DEFAULT_BUFSIZE = 1000000
FILE_MODES_GZ = {'rb', 'wb', 'rt', 'wt'}
ISO966O_UUID_TERMINATION = {ord('$'), ord('.')}
PSX_HEADER = b'\x00\xff\xff\xff\xff\xff\xff\xff\xff\xff\xff\x00'
N64_FIRST_WORD = b'\x80\x37\x12\x40'

# print a log message
def print_log(message='', end='\n', file=stderr):
    print(message, end=end, file=file); file.flush()

# print an error message and exit
def error(message, exitcode=1):
    print(message, file=stderr); exit(exitcode)

# check if a file exists and throw an error if it doesn't
def check_exists(fn):
    if not isfile(fn):
        error("File not found: %s" % fn)

# check if a file doesn't exist and throw an error if it does
def check_not_exists(fn):
    if isfile(fn):
        error("File exists: %s" % fn)

# open an output text file for writing (automatically handle gzip)
def open_file(fn, mode='rt', bufsize=DEFAULT_BUFSIZE):
    if fn == 'stdout':
        from sys import stdout as f
    elif fn == 'stdin':
        from sys import stdin as f
    elif fn.strip().lower().endswith('.gz'):
        if mode not in FILE_MODES_GZ:
            error("Invalid gzip file mode: %s" % mode)
        elif 'r' in mode:
            f = gopen(fn, mode)
        elif 'w' in mode:
            f = gopen(fn, mode, compresslevel=9)
        else:
            error("Invalid gzip file mode: %s" % mode)
    else:
        f = open(fn, mode, buffering=bufsize)
    return f

# helper class to handle disc images
class ISO9660:
    # initialize ISO handling
    def __init__(self, fn, console, bufsize=DEFAULT_BUFSIZE):
        self.fn = abspath(expanduser(fn)); self.size = getsize(fn); self.console = console
        if fn.lower().endswith('.cue'):
            f_cue = open_file(fn, 'rt', bufsize=bufsize)
            self.bins = ['%s/%s' % ('/'.join(abspath(expanduser(fn)).split('/')[:-1]), l.split('"')[1].strip()) for l in f_cue if l.strip().lower().startswith('file')]
            f_cue.close()
            self.size = sum(getsize(b) for b in self.bins)
            self.f = open_file(self.bins[0], 'rb', bufsize=bufsize)
        else:
            self.f = open_file(self.fn, 'rb', bufsize=bufsize)
        if (self.size % 2352) == 0:
            self.block_size = 2352
        elif (self.size % 2048) == 0:
            self.block_size = 2048
        else:
            error("Invalid disc image block size: %s" % fn)

        # PSX raw image starts at 0x18: https://github.com/cebix/ff7tools/blob/21dd8e29c1f1599d7c776738b1df20f2e9c06de0/ff7/cd.py#L30-L40
        if self.console == 'PSX' and self.block_size == 2352:
            self.block_offset = 0x18
        else:
            self.block_offset = 0 # most console disc images start at the beginning

        # read PVD: https://wiki.osdev.org/ISO_9660#The_Primary_Volume_Descriptor
        self.f.seek(self.block_offset + (16 * self.block_size)); self.pvd = self.f.read(2048)

    # get system ID
    def get_system_ID(self):
        system_ID = self.pvd[8 : 40]
        try:
            return system_ID.decode().strip()
        except:
            return system_ID

    # get volume ID
    def get_volume_ID(self):
        volume_ID = self.pvd[40 : 72]
        try:
            return volume_ID.decode().strip()
        except:
            return volume_ID

    # get publisher ID
    def get_publisher_ID(self):
        publisher_ID = self.pvd[318 : 446]
        try:
            return publisher_ID.decode().strip()
        except:
            return publisher_ID

    # get data preparer ID
    def get_data_preparer_ID(self):
        data_preparer_ID = self.pvd[446 : 574]
        try:
            return data_preparer_ID.decode().strip()
        except:
            return data_preparer_ID

    # get UUID (volume creation date + time, but could be at different offsets)
    def get_uuid(self):
        uuid_start_ind = 813 # usually offset 813 of PVD, but could be different, so find it
        for i in range(813, 830):
            if self.pvd[i] in ISO966O_UUID_TERMINATION:
                uuid_start_ind = i - 16; break
        uuid = self.pvd[uuid_start_ind : uuid_start_ind + 16]
        try:
            uuid = uuid.decode().strip()
        except:
            return uuid
        try:
            tmp = uuid[-2:] # last 2 characters are always(?) extra 00
            uuid = datetime.strptime(uuid[:-2], "%Y%m%d%H%M%S")
            uuid = uuid.strftime("%Y-%m-%d-%H-%M-%S-") + tmp # format as YYYY-MM-DD-HH-MM-SS-00
        except:
            return uuid
        return uuid

    # parse filenames: https://wiki.osdev.org/ISO_9660#Recursing_from_the_Root_Directory
    def get_filenames(self, only_root_dir=True):
        root_dir_lba = unpack('<I', self.pvd[156 +  2 : 156 +  6])[0]
        root_dir_len = unpack('<I', self.pvd[156 + 10 : 156 + 14])[0]
        to_explore = [('/', root_dir_lba, root_dir_len)]; files = list()
        while len(to_explore) != 0:
            curr_path, curr_lba, curr_len = to_explore.pop()
            self.f.seek(self.block_offset + (curr_lba * self.block_size))
            curr_data = self.f.read(curr_len); i = 0
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

# get args from user interactively
def get_args_interactive(argv):
    # set things up
    print_log("=== GameID v%s ===" % VERSION)
    arg_input = None; arg_console = None

    # get game filename (--input)
    while arg_input is None:
        print_log("Enter game title (no quotes): ", end='')
        arg_input = input().strip()
        if not isfile(arg_input):
            print_log("ERROR: File not found: %s\n" % arg_input); arg_input = None
    argv += ['--input', arg_input]

    # get console (--console)
    while arg_console is None:
        print_log("Enter console (options: %s): " % ', '.join(sorted(IDENTIFY.keys())), end='')
        arg_console = input().replace('"','').replace("'",'').strip()
        if arg_console not in IDENTIFY:
            print_log("ERROR: Invalid console: %s\n" % arg_console); arg_console = None
    argv += ['--console', arg_console]

# parse user arguments
def parse_args():
    # if --version, just print version and exit
    if '--version' in sys.argv:
        print("GameID v%s" % VERSION); exit()

    # run argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True, type=str, help="Input Game File")
    parser.add_argument('-c', '--console', required=True, type=str, help="Console (options: %s)" % ', '.join(sorted(IDENTIFY.keys())))
    parser.add_argument('-d', '--database', required=False, type=str, default=None, help="GameID Database (db.pkl.gz)")
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File")
    parser.add_argument('--delimiter', required=False, type=str, default='\t', help="Delimiter")
    parser.add_argument('--prefer_gamedb', action="store_true", help="Prefer Metadata in GameDB (rather than metadata loaded from game)")
    parser.add_argument('--version', action="store_true", help="Print GameID Version (%s)" % VERSION)
    args = parser.parse_args()

    # check console
    check_console(args.console)

    # check input game file
    args.input = abspath(expanduser(args.input))
    check_exists(args.input)

    # check input database file
    if args.database is not None:
        args.database = abspath(expanduser(args.database))
        check_exists(args.database)

    # check output file
    if args.output != 'stdout':
        check_not_exists(args.output)

    # all good, so return args
    return args

# load GameID database
def load_db(fn, bufsize=DEFAULT_BUFSIZE):
    if fn is None:
        from urllib.request import urlopen; data = gdecompress(urlopen(DB_URL).read())
    else:
        f = open_file(fn, 'rb', bufsize=bufsize); data = f.read(); f.close()
    return ploads(data)

# identify PSX game
def identify_psx_ps2(fn, db, console, prefer_gamedb=False):
    # set things up
    iso = ISO9660(fn, console); out = None; serial = None

    # try to find file in root directory with name SXXX_XXX.XX
    root_fns = [root_fn.lstrip('/') for root_fn, file_lba, file_len in iso.get_filenames(only_root_dir=True)]
    for prefix in db['GAMEID'][console]['ID_PREFIXES']:
        for root_fn in root_fns:
            if root_fn.startswith(prefix):
                serial = root_fn.replace('.','').replace('-','_')
                if serial not in db[console] and len(serial) > len(prefix): # might have a different delimiter than '-' or '_' (e.g. DQ7 is 'SLUSP012.06)
                    serial = serial[:len(prefix)] + '_' + serial[len(prefix)+1:]
                if serial in db[console]:
                    out = db[console][serial]; break
        if serial is not None:
            break

    # failed to find serial based on file, so try volume ID
    if out is None:
        volume_ID = iso.get_volume_ID()
        if isinstance(volume_ID, str):
            serial = volume_ID.replace('-','_'); num_underscore = serial.count('_')
            if num_underscore == 2:
                serial = '_'.join(serial.split('_')[:2])
            if serial in db[console]:
                out = db[console][serial]

    # finalize output and return
    if out is None:
        error("%s game not found (%s): %s\t%s" % (console, volume_ID, fn, root_fns))
    else:
        out['ID'] = serial
        if not prefer_gamedb:
            out['uuid'] = iso.get_uuid()
        return out

# identify PSX game
def identify_psx(fn, db, prefer_gamedb=False):
    return identify_psx_ps2(fn, db, 'PSX', prefer_gamedb=prefer_gamedb)

# identify PS2 game
def identify_ps2(fn, db, prefer_gamedb=False):
    return identify_psx_ps2(fn, db, 'PS2', prefer_gamedb=prefer_gamedb)

# identify GC game
def identify_gc(fn, db, prefer_gamedb=False):
    # open GC ISO
    try:
        from gciso import IsoFile as GCIsoFile
    except:
        error("Unable to import gciso. Install with: pip install git+https://github.com/pfirsich/gciso.git")
    iso = GCIsoFile(fn)

    # identify game
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

# helper function convert N64 data between little-endian and big-endian
def n64_convert_endianness(data):
    if len(data) % 2 != 0:
        error("Can only convert even-length data")
    out = bytearray(len(data))
    for i in range(0, len(data), 2):
        out[i] = data[i+1]; out[i+1] = data[i]
    return out

# identify N64 game
def identify_n64(fn, db, prefer_gamedb=False):
    f = open_file(fn, mode='rb'); header = f.read(0x40) # stop before "Boot code/strap"

    # determine endianness from first word: https://en64.shoutwiki.com/wiki/ROM
    first_word_data = header[0 : 4]
    if n64_convert_endianness(first_word_data) == N64_FIRST_WORD: # little-endian, so need to convert to big-endian
        header = n64_convert_endianness(header)
    elif first_word_data != N64_FIRST_WORD: # doesn't match either endianness
        error("Invalid N64 ROM: %s" % fn)

    # parse N64 ROM header: https://en64.shoutwiki.com/wiki/ROM#Cartridge_ROM_Header
    cartridge_ID = header[0x3c : 0x3e]
    country_code, version = header[0x3e : 0x40]

    # identify game
    try:
        serial = '%s%s%s' % (chr(cartridge_ID[0]), chr(cartridge_ID[1]), chr(country_code))
    except:
        error("Invalid N64 ROM (%s %s): %s" % (cartridge_ID, country_code, fn))
    if serial in db['N64']:
        out = db['N64'][serial]
        out['ID'] = serial
        if not prefer_gamedb:
            internal_name = header[0x20 : 0x34]
            try:
                out['title'] = internal_name.decode().strip()
            except:
                out['title'] = internal_name
        f.close()
        return out
    f.close(); error("N64 game not found (%s %s): %s" % (cartridge_ID, country_code, fn))

# dictionary storing all identify functions
IDENTIFY = {
    'GC':  identify_gc,
    'N64': identify_n64,
    'PSX': identify_psx,
    'PS2': identify_ps2,
}

# throw an error for unsupported consoles
def check_console(console):
    if console not in IDENTIFY:
        error("Invalid console: %s\nOptions: %s" % (console, ', '.join(sorted(IDENTIFY.keys()))))

# main program logic
def main():
    args = parse_args()
    db = load_db(args.database)
    meta = IDENTIFY[args.console](args.input, db, prefer_gamedb=args.prefer_gamedb)
    if meta is None:
        error("%s game not found: %s" % (args.console, args.input))
    f_out = open_file(args.output, 'wt')
    print('\n'.join('%s%s%s' % (k,args.delimiter,v) for k,v in meta.items()), file=f_out)
    f_out.close()

# run program
if __name__ == "__main__":
    if len(sys.argv) == 1:
        get_args_interactive(sys.argv)
    main()
