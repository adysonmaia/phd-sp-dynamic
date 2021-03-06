from .mobility import Mobility
from sp.core.geometry import point


class StaticMobility(Mobility):
    """Static Mobility
    """

    def __init__(self, position=None):
        """Initialization

        Args:
            position (point.Point): static position
        """
        Mobility.__init__(self)
        self._position = position

    def position(self, *args, **kwargs):
        """Get position

        Args:
            *args: args
            **kwargs: kwargs
        Returns:
            point.Point: static position or None if position is not found
        """
        return self._position

    @staticmethod
    def from_json(json_data):
        """Create a static mobility from a json data

        See :py:func:`sp.core.mobility.static.from_json`

        Args:
            json_data (dict): data loaded from a json
        Returns:
            StaticMobility: loaded mobility
        """
        return from_json(json_data)


def from_json(json_data):
    """Create a static mobility from a json data

    See :py:func:`sp.core.geometry.point.point.from_json`

    Args:
        json_data (dict): data loaded from a json
    Returns:
        StaticMobility: loaded mobility
    Raises:
        KeyError: attribute not found
    """
    pos = point.from_json(json_data)
    return StaticMobility(pos)
