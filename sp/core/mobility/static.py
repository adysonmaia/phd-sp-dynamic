from .mobility import Mobility
from sp.core.geometry import point


class StaticMobility(Mobility):
    def __init__(self, pos=None):
        Mobility.__init__(self)
        self._position = pos

    def position(self, time, tolerance=None):
        return self._position

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = point.from_json(json_data)
    return StaticMobility(pos)
