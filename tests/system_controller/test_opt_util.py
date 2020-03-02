from sp.core.model import Scenario, Node
from sp.physical_system.model import SystemState
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller.utils import opt as opt_utils
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
import json
import unittest


class OptUtilTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_opt_util.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = SystemState()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.env_ctl = EnvironmentController()

    def setUp(self):
        self.assertIsInstance(self.system, SystemState)
        self.assertIsInstance(self.env_ctl, EnvironmentController)
        self.assertEqual(len(self.system.nodes), 4)
        self.assertEqual(len(self.system.bs_nodes), 2)
        self.assertEqual(len(self.system.users), 10)
        self.assertEqual(len(self.system.apps), 1)
        self.assertIsInstance(self.system.cloud_node, Node)

        time = 0
        self.system.time = time
        self.env_ctl.start()
        self.system.environment = self.env_ctl.update(self.system)
        self.assertIsNotNone(self.system.environment)

    def test_feasibility_check(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system)

        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

        solution = OptSolution.create_empty(self.system)
        self.assertFalse(opt_utils.is_solution_valid(self.system, solution))

    def test_delay_calc(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system)

        for app in self.system.apps:
            for dst_node in self.system.nodes:
                proc_delay = opt_utils.calc_processing_delay(app, dst_node, self.system, solution)

                if solution.get_app_placement(app.id, dst_node.id):
                    self.assertGreater(proc_delay, 0.0)
                    self.assertNotEqual(proc_delay, float("inf"))
                else:
                    self.assertEqual(proc_delay, float("inf"))

                for src_node in self.system.nodes:
                    net_delay = opt_utils.calc_network_delay(app, src_node, dst_node, self.system, solution)
                    if src_node == dst_node:
                        self.assertEqual(net_delay, 0.0)
                    else:
                        self.assertGreater(net_delay, 0.0)

                    rt = opt_utils.calc_response_time(app, src_node, dst_node, self.system, solution)
                    self.assertEqual(rt, proc_delay + net_delay)

    def test_alloc_resource(self):
        solution = OptSolution.create_empty(self.system)
        cloud_node = self.system.cloud_node

        for app in self.system.apps:
            solution.app_placement[app.id][cloud_node.id] = True
            for src_node in self.system.nodes:
                solution.load_distribution[app.id][src_node.id][cloud_node.id] = 1.0

        self.assertFalse(opt_utils.is_solution_valid(self.system, solution))
        solution = opt_utils.alloc_demanded_resources(self.system, solution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

    def test_make_mic_feasible(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system)
        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

        app = self.system.apps[0]
        selected_node = self.system.bs_nodes[0]

        self.assertEqual(app.max_instances, 1)
        self.assertTrue(solution.app_placement[app.id][self.system.cloud_node.id])
        solution.app_placement[app.id][selected_node.id] = True

        self.assertFalse(opt_utils.is_solution_valid(self.system, solution))
        solution = opt_utils.make_solution_feasible(self.system, solution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

    def test_make_ldc_feasible(self):
        opt = CloudOptimizer()
        solution = opt.solve(self.system)
        self.assertIsInstance(solution, OptSolution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

        app = self.system.apps[0]
        selected_node = None
        for node in self.system.bs_nodes:
            if self.system.get_generated_load(app.id, node.id) == 0.0:
                selected_node = node
                break
        self.assertIsNotNone(selected_node)

        for node in self.system.nodes:
            solution.load_distribution[app.id][node.id][selected_node.id] = 0.0
            solution.load_distribution[app.id][selected_node.id][node.id] = 0.0

        self.assertFalse(opt_utils.is_solution_valid(self.system, solution))
        solution = opt_utils.make_solution_feasible(self.system, solution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))


if __name__ == '__main__':
    unittest.main()
