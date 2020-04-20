from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller.metric import deadline, availability, power, cost
from sp.system_controller.util import is_solution_valid
from sp.system_controller.optimizer.soga import SOGAOptimizer
from sp.system_controller.optimizer.cloud import CloudOptimizer
import json
import math
import unittest


class SOGAOptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_soga_opt.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
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
        self.env_ctl.init_params()
        self.environment_input = self.env_ctl.update(self.system)
        self.assertIsInstance(self.environment_input, EnvironmentInput)

    def test_solver(self):
        solver = SOGAOptimizer()
        solver.objective = deadline.max_deadline_violation
        solution = solver.solve(self.system, self.environment_input)
        cloud_solution = CloudOptimizer().solve(self.system, self.environment_input)

        self.assertIsInstance(solution, OptSolution)
        self.assertIsNotNone(solution.app_placement)
        self.assertIsNotNone(solution.allocated_resource)
        self.assertIsNotNone(solution.load_distribution)
        self.assertTrue(is_solution_valid(self.system, solution, self.environment_input))

        for metric in self.metrics:
            value = metric(self.system, solution, self.environment_input)
            self.assertGreater(value, 0.0)
            self.assertLess(value, math.inf)
            self.assertFalse(math.isnan(value))

        soga_value = deadline.max_deadline_violation(self.system, solution, self.environment_input)
        cloud_value = deadline.max_deadline_violation(self.system, cloud_solution, self.environment_input)
        self.assertLessEqual(soga_value, cloud_value)


if __name__ == '__main__':
    unittest.main()
