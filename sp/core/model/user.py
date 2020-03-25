from sp.core import mobility


class User:
    def __init__(self):
        self.id = -1
        self.app_id = -1
        self.mobility = None

    def get_position(self, time, tolerance=None):
        if self.mobility is not None:
            return self.mobility.position(time, tolerance)
        else:
            return None

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    u = User()
    u.id = int(json_data["id"])
    u.app_id = int(json_data["app_id"])
    if "pos" in json_data:
        u.mobility = mobility.from_json(json_data["pos"])

    return u


