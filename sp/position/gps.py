from . import Position
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    from pygeodesy.ellipsoidalNvector import LatLon


class GpsPosition(Position):
    LAT_INDEX = 0
    LON_INDEX = 1

    def __init__(self, lat=0, lon=0):
        Position.__init__(self)
        self._values = [0, 0]
        self.lat = lat
        self.lon = lon

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, v):
        self._values = v

    @property
    def lat(self):
        return self.values[self.LAT_INDEX]

    @lat.setter
    def lat(self, v):
        self.values[self.LAT_INDEX] = v

    @property
    def lon(self):
        return self.values[self.LON_INDEX]

    @lon.setter
    def lon(self, v):
        self.values[self.LON_INDEX] = v

    @property
    def lat_lon(self):
        return self.lat, self.lon

    @property
    def lon_lat(self):
        return self.lon, self.lat

    def distance(self, other_pos):
        if not isinstance(other_pos, GpsPosition):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other_pos.lat_lon)
        return s.distanceTo(d)

    def intermediate(self, other_pos, fraction):
        if not isinstance(other_pos, GpsPosition):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other_pos.lat_lon)
        inter_p = s.intermediateTo(d, fraction)
        return GpsPosition(inter_p.lat, inter_p.lon)

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        pos = (float(json_data[0]), float(json_data[1]))
    elif isinstance(json_data, dict):
        if "x" in json_data and "y" in json_data:
            pos = (float(json_data["y"]), float(json_data["x"]))
        elif "lat" in json_data and "lon" in json_data:
            pos = (float(json_data["lat"]), float(json_data["lon"]))
    else:
        raise TypeError
    return GpsPosition(*pos)




