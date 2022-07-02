import networkx as nx
import mamoge.taskplanner.nx as mamogenx


def example_graph_1():
    G = nx.DiGraph()
    G.add_node(0, layer=0, location=(0, 2))

    [G.add_node(i, layer=1, location=(2, p))
     for i, p in zip([1, 2, 3, 4], (3, 1, 2, 4))]
    G.add_node(5, layer=2, location=(4, 3))
    G.add_node(6, layer=2, location=(6, 2))

    [G.add_edge(0, i, distance=mamogenx.G_distance_manhatten(G, 0, i))
     for i in range(1, 5)]
    [G.add_edge(i, 6, distance=mamogenx.G_distance_manhatten(G, i, 6))
     for i in range(2, 5)]
    G.add_edge(1, 5, distance=mamogenx.G_distance_manhatten(G, 1, 5))
    G.add_edge(5, 6, distance=mamogenx.G_distance_manhatten(G, 5, 6))

    return G


def example_graph_2():
    G = example_graph_1()

    [G.add_node(i, layer=3, location=(8, p))
     for i, p in zip([7, 8, 9], (3, 1, 2))]

    G.add_node(10, layer=4, location=(10, 2))
    G.add_node(11, layer=4, location=(11, 3))
    G.add_node(12, layer=4, location=(12, 2))

    G.add_node(13, layer=5, location=(15, 2))
    [G.add_edge(6, i, distance=mamogenx.G_distance_manhatten(G, 6, i))
     for i in range(7, 10)]

    G.add_edge(7, 11, distance=mamogenx.G_distance_manhatten(G, 7, 11))
    G.add_edge(9, 10, distance=mamogenx.G_distance_manhatten(G, 9, 10))
    G.add_edge(11, 12, distance=mamogenx.G_distance_manhatten(G, 11, 12))

    G.add_edge(12, 13, distance=mamogenx.G_distance_manhatten(G, 12, 13))
    G.add_edge(10, 13, distance=mamogenx.G_distance_manhatten(G, 10, 13))
    G.add_edge(8, 13, distance=mamogenx.G_distance_manhatten(G, 8, 13))

    return G
