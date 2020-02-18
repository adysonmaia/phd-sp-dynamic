from . import Mobility
from sp.models import position


class StaticMobility(Mobility):
    def __init__(self, position=None):
        Mobility.__init__(self)
        self.position = position

    @property
    def current_position(self):
        return self.position

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    pos = position.from_json(json_data)
    return StaticMobility(pos)
