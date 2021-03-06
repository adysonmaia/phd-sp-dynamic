from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.estimator import DefaultGeneratedLoadEstimator
from sp.physical_system.coverage.min_distance import MinDistanceCoverage
from future.utils import iteritems
import json
import unittest


class GeneratedLoadEstimatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/physical_system/fixtures/test_gen_load_estimator.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.coverage = MinDistanceCoverage()

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)

        time = 0
        self.system.time = time
        self.environment_input = EnvironmentInput.create_empty(self.system)
        self.environment_input.attached_users = self.coverage.update(self.system, self.environment_input)

    def test_calc(self):
        estimator = DefaultGeneratedLoadEstimator()

        # (app_id, node_id): load
        values = {
            (0, 0): 0.0, (0, 1): 0.0, (0, 2): 20.0,  (0, 3): 20.0,
            (1, 0): 0.0, (1, 1): 0.0, (1, 2): 200.0, (1, 3): 100.0,
            (2, 0): 0.0, (2, 1): 0.0, (2, 2): 1.0,   (2, 3): 2.0,
        }
        for ids, load in iteritems(values):
            self.assertEqual(estimator.calc(*ids, self.system, self.environment_input), load)
            self.assertEqual(estimator(*ids, self.system, self.environment_input), load)

    def test_calc_all_loads(self):
        estimator = DefaultGeneratedLoadEstimator()
        all_loads = estimator.calc_all_loads(self.system, self.environment_input)

        self.assertIsNotNone(all_loads)
        for app in self.system.apps:
            self.assertIn(app.id, all_loads)
            app_loads = all_loads[app.id]
            for node in self.system.nodes:
                self.assertIn(node.id, app_loads)

    def test_calc_node_loads(self):
        estimator = DefaultGeneratedLoadEstimator()
        node_id = 0
        node_loads = estimator.calc_node_loads(node_id, self.system, self.environment_input)

        self.assertIsNotNone(node_loads)
        for app in self.system.apps:
            self.assertIn(app.id, node_loads)

    def test_calc_app_loads(self):
        estimator = DefaultGeneratedLoadEstimator()
        app_id = 0
        app_loads = estimator.calc_app_loads(app_id, self.system, self.environment_input)

        self.assertIsNotNone(app_loads)
        for node in self.system.nodes:
            self.assertIn(node.id, app_loads)


if __name__ == '__main__':
    unittest.main()
