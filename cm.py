# $Id: cm.py 122 2011-02-28 10:30:00Z bbest $

# Temporarily override networkx-1.0 read_edgelist, write_edgelist for handling weights dictionary
# with latest edgelist.py@1560, until incorporated into networkx-1.1
import networkx as NX, edgelist
NX.read_edgelist = edgelist.read_edgelist
NX.write_edgelist = edgelist.write_edgelist

def adj_has_key(a,u,v):
    if a.has_key(u):
        if a[u].has_key(v): return True
        else: return False
    else: return False

def gp_init(version=None):
    # initializing GP here so can access global variable later, eg log fxn
    global GP
    import arcgisscripting
    GP = arcgisscripting.create(version)
    GP.SetProduct('ArcInfo')
    GP.CheckOutExtension('3D')
    GP.CheckOutExtension('Spatial')
    GP.overwriteoutput = 1
    return GP

def adj_lower_tri(v, G, eucthreshold):
    # given a list of centroids v, append lower triangle adjacency matrix pairs paths list p
    # for assigning all possible pairs between centroid-to-centroid paths
    #total pairs = pow(len(v),2)/2 - len(v))
    debug = 0 
    import math
    p = []
    for row in xrange(len(v)):
        for col in xrange(row):
            n1 = v[row]; n2 = v[col]
            d = math.sqrt( math.pow(G.nx[n2] - G.nx[n1], 2) + math.pow(G.ny[n2] - G.ny[n1], 2))
            if debug: log('     d:%g <=? eucthreshold:%g' % (d,eucthreshold)) # debug
            # integers are less than strings, so eucthreshold = '' is still bigger than 1
            if d <= eucthreshold: p.append((d, (n1, n2)))
    p.sort()
    return p

def list_lower_tri(v, t=[]):
    # given a list v, append lower triangle adjacency matrix pairs as key to list t
    for row in xrange(len(v)):
        for col in xrange(row):
            t.append((v[row],v[col]))
    return t

def get_path_weight(p,G):
    # get weight along path
    w = 0
    for i, p1 in enumerate(p[0:len(p)-1]):
        w += G[p1][p[i+1]]['weight']
    return w

def get_pathkey(n1, n2, d):
    if d.has_key((n1,n2)): return(n1,n2)
    elif d.has_key((n2,n1)): return(n2,n1)
    else: return(False)

def log_init(log, leveltxt='info'):
    global logging
    import logging
    levelcod = {'info':logging.INFO,'debug':logging.DEBUG}
    logging.basicConfig(level=levelcod[leveltxt],
                    format='%(asctime)s %(levelname)s %(message)s',
                    filename=log, filemode='w')
    return logging
    
def log(msg, type='info'):
    print(msg)
    if type=='error':
        logging.error(msg)
        GP.AddError(msg)
        raise
    else:
        logging.info(msg)
        GP.AddMessage(msg)

def add_edge_attr(n1,n2,d,v):
    # helper function to add redundant keys for fast read access like d[n1][n2] and d[n2][n1],
    # similar to networkx graph.py add_edge
    ## old method a la networkx
    ##    if not d.has_key(n1):
    ##        d[n1] = {}
    ##    if not d.has_key(n2):
    ##        d[n2] = {}
    ##    d[n1][n2]=v
    ##    if n1!=n2:
    ##        d[n2][n1]=v
    d.setdefault(n1, {})[n2] = v  # see Python Cookbook p. 9
    d.setdefault(n2, {})[n1] = v

def init_g_attr(G):
    G.ntype = {}; G.nbytype = {}; G.npatchid = {}; G.nx = {}; G.ny = {}; G.nz = {}; G.npos = {}
    G.etype = {}; G.ebytype = {}; G.eid = {}; G.ebyid = {}
    G.nbytype['centroid'] = []; G.nbytype['internal'] = []; G.nbytype['perimeter'] = []; G.nbytype['external'] = []
    G.ebytype['boundary'] = []; G.ebytype['internal'] = []; G.ebytype['perimeter'] = []; G.ebytype['external'] = []
    return G

