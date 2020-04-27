from sp.core.model import Scenario, Application, Network, Node, Link, User, Resource
from sp.core.estimator.load import LoadEstimator, TimeSeriesLoadEstimator
import json
import unittest


class ScenarioFromFileCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/core/fixtures/test_scenario_from_file.json"
        scenario = None
        with open(filename) as json_file:
            data = json.load(json_file)
            scenario = Scenario.from_json(data)
        cls.scenario = scenario

    def setUp(self):
        self.assertIsInstance(self.scenario, Scenario)

    def test_properties(self):
        self.assertGreater(len(self.scenario.apps), 0)
        self.assertIsInstance(self.scenario.apps[0], Application)

        self.assertGreater(len(self.scenario.users), 0)
        self.assertIsInstance(self.scenario.users[0], User)

        self.assertGreater(len(self.scenario.resources), 0)
        self.assertIsInstance(self.scenario.resources[0], Resource)

        self.assertIsInstance(self.scenario.network, Network)
        self.assertGreater(len(self.scenario.network.nodes), 0)
        self.assertIsInstance(self.scenario.network.nodes[0], Node)

        self.assertGreater(len(self.scenario.network.links), 0)
        self.assertIsInstance(self.scenario.network.links[0], Link)

        has_ts_load_estimator = False
        for app in self.scenario.apps:
            for node in self.scenario.network.nodes:
                estimator = self.scenario.get_load_estimator(app.id, node.id)
                self.assertIsInstance(estimator, LoadEstimator)
                if isinstance(estimator, TimeSeriesLoadEstimator):
                    has_ts_load_estimator = True
        self.assertTrue(has_ts_load_estimator)
