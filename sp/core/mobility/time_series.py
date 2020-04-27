from sp.core.time_series import InterpolatedTimeSeries
from sp.core.geometry import point
from .mobility import Mobility
import copy


class TimeSeriesMobility(InterpolatedTimeSeries, Mobility):
    """Time Series Mobility
    It stores a time series of positions
    """
    def position(self, time, time_tolerance=None, **kwargs):
        """Get position at a specific time and with certain time tolerance

        If the specified time isn't stored in the series, a position is calculated based on the interpolation
        of two consecutive values v1 and v2 with times t1 and t2 respectively such that (t1 <= time <= t2).
        The interpolation is calculated only if (time - t1 <= tolerance) or (t2 - time <= tolerance)

        Args:
            time (float): time
            time_tolerance (float): a time tolerance to obtain a interpolated position between two consecutive values.
                If None, the tolerance is set to infinity
            **kwargs: kwargs
        Returns:
            point.Point: position or None if position is not found
        """
        try:
            return self.get_value(time, time_tolerance=time_tolerance)
        except KeyError:
            return None

    @staticmethod
    def interpolate(time_1, value_1, time_2, value_2, time):
        inter_value = None
        delta_time = abs(float(time_2 - time_1))
        if delta_time != 0.0:
            fraction = (time - time_1) / delta_time
            inter_value = value_1.intermediate(value_2, fraction)
        else:
            inter_value = copy.deepcopy(value_1)
        return inter_value

    @staticmethod
    def from_json(json_data):
        """Create a Time Series Mobility from a json data
        See :py:func:`sp.core.mobility.time_series.from_json`
        Args:
            json_data (list): data loaded from a json
        Returns:
            TimeSeriesMobility: loaded mobility
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a Time Series Mobility from a json data
    Args:
        json_data (list): loaded data from json
    Returns:
        TimeSeriesMobility: loaded mobility
    Raises:
        KeyError: attributes not found
    """
    ts_mobility = TimeSeriesMobility()
    for item in json_data:
        time, value = _get_item_from_json(item)
        ts_mobility.set_value(time, value)
    return ts_mobility


def _get_item_from_json(json_data):
    """Get an item (time, position) of time series from a json data
    Args:
        json_data (Union[list, dict]): loaded data from json
    Returns:
        tuple: loaded item
    Raises:
        KeyError: attributes not found
    """
    position = point.from_json(json_data)
    time = None
    if isinstance(json_data, list):
        time = int(json_data[2])
    elif isinstance(json_data, dict) and "time" in json_data:
        time = int(json_data["time"])
    elif isinstance(json_data, dict) and "t" in json_data:
        time = int(json_data["t"])
    else:
        raise KeyError

    return time, position
