# $Id: create_network.py 122 2011-02-28 10:30:00Z bbest $

# expecting non-zero integer Patch ID field
#
# TODO:
#  # z tolerance and artifacts?
#  * grow corridors out from paths using rstr_costdist.  see corridor arcgis fxn.
#  * handle patches ID field already using PatchID.' % patches_idfld
#  * tweak edge weights

# C:\temp\connectivity\GoC_connectivity.gdb\portfolio_era54 POTAFOLIO C:\temp\connectivity\tin\costdist_tin # C:\temp\connectivity\GoC_connectivity.gdb\nodes C:\temp\connectivity\GoC_connectivity.gdb\edges C:\temp\connectivity\network\network.txt
# C:\temp\connectivity\cost\cost C:\temp\connectivity\GoC_connectivity.gdb\portfolio_era54 PortfolioID # C:\temp\connectivity\network_cost

import sys, os, time, tempfile, string, shutil, cm, traceback
import networkx as NX

# setup geoprocessor
GP = cm.gp_init(9.3)

# arguments
rstr_cost     = sys.argv[1]
patches_in    = sys.argv[2]  # poly_height = habitat quality?
patches_idfld = sys.argv[3]  # problem: if patches_idfld in nodes fields when doing intersect, join
                             # TODO: so far using numeric.  Limit to LONG,OBJECTID or allow any numeric and TEXT?
z_tolerance   = sys.argv[4]
wd            = sys.argv[5]

# paths
gdb           = '%s/geodb.gdb' % wd
patches       = '%s/patches' % gdb
rstr_costdist = '%s/costdist' % wd
rstr_costdist1= '%s/costdist1' % wd
poly_costdist1= '%s/costdist1' % gdb
tin           = '%s/tin' % wd
nodes_shp     = '%s/nodes' % gdb
edges_shp     = '%s/edges' % gdb
network_txt   = '%s/network.txt' % wd

# paths to temporary objects
centroids    = '%s/centroids' % gdb
edges_tmp    = '%s/edges_tmp' % gdb

# network derivative data files
network          = os.path.splitext(network_txt)[0]
network_edgelist = network + '_edgelist.txt'
network_nodeattr = network + '_nodeattr.csv'
network_edgeattr = network + '_edgeattr.csv'

# initialize output folder
GP.CreateFolder_management(os.path.dirname(wd), os.path.basename(wd))

# logging
log                = '%s/log.txt' % wd
cm.log_init(log, 'debug')

# NetworkX version report and check
cm.log('Using NetworkX %s' % NX.__version__)
if NX.__version__ < '1.0':
    cm.log('MUST FIX: Need NetworkX version 1.0 or higher', type='error')
    
