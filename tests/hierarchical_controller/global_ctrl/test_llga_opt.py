from sp.core.model import Scenario, System
from sp.physical_system.environment_controller import EnvironmentController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalSystem, GlobalControlInput
from sp.hierarchical_controller.global_ctrl.optimizer.llga import GlobalLLGAOptimizer
from sp.hierarchical_controller.global_ctrl.predictor import GlobalEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl.optimizer.llga.ga_operator import GeneralGlobalLLGAOperator
from sp.hierarchical_controller.global_ctrl.optimizer.llga.ga_operator import SimpleGlobalLLGAOperator
import unittest
import json


class GlobalMOGATestCase(unittest.TestCase):

    def setUp(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_llga_opt.json"
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
        global_env_pred.global_period = 1
        global_env_pred.init_params()

        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)

        global_env_pred.update(system, env_input)
        self.global_system = GlobalSystem.from_real_systems(system, global_scenario)
        self.global_env_input = global_env_pred.predict(0)[0]
        self.global_env_pred = global_env_pred

    def test_general_solution(self):
        opt = GlobalLLGAOptimizer()
        opt.environment_predictor = self.global_env_pred
        opt.ga_operator_class = GeneralGlobalLLGAOperator
        opt.prediction_window = 0
        opt.init_params()
        global_ctrl_input = opt.solve(self.global_system, self.global_env_input)
        self._assert_control_input(global_ctrl_input)

    def test_simple_solution(self):
        opt = GlobalLLGAOptimizer()
        opt.environment_predictor = self.global_env_pred
        opt.ga_operator_class = SimpleGlobalLLGAOperator
        opt.prediction_window = 0
        opt.init_params()
        global_ctrl_input = opt.solve(self.global_system, self.global_env_input)
        self._assert_control_input(global_ctrl_input)

    def _assert_control_input(self, global_ctrl_input):
        self.assertIsInstance(global_ctrl_input, GlobalControlInput)

        for app in self.global_system.apps:
            for node in self.global_system.nodes:
                place = global_ctrl_input.get_app_placement(app.id, node.id)
                self.assertGreaterEqual(place, 0)
                self.assertLessEqual(place, len(node.nodes))

                for resource in self.global_system.resources:
                    alloc = global_ctrl_input.get_allocated_resource(app.id, node.id, resource.name)
                    if place > 0:
                        self.assertGreater(alloc, 0.0)
                    else:
                        self.assertEqual(alloc, 0.0)

                for dst_node in self.global_system.nodes:
                    ld = global_ctrl_input.get_load_distribution(app.id, node.id, dst_node.id)
                    dst_place = global_ctrl_input.get_app_placement(app.id, dst_node.id)
                    self.assertGreaterEqual(ld, 0.0)
                    self.assertLessEqual(ld, 1.0)
                    if dst_place == 0:
                        self.assertEqual(ld, 0.0)

