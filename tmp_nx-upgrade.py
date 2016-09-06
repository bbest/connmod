import networkx as nx

# build simple weighted graph
G=nx.Graph()
G.add_edge(1,2,weight=12)
G.add_edge(3,4,weight=34)
G.add_edge(5,6,weight=56)
G.add_edge(7,8,weight=78)

# get edges with attribute data
e_bunch = G.edges(data=True)
print e_bunch
# [(1, 2, {'weight': 12}), (3, 4, {'weight': 34}), (5, 6, {'weight': 56}), (7, 8, {'weight': 78})]

# iterate through edges
for e in e_bunch:
    u,v,d = e
    w = d['weight']
    print u,v,w

# get edge data all at once
ws = [d['weight'] for u,v,d in G.edges(data=True)]
print ws
#print G.get_edge_data()
