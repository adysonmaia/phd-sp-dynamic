from sp.core.model import Scenario
from sp.physical_system.model import SystemState
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
from sp.system_controller.metric.static import availability, cost, deadline, power
import json
import unittest


class StaticMetricTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_static_metric.json"
        system = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = SystemState()
            system.scenario = Scenario.from_json(data)

        system.time = 0
        env_ctl = EnvironmentController()
        env_ctl.start()
        system.environment = env_ctl.update(system)
        opt = CloudOptimizer()
        solution = opt.solve(system)

        cls.system = system
        cls.solution = solution

    def test_deadline(self):
        max_value = deadline.max_deadline_violation(self.system, self.solution)
        avg_value = deadline.avg_deadline_violation(self.system, self.solution)
        sat_rate = deadline.deadline_satisfaction(self.system, self.solution)

        self.assertGreater(max_value, 0.0)
        self.assertGreater(avg_value, 0.0)
        self.assertGreaterEqual(max_value, avg_value)
        self.assertGreaterEqual(sat_rate, 0.0)
        self.assertLessEqual(sat_rate, 1.0)

    def test_availability(self):
        max_unavail = availability.max_unavailability(self.system, self.solution)
        avg_unavail = availability.avg_unavailability(self.system, self.solution)

        self.assertGreater(max_unavail, 0.0)
        self.assertGreater(avg_unavail, 0.0)
        self.assertLessEqual(avg_unavail, 1.0)
        self.assertGreaterEqual(max_unavail, avg_unavail)

        min_avail = availability.min_availability(self.system, self.solution)
        avg_avail = availability.avg_availability(self.system, self.solution)

        self.assertGreater(min_avail, 0.0)
        self.assertGreater(avg_avail, 0.0)
        self.assertLessEqual(avg_avail, 1.0)
        self.assertGreaterEqual(avg_avail, min_avail)

        self.assertEqual(round(avg_avail + avg_unavail), 1.0)

    def test_cost(self):
        overall_value = cost.overall_cost(self.system, self.solution)
        avg_value = cost.avg_cost(self.system, self.solution)
        max_value = cost.max_cost(self.system, self.solution)

        self.assertGreaterEqual(overall_value, max_value)
        self.assertGreaterEqual(max_value, avg_value)
        self.assertGreater(avg_value, 0.0)

    def test_power(self):
        overall_value = power.overall_power_consumption(self.system, self.solution)
        avg_value = power.avg_power_consumption(self.system, self.solution)
        max_value = power.max_power_consumption(self.system, self.solution)

        self.assertGreaterEqual(overall_value, max_value)
        self.assertGreaterEqual(max_value, avg_value)
        self.assertGreater(avg_value, 0.0)


if __name__ == '__main__':
    unittest.main()