from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.coverage.circle import CircleCoverage
from sp.physical_system.coverage.min_distance import MinDistanceCoverage
import json
import unittest


class CoverageTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/physical_system/fixtures/test_coverage.json"
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
        self.environment_input = EnvironmentInput.create_empty(self.system)

    def test_circle_coverage(self):
        radius = 1000
        cov = CircleCoverage(radius=radius)
        self.assertEqual(cov.radius, radius)

        attached_users = cov.update(self.system, self.environment_input)
        self.environment_input.attached_users = attached_users
        count = {None: 0}
        for node in self.system.nodes:
            count[node.id] = 0
        for user in attached_users.values():
            count[user.node_id] += 1

        self.assertEqual(count[None], 3)
        self.assertEqual(count[0], 0)  # Cloud node
        self.assertEqual(count[1], 0)  # Core node
        self.assertEqual(count[2], 2)  # 1st BS node
        self.assertEqual(count[3], 5)  # 2nd BS node
        for node in self.system.nodes:
            self.assertEqual(self.environment_input.get_nb_users(node_id=node.id), count[node.id])

        count = {-1: 0}
        for app in self.system.apps:
            count[app.id] = 0
        for user in self.system.users:
            count[user.app_id] += 1
        for app in self.system.apps:
            self.assertEqual(self.environment_input.get_nb_users(app_id=app.id), count[app.id])

    def test_min_dist_coverage(self):
        cov = MinDistanceCoverage()

        attached_users = cov.update(self.system, self.environment_input)
        self.environment_input.attached_users = attached_users
        count = {None: 0}
        for node in self.system.nodes:
            count[node.id] = 0
        for user in attached_users.values():
            count[user.node_id] += 1
        count = dict(count)

        self.assertEqual(count[None], 0)
        self.assertEqual(count[0], 0)  # Cloud node
        self.assertEqual(count[1], 0)  # Core node
        self.assertEqual(count[2], 4)  # 1st BS node
        self.assertEqual(count[3], 6)  # 2nd BS node
        for node in self.system.nodes:
            self.assertEqual(self.environment_input.get_nb_users(node_id=node.id), count[node.id])

        count = {-1: 0}
        for app in self.system.apps:
            count[app.id] = 0
        for user in self.system.users:
            count[user.app_id] += 1
        for app in self.system.apps:
            self.assertEqual(self.environment_input.get_nb_users(app_id=app.id), count[app.id])


if __name__ == '__main__':
    unittest.main()
