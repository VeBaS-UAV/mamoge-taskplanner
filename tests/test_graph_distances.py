import networkx as nx
from mamoge.taskplanner.location import CartesianLocation, GPSLocation
from mamoge.taskplanner.nx import G_distance_location

# %%
def test_cartesian_distance():
    c1 = CartesianLocation(1,1)
    c2 = CartesianLocation(3,2)

    assert c1.distance_to(c2) == 3

#def test_cartesian_graph_distance():

# %%

def test_cartesian_distance_w_graph():
    c1 = CartesianLocation(1,1)
    c2 = CartesianLocation(4,2)

    G = nx.DiGraph()

    G.add_node(0, location=c1.as_dict())
    G.add_node(1, location=c2.as_dict())

    distance = G_distance_location(G, 0,1)

    assert distance == 4

def test_gps_distance():

    g1 = GPSLocation(51.7444167, 8.8227609)
    g2 = GPSLocation(51.7440672, 8.8233740)

    dist = g1.distance_to(g2)

    assert abs(dist - 57.5) < 0.1

def test_gps_distance_w_graph():

    g1 = GPSLocation(51.7444167, 8.8227609)
    g2 = GPSLocation(51.7440672, 8.8233740)

    G = nx.DiGraph()

    G.add_node(0, location=g1.as_dict())
    G.add_node(1, location=g2.as_dict())

    distance = G_distance_location(G, 0,1)

    assert abs(distance - 57.5) < 0.1
