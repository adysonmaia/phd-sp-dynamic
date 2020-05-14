from sp.core.model import Scenario, Node, System, EnvironmentInput
from sp.core.predictor import ARIMAPredictor, AutoARIMAPredictor, ExpSmoothingPredictor
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.predictor.environment import DefaultEnvironmentPredictor
import json
import math
import unittest


class EnvPredictorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        filename = "tests/system_controller/fixtures/test_env_predictor.json"
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

    def test_prediction(self):
        predictor = DefaultEnvironmentPredictor()
        self.env_ctl.init_params()
        time_start = 0
        time_end = 10
        prediction_steps = 4
        for time in range(time_start, time_end - prediction_steps):
            self.system.time = time
            environment_input = self.env_ctl.update(self.system)
            predictor.update(self.system, environment_input)

        predictions = predictor.predict(prediction_steps)
        self.assertEqual(len(predictions), prediction_steps)

        for step in range(prediction_steps):
            time = time_end - prediction_steps + step
            self.system.time = time
            environment_input = self.env_ctl.update(self.system)

            pred_env = predictions[step]
            self.assertIsInstance(pred_env, EnvironmentInput)

            for app in self.system.apps:
                for src_node in self.system.nodes:
                    pred_load = pred_env.get_generated_load(app.id, src_node.id)
                    self.assertGreaterEqual(pred_load, 0.0)
                    self.assertLess(pred_load, math.inf)

                    for dst_node in self.system.nodes:
                        pred_net_delay = pred_env.get_net_delay(app.id, src_node.id, dst_node.id)
                        self.assertGreaterEqual(pred_net_delay, 0.0)
                        self.assertLess(pred_net_delay, math.inf)

    def test_params(self):
        versions = [None, ARIMAPredictor, AutoARIMAPredictor, ExpSmoothingPredictor]
        for version in versions:
            predictor = DefaultEnvironmentPredictor()
            predictor.load_predictor_class = version
            predictor.net_delay_predictor_class = version

            self.env_ctl.init_params()
            time_start = 0
            time_end = 10
            prediction_steps = 4
            for time in range(time_start, time_end - prediction_steps):
                self.system.time = time
                environment_input = self.env_ctl.update(self.system)
                predictor.update(self.system, environment_input)

            predictions = predictor.predict(prediction_steps)
            self.assertEqual(len(predictions), prediction_steps)


if __name__ == '__main__':
    unittest.main()
