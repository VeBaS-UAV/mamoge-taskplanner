from typing import Any, List
import networkx as nx
from networkx.algorithms import dag
import numpy as np
import matplotlib
import matplotlib.pylab as plt
import functools
import numpy as np
import itertools

from multiprocessing import Pool
from mamoge.taskplanner.location import ZeroDistanceLocation


def G_draw_taskgraph_w_pos_layer(G: nx.Graph):
    pos = nx.drawing.layout.multipartite_layout(G, subset_key="layer")
    return G_draw_taskgraph(G, pos=pos)


def G_draw_taskgraph_w_pos_location(G: nx.Graph):
    pos = {n: G.nodes[n]["location"].as_tuple() for n in G.nodes}
    #print("pos", pos)
    return G_draw_taskgraph(G, pos=pos)


def G_draw_taskgraph(G: nx.Graph, pos=None) -> None:
    """Plot a task graph using location and distance attributes"""
    fig = matplotlib.pyplot.gcf()
    fig.set_size_inches(18.5, 8.5)
#    if pos is None:
#        pos = {n:G.nodes[n]["location"] for n in G.nodes}

    colors = (["#00aaaa"] * len(G))
    colors[0] = "#00aa00"

    try:
        labels_dict = {l: G.nodes[l]["name"] + f"({l})" for l in G.nodes}
    except:
        labels_dict = None

    # nx.draw(G, node_color=colors, pos=pos, with_labels=True, labels=labels_dict, lab)
    new_pos = {k: (v[0]+0.1, v[1]+0.12) for k, v in pos.items()}
    # print(pos)
    nx.draw_networkx(G, node_color=colors, pos=pos,
                     node_shape='s', node_size=1000)
    nx.draw_networkx_labels(G, new_pos, labels=labels_dict, font_size=10)

    try:
        edge_dict = {w: G[w[0]][w[1]] for w in G.edges}
        # if len(edge_dict) >0:
        # print(edge_dict)
        nx.draw_networkx_edge_labels(
            G, pos, edge_labels=edge_dict, font_color='red')
    except:
        # TODO check for distance or length or weight attribute
        pass


def G_draw_locationgraph(G: nx.Graph, path: List[Any] = None):
    """Plot a task graph using location and distance attributes"""

    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    pos = {n: G.nodes[n]["location"].as_tuple() for n in G.nodes}
    offset_label = 0.2
    pos_label = {n: (v[0]+offset_label, v[1]+offset_label)
                 for n, v in pos.items()}

    colors = (["#00aaaa"] * len(G))
    colors[0] = "#00aa00"

    labels_dict = {l: str(G.nodes[l]["name"]) + f"({l})" for l in G.nodes}

    nx.draw(G, node_color=colors, pos=pos)
    nx.draw_networkx_labels(G, pos=pos_label, labels=labels_dict)

    if path:
        nx.draw_networkx_edges(G, pos, edgelist=list(
            zip(path, path[1:])), edge_color='r', width=5)

    # plt.tight_layout()

    xy_lim = G_locations_limits(G)

    ax.set_xlim((xy_lim[0][0]-1, xy_lim[1][0]+1))
    ax.set_ylim((xy_lim[0][1]-1, xy_lim[1][1]+1))


def G_distance_manhatten(G: nx.Graph, i: Any, j: Any, distance_attribute="location") -> float:
    """Return the manhatten distance between two given nodes i and j
       and the attribute used to calculate the distance"""
    l1 = np.array(G.nodes[i][distance_attribute])
    l2 = np.array(G.nodes[j][distance_attribute])

    return float(np.abs(l1-l2).sum())


def G_distance_location(G: nx.Graph, i: Any, j: Any, fallback=None):
    # print("G_distance_location", G, i, j)
    # print(G.nodes)

    n_i = G.nodes[i]
    n_j = G.nodes[j]

    if "location" not in n_i or "location" not in n_j:
        # print("zero distance for node", i, j)
        return 0

    print(n_i, n_j)

    location_i = G.nodes[i]["location"]

    location_j = G.nodes[j]["location"]

    if location_i is None:
        # print("zero distance for node 2", i,j)
        return fallback

    if location_j is None:

        if G.has_edge(i, j):
            # print("zero distance for node 3", i,j)
            return 0
        else:
            # print("zero distance for node 4", i,j)
            return fallback

    if isinstance(location_j, ZeroDistanceLocation):
        if G.has_edge(i, j):
            return 0
        return fallback

    distance = location_i.distance_to(location_j)

    if distance is None:
        return fallback

    return distance


