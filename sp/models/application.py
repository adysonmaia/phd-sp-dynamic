from sp.models.resource import Resource
from sp.estimators import polynomial
from future.utils import iteritems


class Application:
    def __init__(self):
        self.id = -1
        self.type = ""
        self.deadline = 0.0
        self.work_size = 0.0
        self.data_size = 0.0
        self.request_rate = 0.0
        self.max_instances = 0
        self.availability = 0.0
        self.demand = {}

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def cpu_demand(self):
        return self.demand[Resource.CPU]

    @classmethod
    def from_json(cls, json_data):
        return from_json(json_data)


def from_json(json_data):
    app = Application()
    app.id = int(json_data["id"])
    app.type = str(json_data["type"]).upper()
    app.deadline = float(json_data["deadline"])
    app.work_size = float(json_data["work"])
    app.data_size = float(json_data["data"])
    app.request_rate = float(json_data["rate"])
    app.availability = float(json_data["avail"])
    app.max_instances = int(json_data["max_inst"])
    for resource, value in iteritems(json_data["demand"]):
        resource = str(resource).upper()
        estimator = polynomial.from_json(value)
        app.demand[resource] = estimator

    return app
