from . import Mobility
from sp import position


class StaticMobility(Mobility):
    def __init__(self, pos=None):
        Mobility.__init__(self)
        self.position = pos

    @property
    def current_position(self):
        return self.position

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = position.from_json(json_data)
    return StaticMobility(pos)