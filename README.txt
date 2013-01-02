

  --VertAlert 0.1.0--
  
    Find, display, and optionally fix floating point vertex coordinates in
  Source engine .vmf files. Standalone executable has no dependencies, Python
  script requires either Python 2.7 or 3.3.
  
    Latest release hosted at http://www.gyroshot.com/vertalert.htm
  

  --Background--
  
    The .vmf file format, in contrast to the older .rmf format, does not store
  actual vertices for the brushes it contains. Instead, it defines only three
  points per surface, the minimum necessary to define a plane in 3D space. Each
  brush is computed upon load, by intersecting the various planes that make up
  said object.
  
    Sometimes, however, the result can be a bit off. Computed vertices can end
  up slightly off of the grid, with floating point instead of integer positions.
  At my level of understanding, or lack thereof, I have little choice but to
  attribute this phenomenon to the mythical "rounding errors" that I love to
  dread plague the world of floating point operations.
  
    Regardless of the cause, the only way I know of to prevent it is to avoid
  creating extreme, sharp angles, and not work with too small a grid. I have
  a problem with that in the form of the resulting creative limitations, but I
  also can't help pointing out that I've seen this issue while working at a grid
  size of 64 units, so I feel another solution is in order.
  
    Instead of building only chunky architecture, making my maps' more detailed
  flourishes chiefly out of models, or switching to a different engine
  altogether, I spent a couple of days writing this utility.


  --Usage--
  
    Whether using the standalone executable or the Python script, the parameters
  are the same:
  
    vertalert [-h] [-f] [-fn FIXNAME] input
    
      -h, --help
        Shows usage information.
        
      -f, --fix
        If present, writes out a new .vmf with rounded coordinates. See below to
        learn how you can add VertAlert to your normal workflow.
        
      -fn, --fixname
        The filename for use with --fix. The default is to append _VERTALERT to
        the end of the input filename, before the extension.

    Although the --fix option is attractive, and something you can use after the
  fact, I would recommend ignoring it if you can. Some of the brushes it
  calls out as suspect may be the result of accidental scaling, instead of the
  aforementioned rounding errors, and simply snapping them to the nearest whole
  number might have them still some distance from where you intended. Visual
  inspection is typically safest, and the earlier you get started the better, so
  I say use this program periodically as you build your map, and fix the
  displayed brushes by hand as you go.


  --Tech notes--

    The biggest, most important note I can provide is that once you've got a
  brush's vertices fixed, leave it alone. Moving, rotating, duplicating, or
  flipping a brush (among other operations, I imagine) seems to rub the Gods of
  Floating Point the wrong way.
  
    VertAlert currently uses a very primitive means of examining the .vmf file,
  and as a side effect it only looks through VisGroups that you've enabled. The
  critic in me notes that this is born of my laziness, but I try to think of it
  as helping you narrow down the source of your problems, and lets you focus on
  fixing one area at a time.
  
    If the --fix flag is specified, the program will use the so-called "Banker's
  Rounding", where values of exactly 0.5 will be rounded to the even number. If
  you'd rather use something else, you'll need to modify the Python script.
  
    
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
  to point to the vertalert executable, wherever you placed it.
  
    Next, set Parameters to $path\$file.$ext --fix so VertAlert will produce a
  new .vmf with all the problematic coordinates rounded. Check the box labeled
  "Ensure file post-exists:", and set its value to $path\$file_VERTALERT.vmf
  
    After that, it's simply a matter of going through each command (bsp, light,
  rad, Copy File, game) and replacing each instance of $path\$file with the
  alternative $path\$file_VERTALERT (though be careful with Copy File, you don't
  want to lose the .bsp file extension).
  
    Once finished, the program should be transparent. You work on the original
  VMF, the toolchain runs VertAlert to produce an altered file, compiles that
  instead, and launches the modified version for you. The original map file, and
  your original compile settings, remain untouched, and you can easily switch
  back to compiling things as usual.