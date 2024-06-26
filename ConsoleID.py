#! /usr/bin/env python3
'''
ConsoleID: Identify the console of a game
'''

# standard imports
from glob import glob
from gzip import open as gopen
from io import BytesIO
from os.path import abspath, expanduser, isdir, isfile
import argparse
import sys

# non-standard imports
from GameID import DEFAULT_BUFSIZE, GC_MAGIC_WORD, GENESIS_MAGIC_WORDS, SATURN_MAGIC_WORD, SEGACD_MAGIC_WORDS
from GameID import bins_from_cue, check_exists, check_not_exists, error, get_extension, getsize, ISO9660, ISO9660FP, open_file

# ConsoleID constants
MAX_SIZE_CD = 734003200 # 700 MiB
HEADER_SIZE = 1000000 # how many bytes to read when attempting to manually detect game from raw data
CONSOLE_EXTS = { # https://emulation.gametechwiki.com/index.php/List_of_filetypes
    '32X':       {'32x'},                                     # Sega 32X
    '3DS':       {'3ds', 'cia'},                              # Nintendo 3DS
    'Amiga':     {'adf', 'adz', 'dms', 'ipf'},                # Amiga
    'Android':   {'apk', 'obb'},                              # Android
    'Dreamcast': {'bin', 'cdi', 'dat', 'gdi', 'lst'},         # Sega Dreamcast
    'GameGear':  {'gg'},                                      # Sega Game Gear
    'GB':        {'gb'},                                      # Nintendo GameBoy
    'GBA':       {'gba', 'srl'},                              # Nintendo GameBoy Advance
    'GBC':       {'gbc'},                                     # Nintendo GameBoy Color
    'GC':        {'cso', 'gcm', 'gcz', 'iso', 'rvz'},         # Nintendo GameCube
    'Genesis':   {'gen', 'md', 'smd'},                        # Sega Genesis
    'N64':       {'n64', 'ndd', 'v64', 'z64'},                # Nintendo 64
    'NDS':       {'app', 'dsi', 'ids', 'nds', 'srl'},         # Nintendo DS
    'NES':       {'fds', 'nes', 'nez', 'unf', 'unif'},        # Nintendo Entertainment System
    'NGP':       {'ngp'},                                     # SNK Neo Geo Pocket
    'NGPC':      {'ngpc'},                                    # SNK Neo Geo Pocket Color
    'PCE':       {'pce'},                                     # PC Engine
    'PS2':       {'bin', 'chd', 'cso', 'cue', 'iso'},         # Sony PlayStation 2
    'PSP':       {'cso', 'iso'},                              # Sony PlayStation Portable
    'PSX':       {'bin', 'chd', 'cue', 'ecm', 'iso'},         # Sony PlayStation
    'PSV':       {'vpk'},                                     # Sony PlayStation Vita
    'SNES':      {'sfc', 'smc', 'swc'},                       # Super Nintendo Entertainment System
    'Switch':    {'nsp', 'xci'},                              # Nintendo Switch
    'VB':        {'vb'},                                      # Nintendo Virtual Boy
    'Wii':       {'cso', 'gcz', 'iso', 'rvz', 'wad', 'wbfs'}, # Nintendo Wii
    'WS':        {'ws'},                                      # Bandai WonderSwan
    'WSC':       {'wsc'},                                     # Bandai WonderSwan Color
    'XBOX':      {'iso', 'xiso'},                             # Microsoft XBOX
    'XBOX360':   {'iso'},                                     # Microsoft XBOX 360
}
EXT2CONSOLE = {ext:console for console in CONSOLE_EXTS for ext in CONSOLE_EXTS[console] if len([c for c,es in CONSOLE_EXTS.items() if ext in es]) == 1}
ISO9660_EXTS = {'bin', 'cue', 'iso'}

