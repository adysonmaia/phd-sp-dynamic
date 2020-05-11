from .time_series import TimeSeries


class ConstantTimeSeries(TimeSeries):
    """Constant Time Series
    """

    def __init__(self, value=None):
        """Initialization

        Args:
            value (object): constant value
        """
        TimeSeries.__init__(self)
        self._value = value

    @property
    def items(self):
        """Get time series's items

        Returns:
            list: list of a single element as a tuple (None, constant value)
        """
        return [(None, self._value)]

    def get_value(self, *args, **kwargs):
        """Get constant value

        Args:
            *args: args
            **kwargs: kwargs
        Returns:
            object: constant value
        """
        return self._value

    def set_value(self, time=None, value=None):
        """Set constant value

        Args:
            time (float): time
            value (object): constant value
        """
        self._value = value
