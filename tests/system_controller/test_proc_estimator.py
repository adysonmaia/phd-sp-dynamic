from sp.core.model import Scenario, Node, System, ControlInput, EnvironmentInput
from sp.system_controller.estimator.processing import DefaultProcessingEstimator
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.static.cloud import CloudOptimizer
import json
import math
import unittest


class ProcEstimatorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_proc_estimator.json"
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
        self.assertGreater(len(self.system.nodes), 0)
        self.assertGreater(len(self.system.bs_nodes), 0)
        self.assertGreater(len(self.system.users), 0)
        self.assertGreater(len(self.system.apps), 0)
        self.assertIsInstance(self.system.cloud_node, Node)

        time = 0
        self.system.time = time
        self.env_ctl.init_params()
        self.environment_input = self.env_ctl.update(self.system)
        self.assertIsInstance(self.environment_input, EnvironmentInput)

        solver = CloudOptimizer()
        self.control_input = solver.solve(self.system, self.environment_input)
        self.assertIsInstance(self.control_input, ControlInput)

        self.system.environment_input = None

    def test_default_estimator(self):
        estimator = DefaultProcessingEstimator()

        for app in self.system.apps:
            for node in self.system.nodes:
                if not self.control_input.get_app_placement(app.id, node.id):
                    continue

                proc_result = estimator.calc(app.id, node.id,
                                             system=self.system,
                                             control_input=self.control_input,
                                             environment_input=self.environment_input)
                self.assertGreater(proc_result.arrival_rate, 0.0)
                self.assertGreater(proc_result.service_rate, 0.0)
                self.assertGreater(proc_result.service_rate, proc_result.arrival_rate)
                self.assertLess(proc_result.service_rate, math.inf)


if __name__ == '__main__':
    unittest.main()
