from sp.core.model import Scenario, System, EnvironmentInput, Link
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.so_heuristic import SOHeuristicOptimizer
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.cluster_ctrl.model import ClusterEnvironmentInput, ClusterScenario, ClusterSystem
import unittest
import json


class ClusterEnvInputTestCase(unittest.TestCase):

    def test_from_real_env_input(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_env_input.json"
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
        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)

        for global_node in global_scenario.network.nodes:
            cluster_scenario = ClusterScenario.from_global_scenario(global_scenario, global_node)
            self.assertIsInstance(cluster_scenario, ClusterScenario)
            cluster_env_input = ClusterEnvironmentInput.from_real_environment_input(env_input, global_scenario,
                                                                                    global_node)
            self.assertIsInstance(cluster_env_input, ClusterEnvironmentInput)

            for app in cluster_scenario.apps:
                for real_node in global_node.nodes:
                    cluster_load = cluster_env_input.get_generated_load(app.id, real_node.id)
                    real_load = env_input.get_generated_load(app.id, real_node.id)
                    self.assertEqual(cluster_load, real_load)

                    for dst_real_node in global_node.nodes:
                        cluster_net_delay = cluster_env_input.get_net_delay(app.id, real_node.id, dst_real_node.id)
                        real_net_delay = env_input.get_net_delay(app.id, real_node.id, dst_real_node.id)
                        self.assertEqual(cluster_net_delay, real_net_delay)

                for src_node in cluster_scenario.network.nodes:
                    load = cluster_env_input.get_generated_load(app.id, src_node.id)
                    if src_node.is_base_station():
                        self.assertGreaterEqual(load, 0.0)
                    else:
                        self.assertEqual(load, 0.0)

                    for dst_node in cluster_scenario.network.nodes:
                        net_delay = cluster_env_input.get_net_delay(app.id, src_node.id, dst_node.id)
                        self.assertGreaterEqual(net_delay, 0.0)
                        net_path = cluster_env_input.get_net_path(app.id, src_node.id, dst_node.id)
                        self.assertIsInstance(net_path, list)
                        if src_node != dst_node:
                            self.assertGreater(len(net_path), 0)
                            link_start_node_id = net_path[0]
                            for link_end_node_id in net_path[1:]:
                                link = cluster_scenario.network.get_link(link_start_node_id, link_end_node_id)
                                link_start_node_id = link_end_node_id
                                self.assertIsInstance(link, Link)
                        else:
                            self.assertEqual(len(net_path), 0)

    def test_from_real_env_ctrl_input(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_env_input.json"
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
        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)

        opt = SOHeuristicOptimizer()
        opt.init_params()
        ctrl_input = opt.solve(system, env_input)

        for global_node in global_scenario.network.nodes:
            cluster_scenario = ClusterScenario.from_global_scenario(global_scenario, global_node)
            self.assertIsInstance(cluster_scenario, ClusterScenario)
            cluster_env_input = ClusterEnvironmentInput.from_real_environment_input(env_input, global_scenario,
                                                                                    global_node, system, ctrl_input)
            self.assertIsInstance(cluster_env_input, ClusterEnvironmentInput)

            for app in cluster_scenario.apps:
                for node in cluster_scenario.network.external_nodes:
                    place = cluster_env_input.get_nb_instances(app.id, node.id)
                    self.assertGreaterEqual(place, 0)
                    self.assertLessEqual(place, len(node.nodes))

                    load = cluster_env_input.get_additional_received_load(app.id, node.id)
                    if place > 0:
                        self.assertGreaterEqual(load, 0.0)
                    else:
                        self.assertEqual(load, 0.0)

    def test_create_empty(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_env_input.json"
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
        system.time = 0
        system.sampling_time = 1
        env_input = env_ctl.update(system)

        for global_node in global_scenario.network.nodes:
            cluster_system = ClusterSystem.from_real_system(system, global_scenario, global_node)
            self.assertIsInstance(cluster_system, ClusterSystem)

            cluster_env_input = ClusterEnvironmentInput.create_empty(cluster_system)
            self.assertIsInstance(cluster_env_input, ClusterEnvironmentInput)





