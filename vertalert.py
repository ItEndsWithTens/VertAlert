#!/usr/bin/env python
#
# Copyright (c) 2012, 2013 Robert Martens <robert.martens@gmail.com>
# See file COPYING.txt for MIT license terms.


"""
Find floating point vertex coordinates in a Source engine .vmf file.

Looks through a .vmf for any brush planes whose vertices have
non-integer coordinates, printing a list to stdout and optionally
writing out a new file with rounded values. As a side effect of its
brute force regex search, vertalert only checks enabled VisGroups.

"""


import decimal
import os
import re
import sys


def get_dev(coord):
    orig = decimal.Decimal(coord)
    rounded = orig.quantize(1, decimal.ROUND_HALF_EVEN)
    return max(rounded, orig) - min(rounded, orig)


def get_max_dev(planes):
    """
    Search a brush's planes for the largest deviation any of its
    vertices' coordinates make from the nearest integer.

    Keyword arguments:
        planes: list of strings representing the planes to check

    """
    floats = []
    for plane in planes:
        # We're only looking for coordinates that were written to the
        # VMF as floating point values, perhaps in scientific notation.
        floats += re.findall(r'-?\d+\.\d+e?-?\d*', plane)
    devs = []
    for coord in floats:
        devs.append(get_dev(coord))
    return max(devs)


def fix_plane(plane, regex):
    """
    Use 'regex' pattern to find floating point coordinates in 'plane',
    round to nearest integer, and return corrected plane string.

    Keyword arguments:
        plane: string to search for floats
        regex: Regular Expression pattern to use for search

    """
    floats = re.findall(regex, plane)
    plane_new = plane
    for coord in floats:
        orig = decimal.Decimal(coord)
        rounded = orig.quantize(1, decimal.ROUND_HALF_EVEN)
        # I replace str(coord) instead of orig here, since
        # that would miss values using scientific notation.
        plane_new = plane_new.replace(str(coord), str(rounded), 1)
    return plane_new


def fix_brushes(brushes, thresh, vmf_in):
    """
    Find and fix brushes with floating point plane vertex coordinates.

    Returns a tuple containing the total number of brushes with floats,
    a list of the greatest deviation any of a brush's coordinates makes
    from the nearest integer, and a fixed version of vmf_in. Corrects
    only deviations less than 'thresh'.

    Keyword arguments:
        brushes: list of brush strings to search
        thresh: threshold below which to ignore/round coordinates
        vmf_in: string containing input VMF contents

    """
    vmf_out = vmf_in
    float_brushes = 0
    percent = len(brushes) / 100.0
    devs = []
    for i, brush in enumerate(brushes):
        brush_id = int(re.search(r'"id"\s"(\d+)"', brush).group(1))
        float_planes = []
        for plane in re.findall(r'"plane"\s".*?"', brush, re.DOTALL):
            if '.' in plane:
                float_planes.append(plane)
        if not float_planes:
            continue
        else:
            float_brushes += 1
        max_dev = get_max_dev(float_planes)
        if max_dev < thresh:
            brush_new = brush
            for plane in float_planes:
                plane_new = fix_plane(plane, r'-?\d+\.\d+e?-?\d*')
                brush_new = brush_new.replace(plane, plane_new)
            vmf_out = vmf_out.replace(brush, brush_new)
        else:
            devs.append((brush_id, max_dev))
        sys.stdout.write('\r%s%% complete' % str(int(i / percent)))
        sys.stdout.flush()
    sys.stdout.write("\r             \n")
    sys.stdout.flush()
    return (float_brushes, devs, vmf_out)


