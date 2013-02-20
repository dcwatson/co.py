#!/usr/bin/env python

import argparse
import datetime
import sys
import os
import re

# This could probably be an argument or platform-dependent, but Python likes \n, so we do too.
DEFAULT_LINE_ENDING = b'\n'

# Some files have a -*- coding: XXX -*- (or similar) line that must be at the top.
coding_regex = re.compile(b'coding[:=]\\s*([-\\w.]+)')

def make_copyright(args, copy_from=None):
    years = '%04d-%04d' % (copy_from, args.year) if copy_from and args.update else '%04d' % args.year
    name = ' %s' % args.name if args.name else ''
    return '%s Copyright %s%s' % (args.comment, years, name)

def add_copyright(data, args):
    lines = data.splitlines(True)
    copyright_regex = re.compile(b'^' + re.escape(args.comment.encode('ascii')) + b'\\s*Copyright[^\\d]+(?P<from>\\d{4})', re.I)
    copy_line = None
    copy_from = None
    insert_line = 0
    line_ending = DEFAULT_LINE_ENDING
    for idx, line in enumerate(lines[:args.check_lines]):
        if idx == 0 and line:
            if line.startswith(b'#!'):
                insert_line += 1
            if line.endswith(b'\r\n'):
                line_ending = b'\r\n'
            elif line.endswith(b'\r'):
                line_ending = b'\r'
        if idx in (0, 1) and coding_regex.search(line):
            insert_line += 1
        match = copyright_regex.match(line)
        if match:
            copy_line = idx
            copy_from = int(match.groupdict()['from'])
            break
    # TODO: add encoding argument instead of assuming UTF-8
    copyright = make_copyright(args, copy_from).encode('utf-8') + line_ending
    if copy_line is not None:
        lines[copy_line] = copyright
    else:
        lines.insert(insert_line, copyright)
        if not args.no_newline:
            lines.insert(insert_line + 1, line_ending)
    if args.strip:
        for idx in range(len(lines)):
            lines[idx] = lines[idx].rstrip() + DEFAULT_LINE_ENDING
    return b''.join(lines)

def fix_file(path, args):
    if not args.quiet:
        sys.stdout.write(path)
        sys.stdout.write(b'\n')
        sys.stdout.flush()
    if args.print_only:
        return
    with open(path, 'rb') as fp:
        new_data = add_copyright(fp.read(), args)
    if args.backup:
        os.rename(path, path + '.bak')
    with open(path, 'wb') as fp:
        fp.write(new_data)

def scan_directories(args):
    ext = '.%s' % args.extension
    for path in args.path:
        if path.endswith(ext) and os.path.isfile(path):
            fix_file(os.path.abspath(path), args)
        else:
            for root, dirs, files in os.walk(path):
                for name in files:
                    if name.startswith('.') or not name.endswith(ext):
                        continue
                    fix_file(os.path.join(root, name), args)

if __name__ == '__main__':
    current_year = datetime.date.today().year
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', default=current_year, type=int, help='copyright year (default: %s)' % current_year)
    parser.add_argument('-n', '--name', help='copyright holder name')
    parser.add_argument('-u', '--update', action='store_true', help='updates any existing copyright instead of overwriting')
    parser.add_argument('-e', '--extension', default='py', help='file extension to scan (default: py)', metavar='ext')
    parser.add_argument('-c', '--comment', default='#', help='comment characters (default: #)', metavar='chars')
    parser.add_argument('-s', '--strip', action='store_true', help='strip trailing whitespace and convert line endings to UNIX')
    parser.add_argument('-b', '--backup', action='store_true', help='keep backup copies of the original files')
    parser.add_argument('-p', '--print-only', action='store_true', help='prints which files would be modified without changing them')
    parser.add_argument('-q', '--quiet', action='store_true', help='silence any output')
    parser.add_argument('--check-lines', default=5, type=int, help='number of lines to scan for existing copyright (default: 5)', metavar='num')
    parser.add_argument('--no-newline', action='store_true', help='do not insert an extra newline after adding a new copyright line')
    parser.add_argument('path', nargs='+', help='a file or directory')
    scan_directories(parser.parse_args())
