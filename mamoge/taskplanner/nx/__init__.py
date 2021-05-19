from typing import Any
import networkx as nx
from networkx.algorithms import dag
import numpy as np

from mamoge.taskplanner.location import LocationBuilder

def G_draw_taskgraph(G: nx.Graph) -> None:
    """Plot a task graph using location and distance attributes"""
    pos = nx.drawing.layout.multipartite_layout(G, subset_key="layer")
    #pos = {n:G.nodes[n]["location"] for n in G.nodes}

    colors = (["#00aaaa"] * len(G))
    colors[0] = "#00aa00"
    labels_dict = {l:G.nodes[l]["name"] for l in G.nodes}

    nx.draw(G, node_color=colors, pos=pos, with_labels=True, labels=labels_dict)


    edge_dict = {w:G[w[0]][w[1]]['distance'] for w in G.edges}

    nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_dict,font_color='red')


def G_distance_manhatten(G: nx.Graph, i:Any, j:Any, distance_attribute="location") -> float:
    """Return the manhatten distance between two given nodes i and j
       and the attribute used to calculate the distance"""
    l1 = np.array(G.nodes[i][distance_attribute])
    l2 = np.array(G.nodes[j][distance_attribute])

    return float(np.abs(l1-l2).sum())

def G_distance_location(G: nx.Graph, i:Any, j:Any):
    location_i = LocationBuilder.location_from_dict(G.nodes[i]["location"])

    location_j = LocationBuilder.location_from_dict(G.nodes[j]["location"])

    return location_i.distance_to(location_j)


def G_problem_from_dag(G:nx.Graph) -> nx.Graph:
    """Return a graph representing the problem for a task dag"""

    #Gn = nx.DiGraph()
    Gn = G.copy()
    for node, anodes in G.adjacency():
        #print(node, anodes)
        Gn.add_node(node, **G.nodes[node])
        for anode in anodes:
            Gn.add_edge(node, anode, **G.edges[(node, anode)])

        anc = dag.ancestors(G, node)
        desc = dag.descendants(G, node)

        Gt = G.copy()
        Gt.remove_nodes_from(list(anc))
        Gt.remove_nodes_from(list(desc))

        #print("Gt nodes", node, anc, desc,  Gt.nodes)
        for n in Gt.nodes:
            #print("add node", node, n)
            Gn.add_edge(node, n, distance=G_distance_manhatten(G, node, n))

    return Gn

