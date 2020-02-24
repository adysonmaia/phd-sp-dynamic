from . import Point
from scipy.spatial import distance
import numpy as np


class CartesianPoint(Point):
    X_INDEX = 0
    Y_INDEX = 1
    Z_INDEX = 2

    def __init__(self, *args):
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
        return self._values

    @values.setter
    def values(self, v):
        self._values = np.array(v)

    @property
    def x(self):
        return self._values[self.X_INDEX]

    @x.setter
    def x(self, v):
        self._values[self.X_INDEX] = v

    @property
    def y(self):
        return self._values[self.Y_INDEX]

    @y.setter
    def y(self, v):
        self._values[self.Y_INDEX] = v

    @property
    def z(self):
        return self._values[self.Z_INDEX]

    @z.setter
    def z(self, v):
        if len(self._values) > 2:
            self._values[self.Z_INDEX] = v
        elif len(self._values) == 2:
            self._values.append(v)
        else:
            raise IndexError

    def distance(self, other):
        if not isinstance(other, CartesianPoint):
            raise TypeError
        return distance.euclidean(self.values, other.values)

    def intermediate(self, other, fraction):
        if not isinstance(other, CartesianPoint):
            raise TypeError
        inter_pos = self.values
        if fraction > 0.0:
            delta_pos = other.values - self.values
            inter_pos = self.values + delta_pos * fraction
        return CartesianPoint(inter_pos)

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        pos = [float(json_data[0]), float(json_data[1])]
    elif isinstance(json_data, dict):
        pos = [float(json_data["x"]), float(json_data["y"])]
    else:
        raise TypeError
    return CartesianPoint(pos)



