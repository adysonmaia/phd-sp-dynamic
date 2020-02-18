import numpy as np


def from_json(json_data):
    pos = None
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        pos = [float(json_data[0]), float(json_data[1])]
    elif isinstance(json_data, dict):
        pos = [float(json_data["x"]), float(json_data["y"])]
    else:
        raise TypeError
    return np.array(pos)
