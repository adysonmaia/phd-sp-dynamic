from sp.core.model import Network, Node, Link
from sp.core.estimator.polynomial import LinearEstimator
from sp.core.estimator.power import LinearPowerEstimator
import json
import math
import unittest


class NetworkFromFileTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/core/fixtures/test_network_from_file.json"
        network = None
        with open(filename) as json_file:
            data = json.load(json_file)
            network = Network.from_json(data)
        cls.network = network

    def setUp(self):
        self.assertIsNotNone(self.network)
        self.assertIsInstance(self.network, Network)

    def test_nodes_exists(self):
        self.assertEqual(len(self.network.nodes), 4)
        self.assertIsInstance(self.network.nodes[0], Node)
        self.assertEqual(len(self.network.get_nodes_by_type("CLOUD")), 1)
        self.assertEqual(len(self.network.get_nodes_by_type("CORE")), 1)
        self.assertEqual(len(self.network.get_nodes_by_type("BS")), 2)

    def test_cloud_node(self):
        self.assertIsNotNone(self.network.cloud_node)
        node = self.network.cloud_node

        self.assertEqual(node.id, 0)
        self.assertEqual(node.type, "CLOUD")
        self.assertEqual(node.availability, 0.999)
        self.assertEqual(node.position[0], 0.0)
        self.assertEqual(node.position[1], 0.0)
        self.assertIsInstance(node.power_consumption, LinearPowerEstimator)
        self.assertEqual(node.power_consumption.coefficients, (200.0, 400.0))

        for resource in ["CPU", "RAM", "DISK"]:
            self.assertEqual(node.capacity[resource], math.inf)
            self.assertIsInstance(node.cost[resource], LinearEstimator)
            self.assertEqual(node.cost[resource].coefficients, (0.025, 0.025))

    def test_core_node(self):
        nodes = self.network.get_nodes_by_type("CORE")
        self.assertEqual(len(nodes), 1)
        node = nodes[0]

        self.assertEqual(node.id, 1)
        self.assertEqual(node.type, "CORE")
        self.assertEqual(node.availability, 0.99)
        self.assertEqual(node.position[0], 0.0)
        self.assertEqual(node.position[1], 10.0)
        self.assertIsInstance(node.power_consumption, LinearPowerEstimator)
        self.assertEqual(node.power_consumption.coefficients, (50.0, 100.0))

        self.assertEqual(node.capacity["CPU"], 200.0)
        self.assertEqual(node.capacity["RAM"], 8000.0)
        self.assertEqual(node.capacity["DISK"], 32000.0)

        for resource in ["CPU", "RAM", "DISK"]:
            self.assertIsInstance(node.cost[resource], LinearEstimator)
            self.assertEqual(node.cost[resource].coefficients, (0.05, 0.05))

    def test_bs_nodes(self):
        nodes = self.network.bs_nodes
        self.assertEqual(len(nodes), 2)

        for node in nodes:
            self.assertIn(node.id, [2, 3])
            self.assertEqual(node.type, "BS")
            self.assertEqual(node.availability, 0.9)
            self.assertIn(node.position[0], [0.0, 1.0])
            self.assertIn(node.position[1], [11.0, 10.0])
            self.assertIsInstance(node.power_consumption, LinearPowerEstimator)
            self.assertEqual(node.power_consumption.coefficients, (20.0, 50.0))

            self.assertEqual(node.capacity["CPU"], 40.0)
            self.assertEqual(node.capacity["RAM"], 4000.0)
            self.assertEqual(node.capacity["DISK"], 16000.0)

            for resource in ["CPU", "RAM", "DISK"]:
                self.assertIsInstance(node.cost[resource], LinearEstimator)
                self.assertEqual(node.cost[resource].coefficients, (0.1, 0.1))

    def test_links_exists(self):
        self.assertEqual(len(self.network.links), 4)
        self.assertIsInstance(self.network.links[0], Link)

        self.assertIsNotNone(self.network.get_link(0, 1))
        self.assertIsNotNone(self.network.get_link(1, 0))

        self.assertIsNotNone(self.network.get_link(1, 2))
        self.assertIsNotNone(self.network.get_link(1, 3))
        self.assertIsNotNone(self.network.get_link(2, 3))

    def test_links_properties(self):
        link = self.network.get_link(0, 1)
        self.assertEqual(link.bandwidth, 20000000000.0)
        self.assertEqual(link.propagation_delay, 10.0)

        link = self.network.get_link(1, 2)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.0)

        link = self.network.get_link(1, 3)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.0)

        link = self.network.get_link(2, 3)
        self.assertEqual(link.bandwidth, 10000000000.0)
        self.assertEqual(link.propagation_delay, 1.4)


if __name__ == '__main__':
    unittest.main()
