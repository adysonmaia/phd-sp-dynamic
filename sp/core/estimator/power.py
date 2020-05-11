from .estimator import Estimator, abstractmethod


class PowerEstimator(Estimator):
    """CPU Power Consumption Estimator
    """

    @abstractmethod
    def calc(self, utilization):
        """Estimate cpu power consumption

        Args:
            utilization (float): cpu utilization
        Returns:
            float: power consumption
        """
        pass


class LinearPowerEstimator(PowerEstimator):
    """Linear CPU Power Consumption Estimator

    .. math::

        f(x) = idle + (max - idle) * x

    where

    * x (0 <= x <= 1) is the cpu utilization
    * idle is power consumption when 0% of cpu is been used
    * max is power consumption when 100% of cpu is been used

    Estimator can be used as a function or calling the method :py:meth:`LinearPowerEstimator.calc` directly.
    E.g.

    .. code-block:: python

            # f(x) = 2 + (3 - 2) * x
            estimator = LinearPowerEstimator([2, 3])
            # 50% CPU utilization: f(0.5)
            value = estimator(0.5)
            value = estimator.calc(0.5)
    """

    _K1 = "idle"
    _K2 = "max"

    def __init__(self, coefficients=None):
        """Initialization

        Args:
            coefficients (list): two linear coefficients
        """
        PowerEstimator.__init__(self)
        self._coefficients = [0.0, 0.0]
        if coefficients is not None:
            self.coefficients = coefficients

    @property
    def coefficients(self):
        """Get coefficients (idle, max)

        Returns:
            tuple: coefficients
        """
        return self._coefficients[0], self._coefficients[1]

    @coefficients.setter
    def coefficients(self, value):
        """Set coefficients idle, max where :math:`f(x) = idle + (max - idle) * x`

        E.g.:

        .. code-block:: python

            # Tuple
            estimator = LinearPowerEstimator()
            estimator.coefficients = (2, 3)  #  f(x) = 2 + (3 - 2) * x

            # List
            estimator.coefficients = [2, 3]  # f(x) = 2 + (3 - 2) * x

            # Dict
            estimator.coefficients = {'idle': 2, 'max': 3}  # f(x) = 2 + (3 - 2) * x

        Args:
            value (Union[list, tuple, dict]): coefficients
        Raises:
            KeyError: invalid coefficients
        """
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) > 1:
                self._coefficients = [float(value[0]), float(value[1])]
            else:
                self._coefficients = [0.0, 0.0]
        elif isinstance(value, dict):
            self._coefficients = [float(value[self._K1]), float(value[self._K2])]
        else:
            raise KeyError

    @property
    def idle_const(self):
        """Get idle coefficient

        Returns:
            float: coefficient
        """
        return self._coefficients[0]

    @property
    def max_const(self):
        """Get max coefficient

        Returns:
            float: coefficient
        """
        return self._coefficients[1]

    def calc(self, utilization):
        """Calculate cpu power consumption

        Args:
            utilization (float): cpu utilization
        Returns:
            float: power consumption
        """
        return self.idle_const + (self.max_const - self.idle_const) * float(utilization)


def from_json(json_data):
    """Create linear cpu power consumption estimator from json data

    Args:
        json_data (Union[list, tuple, dict]): loaded data from json
    Returns:
        LinearPowerEstimator
    Raises:
        KeyError: attributes not found
    """
    return LinearPowerEstimator(json_data)
