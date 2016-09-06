#   Assess graph connectivity in terms of a threshold distance (edge
#   weight) or sequence of these, to look at how a graph connects 
#   as the threshold distance is systematically increased.
#
#   Contains 4 functions, as they would be used in sequence.

#   Dean Urban September 29, 2007)

import sys, os, time, tempfile, csv, cm, networkx as NX

# setup geoprocessor
GP = cm.gp_init()

# Get arguments:

in_network_txt = sys.argv[1]	# the textfile that locates all the graph stuff
wt_min = sys.argv[2]		# minimum edge weight
wt_max = sys.argv[3]		# max weight
wt_inc = sys.argv[4]		# increment for thresholding sequence (loop)
out_csv = sys.argv[5]		# output CSV file (generates a plot, not an Arc object)

# initialize logging
log = '%s/log_thresholding.txt' % os.path.dirname(in_network_txt)
cm.log_init(log) 

cm.log('Reading network configuration')
F = cm.read_network(in_network_txt)                # read in full network
#nodes_shp   = F.config[('shapefile', 'nodes')]
lcpaths_txt = F.config[('leastcostpaths', 'txt')]
G = NX.XGraph()                                    # create fresh graph

cm.log('Reading least-cost paths into fresh graph with only centroids')
rdr = csv.reader(open(lcpaths_txt,'r'))
headers = rdr.next()
for row in rdr:
    c1,c2,w = row[0:3]
    G.add_edge(int(c1), int(c2), int(w))


# Process and write output:
cm.log('Creating sequence of thresholded networks')
Gts = edge_threshold_sequence(G, wt_min, wt_max, wt_inc)
cm.log('Finding NC and graph diameter of largest component for sequence')
Gcs = graph_comp_sequence(Gts)
cm.log('Writing output file')
write_graph_comp_sequence(Gcs, out_csv)


def edge_threshold(G, max_wt):
    import networkx as nx
    """
    Accepts a (dense) weighted graph (XGraph) and a threshold weight,
    returnsa new graph with only edges for which the weight is
    less than the threshold.  The weights are general but this has been
    designed for (and tested with) distances.

    Usage:  if G is a XGraph with edges < 5000 m, 
    >>> G2 = edge_threshold(G, 3000)
    returns a new graph with edges < 3000 m.

    DL Urban (22 Feb 2007)    
    """
    tG = nx.XGraph()       	# create an empty graph
    nbunch = G.nodes()
    tG.add_nodes_from(nbunch)   # copy the nodes

    for edge in G.edges():
        (tn, fn, w) = edge
        if w <= max_wt:  
            tG.add_edge(edge)
    return tG


def edge_threshold_sequence(G, min_wt, max_wt, winc):
    import networkx as nx
    """
    Accepts a (dense) graph and systematically redefine its
    edges by edge-thresholding it in a loop of calls to
    edge_threshold (above), the loop provided by a min, max,
    and increment.  Note (below) that the increment is added to
    the max_wt to make sure max_wt is included in the range 
    (this is because of the way python does loops).
    Returns a dictionary of graphs keyed by the threshold weights.

    Usage:  if G is a dense XGraph with edge weights <= 10000 m, 
    >>> Gts = edge_threshold_sequence(G,1000,10000,1000)
    returns a dictionary of of 10 new graphs keyed by the numbers
    1000-10000.  To grab one:
    >>> G4000 = Gts[4000]

    DL Urban (22 Feb 2007)
    """

    Gts = {}
    nbunch = G.nodes()
    edges = G.edges()

    for wt in range(min_wt, max_wt+winc, winc):
        tGw = nx.XGraph()
        tGw.add_nodes_from(nbunch)
        for e in edges:
            (n1, n2, w) = e
            if w <= wt:  
                tGw.add_edge(e)
        Gts[wt] = tGw
    return Gts


#   Assess a dictionary of graphs keyed by dispersal distance
#   threshold, in terms of number of components and diameter.

def graph_comp_sequence(Gts):
    import networkx as nx
    """
    Gts is a graph thresholding sequence, a dictionary of graphs
    keyed by threshold distance, see edge_threshold_sequence().
    This function takes that sequence and returns the number of
    components in each graph, along with the diameter of the
    largest component in each graph. The output is a dictionary of
    tuples (NC, D(G)) keyed by threshold distance.

    Requires:  x_diameter(G), local function.

    Usage:  The output is intended to be printed to a file (see
    write_table.txt for syntax), so that a plot can be constructed
    that illustrates the number of components and graph diameter
    as a function of distance.

    DL Urban (22 Feb 2007)
    """

    seq = Gts.keys()
    gcs = {}
    for d in seq:
        g = Gts[d]
        if nx.is_connected(g):
            nc = 1
            diam = x_diameter(g)
        else:
            nc = nx.number_connected_components(g)
            # the largest connected component, #0 in the list:
            gc = nx.connected_component_subgraphs(g)[0]
            diam = x_diameter(gc)
        gcs[d] = (nc, diam)
    return gcs


#   Write these out to a file:

def write_graph_comp_sequence(gcs, path):
    """
    Accept a graph component sequence from edge-thresholding, and
    write the output as a table to a file.

    Usage:  
    >>> Gts = edge_threshold_sequence(G, min, max, inc),
    >>> gcs = graph_conn_sequence(Gts)
    >>> write_graph_conn_sequence(gcs, path)

    DL Urban (22 Feb 2007)
    """

    f = open(path, 'w')
    f.write('%s\n' % 'Distance, NComps, Diameter')
    for k,v in gcs.iteritems():
        (nc, diam) = v
        f.write('%4d, %5d, %10.3f\n' % (k, nc, diam))
    f.close()



