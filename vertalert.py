# Copyright (c) 2012 Robert Martens <robert.martens@gmail.com>
# See file COPYING.txt for MIT license terms.


"""
Find floating point vertex coordinates in a Source engine .vmf file.

Looks through a .vmf for any brushsides whose vertices have non-integer
coordinates, printing a list to stdout and optionally writing out a new file
with rounded values. As a side effect of its brute force regex search, vertalert
only checks enabled VisGroups.

"""


import argparse
import decimal
import os
import re
import sys


def vertalert(file_in, fix=False, fixname=""):
    """
    Find floating point vertex coordinates in a Source engine .vmf file.

    Keyword arguments:
        file_in -- .vmf file to check
        fix -- write out a new file with rounded coordinates (default False)
        fixname -- filename when using --fix (default appends _VERTALERT)

    Please note this function currently only checks enabled VisGroups.

    """
    if not os.path.exists(file_in):
        sys.stderr.write("Could not find " + file_in + "!\n")
        return -1
    if os.path.splitext(file_in)[1] != ".vmf":
        sys.stderr.write("Input must be a .vmf file!\n")
        return -1

    # Can't forget to read the file in 'U'niversal newline mode, or the
    # search will produce different results across operating systems.
    with open(file_in, 'rU') as file:
        vmf_in = file.read()

    vmf_out = vmf_in
    brushes = re.findall(r'solid\n\t{.*?\n\t}', vmf_in, re.DOTALL)
    bad_ids = []
    for brush in brushes:
        brush_id = re.search(r'"id"\s"(\d+)"', brush).group(1)
        planes = re.findall(r'"plane"\s".*?"', brush, re.DOTALL)
        for plane in planes:
            # Hammer only writes a period character into each coordinate
            # if the value is actually a float. Integers are written to
            # the VMF as integer values.
            if '.' in plane:
                if brush_id not in bad_ids:
                    bad_ids.append(brush_id)
                plane_new = plane
                vertex_re = re.compile(r'\((.*?)\)\s\((.*?)\)\s\((.*?)\)')
                vertices = vertex_re.search(plane).groups()
                for vertex in vertices:
                    coords = vertex.split(' ')
                    for coord in coords:
                        if '.' in coord:
                            orig = decimal.Decimal(coord)
                            fixed = orig.quantize(1, decimal.ROUND_HALF_EVEN)
                            plane_new = plane_new.replace(str(orig), str(fixed))
                vmf_out = vmf_out.replace(plane, plane_new)

    # There might be dozens of questionable brushes, so I reverse the
    # list and print the total after the fact so you can examine the
    # earliest created brushes first, and keep an eye on your progress,
    # without having to scroll back up through the program's output.
    bad_ids.sort()
    bad_ids.reverse()
    for id in bad_ids:
        sys.stdout.write(id + '\n')
    bad_count = len(bad_ids)
    suffix = "es"
    if bad_count is 1:
        suffix = ""
    sys.stdout.write(str(bad_count) + " suspect brush" + suffix + "\n")

    if fix:
        if not fixname:
            out_base = os.path.splitext(file_in)
            fixname = out_base[0] + "_VERTALERT" + out_base[1]
        with open(fixname, 'w') as file:
            file.write(vmf_out)
        sys.stdout.write("Successfully wrote " + fixname + "!\n")

    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="VMF to check")
    parser.add_argument(
        "-f", "--fix", help="write fixed up VMF", action="store_true")
    parser.add_argument(
        "-fn", "--fixname",
        help="filename to use with --fix, default appends _VERTALERT suffix")
    args = parser.parse_args()
    vertalert(args.input, args.fix, args.fixname)