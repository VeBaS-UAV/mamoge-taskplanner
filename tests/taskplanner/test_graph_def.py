import networkx as nx
from mamoge.taskplanner.location import GPSLocation, CartesianLocation, Location, NXLocation
import mamoge.taskplanner.nx as mamogenx



#def test_graph_node_lookup():
#    l1 = NXLocation(G_routemap, name="G11")
#    l2 = NXLocation(G_routemap, name="G2-3")
#    type(l1)
#    l1, l2
#
#    path = l1.path_to(l2)
#    path

def test_graph_lookup():
    G = nx.Graph()
    G.add_node(0, name="G10")
    G.add_node(1, name="G11")
    G.add_node(2, name="G12")

    results = mamogenx.G_lookup_node(G, name="G11")

    assert len(results) == 1

    assert results[0] == 1
