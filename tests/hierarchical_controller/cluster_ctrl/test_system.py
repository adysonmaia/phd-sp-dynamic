from sp.core.model import Scenario, System, EnvironmentInput
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.estimator.system import DefaultSystemEstimator
from sp.system_controller.optimizer.so_heuristic import SOHeuristicOptimizer
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.cluster_ctrl.model import ClusterSystem, ClusterControlInput, ClusterEnvironmentInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterScenario
import unittest
import json
import copy


class ClusterSystemTestCase(unittest.TestCase):
    def setUp(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_system.json"
        self.system = System()
        self.system.time = 0
        self.system.sampling_time = 1
        self.clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            self.system.scenario = Scenario.from_json(data)
            self.clusters = data['clusters']
        self.global_scenario = GlobalScenario.from_real_scenario(self.system.scenario, self.clusters)

    def test_from_real_systems(self):
        env_ctl = EnvironmentController()
        sys_estimator = DefaultSystemEstimator()
        opt = SOHeuristicOptimizer()

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

        for index in range(len(systems)):
            system = systems[index]
            for global_node in self.global_scenario.network.nodes:
                cluster_sys = ClusterSystem.from_real_system(system, self.global_scenario, global_node)
                self.assertIsInstance(cluster_sys, ClusterSystem)
                self.assertIsInstance(cluster_sys.real_scenario, Scenario)

                if system.control_input is not None and system.environment_input is not None:
                    self.assertIsInstance(cluster_sys.control_input, ClusterControlInput)
                    self.assertIsInstance(cluster_sys.environment_input, ClusterEnvironmentInput)

    def test_copy(self):
        global_node = self.global_scenario.network.nodes[0]
        cluster_sys = ClusterSystem.from_real_system(self.system, self.global_scenario, global_node)

        cp_system = cluster_sys.clear_copy()
        self.assertIsInstance(cp_system, ClusterSystem)
        self.assertIsInstance(cp_system.scenario, ClusterScenario)
        self.assertIsInstance(cp_system.real_scenario, Scenario)

        cp_system = copy.copy(cluster_sys)
        self.assertIsInstance(cp_system, ClusterSystem)
        self.assertEqual(cp_system.scenario, cluster_sys.scenario)
        self.assertEqual(cp_system.real_scenario, cluster_sys.real_scenario)
