from .estimator import Estimator, abstractmethod
from sp.core.time_series import TimeSeries, InterpolatedTimeSeries


class LoadEstimator(Estimator):
    """Load Estimator
    """

    @abstractmethod
    def calc(self, time, *args, **kwargs):
        """Estimate load at a specific time
        Args:
            time (float): time
            *args: args
            **kwargs: kwargs
        Returns:
            float: estimated load
        """
        pass


class TimeSeriesLoadEstimator(LoadEstimator):
    """Load Estimator based on Time Series

    Attributes:
        series (TimeSeries): time series
    """

    def __init__(self):
        """Initialization
        """
        LoadEstimator.__init__(self)
        self.series = None

    def calc(self, time, *args, **kwargs):
        """Estimate load at a specific time
        Args:
            time (float): time
            *args: args
            **kwargs: kwargs
        Returns:
            float: estimated load
        """
        value = 0.0
        if self.series is not None:
            try:
                value = self.series.get_value(time, *args, **kwargs)
            except KeyError:
                pass
        return max(value, 0.0)


class ConstantLoadEstimator(LoadEstimator):
    """Load Estimator as constant function

    Attributes:
        load (float): constant load
    """

    def __init__(self, load=0.0):
        """Initialization
        Args:
            load (float): constant load
        """
        LoadEstimator.__init__(self)
        self.load = load

    def calc(self, *args, **kwargs):
        """Estimate load
        Args:
            *args: args
            **kwargs: kwargs
        Returns:
            float: constant load
        """
        return self.load


def from_json(json_data):
    """Create a Load Estimator from a json data

    The estimator can be a constant function or based on a time series
    For a constant function, the constant value can be passed as argument
    E.g.:

    .. code-block:: python

        # Constant Load Estimator
        json_data = 3.0
        estimator = sp.core.estimator.load.from_json(json_data)

    For the estimator based on a time series, a list of items can be passed as argument.
    Each item can be a dist, list or tuple
    E.g.:


    .. code-block:: python

        # Time Series as list of dict
        json_data = [
            {'v': 1.0, 't': 0},  # load = 1.0, time = 0
            {'v': 0.0, 't': 1},  # load = 0.0, time = 1
            {'v': 3.0, 't': 2},  # load = 3.0, time = 2
        ]
        estimator = sp.core.estimator.load.from_json(json_data)

        # Time Series as list of list
        json_data = [
            [1.0, 0],  # load = 1.0, time = 0
            [0.0, 1],  # load = 0.0, time = 1
            [3.0, 2],  # load = 3.0, time = 2
        ]
        estimator = sp.core.estimator.load.from_json(json_data)

        # Time Series as list of tuple
        json_data = [
            (1.0, 0),  # load = 1.0, time = 0
            (0.0, 1),  # load = 0.0, time = 1
            (3.0, 2),  # load = 3.0, time = 2
        ]
        estimator = sp.core.estimator.load.from_json(json_data)

    Args:
        json_data (Union[list, float]):  data loaded from a json
    Returns:
        LoadEstimator: created load estimator
    Raises:
        KeyError: attributes not found
    """

    estimator = None
    if isinstance(json_data, list):
        estimator = TimeSeriesLoadEstimator()
        estimator.series = InterpolatedTimeSeries()

        for item in json_data:
            time, load = _get_ts_item(item)
            estimator.series.set_value(time, load)
    else:
        try:
            load = float(json_data)
            estimator = ConstantLoadEstimator(load)
        except ValueError:
            pass

    if estimator is None:
        raise KeyError
    return estimator


def _get_ts_item(json_data):
    """Parse a time series's item
    Args:
        json_data (Union[list, tuple, dict]): json data
    Returns:
        tuple: tuple (time, value)
    Raises:
        KeyError: attributes not found
    """
    time = None
    load = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        load = json_data[0]
        time = json_data[1]
    elif isinstance(json_data, dict):
        time_keys = ["time", "t"]
        for key in time_keys:
            if key in json_data:
                time = json_data[key]
                break
        load_keys = ["load", "l", "value", "v"]
        for key in load_keys:
            if key in json_data:
                load = json_data[key]
                break
    if time is None or load is None:
        raise KeyError
    return time, load
