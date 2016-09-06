# $Id: create_network.py 118 2010-04-26 04:33:39Z bbest $

# "R:\GraphGroup\chapel_hill\prep\cost" "R:\GraphGroup\chapel_hill\prep\patches.shp" "R:\GraphGroup\chapel_hill\network\full\costdist" "R:\GraphGroup\chapel_hill\network\full\tin" "R:\GraphGroup\chapel_hill\network\full\nodes.shp" "R:\GraphGroup\chapel_hill\network\full\edges.shp" "R:\GraphGroup\chapel_hill\network\full\network.txt"
# "D:\code\connmod\branches\ch\data\prep\cost" "D:\code\connmod\branches\ch\data\prep\h16bcrg_poly.shp" "D:\code\connmod\branches\ch\data\network\full\costdist" "D:\code\connmod\branches\ch\data\network\full\tin" "D:\code\connmod\branches\ch\data\network\full\nodes.shp" "D:\code\connmod\branches\ch\data\network\full\edges.shp" "D:\code\connmod\branches\ch\data\network\full\network.txt"
# "C:\CONN_01142008\fr_IN\frcost_clp" "C:\CONN_01142008\fr_IN\fsr_test_hab.shp" "C:\CONN_01142008\fr_OUT_test\costdist" "C:\CONN_01142008\fr_OUT_test\tin" "C:\CONN_01142008\fr_OUT_test\nodes.shp" "C:\CONN_01142008\fr_OUT_test\edges.shp" "C:\CONN_01142008\fr_OUT_test\network.txt"
# "D:\code\connmod\tamara\ConnMod1\create_network.py" "D:\code\connmod\tamara\fr_IN_test\frcost_clp" "D:\code\connmod\tamara\fr_IN_test\fsr_test_hab.shp" "D:\code\connmod\tamara\fr_OUT_test\costdist" "D:\code\connmod\tamara\fr_OUT_test\tin" "D:\code\connmod\tamara\fr_OUT_test\nodes.shp" "D:\code\connmod\tamara\fr_OUT_test\edges.shp" "D:\code\connmod\tamara\fr_OUT_test\network.txt"

# E:\code\connmod\branches\ch\data\prep\cost E:\code\connmod\branches\ch\data\prep\h16rgbc_poly.shp E:\code\connmod\branches\ch\data\net2010\costdist E:\code\connmod\branches\ch\data\net2010\tin E:\code\connmod\branches\ch\data\net2010\nodes.shp E:\code\connmod\branches\ch\data\net2010\edges.shp E:\code\connmod\branches\ch\data\net2010\network.txt

# Creating NetworkX network and nodes shapefile by reading edges shapefile
# ERROR: add_edge() got an unexpected keyword argument 'weight'
# ws=E:\Ryman\scratch\cm_net01
# E:\Ryman\scratch\costs_subset E:\Ryman\data\cm_subset_input\patches_subset.shp %ws%\costdist %ws%\tin %ws%\nodes.shp %ws%\edges.shp %ws%\network.txt
# E:\Ryman\scratch\costs_subset E:\Ryman\data\cm_subset_input\patches_subset.shp E:\Ryman\scratch\cm_net01\costdist E:\Ryman\scratch\cm_net01\tin E:\Ryman\scratch\cm_net01\nodes.shp E:\Ryman\scratch\cm_net01\edges.shp E:\Ryman\scratch\cm_net01\network.txt

# H:\esm270\data\marxan\cost\cost_all H:\esm270\data\GoC.mdb\hexagons HEX_ID H:\esm270\data\connectivity\network\cost_dist H:\esm270\data\connectivity\network\cost_tin 1000 H:\esm270\data\connectivity\GoC_connectivity.mdb\nodes H:\esm270\data\connectivity\GoC_connectivity.mdb\edges H:\esm270\data\connectivity\network\network.txt
# H:\esm270\data\GoC.mdb\portfolio_era54 POTAFOLIO H:\esm270\data\connectivity\tin\costdist_tin # H:\esm270\data\connectivity\GoC_connectivity.mdb\nodes H:\esm270\data\connectivity\GoC_connectivity.mdb\edges H:\esm270\data\connectivity\network\network.txt

# C:\temp\connectivity\GoC_connectivity.gdb\portfolio_era54 POTAFOLIO C:\temp\connectivity\tin\costdist_tin # C:\temp\connectivity\GoC_connectivity.gdb\cost_nodes C:\temp\connectivity\GoC_connectivity.gdb\cost_edges C:\temp\connectivity\network\cost_network.txt

