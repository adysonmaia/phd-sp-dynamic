from .point import Point
import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore", category=DeprecationWarning)
    from pygeodesy.ellipsoidalNvector import LatLon


class GpsPoint(Point):
    """GPS Position
    """

    LON_INDEX = 0
    LAT_INDEX = 1

    def __init__(self, lon=0.0, lat=0.0):
        """Initialization
        Args:
            lon (float): longitude
            lat (float): latitude
        """
        Point.__init__(self)
        self._values = [0.0, 0.0]
        self.lat = lat
        self.lon = lon

    @property
    def values(self):
        """Get GPS position (longitude, latitude)
        Returns:
            list: position [longitude, latitude]
        """
        return self._values

    @values.setter
    def values(self, v):
        """Set GPS position
        Args:
            v (Union[list, tuple]): position (longitude, latitude)
        """
        self._values = list(v)

    @property
    def lat(self):
        """Get position's latitude
        Returns:
            float: latitude
        """
        return self.values[self.LAT_INDEX]

    @lat.setter
    def lat(self, v):
        """Set position's latitude
        Args:
            v (float): latitude
        """
        self.values[self.LAT_INDEX] = v

    @property
    def lon(self):
        """Get position's longitude
        Returns:
            float: longitude
        """
        return self.values[self.LON_INDEX]

    @lon.setter
    def lon(self, v):
        """Set position's longitude
        Args:
            v (float): longitude
        """
        self.values[self.LON_INDEX] = v

    @property
    def lat_lon(self):
        """Get position as (latitude, longitude) tuple
        Returns:
            tuple: (latitude, longitude) tuple
        """
        return self.lat, self.lon

    @property
    def lon_lat(self):
        """Get position as (longitude, latitude) tuple
        Returns:
            tuple: (longitude, latitude) tuple
        """
        return self.lon, self.lat

    def distance(self, other):
        """Calculate distance (in meters) to other GPS position
        Args:
            other (GpsPoint): other position
        Returns:
            float: distance in meters
        Raises:
            TypeError: other point ins't a GpsPoint
        """
        if not isinstance(other, GpsPoint):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other.lat_lon)
        return s.distanceTo(d)

    def intermediate(self, other, fraction):
        """Calculate an intermediate point to the specified point that is a fraction of the distance
        from this object to the specified other point

        Args:
            other (GpsPoint): other point
            fraction (float): distance fraction (value between 0 and 1)

        Returns:
            GpsPoint: intermediate point

        Raises:
            TypeError: other point ins't a GpsPoint
        """

        if not isinstance(other, GpsPoint):
            raise TypeError
        s = LatLon(*self.lat_lon)
        d = LatLon(*other.lat_lon)
        inter_p = s.intermediateTo(d, fraction)
        return GpsPoint(lon=inter_p.lon, lat=inter_p.lat)

    @staticmethod
    def from_json(json_data):
        """Create a GpsPoint object from a json data
        See :py:func:`sp.core.geometry.point.gps.from_json`

        Args:
            json_data (Union[dict, list, tuple]): json data
        Returns:
            GpsPoint: loaded GPS point
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a GpsPoint object from a json data

    E.g.:

    .. code-block:: python

        # Point from list
        json_data = [-122.39488, 37.75134]  # longitude = -122.39488, latitude = 37.75134
        point = sp.core.geometry.point.gps.from_json(json_data)

        # Point from tuple
        json_data = (-122.39488, 37.75134)  # longitude = -122.39488, latitude = 37.75134
        point = sp.core.geometry.point.gps.from_json(json_data)

        # Point from dict
        json_data = {'lon': -122.39488, 'lat': 37.75134}  # longitude = -122.39488, latitude = 37.75134
        point = sp.core.geometry.point.gps.from_json(json_data)

        json_data = {'x': -122.39488, 'y': 37.75134}  # longitude = -122.39488, latitude = 37.75134
        point = sp.core.geometry.point.gps.from_json(json_data)

    Args:
        json_data (Union[dict, list, tuple]): json data
    Returns:
        GpsPoint: loaded GPS point
    Raises:
        KeyError: attributes not found
    """
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
        raise KeyError
    return GpsPoint(lon=lon, lat=lat)




