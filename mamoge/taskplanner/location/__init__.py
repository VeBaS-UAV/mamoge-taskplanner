import numpy as np
import networkx as nx

from abc import abstractmethod
from typing import Any, List

from geopy import distance as gps_distance
from mamoge.taskplanner import nx as mamogenx

# %%


def cached_result(func):
    # print("check cache", func)

    cache = {}

    def inner(*args, **kw_args):
        # breakpoint()
        key = str((args, kw_args))
        # print("cahce check", key)
        if key in cache:
            # print("cache hit")
            return cache[key]
            # return func(*args, **kw_args)

        result = func(*args, **kw_args)
        cache[key] = result
        return result
    return inner


class Location:
    """Represent an abstract location."""

    def __init__(self, type: str):
        self.type = type

    def as_dict(self) -> dict:
        return dict(type=self.type,
                    x=self.x, y=self.y, z=self.z,
                    latitude=self.latitude,
                    longitude=self.longitude,
                    altitude=self.altitude)

    @abstractmethod
    def distance_to(self, other: "Location"):
        """Return the distance to the other location.

        This can be the direct distance or some other distance
        (e.g. along a path).
        """
        pass

    @abstractmethod
    def as_tuple(self):
        pass

    @property
    def x(self):
        """Return the x coordinate of the location.

        In case of global position, x is longitude and y the latitude value
        """
        return self.as_tuple()[0]

    @property
    def y(self):
        """Return the y coordinate of the location.

        In case of global position, x is longitude and y the latitude value
        """
        return self.as_tuple()[1]

    @property
    def z(self):
        """Return the y coordinate of the location.

        In case of global position, x is longitude and y the latitude value
        """
        return self.as_tuple()[2]

    @property
    def latitude(self):
        return self.as_tuple()[1]

    @property
    def longitude(self):
        return self.as_tuple()[0]

    @property
    def altitude(self):
        return self.as_tuple()[2]

    def latlon(self):
        return self.latitude, self.longitude

# __getitem__()


class GraphLocation(Location):
    """Represent a Location in a Graph.

    Thus a :method `path_to` between two locations.
    """

    @abstractmethod
    def path_to(self, other: Location):
        """Return a list of :class `Location` item from the current location to the given one
        """
        return None


class LocationBuilder():
    """Return a Location object based on a dict with a type."""
    _location_classes: Location = {}

    @staticmethod
    def location_from_dict(location_dict: dict) -> Location:
        location_type = location_dict["type"]
        kw_args = location_dict.copy()
        kw_args.pop("type")

        if location_type in LocationBuilder._location_classes:
            location_class = LocationBuilder._location_classes[location_type]
            return location_class(**kw_args)
        else:
            raise Exception(f"Could not find location type {location_type}")

    @staticmethod
    def add_locationclass(type: str, handler: Location):
        LocationBuilder._location_classes[type] = handler


class CartesianLocation(Location):
    """Represent a Location in cartesian space
    """

    def __init__(self, x, y, z=0, distance_func=np.linalg.norm):
        Location.__init__(self, "cartesian")
        self._x = x
        self._y = y
        self._z = z
        self._distance_func = distance_func

    def distance_to(self, other: Location) -> float:
        dx = self.x - other.x
        dy = self.y - other.y

        d_array = np.array([dx, dy])
        return self._distance_func(d_array)

    def __repr__(self):
        return f"CartesianLocation({self.x},{self.y}, {self.z})"

    def as_tuple(self):
        return self._x, self._y, self._z


class GPSLocation(Location):
    """Represent a global location in lat and lon coordinates."""

    def __init__(self, latitude, longitude, altitude=None):
        Location.__init__(self, "gps")
        self._latitude = latitude
        self._longitude = longitude
        self._altitude = altitude

    def as_tuple(self) -> tuple:
        return (self._longitude, self._latitude, self._altitude)

    @cached_result
    def distance_to(self, other: "GPSLocation") -> float:
        """Return the distance between two gps position, using geopy library and WGS84 ellipsoid"""
        return gps_distance.distance(self.latlon(), other.latlon()).meters

    def __repr__(self):
        return f"GPSLocation({self._latitude},{self._longitude},{self._altitude})"

    def location(self):
        """Return the lat and _longitude values as a tuple"""
        return self._latitude, self._longitude, self._altitude


class GPSCartesianLocation(GPSLocation):

    def __init__(self, x, y, origin=None, bearing=0):
        if origin is None:
            origin = 0, 0  # 51.87820297838263, 8.771718854268894 # Senne
        lat, lon = origin
        lat, lon = cartesian_offset_to_latlon(x, y, lat, lon, bearing)
        self._x_init = x
        self._y_init = y
        GPSLocation.__init__(self, lat, lon)

    def __repr__(self):
        return f"GPSCartesianLocation({self.latitude},{self.longitude},{self.altitude},{self._x_init},{self._y_init})"


