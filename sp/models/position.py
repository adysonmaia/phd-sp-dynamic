def from_json(json_data):
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        return [float(json_data[0]), float(json_data[1])]
    elif isinstance(json_data, dict):
        return [float(json_data["x"]), float(json_data["y"])]
    else:
        raise TypeError
