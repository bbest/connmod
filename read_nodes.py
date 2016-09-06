import csv
# ben adds perimeter attributes
in_network_nodeattr = r'C:\bbest\ArcRstats\connmod\example\fullnetwork.nodeattr'

# helper function to return 1 when can be converted to integer (ie is exterior node), or not (ie is a string as with patch nodes)
def likeint(x):
    try: int(x); return(1)
    except: return(0)
def tryint(x):
    try: x = int(x)
    except: pass
    return(x)

# read network node attributes
n = []
x = []
y = []
elevation = []
tintype = []

cr = csv.reader(open(in_network_nodeattr, 'rb'))
for row in cr:
    (n1, position_str, elevation1, tintype1) = row
    n.append(tryint(n1))   # int or str
    x1,y1 = eval(position_str)  # 2-tuple of longs
    x.append(x1)
    y.append(y1)
    elevation.append(float(elevation1))  # float
    tintype.append(tintype1)
