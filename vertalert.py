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


import decimal as dec
import os
import re
import sys


def get_dev(coord, snap):
    """
    Compute a coordinate's deviation from the nearest multiple of snap.

    Keyword arguments:
        coord: the coordinate to check
        snap: base value from which to compute deviation

    """
    orig = dec.Decimal(coord)
    rounded = (orig / snap).quantize(1, dec.ROUND_HALF_EVEN) * snap
    return abs(rounded - orig)


def get_max_dev(planes, snap):
    """
    Search a brush's planes for the largest deviation any one of its
    vertices' coordinates makes from the nearest multiple of snap.

    Keyword arguments:
        planes: list of strings representing the planes to check
        snap: base value from which to compute deviation

    """
    floats = []
    for plane in planes:
        # We're only looking for coordinates that were written to the
        # VMF as floating point values, perhaps in scientific notation.
        floats += re.findall(r'-?\d+\.\d+e?-?\d*', plane)
    devs = []
    for coord in floats:
        devs.append(get_dev(coord, snap))
    return max(devs)


def fix_plane(plane, thresh, snaplo, snaphi):
    """
    Find floating point coordinates in a plane, round to nearest multiple of
    snaplo or snaphi depending on computed deviation, and return corrected plane
    string.

    Keyword arguments:
        plane: string to search for floats
        thresh: threshold between snaplo and snaphi
        snaplo: deviations less than thresh will be rounded to the nearest
                multiple of this value
        snaphi: deviations equal to or greater than thresh will be rounded to
                the nearest multiple of this value

    """
    floats = re.findall(r'-?\d+\.\d+e?-?\d*', plane)
    plane_new = plane
    for coord in floats:
        orig = dec.Decimal(coord)
        if get_dev(orig, snaplo) < thresh:
            rounded = (orig / snaplo).quantize(1, dec.ROUND_HALF_EVEN) * snaplo
        elif snaphi is not None:
            rounded = (orig / snaphi).quantize(1, dec.ROUND_HALF_EVEN) * snaphi

        # I want to remove trailing zeroes from the rounded results, and the
        # normalize method does that. Normalizing all values, however, will
        # introduce scientific notation for integers that end in a zero, so I
        # only modify values containing a decimal point. This is only cosmetic.
        if '.' in str(rounded):
            rounded = rounded.normalize()

        # I replace str(coord) instead of orig here, since
        # that would miss values using scientific notation.
        plane_new = plane_new.replace(str(coord), str(rounded), 1)

    return plane_new


def fix_brushes(brushes, thresh, vmf_in, snaplo, snaphi):
    """
    Find and fix brushes with floating point plane coordinates.

    Returns a tuple containing the total number of brushes whose coordinates
    were rounded, a list of tuples which pairs suspicious brush IDs with the
    greatest deviation any one of their coordinates makes from the nearest
    multiple of snaplo, and a fixed version of vmf_in.

    Keyword arguments:
        brushes: list of brush strings to search
        thresh: threshold between snaplo and snaphi
        vmf_in: string containing input VMF contents
        snaplo: deviations less than thresh will be rounded to the nearest
                multiple of this value
        snaphi: deviations equal to or greater than thresh will be rounded to
                the nearest multiple of this value

    """
    vmf_out = vmf_in
    rounded_count = 0
    percent = len(brushes) / 100.0
    suspects = []
    for i, brush in enumerate(brushes):
        brush_id = int(re.search(r'"id"\s"(\d+)"', brush).group(1))
        float_planes = []
        for plane in re.findall(r'"plane"\s".*?"', brush, re.DOTALL):
            if '.' in plane:
                float_planes.append(plane)
        if not float_planes:
            continue

        max_dev = get_max_dev(float_planes, snaplo)
        if max_dev < thresh or snaphi is not None:
            brush_new = brush
            for plane in float_planes:
                plane_new = fix_plane(plane, thresh, snaplo, snaphi)
                brush_new = brush_new.replace(plane, plane_new)
            vmf_out = vmf_out.replace(brush, brush_new)
            rounded_count += 1
        else:
            suspects.append((brush_id, max_dev))

        sys.stdout.write('\r%s%% complete' % str(int(i / percent)))
        sys.stdout.flush()

    sys.stdout.write("\r             \n")
    sys.stdout.flush()

    return (rounded_count, suspects, vmf_out)


