# $Id: threshold_network.py 115 2010-03-19 20:40:28Z bbest $

# Calculate metrics as a function of threshold distance: # of components, max diameter, min diameter

import sys, os, time, tempfile, csv, ConfigParser, cm
import networkx as NX
import math, numpy as np

# "D:\code\connmod\branches\tncpa\network\full\network.txt"   "1000" "tr1000" "d:\code\connmod\branches\tncpa\network\trunc\network_tr1000.txt"
# "D:\code\connmod\branches\ch\data\network\full\network.txt" "1500" "tr1500" "d:\code\connmod\branches\ch\data\network\trunc\network_tr1500.txt"
# E:\code\connmod\branches\ch\data\net2010\network.txt "1500 Unknown" tr1500 E:\code\connmod\branches\ch\data\net2010\network_tr1500.txt
# E:\Ryman\scratch\cm_net01\network.txt E:\Ryman\scratch\cm_net01\network_thresholds.csv

# setup geoprocessor
GP = cm.gp_init()

# format paths
for i in range(0,len(sys.argv)):
    sys.argv[i] = sys.argv[i].replace('\\','/')

# arguments in
#PROBLEM: disregards actual units!
in_network_txt = sys.argv[1] # in_network_txt = r'E:\Ryman\scratch\cm_net01\network.txt'
out_csv        = sys.argv[2] # out_csv = r'E:\Ryman\scratch\cm_net01\network_thresholds.csv'

# logging
log = '%s/log.txt' % os.path.dirname(out_csv)
cm.log_init(log, 'debug')

##cm.log('Reading input network')
##G = cm.read_network(in_network_txt)
##
### get unique sorted list of edge weights from graph
##edge_weights = sorted(set([int(d['weight']) for (u,v,d) in G.edges(data=True)]), reverse=True)
###i_msg = range(0,len(edge_weights), len(edge_weights)/20)[0:-1]
###i_msg.append(len(edge_weights))
###i_pct = range(0,101,100/20)
##
##out_f = open(out_csv, 'wb')
##writer = csv.writer(out_f)
##writer.writerow(['w_max', 'n_components']) # header
###for i, w_max in enumerate(edge_weights): # w_max = edge_weights[0]
##for i,w_max in enumerate([int(x) for x in np.linspace(max(edge_weights),0,100)]):
##    # get edges beyond w_max
##    ebunch = [(u,v) for (u,v,d) in G.edges(data=True) if d['weight'] > w_max]
##    H = G.copy()
##    #if i in i_msg: cm.log('  %d%% complete' % i_pct[i_msg.index(i)])
##    H.remove_edges_from(ebunch) 
##    n_comp = NX.algorithms.components.number_connected_components(H)
##    #NX.diameter(H) # very slow! TODO: other metrics http://networkx.lanl.gov/reference/algorithms.distance_measures.html
##    writer.writerow([w_max, n_comp])
##    cm.log('  %d%% complete (at w=%d, %d components)' % (i, w_max, n_comp))
##out_f.close()

# see how easy it is to plot a graph in matlplotlib (aka pylab)
import pylab as P
# read in data
out_f = open(out_csv, 'r')
reader = csv.reader(out_f)
reader.next()
n = []; w = []
for row in reader:
    w.append(int(row[0]))
    n.append(int(row[1]))
out_f.close()

# plot
w_log10 = [math.log10(v+1) for v in w]
n_log10 = [math.log10(v) for v in n]
P.plot(w_log10, n_log10, linewidth=1.0)
ax = P.gca()
ax.set_xlim(ax.get_xlim()[::-1])
P.xlabel('log10(max edge weight)')
P.ylabel('log10(number of components)')
P.title('Number of Components as a Function of Max Edge Weight')
P.grid(True)
P.show()

#cols = {'perimeter':1,'interior':2, 'centroid':3, 'exterior':4}
#NX.draw(H, pos=G.npos, with_labels=False, node_size=30, node_color=[cols[G.ntype[v]] for v in H])
#P.savefig(r'D:\code\bbest\thesis\figs\cm_ch_trunc_pylab.png')
#P.show()