def copy_g_attr(G,H):
    # copy dictionaries from one graph to the other one (assume a subgraph = fewer nodes and edges)
    # b/c the networkx copy is only for a "shallow" copy

    H = init_g_attr(H)          # initialize attributes
    for n in H.nodes():         # nodes
        H.nx[n] = G.nx[n]
        H.ny[n] = G.ny[n]
        H.nz[n] = G.nz[n]
        H.npatchid[n] = G.npatchid[n]
        H.ntype[n] = G.ntype[n]
        H.nbytype[H.ntype[n]].append(n)
    for (u,v,w) in H.edges(data=True):   # edges
        w = w['weight']
        ##try:
        add_edge_attr(u, v, H.etype, G.etype[u][v])
        add_edge_attr(u, v, H.eid, G.eid[u][v])
        H.ebytype[G.etype[u][v]].append((u, v))
        H.ebyid[G.eid[u][v]] = (u, v)
        ##except:
        ##    pass  # if deleting edges
    return(H)

def copy_g_nbytype(G,H):
    H = init_g_attr(H)          # initialize attributes
    for n in H.nodes():         # nodes
        H.nbytype[G.ntype[n]].append(n)
    return H
    
def update_shp_fld(G, GP, out_network_fld):
    # get shapefile references
    nodes_shp = G.config[('shapefile', 'nodes')]
    edges_shp = G.config[('shapefile', 'edges')]
    eids = set([G.eid[u][v] for (u,v) in G.edges()])  # get set of unique eid's        

    fcs = {'nodes':(nodes_shp,'NodeID'), 'edges':(edges_shp, 'EdgeID')}
    for fc, (shp, idx) in fcs.iteritems():
        # add field if not already present
        flds = {}
        listflds = GP.ListFields(shp)
        f = listflds.next()
        while f:
            flds[f.Name] = f.Type
            f = listflds.next()
        if out_network_fld not in flds.keys():
            GP.AddField_management(shp, out_network_fld, 'SHORT')
        del listflds, f

        # update field with membership value if in new network
        rows = GP.UpdateCursor(shp)
        row = rows.Next()
        while row:
            id = row.GetValue(idx)
            if fc == 'nodes':
                if G.has_node(id): 
                    row.SetValue(out_network_fld, 1)
                else:
                    row.SetValue(out_network_fld, 0)        
            elif fc == 'edges':
                if id in eids:
                    row.SetValue(out_network_fld, 1)
                else:
                    row.SetValue(out_network_fld, 0)        
            rows.UpdateRow(row)
            row = rows.Next()
        del row, rows

def write_network(G, network_txt):
    import ConfigParser, networkx as NX, csv
        
    # cfg
    cfg = ConfigParser.ConfigParser()

    # cfg network_cfg params
    network_cfg = G.config
    for (section,option),value in network_cfg.iteritems():
        if not cfg.has_section(section):
            cfg.add_section(section)
        cfg.set(section, option, value)

    # cfg graph summary
    cfg.add_section('summary') 
    cfg.set('summary', 'nodes', G.number_of_nodes())
    cfg.set('summary', 'edges', G.number_of_edges())
    cfg.set('summary', 'components', NX.number_connected_components(G))
    cfg.set('summary', 'node centroids', len(G.nbytype['centroid']))
    cfg.set('summary', 'node internal', len(G.nbytype['internal']))
    cfg.set('summary', 'node perimeter', len(G.nbytype['perimeter']))
    cfg.set('summary', 'node external', len(G.nbytype['external']))
    cfg.set('summary', 'edge internal', len(G.ebytype['internal']))
    cfg.set('summary', 'edge perimeter', len(G.ebytype['perimeter']))
    cfg.set('summary', 'edge external', len(G.ebytype['external']))
    cfg.set('summary', 'graph density', NX.density(G))
    if len(G.nx.values()) > 1:
        cfg.set('summary', 'node min x', min(G.nx.values()))
        cfg.set('summary', 'node max x', min(G.nx.values()))
        cfg.set('summary', 'node min y', min(G.ny.values()))
        cfg.set('summary', 'node max y', min(G.ny.values()))
        cfg.set('summary', 'node min z', min(G.nz.values()))
        cfg.set('summary', 'node max z', min(G.nz.values()))
    cfg.write(open(network_txt,'w'))

    # network edgelist
    NX.write_edgelist(G, network_cfg[('network', 'edgelist')])

    # write network node attributes
    f = open(network_cfg[('network', 'nodeattr')], 'wb')
    f.write('"nid","nx","ny","nz","ntype","npatchid"\n')
    cw = csv.writer(f)
    for n in G.nodes():
        data = [n, G.nx[n], G.ny[n], G.nz[n], G.ntype[n], G.npatchid[n]]
        cw.writerow(data)
    f.close()

    # write network edge attributes
    f = open(network_cfg[('network', 'edgeattr')], 'wb')
    f.write('"eid","n1","n2","w","etype"\n')
    cw = csv.writer(f)
    for e in G.edges(data=True):
        (n1,n2,w) = e
        w = w['weight']
        data = [G.eid[n1][n2], n1, n2, w, G.etype[n1][n2]]
        cw.writerow(data)
    f.close()

