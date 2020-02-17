from sp.builders import ModelBuilder
from sp.models.application import Application
from sp.estimators.polynomial import PolyFunc, LinearFunc, ConstFunc
from future.utils import iteritems
import json


class ApplicationsFromFile(ModelBuilder):
    def __init__(self, filename):
        self.filename = filename

    def build(self):
        with open(self.filename) as json_file:
            apps = []

            data = json.load(json_file)
            for item in data["apps"]:
                app = Application()
                app.id = item["id"]
                app.type = item["type"]
                app.deadline = item["deadline"]
                app.work_size = item["work"]
                app.data_size = item["data"]
                app.request_rate = item["rate"]
                app.availability = item["avail"]
                app.max_instances = item["max_inst"]
                for resource, value in iteritems(item["demand"]):
                    app.set_demand(resource, self._build_estimator(value))

                apps.append(app)

        return apps

    def _build_estimator(self, value):
        if isinstance(value, list) or isinstance(value, tuple):
            if len(value) == 1:
                return ConstFunc(value[0])
            elif len(value) == 2:
                return LinearFunc(value)
            else:
                return PolyFunc(list(value))
        elif isinstance(value, dict):
            return LinearFunc(value)
        else:
            return ConstFunc(float(value))
