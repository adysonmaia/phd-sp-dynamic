from .time_series import TimeSeries
import math


class InterpolatedTimeSeries(TimeSeries):
    """Interpolate Time Series

    It is possible to interpolate values for times not defined in the series
    """

    def get_value(self, time, time_tolerance=None, **kwargs):
        """Get item's value at the specified time

        If the specified time isn't defined in the series, the item's value is calculated based on interpolation
        of two consecutive values v1 and v2 with times t1 and t2 respectively such that (t1 <= time <= t2).
        The interpolation is calculated only if (time - t1 <= tolerance) or (t2 - time <= tolerance)

        Args:
            time (float): time
            time_tolerance (float): a time tolerance to obtain a interpolated position between two consecutive values.
                If None, the tolerance is set to infinity
            **kwargs: kwargs
        Returns:
            object: item's value
        Raises:
            KeyError: no (interpolated) value found for the specified time
        """
        time_tolerance = time_tolerance if time_tolerance is not None else math.inf
        if time in self._items:
            return self._items[time]
        elif time_tolerance > 0.0:
            return self._get_interpolated_value(time, time_tolerance)
        else:
            raise KeyError

    def _get_interpolated_value(self, time, time_tolerance):
        """Get interpolate value of an time at the specified time

        Args:
            time (float): time
            time_tolerance (float): time tolerance
        Returns:
            object: interpolated value
        Raises:
            KeyError: no interpolated value found for the specified time
        """
        time_list = list(self._items.keys())
        time_list.sort()
        series_len = len(time_list)
        value = None

        if series_len > 0:
            prev_time = None
            next_time = None
            first_time = time_list[0]
            last_time = time_list[-1]

            for i in range(series_len):
                next_i = min(i + 1, series_len - 1)
                if time_list[i] <= time <= time_list[next_i]:
                    prev_time = time_list[i]
                    next_time = time_list[next_i]
                    break

            interpolate = prev_time is not None and next_time is not None
            interpolate = interpolate and (time - prev_time <= time_tolerance or next_time - time <= time_tolerance)
            if interpolate:
                prev_value = self._items[prev_time]
                next_value = self._items[next_time]
                value = self.interpolate(prev_time, prev_value, next_time, next_value, time)
            elif time_tolerance is not None and not math.isinf(time_tolerance):
                if abs(time - first_time) <= time_tolerance:
                    value = self._items[first_time]
                elif abs(time - last_time) <= time_tolerance:
                    value = self._items[last_time]

        if value is None:
            raise KeyError

        return value

    @staticmethod
    def interpolate(time_1, value_1, time_2, value_2, time):
        """Interpolate a value between two others.
        The values should support the arithmetic operations

        Args:
            time_1 (float): time of first value
            value_1 (object): first value
            time_2 (float): time of second value
            value_2 (object): second value
            time (float): a time between the other two. It interpolates the values for this time
        Returns:
            object: interpolated value
        """
        delta_time = float(time_2 - time_1)
        value = None
        if delta_time > 0.0:
            fraction = (time - time_1) / delta_time
            value = (value_2 - value_1) * fraction + value_1
        else:
            value = value_1
        return value
