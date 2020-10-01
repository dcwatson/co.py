#!/usr/bin/env python

import argparse
import datetime
import os
import re
import sys

# This could probably be an argument or platform-dependent, but Python likes \n, so we do too.
DEFAULT_LINE_ENDING = "\n"

# Some files have a -*- coding: XXX -*- (or similar) line that must be at the top.
coding_regex = re.compile("coding[:=]\\s*([-\\w.]+)")


def make_copyright(args, copy_from=None):
    years = "%04d-%04d" % (copy_from, args.year) if copy_from and args.update else "%04d" % args.year
    name = " %s" % args.name if args.name else ""
    return "%s Copyright %s%s" % (args.comment, years, name)


def compile_copyright_regex(comment):
    return re.compile("^" + re.escape(comment) + r"\s*Copyright[^\d]+(?P<from>\d{4})", re.I)


def add_copyright(data, args):
    lines = data.splitlines(True)
    copyright_regex = compile_copyright_regex(args.comment)
    copy_line = None
    copy_from = None
    insert_line = 0
    line_ending = DEFAULT_LINE_ENDING
    for idx, line in enumerate(lines[: args.check_lines]):
        if idx == 0 and line:
            if line.startswith("#!"):
                insert_line += 1
            if line.endswith("\r\n"):
                line_ending = "\r\n"
            elif line.endswith("\r"):
                line_ending = "\r"
        if idx in (0, 1) and coding_regex.search(line):
            insert_line += 1
        match = copyright_regex.match(line)
        if match:
            copy_line = idx
            copy_from = int(match.groupdict()["from"])
            break
    # TODO: add encoding argument instead of assuming UTF-8
    copyright = make_copyright(args, copy_from) + line_ending
    if copy_line is not None:
        lines[copy_line] = copyright
    else:
        lines.insert(insert_line, copyright)
        if not args.no_newline:
            lines.insert(insert_line + 1, line_ending)
    if args.strip:
        for idx in range(len(lines)):
            lines[idx] = lines[idx].rstrip() + DEFAULT_LINE_ENDING
    return "".join(lines)


def fix_file(path, args):
    if not args.quiet:
        sys.stdout.write(path)
        sys.stdout.write("\n")
    if args.print_only:
        return
    with open(path, "r", newline="") as fp:
        new_data = add_copyright(fp.read(), args)
    if args.backup:
        os.rename(path, path + ".bak")
    with open(path, "w") as fp:
        fp.write(new_data)


def check_file(path, args):
    copyright_regex = compile_copyright_regex(args.comment)
    
    with open(path) as fp:
        lines = fp.readlines()

    found = False
    for line in lines[: args.check_lines]:
        match = copyright_regex.match(line)
        
        # If copyright exists and is up to date:
        if match and match.group(1).endswith(str(args.year)):
            found = True
            break
    
    if not found:
        sys.stdout.write(path)
        sys.stdout.write("\n")
        
    return found


def scan_files(paths, extension):
    ext = ".%s" % extension
    for path in paths:
        if path.endswith(ext) and os.path.isfile(path):
            yield os.path.abspath(path)
        else:
            for root, dirs, files in os.walk(path):
                for name in files:
                    if name.startswith(".") or not name.endswith(ext):
                        continue
                    yield os.path.join(root, name)


def main(args):
    return_value = 0
    for path in scan_files(args.path, args.extension):
        if args.check:
            if not check_file(path, args):
                return_value = 1
        else:
            fix_file(path, args)

        sys.stdout.flush()

    return return_value


if __name__ == "__main__":
    current_year = datetime.date.today().year
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-y", "--year", default=current_year, type=int, help="copyright year (default: %s)" % current_year
    )
    parser.add_argument("-n", "--name", help="copyright holder name")
    parser.add_argument("--check", action="store_true", help="Check whether files should be formatted, rather than formatting them.")
    parser.add_argument(
        "-u", "--update", action="store_true", help="updates any existing copyright instead of overwriting"
    )
    parser.add_argument("-e", "--extension", default="py", help="file extension to scan (default: py)", metavar="ext")
    parser.add_argument("-c", "--comment", default="#", help="comment characters (default: #)", metavar="chars")
    parser.add_argument(
        "-s", "--strip", action="store_true", help="strip trailing whitespace and convert line endings to UNIX"
    )
    parser.add_argument("-b", "--backup", action="store_true", help="keep backup copies of the original files")
    parser.add_argument(
        "-p", "--print-only", action="store_true", help="prints which files would be modified without changing them"
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="silence any output")
    parser.add_argument(
        "--check-lines",
        default=5,
        type=int,
        help="number of lines to scan for existing copyright (default: 5)",
        metavar="num",
    )
    parser.add_argument(
        "--no-newline", action="store_true", help="do not insert an extra newline after adding a new copyright line"
    )
    parser.add_argument("path", nargs="+", help="a file or directory")
    
    sys.exit(main(parser.parse_args()))