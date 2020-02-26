from . import Estimator
import math


class PolyFunc(Estimator):
    def __init__(self, coefficients=None):
        Estimator.__init__(self)
        self.coefficients = []
        if coefficients is not None:
            self.coefficients = coefficients

    def calc(self, x):
        value = 0.0
        for n, c in enumerate(self.coefficients[::-1]):
            value += c * math.pow(x, n)
        return value


class LinearFunc(Estimator):
    K1 = "a"  # Slope constant of a linear function f(x) = ax + b
    K2 = "b"  # Intercept constant of a linear function f(x) = ax + b

    def __init__(self, coefficients=None):
        Estimator.__init__(self)
        self._coefficients = [0.0, 0.0]
        if coefficients is not None:
            self.coefficients = coefficients

    @property
    def coefficients(self):
        return self._coefficients[0], self._coefficients[1]

    @coefficients.setter
    def coefficients(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                self._coefficients = [float(value[0]), float(value[1])]
            elif len(value) == 1:
                self._coefficients = [0.0, float(value[0])]
            else:
                self._coefficients = [0.0, 0.0]
        elif isinstance(value, dict):
            self._coefficients = [float(value[self.K1]), float(value[self.K2])]
        else:
            raise TypeError

    @property
    def slope_const(self):
        return self._coefficients[0]

    @property
    def intercept_const(self):
        return self._coefficients[1]

    def calc(self, x):
        return self._coefficients[0] * float(x) + self._coefficients[1]


class ConstFunc(Estimator):
    def __init__(self, const=0.0):
        Estimator.__init__(self)
        self.const = const

    def calc(self, x):
        return self.const
    

def from_json(json_data):
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        if len(json_data) == 1:
            return ConstFunc(json_data[0])
        elif len(json_data) == 2:
            return LinearFunc(json_data)
        else:
            return PolyFunc(list(json_data))
    elif isinstance(json_data, dict):
        return LinearFunc(json_data)
    else:
        return ConstFunc(float(json_data))
