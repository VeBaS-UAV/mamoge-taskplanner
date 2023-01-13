#!/usr/bin/env python3

from typing import List, Generator
import networkx as nx
from mamoge.models.capabilities import Capabilities, Requirements

from mamoge.models.tasks import Task


def create_subgraph(G, node):
    edges = nx.dfs_successors(G, node)
    nodes = []
    for k, v in edges.items():
        nodes.extend([k])
        nodes.extend(v)
    return G.subgraph(nodes)


def dag_paths(G: nx.DiGraph, path: List[Task]):
    task = path[-1]

    if len(G.edges(task)) == 0:
        yield path

    for _, next_task in G.edges(task):
        new_path = path + [next_task]
        yield from dag_paths(G, new_path)


def dag_paths_until_syncpoint(G: nx.DiGraph, path: List[Task]):
    task = path[-1]

    if len(G.edges(task)) == 0:
        yield path
        return

    if len(G.in_edges(task)) > 1:
        yield path[:-1]
        return

    for _, next_task in G.edges(task):
        new_path = path + [next_task]
        yield from dag_paths_until_syncpoint(G, new_path)


def dag_paths_w_capabilities(G: nx.DiGraph, path: List[Task], cb: Capabilities):
    """return a List[Task] of all possible path in the given Graph"""

    task = path[-1]

    req = sum_requirements(path)
    if not cb.satisfy(req):
        yield path[:-1]
        # return statement in order to stop yielding
        return

    if len(G.edges(task)) == 0:
        yield path
        # return statement in order to stop yielding
        return

    for _, next_task in G.edges(task):
        new_path = path + [next_task]
        yield from dag_paths_w_capabilities(G, new_path, cb)


def sum_requirements(path: List[Task]):

    req = Requirements()
    for t in path:
        req += t.requirements

    return req
