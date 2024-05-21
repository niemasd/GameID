#! /usr/bin/env python3
'''
Extract bytes from a disc image (or general file)
'''
from gzip import open as gopen
from os.path import abspath, expanduser, getsize, isfile
import argparse
DEFAULT_BUFSIZE = 1000000

# parse user args
def parse_args():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input', required=True, type=str, help="Input File")
    parser.add_argument('-s', '--start', required=True, type=str, help="Starting Offset to Read")
    parser.add_argument('-n', '--num_bytes', required=True, type=str, help="Number of Bytes to Read")
    parser.add_argument('-o', '--output', required=False, type=str, default='stdout', help="Output File")
    args = parser.parse_args()
    return args

# open an output text file for writing (automatically handle gzip)
def open_output(fn, bufsize=DEFAULT_BUFSIZE):
    if fn == 'stdout':
        from sys import stdout; f_out = stdout.buffer
    elif fn.strip().lower().endswith('.gz'):
        f_out = gopen(fn, 'wb', compresslevel=9)
    else:
        f_out = open(fn, 'wb', buffering=bufsize)
    return f_out

# load `num_bytes` bytes starting at `start`
def load_bytes(in_fns, start, num_bytes, f_out, bufsize=DEFAULT_BUFSIZE):
    # seek over `start` bytes
    in_fn_ind = 0
    while start > 0:
        if in_fn_ind == len(in_fns):
            return
        curr_size = getsize(in_fns[in_fn_ind])
        if curr_size >= start:
            break
        else:
            start -= curr_size; in_fn_ind += 1
    if start > getsize(in_fns[in_fn_ind]):
        return
    f_in = open(in_fns[in_fn_ind], 'rb', buffering=bufsize)
    f_in.seek(start); start = 0

    # extract bytes
    while num_bytes > 0:
        while True:
            tmp_data = f_in.read(min(bufsize, num_bytes))
            if len(tmp_data) == 0:
                break
            f_out.write(tmp_data); num_bytes -= len(tmp_data)
        in_fn_ind += 1
        if in_fn_ind == len(in_fns):
            return
        f_in = open(in_fns[in_fn_ind], 'rb', buffering=bufsize)

# main program
if __name__ == "__main__":
    args = parse_args()
    if not isfile(args.input):
        print("File not found: %s" % args.input); exit(1)
    if args.output != 'stdout' and isfile(args.output):
        print("File exists: %s" % args.output); exit(1)
    try:
        args.start = int(args.start, 0)
    except:
        print("Invalid integer: %s" % args.start); exit(1)
    try:
        args.num_bytes = int(args.num_bytes, 0)
    except:
        print("Invalid integer: %s" % args.num_bytes); exit(1)
    if args.input.lower().endswith('.cue'):
        in_fns = ['%s/%s' % ('/'.join(abspath(expanduser(args.input)).split('/')[:-1]), l.split('"')[1].strip()) for l in open(args.input) if l.strip().lower().startswith('file')]
    else:
        in_fns = [args.input]
    if len(in_fns) == 0:
        print("Invalid input file: %s" % args.input)
    f_out = open_output(args.output)
    b = load_bytes(in_fns, args.start, args.num_bytes, f_out)
    f_out.close()
