import geopy.distance
import networkx as nx

from mamoge.taskplanner.location import CartesianLocation
from mamoge.taskplanner.location import GPSLocation
from mamoge.taskplanner.location import cartesian_offset_to_latlon
from mamoge.taskplanner.nx import G_distance_location

# %%


def test_cartesian_distance():
    c1 = CartesianLocation(1, 1)
    c2 = CartesianLocation(3, 2)

    assert c1.distance_to(c2) == 3


def test_cartesian_distance_w_graph():
    c1 = CartesianLocation(1, 1)
    c2 = CartesianLocation(4, 2)

    G = nx.DiGraph()

    G.add_node(0, location=c1)
    G.add_node(1, location=c2)

    distance = G_distance_location(G, 0, 1)

    assert distance == 4


def test_gps_distance():

    g1 = GPSLocation(51.7444167, 8.8227609)
    g2 = GPSLocation(51.7440672, 8.8233740)

    dist = g1.distance_to(g2)

    assert abs(dist - 57.5) < 0.1


def test_gps_distance_w_graph():

    g1 = GPSLocation(51.7444167, 8.8227609)
    g2 = GPSLocation(51.7440672, 8.8233740)

    G = nx.DiGraph()

    G.add_node(0, location=g1)
    G.add_node(1, location=g2)

    distance = G_distance_location(G, 0, 1)

    assert abs(distance - 57.5) < 0.1


def test_gps_offset():
    lat, lon = 51.7444167, 8.8227609

    dx = 100
    dy = 0

    lat1, lon2 = cartesian_offset_to_latlon(dx, dy, lat, lon, 90)

    new_distance = geopy.distance.distance((lat, lon), (lat1, lon2)).meters

    assert abs(new_distance - dx) < 0.01
