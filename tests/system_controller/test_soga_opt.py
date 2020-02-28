from sp.core.model import Scenario, Node
from sp.physical_system.model import SystemState
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.system_controller.metric.static import deadline, availability, cost, power
from sp.system_controller.utils import opt as opt_utils
from sp.system_controller.optimizer.static.soga import SOGAOptimizer
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
import json
import unittest


class SOGAOptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_soga_opt.json"
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

    def test_solver(self):
        solver = SOGAOptimizer()
        solver.objective = deadline.max_deadline_violation
        solution = solver.solve(self.system)
        cloud_solution = CloudOptimizer().solve(self.system)

        self.assertIsInstance(solution, OptSolution)
        self.assertIsNotNone(solution.app_placement)
        self.assertIsNotNone(solution.allocated_resource)
        self.assertIsNotNone(solution.load_distribution)
        self.assertTrue(opt_utils.is_solution_valid(self.system, solution))

        for metric in self.metrics:
            value = metric(self.system, solution)
            self.assertGreater(value, 0.0)

        soga_value = deadline.max_deadline_violation(self.system, solution)
        cloud_value = deadline.max_deadline_violation(self.system, cloud_solution)
        self.assertLessEqual(soga_value, cloud_value)


if __name__ == '__main__':
    unittest.main()
