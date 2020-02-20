class Resource:
    CPU = "CPU"

    def __init__(self):
        self.name = ""
        self.unit = ""
        self.type = "float"
        self.precision = 4

    @property
    def id(self):
        return self.name

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    r = Resource()
    if isinstance(json_data, str):
        r.name = str(json_data).upper()
    elif isinstance(json_data, dict):
        r.name = str(json_data["name"]).upper()
        if "unit" in json_data:
            r.unit = str(json_data["unit"])
        if "type" in json_data:
            r.type = str(json_data["type"]).lower()
        if "precision" in json_data:
            r.precision = int(json_data["precision"])
    else:
        raise TypeError

    return r


