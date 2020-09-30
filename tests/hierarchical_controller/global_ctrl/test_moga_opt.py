from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalSystem, GlobalControlInput
from sp.hierarchical_controller.global_ctrl.model import GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.optimizer.moga import GlobalMOGAOptimizer
import unittest
import json


class GlobalMOGATestCase(unittest.TestCase):

    def test_solver(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_moga_opt.json"
        system = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
            clusters = data['clusters']

        env_ctl = EnvironmentController()
        global_scenario = GlobalScenario.from_real_scenario(system.scenario, clusters)

        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)

        global_system = GlobalSystem.from_real_systems(system, global_scenario)
        global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(env_input, global_scenario)

        opt = GlobalMOGAOptimizer()
        opt.init_params()
        global_ctrl_input = opt.solve(global_system, global_env_input)
        self.assertIsInstance(global_ctrl_input, GlobalControlInput)

        for app in global_system.apps:
            for node in global_system.nodes:
                place = global_ctrl_input.get_app_placement(app.id, node.id)
                self.assertGreaterEqual(place, 0)
                self.assertLessEqual(place, len(node.nodes))

                for resource in global_system.resources:
                    alloc = global_ctrl_input.get_allocated_resource(app.id, node.id, resource.name)
                    if place > 0:
                        self.assertGreater(alloc, 0.0)
                    else:
                        self.assertEqual(alloc, 0.0)

                for dst_node in global_system.nodes:
                    ld = global_ctrl_input.get_load_distribution(app.id, node.id, dst_node.id)
                    dst_place = global_ctrl_input.get_app_placement(app.id, dst_node.id)
                    self.assertGreaterEqual(ld, 0.0)
                    self.assertLessEqual(ld, 1.0)
                    if dst_place == 0:
                        self.assertEqual(ld, 0.0)
