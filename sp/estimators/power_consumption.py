from . import Estimator


class LinearPowerEstimator(Estimator):
    def __init__(self, coefficients=[]):
        Estimator.__init__(self)
        self.coefficients = coefficients

    @property
    def coefficients(self):
        return self._coefficients[0], self._coefficients[1]

    @coefficients.setter
    def coefficients(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                self._coefficients = [float(value[0]), float(value[1])]
            else:
                self._coefficients = [0.0, 0.0]
        elif isinstance(value, dict):
            self._coefficients = [float(value[self.K1]), float(value[self.K2])]
        else:
            raise TypeError

    @property
    def idle_const(self):
        return self._coefficients[0]

    @property
    def max_const(self):
        return self._coefficients[1]

    def calc(self, utilization):
        return self.idle_const + (self.max_const - self.idle_const) * float(utilization)


def from_json(json_data):
    return LinearPowerEstimator(json_data)
