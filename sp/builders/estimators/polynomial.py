from sp.builders import ModelBuilder
from sp.estimators.polynomial import PolyFunc, LinearFunc, ConstFunc


class PolyFuncFromJson(ModelBuilder):
    def __init__(self, json_data):
        self.data = json_data

    def build(self):
        if isinstance(self.data, list) or isinstance(self.data, tuple):
            if len(self.data) == 1:
                return ConstFunc(self.data[0])
            elif len(self.data) == 2:
                return LinearFunc(self.data)
            else:
                return PolyFunc(list(self.data))
        elif isinstance(self.data, dict):
            return LinearFunc(self.data)
        else:
            return ConstFunc(float(self.data))