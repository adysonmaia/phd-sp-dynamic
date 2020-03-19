from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.routing.shortest_path import ShortestPathRouting
from sp.physical_system.estimator import DefaultLinkDelayEstimator
import json
import unittest


class RoutingTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/physical_system/fixtures/test_routing.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertEqual(len(self.system.nodes), 11)
        self.assertEqual(len(self.system.bs_nodes), 9)
        self.assertEqual(len(self.system.users), 1)
        self.assertEqual(len(self.system.apps), 1)
        self.assertEqual(self.system.apps[0].id, 0)

        time = 0
        self.system.time = time
        self.environment = EnvironmentInput.create_empty(self.system)

    def test_shortest_path(self):
        app_id = 0
        app = self.system.get_app(app_id)
        routing = ShortestPathRouting()
        routing.static_routing = True
        routing.link_delay_estimator = DefaultLinkDelayEstimator()
        routing.update(self.system, self.environment)

        for link in self.system.links:
            l_nodes = list(link.nodes_id)
            path = routing.get_path(app.id, *l_nodes)
            dist = routing.get_path_length(app.id, *l_nodes)
            self.assertListEqual(l_nodes, path)
            self.assertEqual(dist, 1.001)

        for node in self.system.nodes:
            path = routing.get_path(app.id, node.id, node.id)
            dist = routing.get_path_length(app.id, node.id, node.id)
            self.assertListEqual(path, [])
            self.assertEqual(dist, 0.0)

        path = routing.get_path(app.id, 0, 10)
        dist = routing.get_path_length(app.id, 0, 10)
        self.assertEqual(len(path), 7)
        self.assertEqual(round(dist, 3), 6.006)


if __name__ == '__main__':
    unittest.main()