def G_time_callback(G, u, v, velocity, fallback=24*60*60*360):
    '''calculate the time requirement based on distanve between u,v and given velocity'''
    try:
        distance = G_distance_location(G, u, v)

        # print(u,v, distance)
        if(distance is None):
            return fallback

        time = distance / velocity

        return time
    except Exception as e:
        print("Exception", e)
        print("G,u,v", G, u, v)
        return fallback


def G_first(G: nx.Graph):
    return [n for n in G.nodes if len(list(G.predecessors(n))) == 0][0]
    # return list(dag.topological_sort(G))[0]


def G_last(G: nx.Graph):
    # return list(dag.topological_sort(G))[-1]
    return [n for n in G.nodes if len(G[n]) == 0][0]


def G_problem_from_dag(G: nx.Graph) -> nx.Graph:
    """Return a graph representing the problem for a task dag"""

    # Gn = nx.DiGraph()
    Gn = G.copy()
    for node, anodes in G.adjacency():
        #print("it node", node, G.nodes[node])
        node_args = G.nodes[node]
        if "location" in node_args:
            node_args["location"].G = Gn

        Gn.add_node(node, **G.nodes[node])
        for anode in anodes:
            Gn.add_edge(node, anode, **G.edges[(node, anode)])

        anc = dag.ancestors(G, node)
        desc = dag.descendants(G, node)

        Gt = G.copy()
        Gt.remove_nodes_from(list(anc))
        Gt.remove_nodes_from(list(desc))
        Gt.remove_node(node)

        #print("Gt nodes", node, anc, desc,  Gt.nodes)
        # TODO remove distance calculation, only add edge
        for n in Gt.nodes:

            #print("add edge", node, n, Gn.nodes[node], Gn.nodes[n])
            l1 = Gn.nodes[node]["location"]
            l2 = Gn.nodes[n]["location"]

            # edge_args = Gn.edges[(node,n)]
            # TODO do we need a distance clalculation here?
            #Gn.add_edge(node, n, distance=l1.distance_to(l2))
            Gn.add_edge(node, n)

    return Gn


class TaskConstraint():
    '''structure to save the constraint date for edge(u,v) and dimension with given kwargs'''

    def __init__(self, u: int, v: int, dimension: str = None, **constraint_args):
        self.u = u
        self.v = v
        self.dimension = dimension
        self.kw_args = constraint_args
        pass

    def __repr__(self):
        return f"TaskConstraint({self.u}, {self.v}, dimension:{self.dimension}, {self.kw_args}"


def G_descendent_constrains(G, kw_args_callback=None):
    first, last = G_first(G), G_last(G)

    constrains = []
    for u in G.nodes:

        if u in (first, last):
            continue

        desc = nx.algorithms.dag.descendants(G, u)

        for v in desc:
            if v in (first, last):
                continue

            if (kw_args_callback is not None):
                kw_args = kw_args_callback(u, v)
                if kw_args is not None:
                    constrains.append(TaskConstraint(u, v, **kw_args))
            else:
                constrains.append(TaskConstraint(u, v))

    return constrains


def G_lookup_edge(G: nx.Graph, **query):
    result = []
    for query_key, query_value in query.items():
        if(isinstance(query_value, str)):
            def query_lambda(n): return n == query_value
        else:
            query_lambda = query_value

        for u, v, d in G.edges(data=True):
            if(query_key in d and query_lambda(d[query_key])):
                result.append((u, v, d))

    return result


def G_lookup_node(G: nx.Graph, **query):
    '''select subset of nodes based on keyword arguments (key=value or key=lambda expression)
    example:
     - G_lookup_node(G, name='node_x')
     - G_lookup_node(G, name=lambda name: name in ["node_x", "node_y"])
    '''
    result = []

    for query_key, query_value in query.items():
        if(isinstance(query_value, str)):
            def query_lambda(n): return n == query_value
        else:
            query_lambda = query_value

        for n, d in G.nodes(data=True):
            if(query_key in d and query_lambda(d[query_key])):
                result.append(n)

    return result


def G_print_edges(G: nx.Graph):
    return [G.edges[n] for n in G.edges]


def G_print_nodes(G: nx.Graph):
    return [G.nodes[n] for n in G.nodes]


def G_locations(G):
    locs = [G.nodes[n]["location"] for n in G.nodes]
    xy = np.array([(l.x, l.y) for l in locs])
    return xy


