#! /usr/bin/env python3
'''
ConsoleID: Identify the console of a game
'''

# standard imports
from gzip import open as gopen
from os.path import abspath, expanduser, isdir, isfile
import argparse

# ConsoleID constants
DEFAULT_BUFSIZE = 1000000
FILE_MODES_GZ = {'rb', 'wb', 'rt', 'wt'}
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

# check if a file exists and throw an error if it doesn't
def check_exists(fn):
    if not isfile(fn) and not isdir(fn) and not fn.lower().startswith('/dev/'):
        error("File/folder not found: %s" % fn)

# open an output text file for writing (automatically handle gzip)
def open_file(fn, mode='rt', bufsize=DEFAULT_BUFSIZE):
    ext = fn.split('.')[-1].strip().lower()

    # standard output/input
    if fn == 'stdout':
        from sys import stdout as f
    elif fn == 'stdin':
        from sys import stdin as f

    # GZIP files
    elif ext == 'gz':
        if mode not in FILE_MODES_GZ:
            error("Invalid gzip file mode: %s" % mode)
        elif 'r' in mode:
            f = gopen(fn, mode)
        elif 'w' in mode:
            f = gopen(fn, mode, compresslevel=9)
        else:
            error("Invalid gzip file mode: %s" % mode)

    # Regular files
    else:
        f = open(fn, mode, buffering=bufsize)
    return f

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

# # main program logic
def main():
    args = parse_args()
    f_out = open_file(args.output, 'wt')

# run program
if __name__ == "__main__":
    main()
