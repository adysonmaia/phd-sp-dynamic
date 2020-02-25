from sp import mobility


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

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    u = User()
    u.id = int(json_data["id"])
    u.app_id = int(json_data["app_id"])
    if "pos" in json_data:
        u.mobility = mobility.from_json(json_data["pos"])
    if "node_id" in json_data:
        u.node_id = int(json_data["node_id"])

    return u


