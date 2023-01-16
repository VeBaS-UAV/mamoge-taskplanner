#!/usr/bin/env python3

import networkx as nx
import matplotlib.pylab as plt

from mamoge.models.tasks import Task, TaskSyncPoint


def enhance_layer(G):

    anc = {s: nx.ancestors(G, s) for s in G.nodes}

    for task, ancestors in anc.items():
        nx.set_node_attributes(G, {task: {"layer": len(ancestors)}})

    return G


def determine_node_color(task: Task):
    if isinstance(task, TaskSyncPoint):
        return "black"

    return "#67E568"


def draw_taskgraph(G):
    G = enhance_layer(G)
    pos = nx.drawing.layout.multipartite_layout(G, subset_key="layer")

    node_colors = [determine_node_color(t) for t in G.nodes]

    # fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    fig, ax = plt.subplots(1, 1)
    nx.draw(G, pos, with_labels=False, ax=ax, node_color=node_colors)
    pos = {t: (p[0] + 0.0, p[1] - 0.025) for t, p in pos.items()}
    labels = {t: str(t.name) for t in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, ax=ax)

    return G
