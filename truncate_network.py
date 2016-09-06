# $Id: truncate_network.py 115 2010-03-19 20:40:28Z bbest $

import sys, os, time, tempfile, csv, ConfigParser, cm
import networkx as NX

# "D:\code\connmod\branches\tncpa\network\full\network.txt"   "1000" "tr1000" "d:\code\connmod\branches\tncpa\network\trunc\network_tr1000.txt"
# "D:\code\connmod\branches\ch\data\network\full\network.txt" "1500" "tr1500" "d:\code\connmod\branches\ch\data\network\trunc\network_tr1500.txt"
# E:\code\connmod\branches\ch\data\net2010\network.txt "1500 Unknown" tr1500 E:\code\connmod\branches\ch\data\net2010\network_tr1500.txt

# setup geoprocessor
GP = cm.gp_init()

# format paths
for i in range(0,len(sys.argv)):
    sys.argv[i] = sys.argv[i].replace('\\','/')

# arguments in
#PROBLEM: disregards actual units!
in_network_txt  = sys.argv[1]
if sys.argv[2] == '#':  # if no linear unit specified in optional eucthreshold parameter
    costthreshold = ''
else:
    costthreshold = int(sys.argv[2].split()[0])
out_network_fld = sys.argv[3]
out_network_txt = sys.argv[4]

# setup vars for out_network config
out_network  = os.path.splitext(out_network_txt)[0]
out_edgelist = out_network + '_edgelist.txt'
out_nodeattr = out_network + '_nodeattr.csv'
out_edgeattr = out_network + '_edgeattr.csv'

# logging
log = '%s/log.txt' % os.path.dirname(out_network)
cm.log_init(log, 'debug')

cm.log('Reading input network')
G = cm.read_network(in_network_txt)

cm.log('Trimming graph based on threshold cumulative cost %g' % costthreshold)
H = G.copy()
nlist = []
for n, z in G.nz.iteritems():
    if z >= costthreshold:
        H.remove_edges_from(G.edges(n))
        H.remove_node(n)
edges = H.edges(data=True)
for (u,v,w) in edges:
    if w['weight'] >= costthreshold:
        H.remove_edge(u, v)

cm.log('Trimming isolated nodes with 1 or 0 neighbors')
def gtrim(H):
    i = 0
    for n in H.nodes():
        print '%d' % n
        if n in H.nodes(): # may have deleted it already within loop
            if n == 126:
                print 'now what'
            nbrs = H.neighbors(n)
            if len(nbrs) == 1:
                i += 1
                print '  removing %d (nbr)' % nbrs[0]
                H.remove_node(nbrs[0])
            if len(nbrs) <= 1:
                i += 1
                print '  removing %d (node)' % n
                H.remove_node(n)
    return(i)
i=1; trim_iter = 0; trim_nodes = 0
while i != 0:
    i = gtrim(H)
    trim_nodes += i
    trim_iter += 1
cm.log('  %d nodes trimmed, over %d iterations of the graph' % (trim_nodes, trim_iter))    

cm.log('Copying network attributes to subset network')
H = cm.copy_g_attr(G,H)

H.config = {('network', 'edgelist'):out_edgelist,
            ('network', 'edgeattr'):out_edgeattr,
            ('network', 'nodeattr'):out_nodeattr,
            ('shapefile', 'projection'):G.config[('shapefile', 'projection')],
            ('shapefile', 'nodes'):G.config[('shapefile', 'nodes')],
            ('shapefile', 'edges'):G.config[('shapefile', 'edges')],
            ('surface', 'costdist'):G.config[('surface', 'costdist')],
            ('surface', 'tin'):G.config[('surface', 'tin')]}

cm.log('Updating membership field in nodes and edges shapefiles of full network')
cm.update_shp_fld(H, GP, out_network_fld)

cm.log('Write network to file')
cm.write_network(H, out_network_txt)

# see how easy it is to plot a graph in matlplotlib (aka pylab)
#import pylab as P
#cols = {'perimeter':1,'interior':2, 'centroid':3, 'exterior':4}
#NX.draw(H, pos=G.npos, with_labels=False, node_size=30, node_color=[cols[G.ntype[v]] for v in H])
#P.savefig(r'D:\code\bbest\thesis\figs\cm_ch_trunc_pylab.png')
#P.show()