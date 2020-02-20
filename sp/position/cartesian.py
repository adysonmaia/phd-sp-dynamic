from . import Position
from scipy.spatial import distance
import numpy as np


class CartesianPosition(Position):
    X_INDEX = 0
    Y_INDEX = 1
    Z_INDEX = 2

    def __init__(self, values=[]):
        Position.__init__(self)
        self._values = None
        if len(values) > 0:
            self.values = values
        else:
            self.values = [0.0, 0.0]

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

    @x.setter
    def y(self, v):
        self._values[self.Y_INDEX] = v

    @property
    def z(self):
        return self._values[self.Z_INDEX]

    @z.setter
    def z(self, v):
        self._values[self.Z_INDEX] = v

    def distance(self, other_pos):
        if not isinstance(other_pos, CartesianPosition):
            raise TypeError
        return distance.euclidean(self.values, other_pos.values)

    def intermediate(self, other_pos, fraction):
        if not isinstance(other_pos, CartesianPosition):
            raise TypeError
        inter_pos = self.values
        if fraction > 0.0:
            delta_pos = other_pos.values - self.values
            inter_pos = self.values + delta_pos * fraction
        return CartesianPosition(inter_pos)

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
    return CartesianPosition(pos)