try:
    cm.log('Creating folder and geodatabase')
    if not GP.Exists(gdb):
        GP.CreateFileGDB_management(os.path.dirname(gdb), os.path.basename(gdb))
    GP.workspace  = wd    

    cm.log('Copying patches')
    GP.CopyFeatures(patches_in, patches)
    flds = GP.ListFields(patches)
    if 'PATCHID' in [f.Name.upper() for f in flds]:
        cm.log('The PatchID field name is reserved.  Please remove this field from the input patches.', type='error')
    GP.AddField(patches, 'PatchID', 'LONG')
    GP.CalculateField(patches, 'PatchID', '[%s]' % patches_idfld)
    GP.DeleteField(patches, ';'.join([f.Name for f in flds if f.Name.upper() not in ('OBJECTID','SHAPE','SHAPE_LENGTH','SHAPE_AREA')]))
    
    cm.log('Accumulating cost away from patches')
    GP.CostDistance_sa(patches, rstr_cost, rstr_costdist, '', '')

    cm.log('Creating TIN from cumulative cost surface')
    GP.RasterTin_3d(rstr_costdist, tin, z_tolerance)

    cm.log('Imprinting patches into TIN surface')
    GP.AddField(patches, 'TIN_Z', 'LONG')
    GP.CalculateField(patches, 'TIN_Z', '0')    
    GP.EditTin_3d(tin, patches + ' TIN_Z PatchID hardreplace false')
    
    cm.log('Creating patch centroids for TIN')
    GP.FeatureToPoint_management(patches, centroids, 'INSIDE')
    GP.AddField_management(centroids, 'Z', 'LONG')
    GP.CalculateField_management(centroids, 'Z', '0')
    GP.EditTin_3d(tin, centroids + ' Z PatchID masspoints false')
    
    cm.log('Extracting edges from TIN')
    GP.TinEdge_3d(tin, edges_shp, 'DATA')
    GP.SurfaceLength_3d(tin, edges_shp, 'Length3D', '', '1')
    GP.AddField_management(edges_shp, 'EdgeID', 'LONG')
    GP.CalculateField_management(edges_shp, 'EdgeID', '[Index]', 'VB')
    GP.DeleteField_management(edges_shp, 'Index')

    cm.log('Clipping edges outside cost surface')
    GP.SingleOutputMapAlgebra_sa("int(con(costdist,1))", rstr_costdist1, rstr_costdist)
    GP.RasterToPolygon_conversion(rstr_costdist1, poly_costdist1, "NO_SIMPLIFY", "COUNT")
    GP.Rename(edges_shp, edges_tmp)
    GP.Clip_analysis(edges_tmp, poly_costdist1, edges_shp)
    GP.Delete(edges_tmp)
    
    cm.log('Updating edge attribute EdgeType')
    GP.AddField(edges_shp, 'EdgeType0', 'SHORT')
    GP.CalculateField_management(edges_shp, 'EdgeType0', '[EdgeType]')
    GP.DeleteField(edges_shp, 'EdgeType')
    GP.AddField(edges_shp, 'EdgeType', 'TEXT')
    GP.MakeFeatureLayer (edges_shp, 'lyr')               # internal edges
    GP.SelectLayerByLocation_management('lyr', 'CONTAINED_BY', patches, '', 'NEW_SELECTION')
    GP.SelectLayerByAttribute_management('lyr', 'REMOVE_FROM_SELECTION', 'EdgeType0 = 2')
    GP.CalculateField_management('lyr', 'EdgeType0', '3')
    # GP.CalculateField_management('lyr', 'W', '0')  # presume eweights['internal']=0 set below
    GP.SelectLayerByAttribute_management('lyr', 'CLEAR_SELECTION') # edgetype by name
    codeblock = "def g(e): return({0:'external', 1:'boundary', 2:'perimeter', 3:'internal'}[e])"
    GP.CalculateField_management('lyr', 'EdgeType', 'g(int(!EdgeType0!))', 'PYTHON', codeblock)
    GP.DeleteField_management(edges_shp, 'EdgeType0')
except:
    cm.log('GP Error in TIN Creation/Extraction: %s' % GP.GetMessages(), 'error')

cm.log('Creating NetworkX network and nodes shapefile by reading edges shapefile')

# setup network and dictionaries
G = NX.Graph()  # converted from XGraph to Graph with 'weight' attribute per http://networkx.lanl.gov//reference/api_1.0.html#converting-your-existing-code-to-networkx-1-0
#eweights = {'internal':0.8, 'perimeter':0.9, 'external':1, 'boundary':1}  # tweaking this has major implications, particularly for internal edges
eweights = {'internal':1, 'perimeter':1, 'external':1, 'boundary':1}  # tweaking this has major implications, particularly for internal edges
G = cm.init_g_attr(G)
nodes = {}
edges = {}

# create nodes shapfile
GP.CreateFeatureClass_management(os.path.dirname(nodes_shp), os.path.basename(nodes_shp),'POINT', '', 'DISABLED', 'ENABLED')
GP.AddField(nodes_shp, 'X', 'FLOAT')
GP.AddField(nodes_shp, 'Y', 'FLOAT')
GP.AddField(nodes_shp, 'Z', 'FLOAT')
GP.AddField(nodes_shp, 'NodeID', 'LONG')
GP.AddField(nodes_shp, 'NodeType', 'TEXT')
nodes_oidfld = GP.Describe(nodes_shp).OIDFieldName
cur = GP.InsertCursor(nodes_shp)

# setup iteration over edges shapefile
shapefld = GP.Describe(edges_shp).ShapeFieldName
rows = GP.SearchCursor(edges_shp)
row = rows.Next()
irow = 0; nid = 0; nxy = {}
t0 = time.time()
while row:
    feat = row.getvalue(shapefld) # Create the geometry object

    # edge values
    eid = row.getvalue('EdgeID')
    etype = row.getvalue('EdgeType')
    length3D = row.getvalue('Length3D')
    # feat.length or other?
    ew = eweights[etype] * length3D  # multiply by edge weights, ie make internal 0

    # get parts
    part = feat.getpart(0)   # assume 1 part per row, ie 1 edge, vs polygon w/ multiple lines
    part.reset()

    # add nodes
    n = {}               # store nid of each point
    for i in [0,1]:      # assume 2 points per line
        pnt = part.next()
        x,y,z = (pnt.x, pnt.y, pnt.z)
        if not nxy.has_key((x,y)):  # can uniquely identify by x,y coordinates
            # nid record-keeping
            nid += 1
            nxy[(x,y)] = nid
            n[i] = nid
            # add to network
            G.add_node(nid)
            G.nx[nid] = x
            G.ny[nid] = y
            G.nz[nid] = z
            # add to shapefile
            newrow = cur.NewRow()
            #newrow.id = nid # doesn't work for geodatabase OIDFieldName and isn't editable
            newrow.shape = pnt
            newrow.SetValue('NodeID', nid)            
            newrow.SetValue('X', x)
            newrow.SetValue('Y', y)
            newrow.SetValue('Z', z)
            cur.InsertRow(newrow)   
        else:
            n[i] = nxy[(x,y)]

    # add edge
    G.add_edge(n[0], n[1], weight=ew)
    cm.add_edge_attr(n[0], n[1], G.etype, etype)
    cm.add_edge_attr(n[0], n[1], G.eid, eid)
    G.ebytype[etype].append((n[0], n[1]))
    G.ebyid[eid] = (n[0], n[1])

    row = rows.next() 
