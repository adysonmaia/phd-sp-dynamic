from sp.model.scenario import Scenario
from sp.model.system import System
from sp.coverage.circle import CircleCoverage
from sp.coverage.min_dist import MinDistCoverage
import json
import unittest


class CoverageTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_coverage.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)

        time = 0
        self.system.time = time
        for user in self.system.users:
            user.update_position(time)
            self.assertIsNotNone(user.current_position)

        for node in self.system.nodes:
            self.assertIsNotNone(node.current_position)

    def test_circle_coverage(self):
        radius = 1000
        cov = CircleCoverage(self.system, radius=radius)
        self.assertIsInstance(cov.system, System)
        self.assertEqual(cov.radius, radius)

        cov.update(self.system.time)
        count = {-1: 0}
        for node in self.system.nodes:
            count[node.id] = 0
        for user in self.system.users:
            count[user.node_id] += 1
        count = dict(count)

        self.assertEqual(count[-1], 3)
        self.assertEqual(count[0], 0)  # Cloud node
        self.assertEqual(count[1], 0)  # Core node
        self.assertEqual(count[2], 2)  # 1st BS node
        self.assertEqual(count[3], 5)  # 2nd BS node

    def test_min_dist_coverage(self):
        cov = MinDistCoverage(self.system)
        self.assertIsInstance(cov.system, System)

        cov.update(self.system.time)
        count = {-1: 0}
        for node in self.system.nodes:
            count[node.id] = 0
        for user in self.system.users:
            count[user.node_id] += 1
        count = dict(count)

        self.assertEqual(count[-1], 0)
        self.assertEqual(count[0], 0)  # Cloud node
        self.assertEqual(count[1], 0)  # Core node
        self.assertEqual(count[2], 4)  # 1st BS node
        self.assertEqual(count[3], 6)  # 2nd BS node


if __name__ == '__main__':
    unittest.main()