from sp.core.model import Scenario, Network, Node
from sp.hierarchical_controller.global_ctrl.model import GlobalNetwork, GlobalNode
import unittest
import json


class GlobalNetworkTestCase(unittest.TestCase):

    def test_from_real_network(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_network.json"
        scenario = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            scenario = Scenario.from_json(data)
            clusters = data['clusters']
        self.assertIsInstance(scenario, Scenario)
        self.assertIsInstance(scenario.network, Network)

        real_net = scenario.network
        global_net = GlobalNetwork.from_real_network(real_net, clusters)
        self.assertIsInstance(global_net, GlobalNetwork)

        self.assertGreater(len(global_net.nodes), 0)
        self.assertEqual(len(global_net.nodes), len(clusters))
        self.assertGreater(len(global_net.links), 0)
        self.assertIsInstance(global_net.cloud_node, GlobalNode)
        for global_node in global_net.nodes:
            self.assertIsInstance(global_node, GlobalNode)
            self.assertGreaterEqual(global_node.id, len(real_net.nodes))
            self.assertGreaterEqual(len(global_node.nodes), 1)
            self.assertTrue(global_node.is_cloud() or global_node.is_core() or global_node.is_base_station())
            self.assertIsInstance(global_node.central_node, Node)

