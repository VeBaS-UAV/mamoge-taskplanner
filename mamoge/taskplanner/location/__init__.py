import numpy as np
import networkx as nx

from abc import abstractmethod
from typing import Any

from geopy import distance as gps_distance
from mamoge.taskplanner import nx as mamogenx

# %%

class Location:
    """Represent an abstract location and define some common method defintions."""

    def __init__(self, type:str):
        self.type = type

    @abstractmethod
    def as_dict(self):
        """Return location content as dict
        """
        pass

    @abstractmethod
    def distance_to(self, other:"Location"):
        """Return the distance to the other location.
        This can be the direct distance or some other distance (e.g. along a path)
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

class GraphLocation(Location):
    """Represent a Location in a Graph. Thus a :method `path_to` between two locations
    """
    @abstractmethod
    def path_to(self, other:Location):
        """Return a list of :class `Location` item from the current location to the given one
        """
        return None

class LocationBuilder():
    """Return a Location object based on a dict with a type
    """
    _location_classes: Location = {}
    @staticmethod
    def location_from_dict(location_dict: dict) -> Location:
        location_type = location_dict["type"]
        kw_args = location_dict.copy()
        kw_args.pop("type")

        if location_type in LocationBuilder._location_classes:
            locationClass = LocationBuilder._location_classes[location_type]
            return locationClass(**kw_args)
        else:
            raise Exception(f"Could not find location type {location_type}")

    @staticmethod
    def add_locationclass(type:str, handler:Location):
        LocationBuilder._location_classes[type] = handler


class CartesianLocation(Location):
    """Represent a Location in cartesian space
    """

    def __init__(self, x, y):
        Location.__init__(self, "cartesian")
        self._x = x
        self._y = y

    def as_dict(self) -> dict:
        return dict(type=self.type, x=self.x, y=self.y)

    def distance_to(self, other: Location) -> float:
        dx = self.x - other.x
        dy = self.y - other.y

        # use manhatten distance for debugging
        # TODO use euclidean distance in production / later
        return abs(dx) + abs(dy)

    def __repr__(self):
        return f"CartesianLocation({self.x},{self.y})"

    def as_tuple(self):
        return self._x, self._y

class GPSLocation(Location):
    """Represent a global location in lat and lon coordinates"""

    def __init__(self, latitude, longitude, altitude=None):
       Location.__init__(self, "gps")
       self.latitude = latitude
       self.longitude = longitude
       self.altitude = altitude

    def as_dict(self) -> dict:
        return dict(type=self.type, latitude=self.latitude,
                    longitude=self.longitude, altitude=self.altitude)

    def as_tuple(self) -> tuple:
        return (self.longitude, self.latitude)

    def distance_to(self, other: "GPSLocation") -> float:
        """Return the distance between two gps position, using geopy library and WGS84 ellipsoid"""
        return gps_distance.distance(self.latlon(), other.latlon()).meters

    def __repr__(self):
        return f"GPSLocation({self.latitude},{self.longitude},{self.altitude})"

    def latlon(self):
        """Return the lat and longitude values as a tuple"""
        return self.latitude, self.longitude


class GPSCartesianLocation(GPSLocation):

    def __init__(self, x, y, origin=None, bearing=0):
        if origin is None:
            origin = 51.87820297838263, 8.771718854268894 # Senne
        lat, lon = origin
        lat, lon = cartesian_offset_to_latlon(x, y, lat, lon, bearing)
        self._x_init = x
        self._y_init = y
        GPSLocation.__init__(self, lat, lon)

    def __repr__(self):
        return f"GPSCartesianLocation({self.latitude},{self.longitude},{self.altitude},{self._x_init},{self._y_init})"



class NXLocation(GraphLocation):
    """A graph location"""
    def __init__(self, G_base: nx.Graph(), **nx_args):
       Location.__init__(self, "nx")
       self.G_base = G_base
       self.nx_args = nx_args

    def base_node(self):
        node = mamogenx.G_lookup_node(self.G_base, **self.nx_args)

        if len(node) > 0:
            return node[0]

    def as_dict(self) -> dict:
        base_id = self.base_node()
        base_node = self.G_base.nodes[base_id]

        return {**dict(type=self.type), **self.nx_args, **base_node}

    def as_tuple(self) -> tuple:
        base_id = self.base_node()
        base_node = self.G_base.nodes[base_id]["location"]

        if base_node:
            return base_node.as_tuple()

        return (None, None)

    def distance_to(self, other: "NXLocation") -> float:
        """Return the distance to the next nx location as the distance along the path to the other location in the base graph"""
        path = self.path_to(other)

        return len(path)

    def path_to(self, other: "NXLocation", weight="length") -> list[Any]:
        """Return the path to the other node using astar algorithm.
        """
        l1 = self.base_node()
        l2 = other.base_node()

        path = mamogenx.G_find_path(self.G_base, l1, l2, weight=weight)

        return path

    def __repr__(self):
        bn = self.base_node()
        return f"NXLocation({self.G_base},{self.nx_args}, {bn})"


LocationBuilder.add_locationclass("cartesian", CartesianLocation)
LocationBuilder.add_locationclass("gps", GPSLocation)
LocationBuilder.add_locationclass("nx", NXLocation)

def cartesian_offset_to_latlon(x:float, y:float, lat:float, lon:float, bearing:float=0):
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
