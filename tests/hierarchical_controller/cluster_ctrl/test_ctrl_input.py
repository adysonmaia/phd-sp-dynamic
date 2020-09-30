from sp.core.model import Scenario, System
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.optimizer.so_heuristic import SOHeuristicOptimizer
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.cluster_ctrl.model import ClusterScenario, ClusterControlInput
import unittest
import json


class ClusterCtrlInputTestCase(unittest.TestCase):
    def test_from_real_control_input(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_ctrl_input.json"
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
            cluster_ctrl_input = ClusterControlInput.from_real_control_input(ctrl_input, global_scenario, global_node)
            self.assertIsInstance(cluster_ctrl_input, ClusterControlInput)

            for app in cluster_scenario.apps:
                for node in cluster_scenario.network.internal_nodes:
                    real_place = ctrl_input.get_app_placement(app.id, node.id)
                    cluster_place = cluster_ctrl_input.get_app_placement(app.id, node.id)
                    self.assertEqual(real_place, cluster_place)

                    real_load = ctrl_input.get_received_load(app.id, node.id)
                    cluster_load = cluster_ctrl_input.get_received_load(app.id, node.id)
                    self.assertEqual(real_load, cluster_load)

                    for resource in cluster_scenario.resources:
                        real_alloc = ctrl_input.get_allocated_resource(app.id, node.id, resource.name)
                        cluster_alloc = cluster_ctrl_input.get_allocated_resource(app.id, node.id, resource.name)
                        self.assertEqual(real_alloc, cluster_alloc)

                    for dst_node in cluster_scenario.network.internal_nodes:
                        real_ld = ctrl_input.get_load_distribution(app.id, node.id, dst_node.id)
                        cluster_ld = cluster_ctrl_input.get_load_distribution(app.id, node.id, dst_node.id)
                        self.assertEqual(real_ld, cluster_ld)

                for ext_node in cluster_scenario.network.external_nodes:
                    place_count = 0
                    for node in ext_node.nodes:
                        place_count += int(ctrl_input.get_app_placement(app.id, node.id))
                    cluster_place = cluster_ctrl_input.get_app_placement(app.id, ext_node.id)
                    self.assertEqual(cluster_place, place_count > 0)

                    assert_func = self.assertGreater if place_count > 0 else self.assertEqual
                    for resource in cluster_scenario.resources:
                        alloc = cluster_ctrl_input.get_allocated_resource(app.id, ext_node.id, resource.name)
                        assert_func(alloc, 0.0)
