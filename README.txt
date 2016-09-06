Installation and run-time instructions for ConnMod version 1.0 beta ...
______________________________________________________________________

1.  The connectivity tool now consists of 2 python scripts, create_network
    and network_leastcostpaths, which do all the work.  These are 
    implemented in the Arc ModelBuilder tool Network LCPs. 

2.  To run the tool, Edit it (do not Open it) and set all of the input
    and output files correctly.  Set the Arc Workspace first, then
    specify all paths as %Workspace%/<file>.  There are only 2 input
    files, the COST surface and the habitat PATCH shapefile.  If the
    habitat data is a binary raster grid, use the Prep Patches tool to
    convert it to a simplified shapefile.  Note that this will simplify
    the perimeters via BoundaryClean, so the output won't look exactly
    like the input.

    There are a lot of outputs.  These are written to a single folder, 
    which must exist before the tool is run (i.e., create it first).
    If this is called <workspace>/net, then all of the outputs should
    be specified as %Workspace%\net\<whatever>.  The actual names can
    be (should be) left as they are--including network, tin, costdist, 
    and so on.  Most of these are intermediate files and their names
    don't really matter.  Arc knows how to recognize partial names of
    files in the current environment (i.e., without the folders as
    prefixes); python does not. 

    Be meticulous about names:  the translation from Arc to Python can
    be awkward.  Also, avoid conventional illegal characters in file
    names, even if Windows let's you get away with it (i.e., do not 
    use hyphens etc.). 

    In the network_leastcostpath tool, specify a EUCDISTANCE threshold
    to save paths shorter than this distance.  Thus, to write network
    edges shorter than 5000 m, set this number.  If you do not set the
    threshold, all shortest paths will be computed and this will cream
    the model for large graphs.

    For small networks, specify the DBF output file for the LCPs. This 
    database is a 1:many look-up table that relates each line segment 
    to the least-cost path between pairs of nodes; one segment might be
    shared by a large number of paths.  See below for how to use this.
    For graphs with >>1000 nodes, the DBH output will likely exceed the
    2GB file size limit in Arc and the model will fail.  To avoid this,
    leave this field blank and specify a CSV output file instead (these
    are smaller files).  If the network is very dense, leave both fields
    blank--which will not write any path look-up tables.  In this case,
    the network is written in NetworkX format and the lengths of the 
    LCPs are available, but you will not be able to draw these paths in
    ArcMap.

3.  The main outputs for visualizing the network are the NODE and EDGES
    shapefiles in the <net> output folder.  The node shapefile has all
    of the nodes, including the intersections of the TIN built to 
    represent the COST surface.  To show just the centroids of the 
    patches, use a Query Definition to display the nodes.  Choose
    "NodeType" = "centroids" in the Query Builder to do this.

    Similarly, use a Query Definition to highlight the LCPs in the edge
    shapefile.  Specify "full_lc" = 1 in the Query Builder to draw only
    the LCPs between nodes that are within the threshold distance
    (EucDistance, above). Otherwise, all egdges will be displayed, 
    including all of the interstitial edges of the TIN. 
    
    To display a LC path between two nodes, relate the DBF paths file to
    the node file, select two nodes in the attribute table, and the line
    segments connecting these two nodes should be highlighted in the map.
    You must specify each node as a "to" and a "from" node, as the database
    does not know the direction in which the path was computed. 
    [This part still needs a little work!]


