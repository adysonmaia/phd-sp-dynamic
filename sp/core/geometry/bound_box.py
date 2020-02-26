from sp.core.geometry.point.cartesian import CartesianPoint
import copy


class BoundBox:
    X_INDEX = CartesianPoint.X_INDEX
    Y_INDEX = CartesianPoint.Y_INDEX
    Z_INDEX = CartesianPoint.Z_INDEX

    def __init__(self, *args):
        self_points = []
        self._min_values = []
        self._max_values = []

        if len(args) == 1:
            self.points = args[1]
        elif len(args) > 1:
            self.points = args

    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, value):
        value = list(value)
        if len(value) > 1:
            self._points = value[:2]
        else:
            raise TypeError

        self._set_min_max_values()

    @property
    def width(self):
        return self.get_diff_value(self.X_INDEX)

    @property
    def height(self):
        return self.get_diff_value(self.Y_INDEX)

    @property
    def length(self):
        return self.get_diff_value(self.Z_INDEX)

    @property
    def x_distance(self):
        return self.get_distance(self.X_INDEX)

    @property
    def y_distance(self):
        return self.get_distance(self.Y_INDEX)

    @property
    def z_distance(self):
        return self.get_distance(self.Z_INDEX)

    @property
    def x_min(self):
        return self.get_min_value(self.X_INDEX)

    @property
    def x_max(self):
        return self.get_max_value(self.X_INDEX)

    @property
    def y_min(self):
        return self.get_min_value(self.Y_INDEX)

    @property
    def y_max(self):
        return self.get_max_value(self.Y_INDEX)

    @property
    def z_min(self):
        return self.get_min_value(self.Z_INDEX)

    @property
    def z_max(self):
        return self.get_max_value(self.Z_INDEX)

    def _set_min_max_values(self):
        p_1, p_2 = self.points[0], self.points[1]
        nb_dim = len(p_1.values)
        self._min_values = []
        self._max_values = []
        for d in range(nb_dim):
            d_min = min(p_1[d], p_2[d])
            d_max = max(p_2[d], p_2[d])
            self._min_values.append(d_min)
            self._max_values.append(d_max)

    def get_distance(self, dim):
        p_1, p_2 = self.points
        nb_dim = len(p_1.values)

        other_p = copy.deepcopy(self.points[0])
        for d in range(nb_dim):
            if d == dim:
                continue
            other_p[d] = p_2[d]
        return p_1.distance(other_p)

    def get_diff_value(self, dim):
        return float(self._max_values[dim] - self._min_values[dim])

    def get_min_value(self, dim):
        return self._min_values[dim]

    def get_max_value(self, dim):
        return self._max_values[dim]

