from sp.core.model import Scenario, Node, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller import utils
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
import json
import copy
import unittest


class OptUtilTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_utils.json"
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
        self.assertEqual(len(self.system.apps), 1)
        self.assertIsInstance(self.system.cloud_node, Node)

        time = 0
        self.system.time = time
        self.env_ctl.start()
        self.environment_input = self.env_ctl.update(self.system)
        self.assertIsInstance(self.environment_input, EnvironmentInput)

    def test_feasibility_check(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system, self.environment_input)

        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))

        solution = OptSolution.create_empty(self.system)
        self.assertFalse(utils.is_solution_valid(self.system, solution, self.environment_input))

    def test_delay_calc(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system, self.environment_input)

        for app in self.system.apps:
            for dst_node in self.system.nodes:
                proc_delay = utils.calc_processing_delay(app.id, dst_node.id,
                                                         self.system, solution, self.environment_input)

                if solution.get_app_placement(app.id, dst_node.id):
                    self.assertGreater(proc_delay, 0.0)
                    self.assertNotEqual(proc_delay, float("inf"))
                else:
                    self.assertEqual(proc_delay, float("inf"))

                for src_node in self.system.nodes:
                    net_delay = utils.calc_network_delay(app.id, src_node.id, dst_node.id,
                                                         self.system, solution, self.environment_input)
                    if src_node == dst_node:
                        self.assertEqual(net_delay, 0.0)
                    else:
                        self.assertGreater(net_delay, 0.0)

                    rt = utils.calc_response_time(app.id, src_node.id, dst_node.id,
                                                  self.system, solution, self.environment_input)
                    self.assertEqual(rt, proc_delay + net_delay)

    def test_alloc_resource(self):
        solution = OptSolution.create_empty(self.system)
        cloud_node = self.system.cloud_node

        for app in self.system.apps:
            solution.app_placement[app.id][cloud_node.id] = True
            for src_node in self.system.nodes:
                solution.load_distribution[app.id][src_node.id][cloud_node.id] = 1.0

        self.assertFalse(utils.is_solution_valid(self.system, solution, self.environment_input))
        solution = utils.alloc_demanded_resources(self.system, solution, self.environment_input)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))

    def test_make_mic_feasible(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system, self.environment_input)
        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))

        app = self.system.apps[0]
        selected_node = self.system.bs_nodes[0]

        self.assertEqual(app.max_instances, 1)
        self.assertTrue(solution.app_placement[app.id][self.system.cloud_node.id])
        solution.app_placement[app.id][selected_node.id] = True

        self.assertFalse(utils.is_solution_valid(self.system, solution, self.environment_input))
        solution = utils.make_solution_feasible(self.system, solution, self.environment_input)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))

    def test_make_ldc_feasible(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system, self.environment_input)
        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))

        app = self.system.apps[0]
        selected_node = None
        for node in self.system.bs_nodes:
            if self.environment_input.get_generated_load(app.id, node.id) == 0.0:
                selected_node = node
                break
        self.assertIsNotNone(selected_node)

        for node in self.system.nodes:
            solution.load_distribution[app.id][node.id][selected_node.id] = 0.0
            solution.load_distribution[app.id][selected_node.id][node.id] = 0.0

        self.assertFalse(utils.is_solution_valid(self.system, solution, self.environment_input))
        solution = utils.make_solution_feasible(self.system, solution, self.environment_input)
        self.assertTrue(utils.is_solution_valid(self.system, solution, self.environment_input))


if __name__ == '__main__':
    unittest.main()
