# $Id: network_leastcostpaths.py 123 2011-02-28 19:48:29Z bbest $

# TODO: revisit dbf and csv outputs

# H:\esm270\data\connectivity\network\network.txt # net_01 H:\esm270\data\connectivity\network\net_01.txt # #
# C:\temp\connectivity\network_cost\network.txt # Net_LC C:\temp\connectivity\network_cost\Net_LC.txt

import sys, os, time, tempfile, cm, csv
import networkx as NX

reload(cm)

# "R:\GraphGroup\chapel_hill\network\full\network.txt" "#" "full_lc" "R:\GraphGroup\chapel_hill\network\full_lc\network_lc.txt" "R:\GraphGroup\chapel_hill\network\full_lc\paths_lc.dbf" "R:\GraphGroup\chapel_hill\network\full_lc\paths_lc.txt"    
# "d:\code\connmod\branches\tncpa\network\trunc\network_tr1000.txt" "tr1000lc" "d:\code\connmod\branches\tncpa\network\lc\network_tr1000lc.txt" "d:\code\connmod\branches\tncpa\network\lc\network_tr1000lc.dbf"
# "d:\code\connmod\branches\ch\data\network\trunc\network_tr1000.txt" "tr1000lc2" "d:\code\connmod\branches\ch\data\network\lc\network_tr1000lc2.txt" "d:\code\connmod\branches\ch\data\network\lc\tbl_tr1000lc2.dbf"
# "D:\code\connmod\branches\ch\data\network\full\network_simpleinternal.txt" "" "lc_all" "d:\code\connmod\branches\ch\data\network\lc\network_lc_all.txt" "d:\code\connmod\branches\ch\data\network\lc\tbl_lc_all.dbf"
# "d:\code\connmod\branches\ch\data\network\full\network_simpleinternal.txt" "1000" "SimpIntLC" "d:\code\connmod\branches\ch\data\network\lc\network_SimpIntLC.txt" "d:\code\connmod\branches\ch\data\network\lc\tbl_SimpIntLC.dbf"
# "C:\CONN_01142008\fr_OUT_test\network.txt" "5000 Meters" "full_lcp" "C:\CONN_01142008\fr_OUT_test\network_lc.txt" "C:\CONN_01142008\fr_OUT_test\paths.dbf" "#"
# "D:\code\connmod\tamara\ConnMod1\NETWOR~2.PY"  "d:\code\connmod\tamara\fr_OUT_test\network.txt" "5000 Meters" "full_lcp" "d:\code\connmod\tamara\fr_OUT_test\network_lc.txt" "d:\code\connmod\tamara\fr_OUT_test\paths.dbf" "d:\code\connmod\tamara\fr_OUT_test\paths.txt"
# E:\code\connmod\branches\ch\data\net2010\network.txt # euc_na E:\code\connmod\branches\ch\data\net2010\network_euc_na.txt E:\code\connmod\branches\ch\data\net2010\network_euc_na_paths.dbf E:\code\connmod\branches\ch\data\net2010\network_euc_na_paths.csv
# E:\code\connmod\branches\ch\data\net2010d\network_trunc.txt # trunc_lc E:\code\connmod\branches\ch\data\net2010d\network_trunc_lc.txt E:\code\connmod\branches\ch\data\net2010d\network_trunc_lc_paths.dbf E:\code\connmod\branches\ch\data\net2010d\network_trunc_lc_paths.txt

# C:\temp\connectivity\network\cost_network.txt # net_cost_lc C:\temp\connectivity\network\net_cost_lc.txt # #

# Import Psyco if available: can greatly speed up Python code
try:
    import psyco
    psyco.full()
except ImportError:
    pass

# setup geoprocessor
GP = cm.gp_init()

# arguments in
in_network_txt  = sys.argv[1]
eucthreshold    = sys.argv[2]
net             = sys.argv[3]

dir_net = os.path.dirname(in_network_txt)
edges_fld = net
out_network_txt = '%s/%s.txt' % (dir_net, net)
paths_csv       = ''
wd              = net
GP.workspace    = wd

# setup vars for out_network config
if sys.argv[2] == '#':  # if no linear unit specified in optional eucthreshold parameter
    eucthreshold = ''
else:
    eucthreshold = int(sys.argv[2].split()[0])
out_network  = os.path.splitext(out_network_txt)[0]
out_lcpaths  = out_network + '_lcpaths.txt'
out_edgelist = out_network + '_edgelist.txt'
out_nodeattr = out_network + '_nodeattr.csv'
out_edgeattr = out_network + '_edgeattr.csv'

paths_tbl    = '%s/geodb.gdb/paths_%s' % (os.path.dirname(in_network_txt), net)

log = '%s/log_%s.txt' % (os.path.dirname(wd), net)
cm.log_init(log)

cm.log('Reading in network')
G = cm.read_network(in_network_txt)

cm.log('Converting network edge weights to integer')
for (u,v,d) in G.edges_iter(data=True):
    G.remove_edge(u,v)
    G.add_edge(u,v, weight=int(d['weight']))


H = NX.Graph() # setup empty subgraph to populate with edges