import sys, os, time, tempfile, string, shutil, cm, traceback
import networkx as NX

# setup geoprocessor
GP = cm.gp_init()

# input arguments
##rstr_cost     = sys.argv[1]
patches_shp   = sys.argv[1]  # poly_height = habitat quality?
#patches_idfld      = 'FID'  # may differ for mdb featureclasses
patches_idfld = sys.argv[2]  # problem: if patches_idfld in nodes fields when doing intersect, join
                             # TODO: so far using numeric.  Limit to LONG,OBJECTID or allow any numeric and TEXT?
# output arguments
##rstr_costdist = sys.argv[4]
tin           = sys.argv[3]
z_tolerance   = sys.argv[4]
nodes_shp     = sys.argv[5]
edges_shp     = sys.argv[6]
network_txt   = sys.argv[7]
wd            = os.path.dirname(patches_shp)
GP.workspace  = wd

# future TODO: 1) grow corridors out from paths using rstr_costdist, 2) tweakable tins with ztolerance/maxnodes
#rstr_costdist   = sys.argv[2]
#tin_ztolerance  = sys.argv[4]
#tin_maxnodes    = sys.argv[5]

# network derivative data files
network          = os.path.splitext(network_txt)[0]
network_edgelist = network + '_edgelist.txt'
network_nodeattr = network + '_nodeattr.csv'
network_edgeattr = network + '_edgeattr.csv'
network_prj      = network + '.prj'

# temp files
def tmp(ext, name='-', wd=wd):
    if ext:
        path = '%s/%s.%s' % (wd, name, ext)
    else:
        path = '%s/%s' % (wd, name)
##    while '-' in name or os.path.exists(path):    # dashes in filenames make GP functions bonk
##        tmp = tempfile.TemporaryFile(mode='r', prefix='tmp_', suffix=ext, dir=wd)
##        path = tmp.name
##        tmp.close()
    return path.replace('\\','/')
patchz             = tmp('','patchz')
centroids          = tmp('','centroids')
node_patches       = tmp('','np')
edges_tmp          = tmp('','edges_tmp')
prj                = os.path.splitext(patches_shp)[0] + '.prj'
nodes_prj          = os.path.splitext(nodes_shp)[0] + '.prj'

# logging
log                = '%s/log.txt' % wd
cm.log_init(log, 'debug')

nodes_oidfld = GP.Describe(nodes_shp).OIDFieldName

GP.MakeFeatureLayer_management(nodes_shp, 'lyr')

# flag patchid

# Create a new fieldmappings and add the two input feature classes.
fieldmappings = gp.CreateObject("FieldMappings")
fieldmappings.AddTable(targetFeatures)
fieldmappings.AddTable(joinFeatures)




##cm.log('  Updating node attribute PatchID')
##GP.Intersect_analysis(nodes_shp + ';' + patches_shp, node_patches, 'ONLY_FID', '', 'POINT')
##nodes_base, nodes_ext = os.path.splitext(os.path.basename(nodes_shp))
##patches_base, patches_ext = os.path.splitext(os.path.basename(patches_shp))
##node_patches_base, node_patches_ext = os.path.splitext(os.path.basename(node_patches))
##if node_patches_ext == '.shp':
##    FID_nodes   = 'FID_' + nodes_base[0:6]
##    FID_patches = 'FID_' + patches_base[0:6]
##else:
##    FID_nodes   = 'FID_' + nodes_base
##    FID_patches = 'FID_' + patches_base
##node_patches_oidfld = GP.Describe(node_patches).OIDFieldName
##
##GP.AddJoin_management('lyr', nodes_oidfld, node_patches, FID_nodes, 'KEEP_ALL')
##
##lyr_oidfld = GP.Describe('lyr').OIDFieldName
##
##GP.CalculateField_management('lyr', 'cost_nodes.PatchID', '"np.%s"' % FID_patches) # TODO: *.shp had this - '[%s.%s]' % (tbl_np, FID_patches))
##GP.RemoveJoin_management('lyr', node_patches_base)
##GP.SelectLayerByAttribute_management('lyr', 'NEW_SELECTION', '"NodeType"=\'external\'')
##GP.CalculateField_management('lyr', 'PatchID', '-1')
##
##cm.log('Done')
