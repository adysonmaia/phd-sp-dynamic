from sp.builders import ModelBuilder
from sp.builders.estimators.polynomial import PolyFuncFromJson
from sp.models.application import Application
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
                    estimator = PolyFuncFromJson(value).build()
                    app.set_demand(resource, estimator)

                apps.append(app)

        return apps
