from sp.core.model import Scenario
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNode
from sp.hierarchical_controller.cluster_ctrl.model import ClusterScenario, ClusterNetwork
import unittest
import json


class ClusterScenarioTestCase(unittest.TestCase):

    def test_from_global_scenario(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_scenario.json"
        scenario = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            scenario = Scenario.from_json(data)
            clusters = data['clusters']
        self.assertIsInstance(scenario, Scenario)

        global_scenario = GlobalScenario.from_real_scenario(scenario, clusters)
        self.assertIsInstance(global_scenario, GlobalScenario)
        self.assertEqual(len(global_scenario.network.nodes), len(clusters))

        for global_node in global_scenario.network.nodes:
            self.assertIsInstance(global_node, GlobalNode)
            cluster_scenario = ClusterScenario.from_global_scenario(global_scenario, global_node)
            self.assertIsInstance(cluster_scenario, ClusterScenario)
            self.assertEqual(cluster_scenario.id, global_node.id)
            self.assertEqual(len(cluster_scenario.apps), len(global_scenario.apps))
            self.assertEqual(len(cluster_scenario.resources), len(global_scenario.resources))
            self.assertEqual(cluster_scenario.real_scenario, scenario)
            self.assertIsInstance(cluster_scenario.network, ClusterNetwork)
            self.assertEqual(len(cluster_scenario.network.internal_nodes), len(global_node.nodes))

