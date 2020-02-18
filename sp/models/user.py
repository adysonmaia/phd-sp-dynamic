from sp.mobilities.static import StaticMobility
from sp.mobilities.track import TrackMobility
import json


class User:
    def __init__(self):
        self.id = -1
        self.app_id = -1
        self.node_id = -1
        self.mobility = None

    @property
    def current_position(self):
        if self.mobility is not None:
            return self.mobility.current_position
        else:
            return None

    def update_position(self, time):
        if self.mobility is not None:
            return self.mobility.update_position(time)

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    u = User()
    u.id = int(json_data["id"])
    u.app_id = int(json_data["app_id"])

    if "position" in json_data:
        u.mobility = StaticMobility.from_json(json_data["position"])
    elif "positions" in json_data:
        value = json_data["positions"]
        if isinstance(value, list):
            u.mobility = TrackMobility.from_json(value)
        elif isinstance(value, str):
            with open(value) as file:
                mob_data = json.load(file)
                u.mobility = TrackMobility.from_json(mob_data)
        else:
            raise TypeError
    else:
        raise TypeError

    return u