def print_dev_table(devs, float_brushes, fix):
    """
    Print, to stdout, a table displaying each brush ID and its
    coordinates' maximum deviation from the nearest integer.

    Keyword arguments:
        sorted_devs: a list of tuples pairing brush id with max deviation

    """
    if devs:
        devs = sorted(devs, key=lambda dev: dev[-1])
        max_id_width = len(str(max(devs[0])))
        left_w = max(max_id_width, len("Suspect id"))
        header = ("Suspect ID").rjust(left_w) + '  ' + "Max dev" + '\n'
        sys.stdout.write(header)
        sys.stdout.write('-' * (len(header) - 1) + '\n')
        for dev in devs:
            dev_str = str(dev[0]).rjust(left_w) + "  " + str(dev[1]) + "\n"
            sys.stdout.write(dev_str)
            sys.stdout.flush()
        sys.stdout.write('\n')

        if len(devs) == 1:
            warn_suffix = ""
        else:
            warn_suffix = "es"
        if float_brushes - len(devs) == 1:
            action_suffix = ""
        else:
            action_suffix = "es"
        if fix:
            action = " automatically rounded"
        else:
            action = " ignored"

        sys.stdout.write(str(float_brushes - len(devs)) + " brush" +
                         action_suffix + action + '\n')
        sys.stdout.write(str(len(devs)) + " suspect brush" +
                         warn_suffix + " remaining\n")
        sys.stdout.flush()


def vertalert(file_in, fix=False, fixname=None, thresh=None):
    """
    Find, and optionally fix, floating point plane coordinates in a
    Source engine .vmf file.

    Prints a list to stdout of all values greater than or equal to
    thresh, rounds (when using --fix) or ignores all other values.

    Keyword arguments:
        file_in: .vmf file to check
        fix: write out a new file with rounded coordinates (default False)
        fixname: filename when using --fix (default appends _VERTALERT)
        thresh: threshold below which to ignore/round coordinates (default 0.2)

    Please note this function currently only checks enabled VisGroups.

    """
    if not os.path.exists(file_in):
        sys.stderr.write("Could not find " + file_in + "!\n")
        return -1
    if os.path.splitext(file_in)[1] != ".vmf":
        sys.stderr.write("Input must be a .vmf file!\n")
        return -1
    if fixname is None:
        in_name_split = os.path.splitext(file_in)
        fixname = in_name_split[0] + "_VERTALERT" + in_name_split[1]
    if thresh is None:
        thresh = decimal.Context().create_decimal('0.2')

    with open(file_in, 'r') as vmf:
        vmf_in = vmf.read()

    # I no longer read the input in universal line ending mode above,
    # as that changes the type of line endings written to the output
    # when using --fix. Although Hammer can deal with at least Windows
    # and Unix endings, I prefer to write out the same thing I read in.
    # The \r?\n in this regular expression became necessary to ensure
    # Windows, Linux and OS X worked the same way. The pattern is that
    # of the beginning of a solid entry, whose VisGroup is enabled, and
    # breaks down as follows:
    #
    # solid - The word 'solid'.
    # \r?\n - Zero or one carriage return followed by one newline. In
    #         Windows, \n is what \r\n is under Linux and OS X.
    # \t{ - Tab, open curly brace
    # .*? - Zero or more of any character (including newlines, thanks
    #       to my use of re.DOTALL in the call to findall), non-greedy.
    # \r?\n\t} - Zero or one carriage return, one newline, one tab,
    #            closing curly brace.
    brushes = re.findall(r'solid\r?\n\t{.*?\r?\n\t}', vmf_in, re.DOTALL)
    float_brushes, devs, vmf_out = fix_brushes(brushes, thresh, vmf_in)

    print_dev_table(devs, float_brushes, fix)

    if fix:
        with open(fixname, 'w') as vmf:
            vmf.write(vmf_out)
        sys.stdout.write("\nWrote " + fixname + "!\n")
        sys.stdout.flush()

    return 0


if __name__ == '__main__':
    import argparse
    PARSER = argparse.ArgumentParser(description="VertAlert 0.2.1")
    PARSER.add_argument("input", help="VMF to check")
    PARSER.add_argument(
        "-f", "--fix", help="write fixed up VMF", action="store_true")
    PARSER.add_argument(
        "-fn", "--fixname",
        help="filename to use with --fix (default appends _VERTALERT)")
    PARSER.add_argument(
        "-t", "--thresh",
        type=decimal.Decimal,
        help="threshold below which to ignore/round coordinates (default 0.2)")
    ARGS = PARSER.parse_args()

    vertalert(ARGS.input, ARGS.fix, ARGS.fixname, ARGS.thresh)