# parse user arguments
def parse_args():
    # run argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True, type=str, help="Input Game File")
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File")
    args = parser.parse_args()

    # check input game file
    args.input = abspath(expanduser(args.input))
    check_exists(args.input)

    # check output file
    if args.output != 'stdout':
        check_not_exists(args.output)

    # all good, so return args
    return args

# identify a disc
def identify_disc(fn, bufsize=DEFAULT_BUFSIZE):
    # check root files
    try:
        # if directory, get root files directly
        if isdir(fn):
            iso = None; root_files = {s.split('/')[-1].rstrip(';1').strip().upper():s for s in glob('%s/*' % fn)}

        # if image, get root files from ISO 9660
        else:
            iso = ISO9660(fn)
            root_files = {tup[0].lstrip('/').rstrip(';1').strip().upper():tup for tup in iso.iter_files(only_root_dir=True)}

        # check PSP
        if 'UMD_DATA.BIN' in root_files:
            return 'PSP'

        # check Neo Geo CD
        elif 'IPL.TXT' in root_files:
            return 'NeoGeoCD'

        # check PSX/PS2
        elif 'SYSTEM.CNF' in root_files:
            if isinstance(root_files['SYSTEM.CNF'], str): # directory
                system_cnf = open(root_files['SYSTEM.CNF'], 'rb').read().decode()
            elif isinstance(root_files['SYSTEM.CNF'], tuple): # my ISO9660 implementation
                system_cnf = iso.read_file(root_files['SYSTEM.CNF']).decode()
            if 'BOOT2' in system_cnf:
                return 'PS2'
            elif 'BOOT' in system_cnf:
                return 'PSX'
    except:
        pass

# main logic to identify a console
def identify(fn, bufsize=DEFAULT_BUFSIZE):
    # set things up
    console = None

    # first try to identify console by file extension
    ext = get_extension(fn)
    if console is None and ext in EXT2CONSOLE:
        console = EXT2CONSOLE[ext]

    # next try to identify based on raw data from beginning of file
    if console is None and not isdir(fn):
        if ext == 'cue':
            f = open_file(bins_from_cue(fn)[0], mode='rb')
        else:
            f = open_file(fn, mode='rb')
        header = f.read(HEADER_SIZE); f.close()

        # check GameCube: https://hitmen.c02.at/files/yagcd/yagcd/chap13.html#sec13
        if console is None:
            for i in range(0x100): # 0x100 is arbitrary; too big = slow if not a GC game
                if header[i : i + 4] == GC_MAGIC_WORD:
                    console = 'GC'; break

        # check SegaCD (must do before Genesis, as SegaCD games have Genesis magic words too)
        if console is None:
            for magic_word in SEGACD_MAGIC_WORDS:
                for i in range(0x100): # 0x100 is arbitrary; too big = slow if not a SegaCD game
                    if header[i : i + len(magic_word)] == magic_word:
                        console = 'SegaCD'; break
                if console is not None:
                    break

        # check Genesis
        if console is None:
            for magic_word in GENESIS_MAGIC_WORDS:
                for i in range(0x100, 0x200): # # 0x200 is arbitrary; too big = slow if not a Genesis game
                    if header[i : i + len(magic_word)] == magic_word:
                        console = 'Genesis'; break
                if console is not None:
                    break

        # check Saturn
        if console is None:
            for i in range(0x100): # 0x100 is arbitrary; too big = slow if not a Saturn game
                if header[i : i + 0xF] == SATURN_MAGIC_WORD:
                    console = 'Saturn'; break

    # next try to identify ISO 9660 game (e.g. PSX, PS2, etc.)
    if console is None and (ext in ISO9660_EXTS or isdir(fn)):
        console = identify_disc(fn, bufsize=bufsize)

    # failed to identify console
    return console

# main program logic
def main():
    args = parse_args()
    console = identify(args.input)
    if console is None:
        error("Unable to identify console: %s" % args.input)
    f_out = open_file(args.output, 'wt'); print(console, file=f_out); f_out.close()

# run program
if __name__ == "__main__":
    main()
