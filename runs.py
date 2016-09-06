# helper script for many runs
# 2008-02-07, bbest:
# * cleaned up wd.replace stuff, and check of paths in create_network.py, network_leastcostpaths.py, and truncate_network.py
#   * TODO: other *.py?
# * FIX!: absolute paths in network.txt
# * variable costthreshold allowed
# * 55,000 m -> 55000 m: comma bad for now

# import modules
import csv, os, datetime

# SETUP THESE VARIABLES PER YOUR LOCAL FILESYSTEM
dir_pre  = r'D:\code\connmod\CONN_02062008'
dir_cm   = '%s\\ConnMod1' % dir_pre
runs_csv = '%s\\runs.csv' % dir_pre
log_txt  = '%s\\runs_log.txt' % dir_pre

# run cmd and append to log file
def run(cmd):
    log_f = open(log_txt, 'a'); log_f.write('\n%s: BEGIN\n%s\n' % (datetime.datetime.today().ctime(), cmd)); log_f.close()
    os.system('%s >> %s 2>&1' % (cmd, log_txt))
    log_f = open(log_txt, 'a'); log_f.write('%s: END\n' % (datetime.datetime.today().ctime())); log_f.close()

# read runs.csv to loop through paramaters
runs = open(runs_csv, 'rb')
reader = csv.reader(runs)
header = reader.next()
reader = csv.DictReader(runs, header)    
for row in reader:
    # assign a fresh dictionary of vars
    d = {}
    d['dir_cm'] = dir_cm
    
    # create_network.py
    # - inputs
    d['cost']    = '%s\\%s\\%s' % (dir_pre, row['dir_in'], row['cost'])
    d['patches.shp'] = '%s\\%s\\%s' % (dir_pre, row['dir_in'], row['patches.shp'])
    # - outputs
    d['distcost'] = '%s\\%s\\distcost' % (dir_pre, row['dir_out'])
    d['tin'] = '%s\\%s\\tin' % (dir_pre, row['dir_out'])
    d['nodes.shp'] = '%s\\%s\\nodes.shp' % (dir_pre, row['dir_out'])
    d['edges.shp'] = '%s\\%s\\edges.shp' % (dir_pre, row['dir_out'])
    d['network.txt'] = '%s\\%s\\network.txt' % (dir_pre, row['dir_out'])
    # - command
    if (int(row['create_network'])):
        run('%(dir_cm)s\\create_network.py "%(cost)s" "%(patches.shp)s" "%(distcost)s" "%(tin)s" "%(nodes.shp)s" "%(edges.shp)s" "%(network.txt)s"' % d)

    # truncate_network.py
    # - outputs
    d['max_costdist'] = row['dispersal']
    d['out_network_fld'] = 'tr'
    d['network_tr.txt'] = '%s\\%s\\network_tr.txt' % (dir_pre, row['dir_out'])
    # - command
    if (int(row['truncate_network'])):
        run('%(dir_cm)s\\truncate_network.py "%(network.txt)s" "%(max_costdist)s" "%(out_network_fld)s" "%(network_tr.txt)s"' % d)
    
    # network_leastcostpaths.py
    # - outputs
    d['eucthreshold'] = '#'
    d['out_network_fld'] = 'tr_lc'
    d['network_tr_lc.txt'] = '%s\\%s\\network_tr_lc.txt' % (dir_pre, row['dir_out'])
    d['paths.dbf'] = '%s\\%s\\paths.dbf' % (dir_pre, row['dir_out'])
    d['paths.csv'] = '%s\\%s\\paths.csv' % (dir_pre, row['dir_out'])
    # - command
    if (int(row['network_leastcostpaths'])):
        run('%(dir_cm)s\\network_leastcostpaths.py "%(network_tr.txt)s" "%(eucthreshold)s" "%(out_network_fld)s" "%(network_tr_lc.txt)s" "%(paths.dbf)s" "%(paths.csv)s"' % d)

    # network_centrality.py
    if (int(row['network_centrality'])):
        run('%(dir_cm)s\\network_centrality.py "%(network_tr_lc.txt)s"' % d)    