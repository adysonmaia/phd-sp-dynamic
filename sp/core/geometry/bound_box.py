from sp.core.geometry.point.cartesian import CartesianPoint
import copy


class BoundBox:
    """Bound Box
    """

    X_INDEX = CartesianPoint.X_INDEX
    Y_INDEX = CartesianPoint.Y_INDEX
    Z_INDEX = CartesianPoint.Z_INDEX

    def __init__(self, *args):
        """Initialization

        The bound box has two extreme points that can be passed as a list or each point as an argument

        For a 2D bound box, the extreme points can be top left point and bottom right point. E.g.:

        .. code-block:: python

            # Extreme points
            top_left = CartesianPoint(0.0, 1.0)  # x = 0.0, y = 1.0
            bottom_right = CartesianPoint(1.0, 0.0)  # x = 1.0, y = 0.0

            # From a list of points
            bbox = BoundBox([top_left, bottom_right])

            # From points as different arguments
            bbox = BoundBox(top_left, bottom_right)

        Args:
            *args: extreme points of the box
        """
        self_points = []
        self._min_values = []
        self._max_values = []

        if len(args) == 1:
            self.points = args[1]
        elif len(args) > 1:
            self.points = args

    @property
    def points(self):
        """Get extreme points of the bound box

        Returns:
            tuple: two extreme points
        """
        return self._points

    @points.setter
    def points(self, value):
        """Set extreme points

        Args:
            value (Union[list, tuple]): two extreme points
        Raises:
            TypeError: invalid parameter
        """
        value = list(value)
        if len(value) > 1:
            self._points = value[:2]
        else:
            raise TypeError

        self._set_min_max_values()

    @property
    def width(self):
        """Get bound box's width.
        That is, distance in X-axis of the extreme points

        Returns:
            float: width
        """
        return self.get_delta_value(self.X_INDEX)

    @property
    def height(self):
        """Get bound box's height.
        That is, distance in Y-axis of the extreme points

        Returns:
            float: height
        """
        return self.get_delta_value(self.Y_INDEX)

    @property
    def length(self):
        """Get bound box's length.
        That is, distance in Z-axis of the extreme points

        Returns:
            float: length
        """
        return self.get_delta_value(self.Z_INDEX)

    @property
    def x_distance(self):
        """Get distance in X-axis of the extreme points

        Returns:
            float: distance
        """
        return self.get_distance(self.X_INDEX)

    @property
    def y_distance(self):
        """Get distance in Y-axis of the extreme points

        Returns:
            float: distance
        """
        return self.get_distance(self.Y_INDEX)

    @property
    def z_distance(self):
        """Get distance in Z-axis of the extreme points

        Returns:
            float: distance
        """
        return self.get_distance(self.Z_INDEX)

    @property
    def x_min(self):
        """Get minimum value in the X-axis which is inside the bound box

        Returns:
            float: minimum value
        """
        return self.get_min_value(self.X_INDEX)

    @property
    def x_max(self):
        """Get maximum value in the X-axis which is inside the bound box

        Returns:
            float: maximum value
        """
        return self.get_max_value(self.X_INDEX)

    @property
    def y_min(self):
        """Get minimum value in the Y-axis which is inside the bound box

        Returns:
            float: minimum value
        """
        return self.get_min_value(self.Y_INDEX)

    @property
    def y_max(self):
        """Get maximum value in the Y-axis which is inside the bound box

        Returns:
            float: maximum value
        """
        return self.get_max_value(self.Y_INDEX)

    @property
    def z_min(self):
        """Get minimum value in the Z-axis which is inside the bound box

        Returns:
            float: minimum value
        """
        return self.get_min_value(self.Z_INDEX)

    @property
    def z_max(self):
        """Get maximum value in the Z-axis which is inside the bound box

        Returns:
            float: maximum value
        """
        return self.get_max_value(self.Z_INDEX)

    def _set_min_max_values(self):
        """Set minimum and maximum values for each dimension (axis) of the bound box
        """

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
        """Get distance between the extreme points in a specific dimension (axis)

        Args:
            dim (int): dimension's index
        Returns:
            float: distance
        """
        p_1, p_2 = self.points
        nb_dim = len(p_1.values)

        other_p = copy.deepcopy(self.points[0])
        for d in range(nb_dim):
            if d == dim:
                continue
            other_p[d] = p_2[d]
        return p_1.distance(other_p)

    def get_delta_value(self, dim):
        """Get difference (delta) between the maximum and minimum values in a specific dimension (axis)

        Args:
            dim (index): dimension's index
        Returns:
            float: delta
        """
        return float(self._max_values[dim] - self._min_values[dim])

    def get_min_value(self, dim):
        """Get minimum value inside the bound box for a specific dimension (axis)

        Args:
            dim (index): dimension's index
        Returns:
            float: minimum value
        """
        return self._min_values[dim]

    def get_max_value(self, dim):
        """Get maximum value inside the bound box for a specific dimension (axis)

        Args:
            dim (index): dimension's index
        Returns:
            float: maximum value
        """
        return self._max_values[dim]