class ZeroDistanceLocation(Location):
    """A graph location"""

    def __init__(self):
        Location.__init__(self, "nx")

    @cached_result
    def distance_to(self, other: "Location") -> float:
        """Return the distance 0"""
        return 0

    @cached_result
    def path_to(self, other: "NXLocation", weight="length") -> List[Any]:
        """Return the path to the other node using astar algorithm.
        """
        return []

    def __repr__(self):

        return f"ZeroDistnaceLocation()"


class NXLocation(GraphLocation):
    """A graph location"""

    def __init__(self, G_base: nx.Graph(), **nx_args):
        Location.__init__(self, "nx")
        self.G_base = G_base
        self.nx_args = nx_args

    def base_node(self):
        node_id = self.base_node_id()

        if node_id:
            return self.G_base.nodes[node_id]
        return None

    def base_node_id(self):
        node = mamogenx.G_lookup_node(self.G_base, **self.nx_args)

        if len(node) > 0:
            return node[0]

        return None

    def as_dict(self) -> dict:
        base_id = self.base_node_id()
        base_node = self.G_base.nodes[base_id]

        return {**GraphLocation.as_dict(self), **self.nx_args, **base_node}

    def as_tuple(self) -> tuple:
        base_node = self.base_node()

        if base_node:
            return base_node["location"].as_tuple()

        return (None, None)

    @cached_result
    def distance_to(self, other: "NXLocation") -> float:
        """Return the distance to the next nx location as the distance along the path to the other location in the base graph"""
        path = self.path_to(other)

        if path is None or len(path) == 0:
            return None
        #print("distance to path", path)
        dist = 0
        for s, t in zip(path[:-1], path[1:]):
            sn = self.G_base.nodes[s]["location"]
            tn = self.G_base.nodes[t]["location"]
            # print('s,t', sn, tn)
            dist += sn.distance_to(tn)

        return dist  # len(path)

    @cached_result
    def path_to(self, other: "NXLocation", weight="length") -> List[Any]:
        """Return the path to the other node using astar algorithm.
        """
        l1 = self.base_node_id()
        l2 = other.base_node_id()

        path = mamogenx.G_find_path(self.G_base, l1, l2, weight=weight)

        return path

    def __repr__(self):
        bn = self.base_node()

        return f"NXLocation({self.G_base},Base Ref: {self.nx_args}, {bn})"


class NXLayerLocation(NXLocation):

    def __init__(self, layer_id: Any, base_id: Any, G_layer: nx.Graph, G_base: nx.Graph, **nx_args):
        NXLocation.__init__(self, G_base, **nx_args)
        self.layer_id = layer_id
        self.base_id = base_id
        self.G = G_layer

    @cached_result
    def distance_to(self, other: "NXLayerLocation"):
        # return NXLocation.distance_to(self, other)
        # breakpoint()
        #
        # print("distance to NXLayerlocation", self, other)
        if other is None:
            return 0

        if (self.layer_id == other.layer_id):
            return 0

        if self.G.has_edge(self.layer_id, other.layer_id):
            return NXLocation.distance_to(self, other)
        else:
            return None

    @cached_result
    def path_to(self, other: "NXLayerLocation"):
        try:
            if (self.layer_id == other.layer_id):
                return [self.layer_id]
            if self.G.has_edge(self.layer_id, other.layer_id):
                return NXLocation.path_to(self, other)
            else:
                return None
        except Exception as e:
            print("Could not find path to node", e)
            return None

    def __repr__(self):
        bn = self.base_node()

        return f"NXLayerLocation({self.layer_id}->{self.base_id}, {bn})"

    def as_dict(self):
        return {**NXLocation.as_dict(self), **self.base_node()}


LocationBuilder.add_locationclass("cartesian", CartesianLocation)
LocationBuilder.add_locationclass("gps", GPSLocation)
LocationBuilder.add_locationclass("nx", NXLocation)


def cartesian_offset_to_latlon(x: float, y: float, lat: float, lon: float, bearing: float = 0):
    """Reterns an offset location auf the given x,y offset from the given lat lon coordinates and bearing
    Parameters:
        x: offset in x direction (in meter)
        y: offset in y direction (in meter)
        lat: latitude of origin
        lon: longitude of origin
        bearing: the bearing for x,y offset (in degraa, not radians)
    """
    start = lat, lon
    dx = gps_distance.geodesic(kilometers=x/1000)
    dy = gps_distance.geodesic(kilometers=y/1000)
    target_x = dx.destination(point=start, bearing=bearing-90)
    target_y = dy.destination(point=start, bearing=bearing+180)

    d_lat = (lat - target_x.latitude) + (lat - target_y.latitude)
    d_lon = (lon - target_x.longitude) + (lon - target_y.longitude)

    return lat + d_lat, lon + d_lon


# %%
