from sp.core.model import Scenario, System
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer import CloudOptimizer, SOHeuristicOptimizer
from sp.system_controller.metric import migration, deadline
import json
import math
import unittest


class DynamicMetricTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_dynamic_metric.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)

        optimizers = [CloudOptimizer(), SOHeuristicOptimizer()]
        sys_estimator = DefaultSystemEstimator()
        env_ctl = EnvironmentController()
        env_ctl.init_params()

        time_duration = 5
        systems = []
        control_inputs = []
        env_inputs = []
        for time in range(time_duration + 1):
            system.time = time
            system.sampling_time = 1
            env_input = env_ctl.update(system)

            opt = optimizers[time % len(optimizers)]
            control_input = opt.solve(system, env_input)

            systems.append(system)
            env_inputs.append(env_input)
            control_inputs.append(control_input)

            system = sys_estimator(system, control_input, env_input)

        cls.time_duration = time_duration
        cls.systems = systems
        cls.control_inputs = control_inputs
        cls.environment_inputs = env_inputs

    def test_migration(self):
        funcs = [migration.avg_migration_cost, migration.max_migration_cost, migration.overall_migration_cost]
        values = [[] for _ in funcs]

        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            for (func_index, func) in enumerate(funcs):
                value = func(system, control_input, env_input)
                self.assertGreaterEqual(value, 0.0)
                self.assertLess(value, math.inf)
                self.assertFalse(math.isnan(value))
                values[func_index].append(value)

        for value in values:
            sum_value = sum(value)
            self.assertGreater(sum_value, 0.0)
            self.assertLess(sum_value, math.inf)
            self.assertFalse(math.isnan(sum_value))

    def test_deadline(self):
        for time in range(self.time_duration + 1):
            system = self.systems[time]
            control_input = self.control_inputs[time]
            env_input = self.environment_inputs[time]

            max_value = deadline.max_deadline_violation(system, control_input, env_input)
            avg_value = deadline.avg_deadline_violation(system, control_input, env_input)
            sat_rate = deadline.deadline_satisfaction(system, control_input, env_input)

            self.assertGreater(max_value, 0.0)
            self.assertGreater(avg_value, 0.0)
            self.assertGreaterEqual(max_value, avg_value)
            self.assertGreaterEqual(sat_rate, 0.0)
            self.assertLessEqual(sat_rate, 1.0)
            self.assertLess(avg_value, math.inf)
            self.assertLess(max_value, math.inf)


if __name__ == '__main__':
    unittest.main()
