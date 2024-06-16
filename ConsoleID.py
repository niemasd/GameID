#! /usr/bin/env python3
'''
ConsoleID: Identify the console of a game
'''

# standard imports
from glob import glob
from gzip import open as gopen
from os.path import abspath, expanduser, isdir, isfile
from sys import stderr
import argparse

# non-standard imports
from GameID import bins_from_cue, check_exists, DEFAULT_BUFSIZE, error, get_extension, getsize, ISO9660, ISO9660FP, open_file
from pycdlib import PyCdlib

# ConsoleID constants
MAX_SIZE_CD = 734003200 # 700 MiB
CONSOLE_EXTS = { # https://emulation.gametechwiki.com/index.php/List_of_filetypes
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
    'NGP':       {'ngp'},                                     # Neo Geo Pocket
    'NGPC':      {'ngpc'},                                    # Neo Geo Pocket Color
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
            root_files = {s.split('/')[-1].strip() for s in glob('%s/*' % fn)}

        # if image, get root files from ISO 9660
        else:
            iso = PyCdlib(); iso.open_fp(ISO9660FP(fn,'rb'))
            root_files = {f.file_identifier().decode().strip().upper():f for f in iso.list_children(iso_path='/')}

        # check PSP
        if 'UMD_DATA.BIN' in root_files:
            return 'PSP'

        # check PSX/PS2
        elif 'SYSTEM.CNF' in root_files or 'SYSTEM.CNF;1' in root_files:
            # first check image size
            if get_extension(fn) == 'cue':
                size = sum(getsize(b) for b in bins_from_cue(fn))
            else:
                size = getsize(fn)
            if size > MAX_SIZE_CD: # if image is larger than CD, must be PS2
                return 'PS2'
            else:
                return 'PSX/PS2' # TODO need to figure out how to distinguish PSX vs small PS2 images
    except:
        pass

    # check block size
    try:
        if ISO9660(fn).block_size == 2352: # assume all ISO 9660 images with a block size of 2352 are PSX games
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