def G_locations_limits(G):
    xy = G_locations(G)
    return xy.min(axis=0), xy.max(axis=0)


def G_enhance_length(G: nx.Graph):
    '''add length attribute to each edge base on underlying location distance'''
    for ed in G.edges:
        l1 = G.nodes[ed[0]]["location"]
        l2 = G.nodes[ed[1]]["location"]
        length = l1.distance_to(l2)

        G.edges[ed]['length'] = length
    return G


def G_enhance_xy(G: nx.Graph):
    '''add x,y coordinates from lat,lon to each node'''
    for n in G.nodes():
        node = G.nodes[n]
        loc = node["location"]
        node["x"] = loc.x
        node["y"] = loc.y
    return G


def G_task_to_multigraph(G: nx.Graph):
    return nx.MultiDiGraph(G)


def path_heuristic_distance_to(G: nx.Graph, s: int, t: int):
    sl = G.nodes[s]["location"]
    tl = G.nodes[t]["location"]

    return sl.distance_to(tl)


def G_find_path(G: nx.Graph, source: int, target: int, weight, heuristic=None):
    """Return the path from source to target location using astar algorithm from
    :func:`networkx.algorithms.shortest_paths.astar_path`
    """
    if heuristic is None:
        heuristic_func = functools.partial(path_heuristic_distance_to, G)

    return nx.algorithms.shortest_paths.astar_path(G, source, target,
                                                   heuristic=heuristic_func, weight=weight)


def G_path_length(G: nx.Graph, path: List[int]):
    dist = 0

    if isinstance(path[0], list):  # list of path
        for p in path:
            dist += G_path_length(G, p)

    else:
        for i, j in zip(path[:-1], path[1:]):
            li = G.nodes[i]["location"]
            lj = G.nodes[j]["location"]

            d = li.distance_to(lj)

            #print(li, lj, d)
            dist += d

    return dist


def G_nxnodelist_to_subpaths(G: nx.Graph, tasklist: List[int]):
    task_path = []

    for t1, t2 in zip(tasklist[:-1], tasklist[1:]):
        # print(t1, t2)
        l1 = G.nodes[t1]["location"]
        l2 = G.nodes[t2]["location"]

        subpath = l1.path_to(l2)
        task_path.append(subpath)

        #print("->", subpath)
        # print("######")
    return task_path


def G_cost_vector(G, cost_callback, cost_fallback=np.inf):
    l = len(G)
    cost_vector = np.zeros(l)
    # cost_vector

    for i in range(l):
        d1 = cost_callback(i)

        # check if there is a way to the other location
        if (d1 is None):
            d1 = cost_fallback

        cost_vector[i] = d1

    return cost_vector


def G_distance_matrix(G, distance_fallback=np.inf):
    l = len(G)
    distance_matrix = np.zeros((l, l))
    # distance_matrix

    for i, j in itertools.combinations(range(l), r=2):
        l1 = G.nodes[i]["location"]
        l2 = G.nodes[j]["location"]

        d1 = l1.distance_to(l2)

        # check if there is a way to the other location
        if (d1 is None):
            d1 = distance_fallback

        distance_matrix[i, j] = d1
        distance_matrix[j, i] = d1

    return distance_matrix


def G_cost_matrix(G, cost_callback, cost_fallback=np.inf):
    l = len(G)
    cost_matrix = np.zeros((l, l))
    # cost_matrix

    ij_args = list(itertools.combinations(range(l), r=2))
    # print(list(ij_args))

    run_mp = False
    if run_mp:
        with Pool(5) as mp:
            # results = mp.map(functools.partial(cost_callback, G), ij_args)
            results = mp.map(functools.partial(
                multiprocessing_partial, cost_callback, G), ij_args)
            # results = mp.map(cost_callback, ij_args
    else:
        results = {}
        for ij, (i, j) in enumerate(ij_args):
            results[ij] = cost_callback(G, i, j)

    for ij, (i, j) in enumerate(ij_args):
        d1 = results[ij]
    # for i, j in itertools.combinations(range(l), r=2):
        # d1 = cost_callback((i,j))

        # check if there is a way to the other location
        if (d1 is None):
            d1 = cost_fallback
        else:
            d1 = int(d1)
        cost_matrix[i, j] = d1
        cost_matrix[j, i] = d1

    return cost_matrix


def log_args(*args, **kw_args):
    print("log_args", args, kw_args)
    return args, kw_args


def multiprocessing_partial(func, static_args, dynamic_args):
    return func(*[static_args], *dynamic_args)
