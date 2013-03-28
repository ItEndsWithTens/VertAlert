
  --VertAlert 1.0.0--

    Find, display, and optionally round floating point plane coordinates in
  Source engine .vmf files. Standalone executables have no dependencies, Python
  script requires either Python 2.7 or 3.3. Supports Windows, Linux, and OS X.

    Latest release hosted at http://www.gyroshot.com/vertalert.htm

    Comments and questions can be sent by email to robert.martens@gmail.com or
  via Twitter to @ItEndsWithTens.


  --Usage--

    The standalone executables and Python script share the same parameters:

    vertalert [-h] [-f] [-fn FIXNAME] [-t THRESH]
              [-sl SNAPLO] [-sh SNAPHI] input

      -h, --help
        Shows usage information.

      -f, --fix
        Writes out a new .vmf with rounded coordinates. Will overwrite existing
      output file without prompting. If you use this flag, please be careful to
      rename the resulting file before building cubemaps; not only do cubemaps
      break if the filename changes after the fact, but you may not be able to
      build them at all if the filename is too long.

      -fn, --fixname
        The filename for use with --fix. The default is to append _VERTALERT to
      the end of the input filename, before the extension.

      -t, --thresh
        Threshold between snaplo and snaphi. A setting of 0 will display all
      float coordinates, effectively disabling rounding. Default snaplo * 0.2.

      -sl, --snaplo
        Coordinates with deviations less than thresh will be rounded to the
      nearest multiple of this value; said multiple also serves as the basis for
      calculating a coordinate's deviation. Default 1.

      -sh, --snaphi
        Coordinates with deviations equal to or greater than thresh will be
      rounded to the nearest multiple of this value. Default None.


  --Tech notes--

    VertAlert currently uses a very primitive means of examining the .vmf file,
  and as a side effect it only looks through VisGroups that you've enabled. The
  critic in me notes that this is born of my laziness, but I try to think of it
  as helping you narrow down the source of your problems, and lets you focus on
  fixing one area at a time.

    If the --fix flag is specified, and you've used a large enough threshold, 
  VertAlert will use the so-called "Banker's Rounding", where values of exactly
  0.5 will be rounded to the even number. If you'd rather use something else,
  you'll need to modify the Python script.

    When not using snaphi, brushes whose max deviation is less than thresh will
  have their float coordinates rounded, while brushes with even one coordinate
  equal to or greater than thresh will be left completely untouched. If you are
  using snaphi, on the other hand, coordinates are treated individually, and a
  given brush might have some rounded to snaplo and some to snaphi, depending on
  their distance from snaplo.

    The test map test_snaphi was created by using the spike tool to create an
  eight-sided spike measuring 64x64x64. Scaling the result down to 32x32x32
  produces a spike whose corner vertices (northeast, southwest, etc.) land at
  exactly 0.5 units between one grid line and the next. Duplicate the spike,
  then move the whole group slightly. Move the group back where it was, save,
  close, and reopen the file, and you should get an invalid solids error. Run
  VertAlert on the file, though, and those spikes should be corrected, allowing
  the vmf to open in Hammer without a problem.


  --Hammer setup--

    Through use of the --fix and --fixname options, the standalone version of
  this tool can be easily integrated with your Hammer compile options. Bring up
  the Run Map dialog in Hammer with F9, then click Edit next to the drop-down
  list of Configurations.

    Highlight Default, for the sake of this example, and click Copy. Provide a
  new name, I'll use "VertAlert (Default)" to demonstrate. Close the Run Map
  Configurations dialog box, then choose the new configuration from the list.

    Click New to be given a blank command, then hit Move Up until it's all the
  way at the top. Now, with it selected, use the right hand pane to set Command
  to point to the VertAlert executable, wherever you placed it.

    Next, set Parameters to $path\$file.$ext --fix so VertAlert will produce a
  new .vmf with all the problematic coordinates rounded. Check the box labeled
  "Ensure file post-exists:", and set its value to $path\$file_VERTALERT.vmf

    After that, it's simply a matter of going through each command (bsp, light,
  rad, Copy File, game) and replacing each instance of $path\$file with the
  alternative $path\$file_VERTALERT (though be careful with Copy File, you don't
  want to accidentally delete the .bsp file extension).

    Once finished, the program should be transparent. You work on the original
  VMF, the toolchain runs VertAlert to produce an altered file, compiles that
  instead, and launches the modified version for you. The original map file, and
  your original compile settings, remain untouched, and you can easily switch
  back to compiling things as usual.


  --Background--

    My original reason for developing VertAlert is moot, as it turns out. The
  initial motivation was the tendency of Hammer to occasionally throw some brush
  vertices off the grid ever so slightly upon opening a map, suggesting some
  sort of problem.

    That phenomenon is the result of the fact that the .vmf file format, in
  contrast to the older .rmf format, does not store actual vertices for the
  brushes it contains. Instead, it defines only three points per surface, the
  minimum necessary to define a plane in 3D space. Each brush is computed upon
  load, by intersecting the various planes that make up said object.

    Sometimes, however, the result can be a bit off. Computed vertices can end
  up slightly off of the grid, with floating point instead of integer positions.
  At my level of understanding, or lack thereof, I have little choice but to
  attribute this phenomenon to the mythical "rounding errors" that I love to
  dread plague the world of floating point operations.

    It so happens, however, that the first step in the map compilation process,
  VBSP, already accounts for this. Some admittedly informal testing shows that
  the program snaps everything to the nearest whole number if it's less than 0.2
  units away, which most (perhaps all) Hammer rounding errors are. This behavior
  can be readily demonstrated by compiling test_threshold.vmf, bundled with the
  VertAlert source distribution, as-is. It includes an outer wall brush that
  creates a 0.15 unit gap, exposing the inside of the map to the void, but VBSP
  handles it without issue.

    Since most of the larger errors are either the result of intentional brush
  rotations or accidental scales, and should be visually examined one by one,
  the --fix option is of limited utility unless combined with --snaphi.


  --Changes--

    1.0.0 - March 28th, 2013
      Add snaplo and snaphi parameters

    0.2.1 - January 1st, 2013
      Update fix_plane's use of string replace method

    0.2.0 - November 27th, 2012
      Added --thresh
      Added shebang line
      Fixed writing out OS-specific line endings

    0.1.0 - November 24th, 2012
      Initial release