del row, rows, newrow, cur
#GP.DeleteField(nodes_shp, 'Id')

# nodes shapefile projection
patches_prj = GP.Describe(patches).SpatialReference
GP.DefineProjection(nodes_shp, patches_prj)

# set node attributes
cm.log('Updating node attributes')
try:
    # flag centroid nodes
    GP.MakeFeatureLayer_management(nodes_shp, 'lyr')
    GP.SelectLayerByLocation_management('lyr', 'INTERSECT', centroids, '', 'NEW_SELECTION')
    GP.CalculateField_management('lyr', 'NodeType', '"centroid"')

    # set other NodeType values
    cm.log('  Updating node attribute NodeType')
    GP.SelectLayerByAttribute_management('lyr','NEW_SELECTION', '"NodeType" IS NULL OR "NodeType"=\'\'')
    GP.SelectLayerByLocation_management('lyr', 'COMPLETELY_WITHIN', patches, '', 'SUBSET_SELECTION')
    GP.CalculateField_management('lyr', 'NodeType', '"internal"')
    GP.SelectLayerByAttribute_management('lyr','NEW_SELECTION', '"NodeType" IS NULL OR "NodeType"=\'\'')
    GP.SelectLayerByLocation_management('lyr', 'CONTAINED_BY', patches, '', 'SUBSET_SELECTION')
    GP.CalculateField_management('lyr', 'NodeType', '"perimeter"')
    GP.SelectLayerByAttribute_management('lyr','NEW_SELECTION', '"NodeType" IS NULL OR "NodeType"=\'\'')
    GP.CalculateField_management('lyr', 'NodeType', '"external"')
    GP.Delete('lyr')

    # flag patchid
    cm.log('  Updating node attribute PatchID')
    GP.SpatialJoin_analysis(nodes_shp, patches, "in_memory\\nodes_SpatialJoin") # , "JOIN_ONE_TO_ONE", "KEEP_ALL")
    GP.JoinField_management(nodes_shp, "NodeID", "in_memory\\nodes_SpatialJoin", "NodeID", "PatchID")
    GP.CalculateField_management(nodes_shp, "PatchID", "ZeroToNeg(!PatchID!)", "PYTHON", "def ZeroToNeg(v):\\n  if v==0:\\n    return -1\\n  else:\\n    return v\\n ")

    # update node attributes in network
    t0 = time.time()
    rows = GP.SearchCursor(nodes_shp)  # Create search cursor
    row = rows.Next()
    while row:
        nid             = row.GetValue('NodeID')
        G.npatchid[nid] = row.GetValue('PatchID')
        ntype           = row.GetValue('NodeType')
        G.ntype[nid]    = ntype
        G.nbytype[ntype].append(n)        
        row = rows.Next()
    del row, rows
except:
    cm.log('GP Error updating nodes: %s' % GP.GetMessages(), 'error')

cm.log('Writing network to file')
G.config = {('network','edgelist'):network_edgelist,
            ('network','edgeattr'):network_edgeattr,
            ('network','nodeattr'):network_nodeattr,
            ('shapefile','nodes'):nodes_shp,
            ('shapefile','edges'):edges_shp,
            ('surface','costdist'):rstr_costdist,
            ('surface','tin'):tin}
# G.edges(data=True)[0], G.etype
cm.write_network(G, network_txt)

# cleanup files
try:
    cm.log('Deleting temporary files')
    GP.RefreshCatalog(wd)
#    for i in [centroids, edges_tmp]: # , nodes_intersect # DEBUG
#        if GP.Exists(i): GP.Delete(i)
except:
    cm.log('GP Error Cleanup Deleting: %s' % GP.GetMessages(), 'error')

GP.SetParameterAsText(5,network_txt)

cm.log('Done')
