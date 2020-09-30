from sp.core.model import Scenario, Network, Node
from sp.hierarchical_controller.global_ctrl.model import GlobalNetwork, GlobalNode
from sp.hierarchical_controller.cluster_ctrl.model import ClusterNetwork
import unittest
import json


class ClusterNetworkTestCase(unittest.TestCase):

    def test_from_real_network(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_network.json"
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
        self.assertEqual(len(global_net.nodes), len(clusters))

        for global_node in global_net.nodes:
            self.assertIsInstance(global_node, GlobalNode)
            cluster_net = ClusterNetwork.from_global_network(global_net, global_node)
            self.assertIsInstance(cluster_net, ClusterNetwork)
            self.assertEqual(cluster_net.real_network, real_net)
            self.assertEqual(len(cluster_net.links), len(real_net.links))

            self.assertGreater(len(cluster_net.internal_nodes), 0)
            self.assertEqual(len(cluster_net.internal_nodes), len(global_node.nodes))
            self.assertGreater(len(cluster_net.external_nodes), 0)
            self.assertEqual(len(cluster_net.external_nodes), len(clusters) - 1)
            self.assertEqual(len(cluster_net.internal_nodes) + len(cluster_net.external_nodes), len(cluster_net.nodes))

            for ext_node in cluster_net.external_nodes:
                self.assertIsInstance(ext_node, GlobalNode)

            cloud_node = None
            try:
                cloud_node = cluster_net.cloud_node
            except AttributeError:
                pass
            self.assertIsNotNone(cloud_node)

