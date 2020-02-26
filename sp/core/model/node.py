from sp.core.model import Resource
from sp.core.geometry import point
from sp.core.estimator import polynomial
from sp.core.estimator import power_consumption
from future.utils import iteritems
from functools import total_ordering


@total_ordering
class Node:
    BS_TYPE = "BS"
    CORE_TYPE = "CORE"
    CLOUD_TYPE = "CLOUD"

    def __init__(self):
        self.id = -1
        self.type = ""
        self.availability = 0.0
        self.capacity = {}
        self.cost = {}
        self.power_consumption = None
        self.position = None

    def __eq__(self, other):
        return self.id == other.id

    def __lt__(self, other):
        return self.id < other.id

    @property
    def cpu_capacity(self):
        return self.capacity[Resource.CPU]

    def is_base_station(self):
        return self.type == self.BS_TYPE

    def is_core(self):
        return self.type == self.CORE_TYPE

    def is_cloud(self):
        return self.type == self.CLOUD_TYPE

    @staticmethod
    def from_json(json_data):
        return from_json(json_data)


def from_json(json_data):
    node = Node()
    node.id = int(json_data["id"])
    node.type = str(json_data["type"]).upper()
    node.availability = float(json_data["avail"])
    node.power_consumption = power_consumption.from_json(json_data["power"])
    node.position = point.from_json(json_data["position"])

    for resource, value in iteritems(json_data["capacity"]):
        node.capacity[resource] = float(value)

    for resource, value in iteritems(json_data["cost"]):
        resource = str(resource).upper()
        estimator = polynomial.from_json(value)
        node.cost[resource] = estimator

    return node
