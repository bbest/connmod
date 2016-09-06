# $Id: network_centrality.py 118 2010-04-26 04:33:39Z bbest $

import sys, os, time, tempfile, csv, cm, networkx as NX

# Running script network_centrality...
# <type 'exceptions.AttributeError'>: 'NoneType' object has no attribute 'getframe'
# Failed to execute (Network Centrality Metrics).
# E:\Ryman\scratch\cm_net01\network_trunc_lc.txt


# setup geoprocessor
GP = cm.gp_init()

# G: = \\nicknet.env.duke.edu\network\research\lel\GraphGroup
# G:\chapel_hill\network\full_lc\network_lc.txt
# easy_install -U networkx # got networkx-0.35.1
# E:\code\connmod\branches\ch\data\net2010\network_euc_na.txt


# get arguments
in_network_txt = sys.argv[1]

# initialize logging
log = '%s/log_centrality.txt' % os.path.dirname(in_network_txt)
cm.log_init(log) 

cm.log('Reading network configuration')
F = cm.read_network(in_network_txt)                # read in full network
nodes_shp   = F.config[('shapefile', 'nodes')]
lcpaths_txt = F.config[('leastcostpaths', 'txt')]
G = NX.Graph()                                    # create fresh graph

cm.log('Reading least-cost paths into fresh graph with only centroids')
rdr = csv.reader(open(lcpaths_txt,'r'))
headers = rdr.next()
for row in rdr:
    c1,c2,w = row[0:3]
    G.add_edge(int(c1), int(c2), weight=int(w))
    
cm.log('Calculating centrality metrics (only works with NetworkX 0.35.1 and higher)')
btwn = NX.centrality.betweenness_centrality(G, normalized=False, weighted_edges=True)
clsn = NX.centrality.closeness_centrality(G, v=None, weighted_edges=True)
degr = NX.centrality.degree_centrality(G)

cm.log('Adding fields in nodes shapefile if they do not already exist')
gp_flds = GP.ListFields(nodes_shp); f = gp_flds.next(); flds = []
while f:
    flds.append(f.Name); f = gp_flds.next()    
for f in ('NBetween', 'NClose', 'NDegree'):
    if f not in flds: GP.AddField(nodes_shp, f, 'FLOAT')

cm.log('Updating fields with centrality values for centroid nodes')
cur = GP.UpdateCursor(nodes_shp, '"NodeType" = \'centroid\'')
row = cur.Next()
while row:
    nid = row.GetValue('NodeID')
    if btwn.has_key(nid):
        row.SetValue('NBetween', btwn[nid])
        row.SetValue('NClose', clsn[nid])
        row.SetValue('NDegree', degr[nid])
        cur.UpdateRow(row)
    row = cur.Next()
del row, cur