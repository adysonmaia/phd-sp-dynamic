from sp.core.model import Scenario, System
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.dynamic.llc import LLCOptimizer
from sp.system_controller.model import OptSolution
from sp.system_controller.utils import is_solution_valid
from sp.system_controller.metric.static import deadline, cost, availability
from sp.system_controller.metric.dynamic import migration
import json
import copy
import unittest


class LLCOptTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_llc_opt.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
        cls.system = system
        cls.environment_controller = EnvironmentController()
        cls.system_estimator = DefaultSystemEstimator()

    def test_solver(self):
        solver = LLCOptimizer()
        solver.prediction_window = 4
        solver.max_iterations = 3
        solver.objective = [
            deadline.max_deadline_violation,
            cost.overall_cost,
            availability.avg_unavailability,
            migration.overall_migration_cost
        ]

        time_start = 0
        # time_end = 50
        time_end = 5

        system = copy.copy(self.system)
        self.environment_controller.start()
        for time in range(time_start, time_end + 1):
            system.time = time
            system.sampling_time = 1
            env_input = self.environment_controller.update(system)

            control_input = solver.solve(system, env_input)
            self.assertIsInstance(control_input, OptSolution)
            self.assertTrue(is_solution_valid(system, control_input, env_input))

            result = {"time": time, "prediction_window": solver.prediction_window}
            for func in solver.objective:
                value = func(system, control_input, env_input)
                result[func.__name__] = value
            print(result)

            system = self.system_estimator(system, control_input, env_input)


if __name__ == '__main__':
    unittest.main()
