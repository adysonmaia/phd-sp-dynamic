from sp.core.model import Scenario, Node, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller.optimizer.cloud import CloudOptimizer
from sp.system_controller.utils import is_solution_valid
import json
import unittest


class CloudOptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_cloud_opt.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.env_ctl = EnvironmentController()

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
        self.env_ctl.init_params()
        self.environment_input = self.env_ctl.update(self.system)
        self.assertIsInstance(self.environment_input, EnvironmentInput)

    def test_solver(self):
        solver = CloudOptimizer()
        solution = solver.solve(self.system, self.environment_input)

        self.assertIsInstance(solution, OptSolution)
        self.assertIsNotNone(solution.app_placement)
        self.assertIsNotNone(solution.allocated_resource)
        self.assertIsNotNone(solution.load_distribution)
        self.assertTrue(is_solution_valid(self.system, solution, self.environment_input))

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
