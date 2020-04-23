from .estimator import Estimator
import math


class PolynomialEstimator(Estimator):
    """Polynomial Function Estimator
    f(x)= a_n * x^n + a_(n−1) * x^(n−1) + ... + a_2 * x^2 + a_1 * x + a_0

    Estimator can be used as a function or calling the method :py:meth:`PolynomialEstimator.calc` directly
    E.g.

    .. code-block:: python

            # f(x) = 1*x^3 + 2*x^2 + 3*x + 4
            estimator = PolynomialEstimator([1, 2, 3, 4])
            # f(10)
            value = estimator(10)
            value = estimator.calc(10)


    Attributes:
        coefficients (list): list of coefficients
    """
    def __init__(self, coefficients=None):
        """Initialization
        Args:
            coefficients (list): list of coefficients
        """
        Estimator.__init__(self)
        self.coefficients = []
        if coefficients is not None:
            self.coefficients = coefficients

    def calc(self, x):
        """Calculate the polynomial function f(x)
        Args:
            x (float): variable
        Returns:
            float: function result
        """
        value = 0.0
        for (n, c) in enumerate(self.coefficients[::-1]):
            value += c * math.pow(x, n)
        return value


class LinearEstimator(Estimator):
    """Linear Function Estimator
    f(x) = a * x + b
    """

    K1 = "a"  # Slope constant of a linear function f(x) = ax + b
    K2 = "b"  # Intercept constant of a linear function f(x) = ax + b

    def __init__(self, coefficients=None):
        Estimator.__init__(self)
        self._coefficients = [0.0, 0.0]
        if coefficients is not None:
            self.coefficients = coefficients

    @property
    def coefficients(self):
        """Get linear coefficients a, b where f(x) = a*x + b
        Returns:
            tuple: coefficients
        """
        return self._coefficients[0], self._coefficients[1]

    @coefficients.setter
    def coefficients(self, value):
        """Set linear coefficients a, b where f(x) = a*x + b

        E.g.:

        .. code-block:: python

            # Tuple
            estimator = LinearEstimator()
            estimator.coefficients = (2, 3)  # f(x) = 2*x + 3

            # List
            estimator.coefficients = [2, 3]  # f(x) = 2*x + 3

            # Dict
            estimator.coefficients = {'a': 2, 'b': 3}  # f(x) = 2*x + 3

        Args:
            value (Union[list, tuple, dict]): coefficients
        Raises:
            KeyError: invalid coefficients
        """
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
            raise KeyError

    @property
    def slope_const(self):
        """Get the slope constant 'a' of the linear function f(x) = a*x + b
        Returns:
            float: slope constant
        """
        return self._coefficients[0]

    @property
    def intercept_const(self):
        """Get the intercept constant 'b' of the linear function f(x) = a*x + b
        Returns:
            float: intercept constant
        """
        return self._coefficients[1]

    def calc(self, x):
        """Calculate the linear function
        Args:
            x (float): value
        Returns:
            float: function result
        """
        return self._coefficients[0] * float(x) + self._coefficients[1]


class ConstEstimator(Estimator):
    """Constant Estimator
    f(x) = c, where c is a constant

    Attributes:
        const (float): constant
    """
    def __init__(self, const=0.0):
        """Initialization
        Args:
            const (float): constant
        """
        Estimator.__init__(self)
        self.const = const

    def calc(self, x):
        """Calculate the function
        Args:
            x (float): value
        Returns:
            float: constant result
        """
        return self.const
    

def from_json(json_data):
    """Create Polynomial, Linear or Constant Estimator from a json data

    The type of estimator is based on length of coefficients specified in the json data
    E.g.:

        .. code-block:: python

            # Polynomial Estimator
            json_data = [2, 3, 1] #  f(x) = 2x^2 + 3x + 1
            estimator = sp.core.estimator.polynomial.from_json(json_data)

            # Linear Estimator
            json_data = [3, 1]  # f(x) = 3x + 1
            estimator = sp.core.estimator.polynomial.from_json(json_data)

            # Constant Estimator
            json_data = [1]  # f(x) = 1
            estimator = sp.core.estimator.polynomial.from_json(json_data)

    Args:
        json_data (Union[list, tuple, dict]): loaded data from json
    Returns:
        Estimator: polynomial, linear or constant estimator
    Raises:
        KeyError: attributes not found
    """
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        if len(json_data) == 1:
            return ConstEstimator(json_data[0])
        elif len(json_data) == 2:
            return LinearEstimator(json_data)
        else:
            return PolynomialEstimator(list(json_data))
    elif isinstance(json_data, dict):
        return LinearEstimator(json_data)
    else:
        return ConstEstimator(float(json_data))
