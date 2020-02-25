from . import Mobility
from sp.geometry import point


class StaticMobility(Mobility):
    def __init__(self, pos=None):
        Mobility.__init__(self)
        self.position = pos

    @property
    def current_position(self):
        return self.position

    def update_position(self, time):
        pass

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = point.from_json(json_data)
    return StaticMobility(pos)
