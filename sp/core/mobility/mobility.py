from abc import ABC, abstractmethod


class Mobility(ABC):
    """Mobility Class
    """

    @abstractmethod
    def position(self, time, tolerance=None):
        """Get position at a specific time and with certain tolerance
        Args:
            time (float): time
            tolerance (object): tolerance
        Returns:
            sp.core.geometry.point.Point: position or None if position is not found
        """
        pass


def from_json(json_data):
    """Create a Mobility Pattern from a json data
    Mobility can be static or based on traces

    For the static mobility, the position should be passed as a dict
    E.g.:

    .. code-block:: python

        # Cartesian point
        json_data = {'x': 0, 'y': 0}
        static_mobility = sp.core.mobility.mobility.from_json(json_data)

        # GPS coordinate
        json_data = {'lat': 37.75134, 'lon': -122.39488}
        static_mobility = sp.core.mobility.mobility.from_json(json_data)

    For trace mobility, positions with timestamp should be passed as a list
    E.g.:

    .. code-block:: python

        # Cartesian points
        json_data = [
            {'x': 0.0, 'y': 0.0, 't': 0},  # time 0, position (x=0.0, y=0.0)
            {'x': 0.0, 'y': 0.0, 't': 1},  # time 1, position (x=0.0, y=0.0)
            {'x': 1.0, 'y': 0.0, 't': 2}  # time 2, position (x=1.0, y=0.0)
        ]
        trace_mobility = sp.core.mobility.mobility.from_json(json_data)

        # GPS coordinates
        json_data = [
            {'lat': 37.75134, 'lon': -122.39488, 't': 1213084687},
            {'lat': 37.75136, 'lon': -122.39527, 't': 1213084659},
            {'lat': 37.75199, 'lon': -122.3946, 't': 1213084540}
        ]
        trace_mobility = sp.core.mobility.mobility.from_json(json_data)

    Args:
        json_data (Union[list, dict]): data loaded from a json
    Returns:
        Mobility: loaded mobility
    Raises:
        KeyError: Attribute not found
    """

    from . import static
    from . import track
    from sp.core.util import json_util

    loader = None
    json_data = json_util.load_content(json_data)

    if isinstance(json_data, dict):
        loader = static.from_json
    elif isinstance(json_data, list) and len(json_data) > 0:
        item = json_data[0]
        if isinstance(item, list) or isinstance(item, dict):
            loader = track.from_json
        else:
            loader = static.from_json

    if loader is None:
        raise TypeError

    return loader(json_data)
