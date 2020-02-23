from sp.model import System, Scenario
from sp.estimator.request_load import RequestLoadEstimator, DefaultRequestLoadEstimator
from sp.coverage.min_dist import MinDistCoverage
from future.utils import iteritems
import json
import unittest


class RequestLoadEstimatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_req_load_estimator.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.coverage = MinDistCoverage(system)

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)

        time = 0
        self.system.time = time
        for user in self.system.users:
            user.update_position(time)
            self.assertIsNotNone(user.current_position)

        for node in self.system.nodes:
            self.assertIsNotNone(node.current_position)

        self.coverage.update(time)

    def test_calc(self):
        estimator = DefaultRequestLoadEstimator(self.system)

        # (app_id, node_id): load
        values = {
            (0, 0): 0.0, (0, 1): 0.0, (0, 2): 20.0,  (0, 3): 20.0,
            (1, 0): 0.0, (1, 1): 0.0, (1, 2): 200.0, (1, 3): 100.0,
            (2, 0): 0.0, (2, 1): 0.0, (2, 2): 1.0,   (2, 3): 2.0,
        }
        for ids, load in iteritems(values):
            self.assertEqual(estimator.calc(*ids), load)

    def test_calc_all_loads(self):
        estimator = DefaultRequestLoadEstimator(self.system)
        all_loads = estimator.calc_all_loads()

        self.assertIsNotNone(all_loads)
        for app in self.system.apps:
            self.assertIn(app.id, all_loads)
            app_loads = all_loads[app.id]
            for node in self.system.nodes:
                self.assertIn(node.id, app_loads)

    def test_calc_node_loads(self):
        estimator = DefaultRequestLoadEstimator(self.system)
        node_id = 0
        node_loads = estimator.calc_node_loads(node_id)

        self.assertIsNotNone(node_loads)
        for app in self.system.apps:
            self.assertIn(app.id, node_loads)

    def test_calc_app_loads(self):
        estimator = DefaultRequestLoadEstimator(self.system)
        app_id = 0
        app_loads = estimator.calc_app_loads(app_id)

        self.assertIsNotNone(app_loads)
        for node in self.system.nodes:
            self.assertIn(node.id, app_loads)


if __name__ == '__main__':
    unittest.main()
