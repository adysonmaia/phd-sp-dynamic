from sp.core.model import Scenario
from sp.physical_system.model import SystemState, EnvironmentInput
from sp.physical_system.estimator import DefaultRequestLoadEstimator
from sp.physical_system.coverage.min_distance import MinDistanceCoverage
from future.utils import iteritems
import json
import unittest


class RequestLoadEstimatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/physical_system/fixtures/test_req_load_estimator.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = SystemState()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.coverage = MinDistanceCoverage()

    def setUp(self):
        self.assertIsInstance(self.system, SystemState)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)

        time = 0
        self.system.time = time
        self.system.environment = EnvironmentInput.create_empty(self.system)
        self.system.environment.attached_users = self.coverage.update(self.system)

    def test_calc(self):
        estimator = DefaultRequestLoadEstimator()

        # (app_id, node_id): load
        values = {
            (0, 0): 0.0, (0, 1): 0.0, (0, 2): 20.0,  (0, 3): 20.0,
            (1, 0): 0.0, (1, 1): 0.0, (1, 2): 200.0, (1, 3): 100.0,
            (2, 0): 0.0, (2, 1): 0.0, (2, 2): 1.0,   (2, 3): 2.0,
        }
        for ids, load in iteritems(values):
            self.assertEqual(estimator.calc(self.system, *ids), load)
            self.assertEqual(estimator(self.system, *ids), load)

    def test_calc_all_loads(self):
        estimator = DefaultRequestLoadEstimator()
        all_loads = estimator.calc_all_loads(self.system)

        self.assertIsNotNone(all_loads)
        for app in self.system.apps:
            self.assertIn(app.id, all_loads)
            app_loads = all_loads[app.id]
            for node in self.system.nodes:
                self.assertIn(node.id, app_loads)

    def test_calc_node_loads(self):
        estimator = DefaultRequestLoadEstimator()
        node_id = 0
        node_loads = estimator.calc_node_loads(self.system, node_id)

        self.assertIsNotNone(node_loads)
        for app in self.system.apps:
            self.assertIn(app.id, node_loads)

    def test_calc_app_loads(self):
        estimator = DefaultRequestLoadEstimator()
        app_id = 0
        app_loads = estimator.calc_app_loads(self.system, app_id)

        self.assertIsNotNone(app_loads)
        for node in self.system.nodes:
            self.assertIn(node.id, app_loads)


if __name__ == '__main__':
    unittest.main()
