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

    def test_req_load(self):
        estimator = DefaultRequestLoadEstimator(self.system)

        # (app_id, node_id): load
        values = {
            (0, 0): 0.0, (0, 1): 0.0, (0, 2): 20.0,  (0, 3): 20.0,
            (1, 0): 0.0, (1, 1): 0.0, (1, 2): 200.0, (1, 3): 100.0,
            (2, 0): 0.0, (2, 1): 0.0, (2, 2): 1.0,   (2, 3): 2.0,
        }
        for ids, load in iteritems(values):
            self.assertEqual(estimator.calc(*ids), load)


if __name__ == '__main__':
    unittest.main()