def read_network(network_txt):
    import ConfigParser, networkx as NX, csv
    
    # read in_network config
    cfg = ConfigParser.ConfigParser()
    cfg.readfp(open(network_txt))
    edgelist  = cfg.get('network','edgelist')
    nodeattr  = cfg.get('network','nodeattr')
    edgeattr  = cfg.get('network','edgeattr')
#    prj       = cfg.get('shapefile','projection')
    nodes_shp = cfg.get('shapefile','nodes')
    edges_shp = cfg.get('shapefile','edges')
    costdist  = cfg.get('surface','costdist')
    tin       = cfg.get('surface','tin')

    # get leastcostpaths,txt
    if cfg.has_option('leastcostpaths', 'txt'):
        lcpaths_txt = cfg.get('leastcostpaths', 'txt')
    else:
        lcpaths_txt = False

    # read graph
    #G = NX.read_edgelist(edgelist,create_using=NX.Graph(), nodetype=int, edgetype=float)
    #G = NX.read_edgelist(edgelist, data=True) # , comments="#", delimiter=' ', create_using=None, nodetype=None, data=(('weight',float),))
    G = NX.read_edgelist(edgelist, nodetype=int, data=True) # , comments="#", delimiter=' ', create_using=None, nodetype=None, data=(('weight',float),))

    
    # setup helper dictionaries and lists
    G = init_g_attr(G)  # missing
    #G.ntype = {}; G.nbytype = {}; G.nx = {}; G.ny = {}; G.nz = {}; G.npatchid = {}
    #G.etype = {}; G.ebytype = {}; G.eid = {}; G.ebyid = {}
    #G.nbytype['centroid'] = []; G.nbytype['internal'] = []; G.nbytype['perimeter'] = []; G.nbytype['external'] = []
    #G.ebytype['boundary'] = []; G.ebytype['internal'] = []; G.ebytype['perimeter'] = []; G.ebytype['external'] = []

    # set config
    G.config = {('network', 'edgelist'):edgelist,
                ('network', 'edgeattr'):edgeattr,
                ('network', 'nodeattr'):nodeattr,
                ('shapefile', 'nodes'):nodes_shp,
                ('shapefile', 'edges'):edges_shp,
                ('surface', 'costdist'):costdist,
                ('surface', 'tin'):tin,
                ('leastcostpaths', 'txt'):lcpaths_txt,
                }
                #('shapefile', 'projection'):prj,
    # read node attributes
    cr = csv.reader(open(nodeattr, 'rb'))
    i = 0
    for row in cr:
        if i==0: i =+ 1; continue               # skip header line
        (n, nx, ny, nz, ntype, npatchid) = row  # csv fields: nid,nx,ny,nz,ntype
        # exclude external nodes without npatchid's
        if npatchid=='':
            pass
        n, nx, ny, nz, npatchid = (int(n), float(nx), float(ny), float(nz), int(float(npatchid)))
        G.nx[n]       = nx
        G.ny[n]       = ny
        G.nz[n]       = nz
        G.ntype[n]    = ntype
        G.npatchid[n] = npatchid
        G.npos[n]     = (nx, ny)
        G.nbytype[ntype].append(n)

    # read edge attributes
    G.eid     = {}
    G.ebyid   = {}
    G.etype   = {}
    G.ebytype = {} # helper dictionary making it easy to iterate through edges by type
    G.ebytype['boundary'] = []; G.ebytype['internal'] = []; G.ebytype['perimeter'] = []; G.ebytype['external'] = []
    cr = csv.reader(open(edgeattr, 'rb'))
    i = 0
    for row in cr:
        if i==0: i =+ 1; continue         # skip header line
        (eid, n1, n2, w, etype) = row     # csv fields
        eid, n1, n2, w = (int(eid), int(n1), int(n2), float(w))
        add_edge_attr(n1, n2, G.etype, etype)
        add_edge_attr(n1, n2, G.eid, eid)
        G.ebytype[etype].append((n1, n2))
        G.ebyid[eid] = (n1, n2)

    # return network        
    return(G)