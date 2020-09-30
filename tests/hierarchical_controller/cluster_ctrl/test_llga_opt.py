from sp.core.model import Scenario, System
from sp.physical_system.environment_controller import EnvironmentController
from sp.system_controller.model import OptSolution
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalSystem, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.predictor import GlobalEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalMOGAOptimizer
from sp.hierarchical_controller.global_ctrl.util.make import make_global_limits
from sp.hierarchical_controller.cluster_ctrl.optimizer import ClusterLLGAOptimizer
from sp.hierarchical_controller.cluster_ctrl.optimizer import GeneralClusterLLGAOperator, SimpleClusterLLGAOperator
from sp.hierarchical_controller.cluster_ctrl import metric
import unittest
import json


class ClusterLLGATestCase(unittest.TestCase):
    def setUp(self):
        filename = "tests/hierarchical_controller/cluster_ctrl/fixtures/test_llga_opt.json"
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

        self.global_system = GlobalSystem.from_real_systems(self.system, self.global_scenario)
        self.global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(self.env_input,
                                                                                    self.global_scenario)

        opt = GlobalMOGAOptimizer()
        opt.init_params()
        self.global_ctrl_input = opt.solve(self.global_system, self.global_env_input)
        self.global_ctrl_input = make_global_limits(self.global_system, self.global_ctrl_input, self.global_env_input)

        self.global_env_pred = GlobalEnvironmentPredictor()
        self.global_env_pred.global_scenario = self.global_system.scenario
        self.global_env_pred.global_period = 1
        self.global_env_pred.init_params()
        self.global_env_pred.update(self.system, self.env_input)

    def test_general_solution(self):
        opt = ClusterLLGAOptimizer()
        opt.prediction_window = 1
        opt.max_iteration = 1
        opt.environment_predictor = None
        opt.ga_operator_class = GeneralClusterLLGAOperator
        opt.ga_params = {"pool_size": 4, "timeout": 60}
        opt.ga_operator_params = {
            "objective": [metric.deadline.weighted_avg_deadline_violation,
                          metric.cost.overall_cost,
                          metric.migration.weighted_migration_rate],
        }

        opt.init_params()
        solution = opt.solve(self.system, self.env_input, self.global_scenario, self.global_ctrl_input)
        self.assertIsInstance(solution, OptSolution)
