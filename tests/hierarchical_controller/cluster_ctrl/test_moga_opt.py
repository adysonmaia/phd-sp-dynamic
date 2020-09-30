from sp.core.model import Scenario, System
from sp.core.heuristic.brkga import GAIndividual
from sp.physical_system.environment_controller import EnvironmentController
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalSystem, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalMOGAOptimizer
from sp.hierarchical_controller.global_ctrl.util.make import make_global_limits
from sp.hierarchical_controller.cluster_ctrl.model import ClusterEnvironmentInput, ClusterSystem, ClusterControlInput
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlLimit
from sp.hierarchical_controller.cluster_ctrl.optimizer.moga import ClusterMOGAOperator
import unittest
import json


class ClusterMOGATestCase(unittest.TestCase):
    def setUp(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_moga_opt.json"
        self.system = None
        self.clusters = None
        with open(filename) as json_file:
            data = json.load(json_file)
            self.system = System()
            self.system.scenario = Scenario.from_json(data)
            self.clusters = data['clusters']

        self.env_ctl = EnvironmentController()
        self.global_scenario = GlobalScenario.from_real_scenario(self.system.scenario, self.clusters)

        self.env_ctl.init_params()
        self.system.time = 0
        self.system.sampling_time = 1
        self.env_input = self.env_ctl.update(self.system)

    def test_decode(self):
        for global_node in self.global_scenario.network.nodes:
            cluster_sys = ClusterSystem.from_real_system(self.system, self.global_scenario, global_node)
            cluster_env = ClusterEnvironmentInput.from_real_environment_input(self.env_input, self.global_scenario,
                                                                              global_node)
            cluster_limit = None
            objective = None

            ga_operator = ClusterMOGAOperator(objective=objective, system=cluster_sys, environment_input=cluster_env,
                                              control_limit=cluster_limit)
            ga_operator.init_params()
            population = ga_operator.first_population()
            for individual in population:
                self.assertIsInstance(individual, GAIndividual)
                solution = ga_operator.decode(individual)
                self.assertIsInstance(solution, ClusterControlInput)

                for app in cluster_sys.apps:
                    for ext_node in cluster_sys.external_nodes:
                        place = solution.get_app_placement(app.id, ext_node.id)
                        self.assertEqual(place, ext_node.is_cloud())

    def test_control_limit(self):
        global_system = GlobalSystem.from_real_systems(self.system, self.global_scenario)
        global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(self.env_input, self.global_scenario)

        opt = GlobalMOGAOptimizer()
        opt.init_params()
        global_ctrl_input = opt.solve(global_system, global_env_input)
        global_ctrl_input = make_global_limits(global_system, global_ctrl_input, global_env_input)

        for global_node in self.global_scenario.network.nodes:
            cluster_sys = ClusterSystem.from_real_system(self.system, self.global_scenario, global_node)
            cluster_env = ClusterEnvironmentInput.from_real_environment_input(self.env_input, self.global_scenario,
                                                                              global_node)
            cluster_limit = ClusterControlLimit()
            for app in cluster_sys.apps:
                max_instances = global_ctrl_input.get_max_app_placement(app.id, global_node.id)
                min_instances = global_ctrl_input.get_min_app_placement(app.id, global_node.id)
                cluster_limit.max_app_placement[app.id] = max_instances
                cluster_limit.min_app_placement[app.id] = min_instances

                for ext_node in cluster_sys.external_nodes:
                    nb_instances = global_ctrl_input.get_max_app_placement(app.id, ext_node.id)
                    cluster_env.nb_instances[app.id][ext_node.id] = nb_instances

                    max_dispatch_load = global_ctrl_input.get_max_load(app.id, global_node.id, ext_node.id)
                    cluster_limit.max_dispatch_load[app.id][ext_node.id] = max_dispatch_load

                    gen_load = global_ctrl_input.get_max_load(app.id, ext_node.id, global_node.id)
                    cluster_env.generated_load[app.id][ext_node.id] = gen_load

                    cluster_env.additional_received_load[app.id][ext_node.id] = 0.0

            objective = None
            ga_operator = ClusterMOGAOperator(objective=objective, system=cluster_sys, environment_input=cluster_env,
                                              control_limit=cluster_limit)
            ga_operator.init_params()
            population = ga_operator.first_population()
            for individual in population:
                self.assertIsInstance(individual, GAIndividual)
                solution = ga_operator.decode(individual)
                self.assertIsInstance(solution, ClusterControlInput)

                for app in cluster_sys.apps:
                    place_count = sum(map(lambda n: int(solution.get_app_placement(app.id, n.id)),
                                          cluster_sys.internal_nodes))
                    self.assertGreaterEqual(place_count, cluster_limit.get_min_app_placement(app.id))
                    self.assertLessEqual(place_count, cluster_limit.get_max_app_placement(app.id))
