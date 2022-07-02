import itertools

import networkx as nx

from mamoge.taskplanner.location import GPSLocation, NXLayerLocation


def G_routemap_fully_connected(nodes):
    graph = nx.Graph()

    # print("-----------------")
    # print(nodes)
    # print("0-00000000000000000")
    for (i, n_i), (j, n_j) in itertools.combinations(nodes, 2):
        # print("ij", i, j, ni, nj)
        graph.add_node(i,
                       name=f'{i}',
                       layer=1,
                       location=GPSLocation(latitude=n_i["latitude"],
                                            longitude=n_i["longitude"],
                                            altitude=n_i["altitude"]))
        graph.add_node(j,
                       name=f'{j}',
                       layer=1,
                       location=GPSLocation(latitude=n_j["latitude"],
                                            longitude=n_j["longitude"],
                                            altitude=n_i["altitude"]))
        graph.add_edge(i, j)

    return graph


def DAG_all_parallel(G_routemap, base_id, nodes):
    print("DAG_all_parallel", base_id)
    digraph_tasks = nx.DiGraph()
    digraph_tasks.graph["crs"] = "epsg:4326"

    task_base_id = "START_base"
    digraph_tasks.add_node(task_base_id,
                           name="start",
                           layer=0,
                           location=NXLayerLocation(layer_id=task_base_id,
                                                    base_id=base_id,
                                                    G_layer=digraph_tasks,
                                                    G_base=G_routemap,
                                                    name=f"{base_id}"))

    for n_id, n in nodes:
        g_ref = G_routemap.nodes[n_id]
        task_id = f"{n_id}"
        digraph_tasks.add_node(task_id,
                               name=task_id,
                               layer=1,
                               location=NXLayerLocation(layer_id=task_id,
                                                        base_id=n_id,
                                                        G_layer=digraph_tasks,
                                                        G_base=G_routemap,
                                                        name=g_ref["name"]))
        digraph_tasks.add_edge(task_base_id, task_id)

    end_id = "END_base"

    digraph_tasks.add_node(end_id,
                           name="end",
                           layer=2,
                           location=NXLayerLocation(layer_id=end_id,
                                                    base_id=base_id,
                                                    G_layer=digraph_tasks,
                                                    G_base=G_routemap,
                                                    name=f"{base_id}"))
    [digraph_tasks.add_edge(task_id, end_id) for task_id in list(digraph_tasks.nodes)[1:-1]]

    return digraph_tasks
