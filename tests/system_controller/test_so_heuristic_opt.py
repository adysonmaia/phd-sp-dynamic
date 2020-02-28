from sp.core.model import Scenario, Node
from sp.physical_system.model import SystemState
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller.utils import opt as opt_utils
from sp.system_controller.metric.static import deadline, availability, cost, power
from sp.system_controller.optimizer.static.so_heuristic import SOHeuristicOptimizer
import json
import unittest


class SOHeuristicOptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_so_heuristic_opt.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = SystemState()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.env_ctl = EnvironmentController()
        cls.metrics = [
            deadline.max_deadline_violation,
            availability.avg_availability,
            cost.overall_cost,
            power.overall_power_consumption
        ]

    def setUp(self):
        time = 0
        self.system.time = time
        self.env_ctl.start()
        self.system.environment = self.env_ctl.update(self.system)
        self.assertIsNotNone(self.system.environment)

    def test_versions(self):
        versions = ["cloud", "net_delay", "deadline", "cluster_metoids", "cluster_metoids_sc"]
        for version in versions:
            opt = SOHeuristicOptimizer(version=version)
            solution = opt.solve(self.system)

            self.assertIsInstance(solution, OptSolution)
            self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

            for metric in self.metrics:
                value = metric(self.system, solution)
                self.assertGreater(value, 0.0)

    def test_merged_versions(self):
        versions = ["cloud", "net_delay", "cluster_metoids", "deadline", "cluster_metoids_sc"]
        for i in range(len(versions)):
            for j in range(i+1, len(versions)):
                version = [versions[i], versions[j]]
                opt = SOHeuristicOptimizer(version=version)
                solution = opt.solve(self.system)

                self.assertIsInstance(solution, OptSolution)
                self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

                for metric in self.metrics:
                    value = metric(self.system, solution)
                    self.assertGreater(value, 0.0)


if __name__ == '__main__':
    unittest.main()