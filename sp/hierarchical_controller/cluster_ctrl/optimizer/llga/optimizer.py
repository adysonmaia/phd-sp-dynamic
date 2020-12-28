from sp.system_controller.predictor import DefaultEnvironmentPredictor, EnvironmentPredictor
from sp.hierarchical_controller.cluster_ctrl.optimizer import ClusterOptimizer
from sp.hierarchical_controller.cluster_ctrl import metric
from .iter_coop import IterativeCooperation
from .no_coop import NoCooperation
from .ga_operator import GeneralClusterLLGAOperator


class ClusterLLGAOptimizer(ClusterOptimizer):
    """Cluster Distributed Limited Lookahead GA control Optimizer

    Attributes:
        prediction_window (int): prediction window size
        max_iteration (int): max coordination iteration
        pool_size (int): coordination multi-threading pool size
        objective (list): list of objective functions
        ga_params (dict): GA parameters
        ga_operator_class: GA operator class
        ga_operator_params (dict): GA operator initialization parameters
        environment_predictor (EnvironmentPredictor): real environment predictor
    """

    def __init__(self):
        """Initialization
        """
        ClusterOptimizer.__init__(self)

        self.prediction_window = 1
        self.max_iteration = 1
        self.pool_size = 0
        self.objective = None
        self.ga_params = {}
        self.ga_operator_class = None
        self.ga_operator_params = {}
        self.environment_predictor = None

        self._iter_coop = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.objective is None:
            self.objective = [metric.deadline.weighted_avg_deadline_violation,
                              metric.cost.overall_cost,
                              metric.migration.weighted_migration_rate]

        if self.ga_operator_class is None:
            self.ga_operator_class = GeneralClusterLLGAOperator

        if self.environment_predictor is None:
            self.environment_predictor = DefaultEnvironmentPredictor()
            # TODO: predictor that is shared with multiple objects
            self.environment_predictor.init_params()

        if self.max_iteration > 0:
            self._iter_coop = IterativeCooperation(objective=self.objective,
                                                   ga_params=self.ga_params,
                                                   ga_operator_class=self.ga_operator_class,
                                                   ga_operator_params=self.ga_operator_params,
                                                   max_iteration=self.max_iteration,
                                                   pool_size=self.pool_size,
                                                   monitor=self.monitor)
        else:
            self._iter_coop = NoCooperation(objective=self.objective,
                                            ga_params=self.ga_params,
                                            ga_operator_class=self.ga_operator_class,
                                            ga_operator_params=self.ga_operator_params,
                                            pool_size=self.pool_size,
                                            monitor=self.monitor)

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
