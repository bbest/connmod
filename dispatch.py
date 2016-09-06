# $Id: dispatch.py 98 2007-05-07 21:03:20Z bbest $
# dispatch geoprocessor (GP) object and check for required programs and versions

# import modules
import sys, os
from win32com.client import Dispatch

# working directory
script = sys.argv[0]
wdir = os.path.dirname(script).replace('\\','/')

# initialize ESRI ArcGIS geoprocessor
try:
    GP = Dispatch('esriGeoprocessing.GpDispatch.1')
    GP.CheckOutExtension('Spatial')
    GP.OverwriteOutput = 1    # setup for overwrite
    print 'GP (ArcGIS geoprocessor) successfully dispatched.'
except:
    s = 'ERROR: GP not successful dispatching ArcGIS with options Spatial and OverwriteOutput: %s' % GP.GetMessages()
    print s
    GP.AddError(s)

# check Python version
if (not hasattr(sys, 'version_info') or sys.version_info < (2,3,5, 'alpha', 0)):
    s = "WARNING: Python-2.3.5 or higher needed."
    print s
    GP.AddWarning(s)

# check Python NetworkX version
try:
    import networkx as NX
    print 'NetworkX Python module successfully imported.'
except:
    s = 'ERROR: NetworkX Python module not imported.'
if NX.__version__ != '0.29':
    s = 'WARNING: NetworkX Python module is not the required version 0.29.'
    print s
    GP.AddWarning(s)