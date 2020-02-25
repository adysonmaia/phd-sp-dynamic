from sp.model import System, Scenario, Node, Allocation
from sp.controller.environment import EnvironmentController, DefaultEnvironmentController
from sp.solver.static.cloud import CloudSolver
import json
import unittest


class CloudSolverTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "./tests/fixtures/test_cloud_solver.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.env_ctl = DefaultEnvironmentController()

    def setUp(self):
        self.assertIsInstance(self.system, System)
        self.assertIsInstance(self.env_ctl, EnvironmentController)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 3)
        self.assertIsInstance(self.system.cloud_node, Node)

        time = 0
        self.system.time = time
        self.env_ctl.start(self.system)
        self.env_ctl.update(time)

    def test_solver(self):
        solver = CloudSolver()
        solution = solver.solve(self.system, self.system.time)

        self.assertIsInstance(solution, Allocation)
        self.assertIsNotNone(solution.app_placement)
        self.assertIsNotNone(solution.allocated_resource)
        self.assertIsNotNone(solution.load_distribution)

        for app in self.system.apps:
            for dst_node in self.system.nodes:
                placement = solution.get_app_placement(app.id, dst_node.id)
                self.assertEqual(placement, dst_node.is_cloud())

                for resource in self.system.resources:
                    allocated = solution.get_allocated_resource(app.id, dst_node.id, resource.id)
                    if dst_node.is_cloud():
                        self.assertGreater(allocated, 0.0)
                    else:
                        self.assertEqual(allocated, 0.0)

                for src_node in self.system.nodes:
                    ld = solution.get_load_distribution(app.id, src_node.id, dst_node.id)
                    self.assertEqual(ld, 1.0 * int(dst_node.is_cloud()))


if __name__ == '__main__':
    unittest.main()
