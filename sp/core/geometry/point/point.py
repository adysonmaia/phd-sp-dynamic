from abc import ABC, abstractmethod


class Point(ABC):
    """An Abstract Geometric Point
    """

    def __init__(self):
        """Initialization
        """
        ABC.__init__(self)

    def __getitem__(self, index):
        """Get coordinate's value of a specified dimension
        Args:
            index (int): coordinate dimension
        Returns:
            float: coordinate's value
        """
        return self.values[index]

    def __setitem__(self, index, value):
        """Set coordinate's value of a specified dimension
        Args:
            index (int): coordinate dimension
            value (float): value
        """
        self.values[index] = value

    def __str__(self):
        """Get string representation of the object
        Returns:
            str: string representation
        """
        return str(self.values)

    @property
    @abstractmethod
    def values(self):
        """Get point's coordinates
        Returns:
            list: coordinates
        """
        return []

    @values.setter
    @abstractmethod
    def values(self, v):
        """Set point's coordinates
        Args:
            v (list): coordinates
        """
        pass

    @abstractmethod
    def distance(self, other):
        """Calculate distance to other point
        Args:
            other (Point): other point
        Returns:
            float: distance
        """
        return 0.0

    @abstractmethod
    def intermediate(self, other, fraction):
        """Calculate an intermediate point to the specified point that is a fraction of the distance
        from this object to the specified other point

        Args:
            other (Point): other point
            fraction (float): distance fraction (value between 0 and 1)

        Returns:
            Point: intermediate point
        """
        pass


def from_json(json_data, coord=None):
    """Create a point from a json data
    The created point can use Cartesian Coordinate System or GPS Coordinate System

    For a Cartesian Point, data can be a dict, list or tuple. E.g.:

    .. code-block:: python

        #Cartesian Point as dict
        json_data = {'x': 0.0, 'y': 1.0}
        point = sp.core.geometry.point.from_json(json_data)

        json_data = {'x': 0.0, 'y': 1.0, 'z': 2.0}
        point = sp.core.geometry.point.from_json(json_data)

        #Cartesian Point as list or tuple
        json_data = [0.0, 1.0]  # x = 0.0, y = 0.0
        point = sp.core.geometry.point.from_json(json_data)

        json_data = (0.0, 1.0)  # x = 0.0, y = 0.0
        point = sp.core.geometry.point.from_json(json_data)

        json_data = [0.0, 1.0, 2.0]  # x = 0.0, y = 0.0, z = 2.0
        point = sp.core.geometry.point.from_json(json_data)

    For a GPS Point, data needs to be a dict

    .. code-block:: python

        #GPS Point as dict
        json_data = {'lon': -122.39488, 'lat': 37.75134}
        point = sp.core.geometry.point.from_json(json_data)

    Args:
        json_data (Union[dict, list, tuple]): loaded json data
        coord (str): type of the coordinate system. Possible values are 'gps' or 'cartesian'.
            If None, it tries to automatic detect the coordinate system based on json data's parameters
    Returns:
        Point: loaded point from json data
    Raises:
        KeyError: attributes not found
    """
    from . import cartesian
    from . import gps

    loader = None
    if coord == "gps" or "lat" in json_data:
        loader = gps.from_json
    else:
        loader = cartesian.from_json

    return loader(json_data)



