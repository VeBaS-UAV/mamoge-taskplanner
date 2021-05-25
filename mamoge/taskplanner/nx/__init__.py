from typing import Any, List
import networkx as nx
from networkx.algorithms import dag
import numpy as np
import matplotlib.pylab as plt
import functools

def G_draw_taskgraph_w_pos_layer(G: nx.Graph):
    pos = nx.drawing.layout.multipartite_layout(G, subset_key="layer")
    return G_draw_taskgraph(G, pos=pos)

def G_draw_taskgraph_w_pos_location(G: nx.Graph):
    pos = {n:G.nodes[n]["location"].as_tuple() for n in G.nodes}
    #print("pos", pos)
    return G_draw_taskgraph(G, pos=pos)

def G_draw_taskgraph(G: nx.Graph, pos=None) -> None:

    """Plot a task graph using location and distance attributes"""
#    if pos is None:
#        pos = {n:G.nodes[n]["location"] for n in G.nodes}

    colors = (["#00aaaa"] * len(G))
    colors[0] = "#00aa00"

    try:
        labels_dict = {l:G.nodes[l]["name"] + f"({l})" for l in G.nodes}
    except:
        labels_dict = None

    nx.draw(G, node_color=colors, pos=pos, with_labels=True, labels=labels_dict)


    try:
        edge_dict = {w:G[w[0]][w[1]]['distance'] for w in G.edges}
        nx.draw_networkx_edge_labels(G,pos,edge_labels=edge_dict,font_color='red')
    except:
        #TODO check for distance or length or weight attribute
        pass

def G_draw_locationgraph(G: nx.Graph, path:list[Any] = None):
    """Plot a task graph using location and distance attributes"""

    fig,ax = plt.subplots(1,1, figsize=(10,5))
    pos = {n:G.nodes[n]["location"].as_tuple() for n in G.nodes}
    offset_label = 0.2
    pos_label = {n:(v[0]+offset_label, v[1]+offset_label) for n,v in pos.items()}

    colors = (["#00aaaa"] * len(G))
    colors[0] = "#00aa00"

    labels_dict = {l:str(G.nodes[l]["name"]) + f"({l})" for l in G.nodes}

    nx.draw(G, node_color=colors, pos=pos)
    nx.draw_networkx_labels(G, pos=pos_label, labels=labels_dict)

    if path:
        nx.draw_networkx_edges(G, pos, edgelist=list(zip(path,path[1:])), edge_color='r', width=5)

    #plt.tight_layout()

    xy_lim = G_locations_limits(G)

    ax.set_xlim((xy_lim[0][0]-1, xy_lim[1][0]+1))
    ax.set_ylim((xy_lim[0][1]-1, xy_lim[1][1]+1))

def G_distance_manhatten(G: nx.Graph, i:Any, j:Any, distance_attribute="location") -> float:
    """Return the manhatten distance between two given nodes i and j
       and the attribute used to calculate the distance"""
    l1 = np.array(G.nodes[i][distance_attribute])
    l2 = np.array(G.nodes[j][distance_attribute])

    return float(np.abs(l1-l2).sum())

def G_distance_location(G: nx.Graph, i:Any, j:Any):
    location_i = G.nodes[i]["location"]

    location_j = G.nodes[j]["location"]

    return location_i.distance_to(location_j)


def G_first(G:nx.Graph):
    return [n for n in G.nodes if len(list(G.predecessors(n)))==1][0]
    #return list(dag.topological_sort(G))[0]

def G_last(G:nx.Graph):
    #return list(dag.topological_sort(G))[-1]
    return [n for n in G.nodes if len(G[n])==1][0]

