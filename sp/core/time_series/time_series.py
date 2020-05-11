from collections import OrderedDict
from collections.abc import Iterator, Iterable
from future.utils import iteritems


class TimeSeries:
    """A Time Series Collection

    In this series, each item is attached to a timestamp
    """

    def __init__(self):
        """Initialization
        """
        self._items = OrderedDict()

    def __getitem__(self, time):
        """Get value at a specific time

        Args:
            time (float): time
        Returns:
            object: value at the specified time
        Raises:
            KeyError: no value found for the specified time
        """
        return self.get_value(time)

    def __setitem__(self, time, value):
        """Set a value at a specific time

        Args:
            time (float): time
            value (object): value
        """
        self.set_value(time, value)

    def __iter__(self):
        """Returns time series's iterator.
        Each item during the iteration is a tuple (time, value)

        Returns:
            Iterator: time series's iterator
        """
        items = self.items
        if isinstance(items, Iterator):
            return items
        else:
            return iter(items)

    @property
    def items(self):
        """Get all items in the time series.
        An item is a tuple (time, value)

        Returns:
            Iterable: items as list, iterator or view
        """
        return iteritems(self._items)

    def get_value(self, time, **kwargs):
        """Get an item's value at the specified time

        Args:
            time (float): time
            **kwargs: kwargs
        Returns:
            object: item's value
        Raises:
            KeyError: no value found for the specified time
        """
        return self._items[time]

    def set_value(self, time, value):
        """Set value of an item at the specified time

        Args:
            time (float): time
            value (object): item's value
        """
        self._items[time] = value
