from abc import ABC, abstractmethod


class Mobility(ABC):
    @abstractmethod
    def position(self, time, tolerance=None):
        pass


def from_json(json_data):
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