def print_dev_table(suspects, rounded_count, fix):
    """
    Print, to stdout, a table displaying each brush ID and its
    coordinates' maximum deviation from the nearest multiple of snaplo.

    Keyword arguments:
        suspects: a list of tuples pairing brush id with max deviation
        rounded_count: the number of brushes whose coordinates were rounded
        fix: whether or not a modified VMF is being written to disk

    """
    if suspects:
        suspects = sorted(suspects, key=lambda suspect: suspect[-1])
        max_id_width = len(str(max(suspects[0])))
        left_w = max(max_id_width, len("Suspect ID"))
        header = ("Suspect ID").rjust(left_w) + '  ' + "Max dev" + '\n'
        sys.stdout.write(header)
        sys.stdout.write('-' * (len(header) - 1) + '\n')
        for suspect in suspects:
            left = str(suspect[0]).rjust(left_w)
            right = str(suspect[1])
            sys.stdout.write(left + "  " + right + "\n")
            sys.stdout.flush()
        sys.stdout.write('\n')

    if len(suspects) == 1:
        warn_suffix = ""
    else:
        warn_suffix = "es"
    if rounded_count == 1:
        action_suffix = ""
    else:
        action_suffix = "es"
    if fix:
        action = " automatically rounded"
    else:
        action = " ignored"

    sys.stdout.write(str(rounded_count) + " brush" +
                     action_suffix + action + '\n')
    sys.stdout.write(str(len(suspects)) + " suspect brush" +
                     warn_suffix + " remaining\n")
    sys.stdout.flush()


def vertalert(file_in, fix=False, fixname=None, thresh=None,
              snaplo=None, snaphi=None):
    """
    Find, display, and optionally round floating point plane coordinates in a
    Source engine .vmf file.

    Keyword arguments:
        file_in: .vmf file to check
        fix: write out a new file with rounded coordinates (default False)
        fixname: filename when using --fix (default appends _VERTALERT)
        thresh: threshold between snaplo and snaphi (default snaplo * 0.2)
        snaplo: deviations less than thresh will be rounded to the nearest
                multiple of this value (default 1)
        snaphi: deviations equal to or greater than thresh will be rounded to
                the nearest multiple of this value (default None)

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
    if snaplo is None:
        snaplo = dec.Decimal('1')
    if thresh is None:
        thresh = snaplo * dec.Decimal('0.2')

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
    rounded_count, suspects, vmf_out = fix_brushes(brushes, thresh, vmf_in,
                                                   snaplo, snaphi)

    print_dev_table(suspects, rounded_count, fix)

    if fix:
        with open(fixname, 'w') as vmf:
            vmf.write(vmf_out)
        sys.stdout.write("\nWrote " + fixname + "!\n")
        sys.stdout.flush()

    return 0


if __name__ == '__main__':
    import argparse
    PARSER = argparse.ArgumentParser(description="VertAlert 1.0.0")
    PARSER.add_argument("input", help="VMF to check")
    PARSER.add_argument(
        "-f", "--fix", help="write fixed up VMF", action="store_true")
    PARSER.add_argument(
        "-fn", "--fixname",
        help="filename to use with --fix (default appends _VERTALERT)")
    PARSER.add_argument(
        "-t", "--thresh",
        type=dec.Decimal,
        help="threshold below which to ignore/round coordinates "
             "(default snaplo * 0.2)")
    PARSER.add_argument(
        "-sl", "--snaplo",
        type=dec.Decimal,
        help="coordinates with deviations less than thresh will be rounded to "
             "the nearest multiple of this value (default 1)")
    PARSER.add_argument(
        "-sh", "--snaphi",
        type=dec.Decimal,
        help="coordinates with deviations equal to or greater than thresh will "
             "be rounded to the nearest multiple of this value (default None)")
    ARGS = PARSER.parse_args()

    vertalert(ARGS.input, ARGS.fix, ARGS.fixname, ARGS.thresh,
              ARGS.snaplo, ARGS.snaphi)
