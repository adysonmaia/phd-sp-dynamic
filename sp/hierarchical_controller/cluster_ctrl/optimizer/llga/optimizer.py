from sp.system_controller.predictor import DefaultEnvironmentPredictor
from sp.hierarchical_controller.cluster_ctrl.optimizer import ClusterOptimizer
from .iter_coop import IterativeCooperation
from .ga_operator import GeneralClusterLLGAOperator


class ClusterLLGAOptimizer(ClusterOptimizer):
    """Cluster Distributed Limited Lookahead GA control Optimizer

    """

    def __init__(self):
        """Initialization
        """
        ClusterOptimizer.__init__(self)

        self.prediction_window = 1
        self.max_iteration = 1
        self.ga_params = {}
        self.ga_operator_class = None
        self.ga_operator_params = {}
        self.environment_predictor = None

        self._iter_coop = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.ga_operator_class is None:
            self.ga_operator_class = GeneralClusterLLGAOperator

        if self.environment_predictor is None:
            self.environment_predictor = DefaultEnvironmentPredictor()
        self.environment_predictor.init_params()

        self._iter_coop = IterativeCooperation(ga_params=self.ga_params,
                                               ga_operator_class=self.ga_operator_class,
                                               ga_operator_params=self.ga_operator_params,
                                               max_iteration=self.max_iteration)
        self._iter_coop.init_params()

    def clear_params(self):
        """Clear parameters of a simulation
        """
        if self._iter_coop is not None:
            self._iter_coop.clear_params()

        if self.environment_predictor is not None:
            self.environment_predictor.clear()

    def solve(self, system, environment_input, global_scenario=None, global_control_input=None):
        """Solve the service placement problem

        Args:
            system (System): current real system's state
            environment_input (EnvironmentInput): real environment input
            global_scenario (GlobalScenario): global scenario
            global_control_input (GlobalControlInput): global control input
        Returns:
            ClusterControlInput: control input
        Raises:
            OptimizerError: error found while solving the problem
        """
        self.environment_predictor.update(system, environment_input)

        env_inputs = [environment_input]
        if self.environment_predictor is not None and self.prediction_window > 0:
            env_inputs += self.environment_predictor.predict(self.prediction_window)

        solution = self._iter_coop.solve(system, env_inputs, global_scenario, global_control_input)
        return solution