cm.log('Building centroid-to-centroid paths restricted by component using bidirectional_dijkstra')
Cs = NX.connected_component_subgraphs(G)
nC = len(Cs); paths = {}; nbunch = {}; iskip = 0
f = open(out_lcpaths, 'wb')
f.write('"centroid1","centroid2","dist","path"\n')
cw = csv.writer(f)
for iC,C in enumerate(Cs):
    C = cm.copy_g_nbytype(G,C)
    centroids = C.nbytype['centroid']; nc = len(centroids)
    #if iC >= 3: continue  # DEBUG
    cm.log('  component %d of %d: %d centroids => %d lower triangle adjacency matrix pairs to add' % (iC + 1, nC, nc, (pow(nc,2) - nc)/2))
    cpaths = cm.adj_lower_tri(centroids, G, eucthreshold)
    i = 0; np = len(cpaths)
    cm.log('  component %d: calculating %d centroid-to-centroid least-cost paths limited by eucdistance' % (iC + 1, len(cpaths)))
    t0 = time.time();
    for (d,(c1, c2)) in cpaths:
        i += 1;
        if i % 10 == 0:                                  # show timed progress per component at path calculation intervals
            dt = time.time() - t0; ti = dt/i; tend = (np - i)*ti
            msg = '    path %d of %d (%d skipped) - min: %.1f in, %.1f to go' % (i, np, iskip, dt/60, tend/60); cm.log(msg)
        if not cm.adj_has_key(paths,c1,c2):
            d, p = NX.bidirectional_dijkstra(C, c1, c2)  # real work is here to calculate shortest path
            cm.add_edge_attr(c1,c2,paths,(d, p))         # add path
            nbunch.update({}.fromkeys(p))                # add nodes
            cw.writerow([c1,c2,d,p])                     # write path to text file
            # add edges to subgraph
            for x in range(len(p)-1):
                H.add_edge(p[x], p[x+1], weight=G[p[x]][p[x+1]]['weight'])

            # extract any intermediary least-cost centroid-to-centroid paths between c1 and c2 for efficiency sake
            cp = set(centroids) & set(p)                        # get unique set of centroids in path
            if len(cp) > 2:                                     # if more than 2 centroids, then has intermediary least-cost centroid-to-centroid paths
                cc = cm.list_lower_tri(list(cp), [])            # get all unique centroid-to-centroid pairs
                for cc1,cc2 in cc:                              # iterate through centroid pairs
                    if not cm.adj_has_key(paths, cc1, cc2):     # if lc path not already calculated
                        idx = [p.index(cc1),p.index(cc2)]       # get indexes to centroids in original path
                        pp = p[min(idx):max(idx)+1]             # get path between indexes
                        w = cm.get_path_weight(pp,G)            # get cumulative edge weight
                        cm.add_edge_attr(cc1,cc2,paths,(w, pp)) # add path
                        cw.writerow([cc1,cc2,w,pp])             # write path to text file
        else: iskip += 1
f.close()

cm.log('Getting subgraph of unique nodes in paths')
##H = G.subgraph(nbunch)

cm.log('Copying network attributes to subset network')
H = cm.copy_g_attr(G,H)

cm.log('Copying node and edge attributes into subgraph')
H = cm.copy_g_attr(G,H)
H.config = {('network', 'edgelist'):out_edgelist,
            ('network', 'edgeattr'):out_edgeattr,
            ('network', 'nodeattr'):out_nodeattr,
            ('shapefile', 'nodes'):G.config[('shapefile', 'nodes')],
            ('shapefile', 'edges'):G.config[('shapefile', 'edges')],
            ('surface', 'costdist'):G.config[('surface', 'costdist')],
            ('surface', 'tin'):G.config[('surface', 'tin')],
            ('leastcostpaths', 'txt'):out_lcpaths,
            }

cm.log('Adding/updating membership field from full network nodes and edges shapefiles')
cm.update_shp_fld(H, GP, edges_fld)

cm.log('Writing network to file: %s' % out_network_txt)
cm.write_network(H, out_network_txt)

# commenting out writing of table to dbf, since 2GB max
# 1) optional outputs for: dbf/csv/mdb
# 2) fxnality, :
#    * metric - 1:1 - edge betweenness of given path -- could do NX fxn instead (seperate fxn)
#    * display - 1:many - paths passing through given edge
#       a) ArcMap VB utility to parse the paths (slow)
#       b) use long relational srxr below
#    * display - 1:many - given path between two centroids


#if paths_dbf:
cm.log('Writing paths to table %s for relating to edges shapefile' % os.path.basename(paths_tbl))
GP.CreateTable(os.path.dirname(paths_tbl), os.path.basename(paths_tbl))
GP.AddField(paths_tbl, 'PathID', 'TEXT')
GP.AddField(paths_tbl, 'PathDist', 'LONG')
GP.AddField(paths_tbl, 'EdgeID', 'LONG')
GP.AddField(paths_tbl, 'FromNode', 'LONG')
GP.AddField(paths_tbl, 'ToNode', 'LONG')
rows = GP.InsertCursor(paths_tbl)
for c1, d in paths.iteritems():
    for c2,(dist, path) in d.iteritems():
        for i,n1 in enumerate(path[0:-1]):
            n2 = path[i+1]
            eid = H.eid[n1][n2]
            row = rows.NewRow()
            row.SetValue('EdgeID', eid)
            row.SetValue('PathID', str((c1,c2)))
            row.SetValue('PathDist', dist)
            row.SetValue('FromNode', c1)
            row.SetValue('ToNode', c2)
            rows.InsertRow(row)
del rows
try:
    del row
except NameError:  #skip if row doesn't exist b/c of zero least-cost paths
    pass

if paths_csv:
    # writing to text file
    cm.log('Writing paths to csv table for relating to edges shapefile')    
    f = open(paths_csv, 'wb')
    f.write('"ObjectID","EdgeID","PathID","PathDist","FromNode","ToNode"\n')  # note that ObjectID required for relating csv
    csvf = csv.writer(f)
    j = 0
    for c1, d in paths.iteritems():
        for c2,(dist, path) in d.iteritems():
            for i,n1 in enumerate(path[0:-1]):
                j+=1
                n2 = path[i+1]
                eid = H.eid[n1][n2]
                csvf.writerow([j, eid, str((c1,c2)), dist, c1, c2])  # write path to text file
    f.close()


GP.SetParameterAsText(3,out_network_txt)

