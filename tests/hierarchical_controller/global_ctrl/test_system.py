from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.system_controller.optimizer.so_heuristic import SOHeuristicOptimizer
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalSystem, GlobalControlInput
from sp.hierarchical_controller.global_ctrl.model import GlobalEnvironmentInput
import unittest
import json
import copy


class GlobalSystemTestCase(unittest.TestCase):
    def setUp(self):
        filename = "tests/hierarchical_controller/global_ctrl/fixtures/test_system.json"
        self.system = System()
        self.system.time = 0
        self.system.sampling_time = 1
        self.clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            self.system.scenario = Scenario.from_json(data)
            self.clusters = data['clusters']

    def test_from_real_systems(self):
        env_ctl = EnvironmentController()
        sys_estimator = DefaultSystemEstimator()
        opt = SOHeuristicOptimizer()
        global_scenario = GlobalScenario.from_real_scenario(self.system.scenario, self.clusters)

        time_duration = 5
        systems = []
        control_inputs = []
        env_inputs = []
        system = self.system
        for time in range(time_duration):
            system.time = time
            system.sampling_time = 1
            env_input = env_ctl.update(system)
            control_input = opt.solve(system, env_input)

            systems.append(system)
            env_inputs.append(env_input)
            control_inputs.append(control_input)

            system = sys_estimator(system, control_input, env_input)

        global_system = GlobalSystem.from_real_systems(systems, global_scenario)
        self.assertIsInstance(global_system, GlobalSystem)
        self.assertIsInstance(global_system.control_input, GlobalControlInput)
        self.assertIsInstance(global_system.environment_input, GlobalEnvironmentInput)

    def test_copy(self):
        global_scenario = GlobalScenario.from_real_scenario(self.system.scenario, self.clusters)
        global_system = GlobalSystem.from_real_systems(self.system, global_scenario)

        cp_system = global_system.clear_copy()
        self.assertIsInstance(cp_system, GlobalSystem)
        self.assertIsInstance(cp_system.scenario, GlobalScenario)
        self.assertIsInstance(cp_system.real_scenario, Scenario)
        self.assertIsInstance(cp_system.real_system, System)

        cp_system = copy.copy(global_system)
        self.assertIsInstance(cp_system, GlobalSystem)
        self.assertEqual(cp_system.scenario, global_system.scenario)
        self.assertEqual(cp_system.real_scenario, global_system.real_scenario)
        self.assertEqual(cp_system.real_system, global_system.real_system)
