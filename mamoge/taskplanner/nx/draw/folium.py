import networkx as nx
import numpy as np
import folium
import folium.plugins
import osmnx as ox
import osmnx
import osmnx.folium

import mamoge.taskplanner.nx as mamogenx

def draw_folium_new_map(G:nx.Graph):
        origin = np.array(list(nx.get_node_attributes(G, "y").values())).mean(), \
                    np.array(list(nx.get_node_attributes(G, "x").values())).mean()
        folium_map=folium.Map(location=origin, zoom_start=14)

        #folium_map.add_child(folium.LayerControl())
        folium_map.add_child(folium.plugins.MeasureControl())

        return folium_map

def draw_folium_map_route(G, folium_map=None):

    if folium_map is None:
        folium_map = draw_folium_new_map(G)

    fg_route=folium.FeatureGroup(name='routegraph', show=True, control=True, overlay=True)
    #fg_map=folium.FeatureGroup(name='map', show=True, control=True)

    folium_map.add_child(fg_route)
    #imap.add_child(fg_map)

    ox.folium.plot_graph_folium(mamogenx.G_task_to_multigraph(G), graph_map=fg_route)

    return folium_map

def draw_folium_poi(G, poi_ids, folium_map=None, name="POI", show=True,**draw_args):

    if folium_map is None:
        folium_map = draw_folium_new_map(G)

    fg_poi = folium.FeatureGroup(name=name, show=show, control=True, overlay=True)
    folium_map.add_child(fg_poi)

    for i, _id in enumerate(poi_ids):
        _node = G.nodes[_id]
        loc = _node["location"]
        name = _node["name"]

        tagname = f"{name}({i})"


        folium.Marker(location=(loc.y, loc.x),
                      popup=tagname, icon=folium.Icon(**draw_args)).add_to(fg_poi)

    return folium_map

def draw_folium_path(G, path, folium_map=None, name="name", color=None, show=True, **draw_args):



    if folium_map is None:
        folium_map = draw_folium_new_map(G)


    if isinstance(path[0], list):
        print(path)
        for i, subpath in enumerate(path):
            folium_map = draw_folium_path(G, subpath, folium_map=folium_map, name=f"path {i}", show=show)

        return folium_map

    colors = ['red', 'green', 'yellow', 'orange', 'black', 'purple']

    if color is None:
        color = np.random.choice(colors)

    fg_path=folium.FeatureGroup(name=name, show=show, control=True, overlay=True)
    folium_map.add_child(fg_path)

    xv = [G.nodes[i]["x"] for i in path]
    yv = [G.nodes[i]["y"] for i in path]
    loc = [(y,x) for y,x in zip(yv, xv)]

    folium.plugins.AntPath(locations=loc, color=color, **draw_args).add_to(fg_path)
    return folium_map
