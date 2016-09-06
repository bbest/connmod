# $Id: simplify_internal_edges.py 98 2007-05-07 21:03:20Z bbest $

import sys, os, time, tempfile, csv, ConfigParser, cm
import networkx as NX

# "D:\code\connmod\branches\tncpa\network\full\network.txt"   "tr1000" "d:\code\connmod\branches\tncpa\network\trunc\network_tr1000.txt"
# "D:\code\connmod\branches\ch\data\network\full\network.txt" "SimpleInternal" "d:\code\connmod\branches\ch\data\network\full\network_simpleinternal.txt"

# setup geoprocessor
GP = cm.gp_init()

# format paths
for i in range(0,len(sys.argv)):
    sys.argv[i] = sys.argv[i].replace('\\','/')

# arguments in
in_network_txt  = sys.argv[1]
out_network_fld = sys.argv[2]
out_network_txt = sys.argv[3]

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

# PROBLEM: patches sharing same node, ie edge
#Identity_analysis full\nodes patches D:\code\connmod\branches\ch\data\network\full_2\nodes_identity.shp ALL "" KEEP_RELATIONSHIPS

cm.log('Removing existing internal nodes (%d) and edges (%d)' % (len(G.nbytype['internal']), len(G.ebytype['internal'])))
H = G.copy()
H.delete_edges_from(G.ebytype['internal'])
H.delete_nodes_from(G.nbytype['internal'])
cm.copy_g_attr(G, H)

cm.log('Adding edges from centroids (%d) to perimeter nodes (%d)' % (len(G.nbytype['centroid']), len(G.nbytype['perimeter'])))
centroids = G.nbytype['centroid']
patch_centroids = {}
for c in centroids: patch_centroids[G.npatchid[c]] = c
eid = max(G.ebyid.keys())
#cur = GP.InsertCursor(edges_shp)
for n in G.nbytype['perimeter']:
	c = patch_centroids[G.npatchid[n]]
	H.add_edge(n, c, 0)  # assume 0 weight for internal edges
	eid += 1
	cm.add_edge_attr(n, c, H.eid, eid)
	H.ebyid[eid] = (n,c)
	cm.add_edge_attr(n, c, H.etype, 'internal')
	H.ebytype['internal'] = (n,c)
	# add to shapefile: TODO
	#newrow = cur.NewRow()
	#pt H.nx[n]

H.config = {('network', 'edgelist'):out_edgelist,
            ('network', 'edgeattr'):out_edgeattr,
            ('network', 'nodeattr'):out_nodeattr,
            ('shapefile', 'projection'):G.config[('shapefile', 'projection')],
            ('shapefile', 'nodes'):G.config[('shapefile', 'nodes')],
            ('shapefile', 'edges'):G.config[('shapefile', 'edges')],
            ('surface', 'costdist'):G.config[('surface', 'costdist')],
            ('surface', 'tin'):G.config[('surface', 'tin')]}

##cm.log('Updating membership field in nodes and edges shapefiles of full network')
##cm.update_shp_fld(H, GP, out_network_fld)

cm.log('Write network to file')
cm.write_network(H, out_network_txt)

### see how easy it is to plot a graph in matlplotlib (aka pylab)
##import pylab as P
##cols = {'perimeter':1,'internal':2, 'centroid':3, 'external':4}
##NX.draw(H, pos=G.npos, with_labels=False, node_size=30, node_color=[cols[G.ntype[v]] for v in H])
###P.savefig(r'D:\code\bbest\thesis\figs\cm_ch_trunc_pylab.png')
##P.show()