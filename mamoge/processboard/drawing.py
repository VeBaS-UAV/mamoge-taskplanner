#!/usr/bin/env python3

import networkx as nx
import matplotlib.pylab as plt


def enhance_layer(G):

    anc = {s: nx.ancestors(G, s) for s in G.nodes}

    for task, ancestors in anc.items():
        nx.set_node_attributes(G, {task: {"layer": len(ancestors)}})

    return G


def draw_taskgraph(G):
    G = enhance_layer(G)
    pos = nx.drawing.layout.multipartite_layout(G, subset_key="layer")
    # fig, ax = plt.subplots(1, 1, figsize=(12, 12))
    fig, ax = plt.subplots(1, 1)
    nx.draw(G, pos, with_labels=False, ax=ax)
    pos = {t: (p[0] + 0.0, p[1] - 0.025) for t, p in pos.items()}
    labels = {t: str(t) for t in G.nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=7, ax=ax)

    return G
