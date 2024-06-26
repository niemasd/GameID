#! /usr/bin/env python3
'''
Test ConsoleID.py and GameID.py on a series of test files
'''

# imports
from glob import glob
from os.path import abspath, expanduser, isdir, isfile
from subprocess import check_output
import argparse
import sys

# constants
SELF_PATH = abspath(expanduser(__file__))
DEFAULT_CONSOLEID_PATH = SELF_PATH.replace('/scripts/test.py', '/ConsoleID.py')
DEFAULT_GAMEID_PATH = SELF_PATH.replace('/scripts/test.py', '/GameID.py')
DEFAULT_GAMEID_DB_PATH = SELF_PATH.replace('/scripts/test.py', '/db.pkl.gz')
DEFAULT_TEST_FILES_PATH = SELF_PATH.replace('/scripts/test.py', '/example')

# parse user args
def parse_args():
    # run argparse
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-c', '--consoleid_path', required=False, type=str, default=DEFAULT_CONSOLEID_PATH, help="Path to ConsoleID.py script")
    parser.add_argument('-g', '--gameid_path', required=False, type=str, default=DEFAULT_GAMEID_PATH, help="Path to GameID.py script")
    parser.add_argument('-d', '--gameid_db_path', required=False, type=str, default=DEFAULT_GAMEID_DB_PATH, help="Path to GameID database")
    parser.add_argument('-t', '--test_files_path', required=False, type=str, default=DEFAULT_TEST_FILES_PATH, help="Path to folder containing test files")
    parser.add_argument('-q', '--quiet', action="store_true", help="Suppress messages")
    args = parser.parse_args()

    # check args and return
    for fn in [args.consoleid_path, args.gameid_path, args.gameid_db_path]:
        if not isfile(fn):
            print("File not found: %s" % fn); exit(1)
    args.test_files_path = args.test_files_path.rstrip('/')
    if not isdir(args.test_files_path):
        print("Directory not found: %s" % args.test_files_path); exit(1)
    return args

# get bins from CUE
def bins_from_cue(fn):
    f_cue = open(fn, 'rt')
    bins = ['%s/%s' % ('/'.join(abspath(expanduser(fn)).split('/')[:-1]), l.split('"')[1].strip()) for l in f_cue if l.strip().lower().startswith('file')]
    f_cue.close()
    return bins

# run tests
def run_tests(consoleid_path, gameid_path, gameid_db_path, test_files_path, quiet=False):
    # import GameID console list
    sys.path.append('/'.join(gameid_path.split('/')[:-1]))
    from GameID import GAMEID_CONSOLES
    sys.path.pop()

    # run tests
    num_pass = 0; num_fail = 0
    for console in GAMEID_CONSOLES:
        test_files = set(glob('%s/%s/*' % (test_files_path, console)))

        # remove other files associated with CUE files (which may fail on their own, e.g. multi-track discs)
        cue_files = {fn for fn in test_files if fn.split('.')[-1].lower() == 'cue'}
        for fn in cue_files:
            for bin_fn in bins_from_cue(fn):
                test_files.discard(bin_fn)

        # run test on current file
        for fn in test_files:
            consoleid_pass = True; gameid_pass = True

            # first check ConsoleID
            try:
                consoleid_out = check_output(['python3', consoleid_path, '-i', fn]).decode().strip()
                if consoleid_out.strip().upper() != console.upper():
                    consoleid_pass = False
            except:
                consoleid_pass = False
            if (consoleid_pass == False) and (not quiet):
                print("ConsoleID failed: %s" % fn)

            # then check GameID
            try:
                gameid_out = check_output(['python3', gameid_path, '-d', gameid_db_path, '-c', console, '-i', fn]).decode().strip()
            except:
                gameid_pass = False
            if (gameid_pass == False) and (not quiet):
                print("GameID failed: %s" % fn)

            # update global test results
            if consoleid_pass and gameid_pass:
                num_pass += 1
            else:
                num_fail += 1
    return num_pass, num_fail

# main program
if __name__ == "__main__":
    args = parse_args()
    num_pass, num_fail = run_tests(args.consoleid_path, args.gameid_path, args.gameid_db_path, args.test_files_path, quiet=args.quiet)
    if not args.quiet:
        print("Pass: %d" % num_pass)
        print("Fail: %d" % num_fail)
    exit(num_fail)
