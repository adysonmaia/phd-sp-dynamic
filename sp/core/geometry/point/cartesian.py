from .point import Point
from scipy.spatial import distance
import numpy as np


class CartesianPoint(Point):
    """Point in Cartesian Coordinate System
    """

    X_INDEX = 0
    Y_INDEX = 1
    Z_INDEX = 2

    def __init__(self, *args):
        """Initialization
        Coordinate's value can be passed as a list or each value being a argument

        E.g.:

        .. code-block:: python

            # Point from a list (or tuple)
            point = CartesianPoint([0.0, 1.0, 2.0])  # x = 0.0, y = 1.0, z = 2.0
            point = CartesianPoint((0.0, 1.0, 2.0))  # x = 0.0, y = 1.0, z = 2.0

            # Each dimension's value as a separated argument
            point = CartesianPoint(0.0, 1.0, 2.0)  # x = 0.0, y = 1.0, z = 2.0

        Args:
            *args: coordinate's values
        """

        Point.__init__(self)
        self._values = [0.0, 0.0]
        if len(args) == 1:
            if isinstance(args[0], list) or isinstance(args[0], tuple):
                self.values = args[0]
            else:
                self.values = list(args[0])
        elif len(args) > 1:
            self.values = args

    @property
    def values(self):
        """Get point's coordinates
        Returns:
            np.ndarray: coordinates
        """
        return self._values

    @values.setter
    def values(self, v):
        """Set point's coordinates
        Args:
            v (Union[list, tuple, np.ndarray]): coordinates
        """
        self._values = np.array(v)

    @property
    def x(self):
        """Get value in X-axis
        Returns:
            float: value
        """
        return self._values[self.X_INDEX]

    @x.setter
    def x(self, v):
        """Set value in X-axis
        Args:
            v (float): value
        """
        self._values[self.X_INDEX] = v

    @property
    def y(self):
        """Get value in Y-axis
        Returns:
            float: value
        """
        return self._values[self.Y_INDEX]

    @y.setter
    def y(self, v):
        """Set value in Y-axis
        Args:
            v (float): value
        """
        self._values[self.Y_INDEX] = v

    @property
    def z(self):
        """Set value in Z-axis
        Returns:
            float: value
        """
        return self._values[self.Z_INDEX]

    @z.setter
    def z(self, v):
        """Set value in Z-axis
        Args:
            v (float): value
        Raises:
            IndexError: Z-axis doesn't exist in the point
        """
        if len(self._values) > 2:
            self._values[self.Z_INDEX] = v
        elif len(self._values) == 2:
            self._values.append(v)
        else:
            raise IndexError

    def distance(self, other):
        """Calculate distance to other point
        Args:
            other (Cartesian): other point
        Returns:
            float: distance
        Raises:
            TypeError: other point ins't a CartesianPoint
        """
        if not isinstance(other, CartesianPoint):
            raise TypeError
        return distance.euclidean(self.values, other.values)

    def intermediate(self, other, fraction):
        """Calculate an intermediate point to the specified point that is a fraction of the distance
        from this object to the specified other point

        Args:
            other (CartesianPoint): other point
            fraction (float): distance fraction (value between 0 and 1)
        Returns:
            CartesianPoint: intermediate point
        Raises:
            TypeError: other point ins't a CartesianPoint
        """

        if not isinstance(other, CartesianPoint):
            raise TypeError
        inter_pos = self.values
        if fraction > 0.0:
            delta_pos = other.values - self.values
            inter_pos = self.values + delta_pos * fraction
        return CartesianPoint(inter_pos)

    @staticmethod
    def from_json(json_data):
        """Create a CartesianPoint object from a json data
        See :py:func:`sp.core.geometry.point.cartesian.from_json`

        Args:
            json_data (Union[list, tuple, dict]): json data
        Returns:
            CartesianPoint: loaded point
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a CartesianPoint object from a json data

    E.g.:

    .. code-block:: python

        # Point from list
        json_data = (0.0, 1.0)  # x = 0.0, y = 1.0
        point = sp.core.geometry.point.cartesian.from_json(json_data)

        json_data = [0.0, 1.0, 2.0]  # x = 0.0, y = 1.0, z = 0.0
        point = sp.core.geometry.point.cartesian.from_json(json_data)

        # Point from tuple
        json_data = (0.0, 1.0, 2.0)  # x = 0.0, y = 1.0, z = 0.0
        point = sp.core.geometry.point.cartesian.from_json(json_data)

        # Point from dict
        json_data = {'x': 0.0, 'y': 1.0}  # x = 0.0, y = 1.0
        point = sp.core.geometry.point.cartesian.from_json(json_data)

        json_data = {'x': 0.0, 'y': 1.0, 'z': 2.0}  # x = 0.0, y = 1.0, z = 2.0
        point = sp.core.geometry.point.cartesian.from_json(json_data)

    Args:
        json_data (Union[list, tuple, dict]): json data
    Returns:
        CartesianPoint: loaded point
    Raises:
        KeyError: attributes not found
    """

    pos = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        pos = [float(json_data[0]), float(json_data[1])]
    elif isinstance(json_data, dict):
        pos = [float(json_data["x"]), float(json_data["y"])]
    else:
        raise KeyError
    return CartesianPoint(pos)



