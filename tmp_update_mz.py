
import sys, os, time, tempfile, string, shutil, cm, traceback, networkx as NX, math

# print traceback.print_exc()

# setup geoprocessor
GP = cm.gp_init()

edges_shp = r'E:\code\connmod\branches\ch\data\net2010c\tin_TinEdge.shp'

# setup iteration over edges shapefile
desc = GP.Describe(edges_shp)
shapefld = desc.ShapeFieldName
cur = GP.UpdateCursor(edges_shp)
row = cur.Next()
while row:
    feat = row.getvalue(shapefld) # Create the geometry object

    # feat.length or other?
    row.SetValue('LengthTIN', feat.length)
    line = feat.GetPart(0); pt1 = line.next(); pt2 = line.next()
    xy_length = math.sqrt(math.pow(pt1.x - pt2.x, 2) + math.pow(pt1.y - pt2.y, 2))
    row.SetValue('LengthXY', xy_length)    
    xyz_length = math.sqrt(math.pow(pt1.x - pt2.x, 2) + math.pow(pt1.y - pt2.y, 2) + math.pow(pt1.z - pt2.z, 2))

    row.SetValue('CalcXYZ', math.sqrt(math.pow(pt1.x - pt2.x, 2) + math.pow(pt1.y - pt2.y, 2) + math.pow(pt1.z - pt2.z, 2)))    

def getX(feat):
    a = feat.firstpoint
    b = feat.lastpoint
    math.sqrt(math.pow(a.x - b.x, 2) + math.pow(a.y - b.y, 2) + math.pow(a.z - b.z, 2))
    

    row.SetValue('CalcXYZ', xy_length)    

    #row.SetValue('M', feat.M)
    #row.SetValue('Z', feat.Z)
    cur.UpdateRow(row)
    row = cur.Next()
del cur