def G_problem_from_dag(G:nx.Graph) -> nx.Graph:
    """Return a graph representing the problem for a task dag"""

    #Gn = nx.DiGraph()
    Gn = G.copy()
    for node, anodes in G.adjacency():
        #print("it node", node, G.nodes[node])
        Gn.add_node(node, **G.nodes[node])
        for anode in anodes:
            Gn.add_edge(node, anode, **G.edges[(node, anode)])

        anc = dag.ancestors(G, node)
        desc = dag.descendants(G, node)

        Gt = G.copy()
        Gt.remove_nodes_from(list(anc))
        Gt.remove_nodes_from(list(desc))

        #print("Gt nodes", node, anc, desc,  Gt.nodes)
        # TODO remove distance calculation, only add edge
        for n in Gt.nodes:
            #print("add edge", node, n, Gn.nodes[node], Gn.nodes[n])
            l1 = Gn.nodes[node]["location"]
            l2 = Gn.nodes[n]["location"]

            Gn.add_edge(node, n, distance=l1.distance_to(l2))

    return Gn

def G_lookup_edge(G:nx.Graph, **query):
    result = []
    for query_key, query_value in query.items():
        if(isinstance(query_value, str)):
            query_lambda = lambda n: n == query_value
        else:
            query_lambda = query_value

        for e,d in G.edges(data=True):
            if(query_key in d and query_lambda(d[query_key])):
                result.append(e)

    return result

def G_lookup_node(G:nx.Graph, **query):
    result = []

    for query_key, query_value in query.items():
        if(isinstance(query_value, str)):
            query_lambda = lambda n: n == query_value
        else:
            query_lambda = query_value

        for n,d in G.nodes(data=True):
            if(query_key in d and query_lambda(d[query_key])):
                result.append(n)

    return result

def G_print_edges(G:nx.Graph):
    return [G.edges[n] for n in G.edges]

def G_print_nodes(G:nx.Graph):
    return [G.nodes[n] for n in G.nodes]

def G_locations(G):
    locs = [G.nodes[n]["location"] for n in G.nodes]
    xy = np.array([(l.x, l.y) for l in locs])
    return xy

def G_locations_limits(G):
    xy = G_locations(G)
    return xy.min(axis=0), xy.max(axis=0)

def G_enhance_length(G:nx.Graph):
    for ed in G.edges:
        l1 = G.nodes[ed[0]]["location"]
        l2 = G.nodes[ed[1]]["location"]
        length = l1.distance_to(l2)

        G.edges[ed]['length'] = length
    return G

def G_enhance_xy(G:nx.Graph):
    for n in G.nodes():
        node = G.nodes[n]
        loc = node["location"]
        node["x"] = loc.x
        node["y"] = loc.y
    return G

def G_task_to_multigraph(G:nx.Graph):
    return nx.MultiDiGraph(G)

def path_heuristic_distance_to(G:nx.Graph, s:int,t:int):
        sl = G.nodes[s]["location"]
        tl = G.nodes[t]["location"]

        return sl.distance_to(tl)

def G_find_path(G:nx.Graph, source:int, target:int, weight, heuristic=None):
    """Return the path from source to target location using astar algorithm from
    :func:`networkx.algorithms.shortest_paths.astar_path`
    """
    if heuristic is None:
        heuristic_func = functools.partial(path_heuristic_distance_to, G)

    return nx.algorithms.shortest_paths.astar_path(G, source, target,
                                                   heuristic=heuristic_func, weight=weight)

def G_path_length(G:nx.Graph, path:List[int]):
    dist = 0

    if isinstance(path[0], list): # list of path
        for p in path:
            dist += G_path_length(G, p)

    else:
        for i,j in zip(path[:-1], path[1:]):
            li = G.nodes[i]["location"]
            lj = G.nodes[j]["location"]

            d = li.distance_to(lj)

            #print(li, lj, d)
            dist += d

    return dist

def G_nxnodelist_to_subpaths(G:nx.Graph, tasklist:List[int]):
    task_path = []

    for t1, t2 in zip(tasklist[:-1], tasklist[1:]):
        #print(t1, t2)
        l1 = G.nodes[t1]["location"]
        l2 = G.nodes[t2]["location"]

        subpath = l1.path_to(l2)
        task_path.append(subpath)

        #print("->", subpath)
        #print("######")
    return task_path
