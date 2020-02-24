class Point:
    def __init__(self):
        pass

    def __getitem__(self, index):
        return self.values[index]

    def __setitem__(self, index, value):
        self.values[index] = value

    def __str__(self):
        return str(self.values)

    @property
    def values(self):
        return None

    @values.setter
    def values(self, v):
        pass

    def distance(self, other):
        return 0.0

    def intermediate(self, other, fraction):
        return None


def from_json(json_data, coord=None):
    from . import cartesian
    from . import gps

    loader = None
    if coord == "gps" or "lat" in json_data:
        loader = gps.from_json
    else:
        loader = cartesian.from_json

    return loader(json_data)



