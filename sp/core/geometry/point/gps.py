from . import Point
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    from pygeodesy.ellipsoidalNvector import LatLon


class GpsPoint(Point):
    LON_INDEX = 0
    LAT_INDEX = 1

    def __init__(self, lon=0, lat=0):
        Point.__init__(self)
        self._values = [0, 0]
        self.lat = lat
        self.lon = lon

    @property
    def values(self):
        return self._values

    @values.setter
    def values(self, v):
        self._values = list(v)

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

    def distance(self, other):
        if not isinstance(other, GpsPoint):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other.lat_lon)
        return s.distanceTo(d)

    def intermediate(self, other, fraction):
        if not isinstance(other, GpsPoint):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other.lat_lon)
        inter_p = s.intermediateTo(d, fraction)
        return GpsPoint(lon=inter_p.lon, lat=inter_p.lat)

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    lat = None
    lon = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        lon = float(json_data[0])
        lat = float(json_data[1])
    elif isinstance(json_data, dict):
        if "x" in json_data and "y" in json_data:
            lon = float(json_data["x"])
            lat = float(json_data["y"])
        elif "lat" in json_data and "lon" in json_data:
            lon = float(json_data["lon"])
            lat = float(json_data["lat"])
    else:
        raise TypeError
    return GpsPoint(lon=lon, lat=lat)




