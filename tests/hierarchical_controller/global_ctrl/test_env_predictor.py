from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalEnvironmentInput, GlobalSystem
from sp.hierarchical_controller.global_ctrl.predictor import GlobalEnvironmentPredictor
import unittest
import json


class GlobalEnvPredictorTestCase(unittest.TestCase):

    def test_predict(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_env_predictor.json"
        system = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
            clusters = data['clusters']

        env_ctl = EnvironmentController()
        global_scenario = GlobalScenario.from_real_scenario(system.scenario, clusters)

        global_env_pred = GlobalEnvironmentPredictor()
        global_env_pred.global_scenario = global_scenario
        global_env_pred.global_period = 2
        global_env_pred.init_params()

        env_ctl.init_params()
        real_env_inputs = []
        time_start = 0
        time_end = 10
        for time in range(time_start, time_end):
            system.time = time
            env_input = env_ctl.update(system)
            global_env_pred.update(system, env_input)
            real_env_inputs.append(env_input)

        global_env_inputs = global_env_pred.predict(0)
        self.assertEqual(len(global_env_inputs), 1)
        self.assertIsInstance(global_env_inputs[0], GlobalEnvironmentInput)

        prediction_window = 2
        global_env_inputs = global_env_pred.predict(prediction_window)
        self.assertEqual(len(global_env_inputs), prediction_window)
        for env_input in global_env_inputs:
            self.assertIsInstance(env_input, GlobalEnvironmentInput)

    def test_step_zero(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_env_predictor.json"
        system = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
            clusters = data['clusters']

        env_ctl = EnvironmentController()
        global_scenario = GlobalScenario.from_real_scenario(system.scenario, clusters)

        predictor = GlobalEnvironmentPredictor()
        predictor.global_scenario = global_scenario
        predictor.global_period = 1
        predictor.init_params()

        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)
        predictor.update(system, env_input)

        global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(env_input, global_scenario)
        pred_env_inputs = predictor.predict(0)
        self.assertEqual(len(pred_env_inputs), 1)
        pred_env_input = pred_env_inputs[0]
        self.assertIsInstance(pred_env_input, GlobalEnvironmentInput)

        for app in global_scenario.apps:
            for src_node in global_scenario.network.nodes:
                load = global_env_input.get_generated_load(app.id, src_node.id)
                pred_load = pred_env_input.get_generated_load(app.id, src_node.id)
                self.assertEqual(load, pred_load)

                for dst_node in global_scenario.network.nodes:
                    net_delay = global_env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    pred_net_delay = pred_env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    self.assertEqual(net_delay, pred_net_delay)
