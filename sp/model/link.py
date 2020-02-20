class Link:
    def __init__(self):
        self.nodes_id = (-1, -1)
        self.bandwidth = 0.0
        self.propagation_delay = 0.0

    def __eq__(self, other):
        ids_1 = self.nodes_id
        ids_2 = other.nodes_id
        ids_3 = ids_2[::-1]
        return (ids_1 == ids_2) or (ids_1 == ids_3)

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def _nodes_from_json(json_data):
    if isinstance(json_data, list) or isinstance(json_data, tuple):
        return int(json_data[0]), int(json_data[1])
    elif isinstance(json_data, dict):
        return int(json_data["s"]), int(json_data["d"])
    else:
        raise TypeError


def from_json(json_data):
    link = Link()
    link.nodes_id = _nodes_from_json(json_data["nodes"])
    link.bandwidth = float(json_data["bw"])
    link.propagation_delay = float(json_data["delay"])
    return link
