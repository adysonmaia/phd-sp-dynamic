from abc import ABC, abstractmethod


class Mobility:
    def __init__(self):
        pass

    @property
    @abstractmethod
    def current_position(self):
        return None

    @abstractmethod
    def update_position(self, time):
        pass


def from_json(json_data):
    from . import static
    from . import track
    from sp.utils import json_util

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
