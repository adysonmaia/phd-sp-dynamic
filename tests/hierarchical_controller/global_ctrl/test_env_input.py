from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalEnvironmentInput, GlobalSystem
import unittest
import json


class GlobalEnvInputTestCase(unittest.TestCase):

    def test_from_real_env_inputs(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_env_input.json"
        system = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
            clusters = data['clusters']

        env_ctl = EnvironmentController()
        global_scenario = GlobalScenario.from_real_scenario(system.scenario, clusters)

        env_ctl.init_params()
        real_env_inputs = []
        time_start = 0
        # time_end = 10
        time_end = 5
        for time in range(time_start, time_end):
            system.time = time
            env_input = env_ctl.update(system)
            real_env_inputs.append(env_input)

        global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(real_env_inputs, global_scenario)
        self.assertIsInstance(global_env_input, GlobalEnvironmentInput)

        for app in global_scenario.apps:
            for src_node in global_scenario.network.nodes:
                src_central = src_node.central_node
                load = global_env_input.get_generated_load(app.id, src_node.id)
                if src_node.is_base_station():
                    self.assertGreater(load, 0.0)
                else:
                    self.assertEqual(load, 0.0)

                for dst_node in global_scenario.network.nodes:
                    global_delay = global_env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                    if src_node != dst_node:
                        dst_central = dst_node.central_node
                        central_delay = real_env_inputs[0].get_net_delay(app.id, src_central.id, dst_central.id)
                        self.assertEqual(global_delay, central_delay)
                    elif len(src_node.nodes) == 1:
                        self.assertEqual(global_delay, 0.0)
                    else:
                        self.assertGreater(global_delay, 0.0)

    def test_create_empty(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_env_input.json"
        system = None
        clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            system = System()
            system.scenario = Scenario.from_json(data)
            clusters = data['clusters']

        system.time = 0
        system.sampling_time = 1
        global_scenario = GlobalScenario.from_real_scenario(system.scenario, clusters)
        global_system = GlobalSystem.from_real_systems(system, global_scenario)
        self.assertIsInstance(global_system, GlobalSystem)

        global_env_input = GlobalEnvironmentInput.create_empty(global_system)
        self.assertIsInstance(global_env_input, GlobalEnvironmentInput)
        self.assertEqual(len(global_env_input.generated_load.keys()), len(system.apps))
        self.assertEqual(len(global_env_input.generated_load[0].keys()), len(global_system.nodes))
