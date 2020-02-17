from sp.models import Topology, Node, Link
from sp.builders import ModelBuilder
from sp.estimators.polynomial import PolyFunc, LinearFunc, ConstFunc
from sp.estimators.power_consumption import LinearPowerEstimator
from future.utils import iteritems
import networkx as nx
import json


class TopologyFromFile(ModelBuilder):
    def __init__(self, filename):
        self.filename = filename

    def build(self):
        with open(self.filename) as json_file:
            t = Topology()
            g = nx.Graph()
            data = json.load(json_file)

            for item in data["nodes"]:
                node = Node()
                node.id = item["id"]
                node.type = item["type"]
                node.availability = item["avail"]
                node.power_consumption = self._build_power_estimator(item["power"])
                node.position = item["position"]
                for resource, value in iteritems(item["capacity"]):
                    node.set_capacity(resource, value)
                for resource, value in iteritems(item["cost"]):
                    node.set_cost(resource, self._build_cost_estimator(value))
                t.add_node(node)
                g.add_node(node.id)

            for item in data["links"]:
                link = Link()
                link.nodes_id = item["nodes"]
                link.bandwidth = item["bw"]
                link.propagation_delay = item["delay"]
                t.add_link(link)
                g.add_edge(*link.nodes_id)

            t.graph = g
            return t

    def _build_cost_estimator(self, value):
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

    def _build_power_estimator(self, value):
        return LinearPowerEstimator(value)
