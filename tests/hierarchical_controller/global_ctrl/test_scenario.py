from sp.core.model import Scenario
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalNetwork
import unittest
import json


class GlobalScenarioTestCase(unittest.TestCase):

    def test_from_real_scenario(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_scenario.json"
        scenario = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            scenario = Scenario.from_json(data)
            clusters = data['clusters']
        self.assertIsInstance(scenario, Scenario)

        global_scenario = GlobalScenario.from_real_scenario(scenario, clusters)
        self.assertIsInstance(global_scenario, GlobalScenario)
        self.assertEqual(global_scenario.real_scenario, scenario)
        self.assertIsInstance(global_scenario.network, GlobalNetwork)

        self.assertEqual(len(global_scenario.apps), 2)
        self.assertEqual(len(global_scenario.resources), 3)
        self.assertEqual(len(global_scenario.users), 6)
        self.assertEqual(len(global_scenario.network.nodes), len(clusters))


