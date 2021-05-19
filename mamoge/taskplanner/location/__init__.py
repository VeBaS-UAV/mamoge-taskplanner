import numpy as np
import networkx as nx

from abc import abstractmethod
from typing import Any

from geopy import distance as gps_distance

# %%

class Location:

    def __init__(self, type):
        self.type = type

    @abstractmethod
    def as_dict(self):
        pass

    @abstractmethod
    def distance_to(self, other):
        pass

    @abstractmethod
    def as_tuple(self):
        pass

class LocationBuilder():

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

    def __init__(self, x, y):
        Location.__init__(self, "cartesian")
        self.x = x
        self.y = y

    def as_dict(self) -> dict:
        return dict(type=self.type, x=self.x, y=self.y)

    def distance_to(self, other: "CartesianLocation") -> float:
        dx = self.x - other.x
        dy = self.y - other.y

        # use manhatten distance
        return abs(dx) + abs(dy)

    def __repr__(self):
        return f"CartesianLocation({self.x},{self.y})"

    def as_tuple(self):
        return self.x, self.y


class GPSLocation(Location):

    def __init__(self, latitude, longitude, altitude=None):
       Location.__init__(self, "gps")
       self.latitude = latitude
       self.longitude = longitude
       self.altitude = altitude

    def as_dict(self) -> dict:
        return dict(type=self.type, latitude=self.latitude,
                    longitude=self.longitude, altitude=self.altitude)

    def as_tuple(self) -> tuple:
        return (self.latitude, self.longitude, self.altitude)

    def distance_to(self, other: "GPSLocation") -> float:
        return gps_distance.distance(self.as_tuple(), other.as_tuple()).meters

    def __repr__(self):
        return f"GPSLocation({self.latitude},{self.longitude},{self.altitude})"

LocationBuilder.add_locationclass("cartesian", CartesianLocation)
LocationBuilder.add_locationclass("gps", GPSLocation)


# %%
