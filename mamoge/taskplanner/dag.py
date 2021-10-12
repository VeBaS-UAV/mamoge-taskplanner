
import itertools
from mamoge.taskplanner.location import GPSLocation, NXLayerLocation
import networkx as nx

import numpy.random as random

def G_routemap_fully_connected(nodes):
    G = nx.Graph()

    # print("-----------------")
    # print(nodes)
    # print("0-00000000000000000")
    for (i, ni), (j, nj) in itertools.combinations(nodes, 2):
        # print("ij", i,j, ni, nj)
        G.add_node(i, name=f'{i}', layer=1, location=GPSLocation(latitude=ni["latitude"], longitude=ni["longitude"], altitude=ni["altitude"]))
        G.add_node(j, name=f'{j}', layer=1, location=GPSLocation(latitude=nj["latitude"], longitude=nj["longitude"], altitude=ni["altitude"]))
        G.add_edge(i, j)

    return G

def DAG_all_parallel(G_routemap, base_id, nodes):
    print("DAG_all_parallel", base_id)
    G_tasks = nx.DiGraph()
    G_tasks.graph["crs"] = "epsg:4326"

    task_base_id = f"START_base"
    G_tasks.add_node(task_base_id, name="start", layer=0, location=NXLayerLocation(layer_id=task_base_id, base_id=base_id, G_layer=G_tasks, G_base=G_routemap, name=f"{base_id}"))

    for n_id, n in nodes:
        n_id
        G_ref = G_routemap.nodes[n_id]
        task_id = f"Task_{n_id}"
        G_tasks.add_node(task_id, name=task_id, layer=1, location=NXLayerLocation(layer_id=task_id, base_id=n_id, G_layer=G_tasks, G_base=G_routemap, name=G_ref["name"]))
        G_tasks.add_edge(task_base_id,task_id)

    end_id = f"END_base"

    G_tasks.add_node(end_id, name="end", layer=2, location=NXLayerLocation(layer_id=end_id, base_id=base_id, G_layer=G_tasks, G_base=G_routemap, name=f"{base_id}"))
    [G_tasks.add_edge(task_id,end_id) for task_id in list(G_tasks.nodes)[1:-1]]


    return G_tasks
