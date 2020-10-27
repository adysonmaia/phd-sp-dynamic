from sp.core.heuristic.nsgaii import NSGAII
from sp.system_controller.util import pareto_dominates, preferred_dominates
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalOptimizer
from sp.hierarchical_controller.global_ctrl.estimator.system import GlobalSystemEstimator
from sp.hierarchical_controller.global_ctrl.predictor.environment import GlobalEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl import metric
from .ga_operator import GeneralGlobalLLGAOperator, SimpleGlobalLLGAOperator
import copy


_GA_PARAMS = {
    "nb_generations": 100,
    "population_size": 100,
    "elite_proportion": 0.1,
    "mutant_proportion": 0.1,
    "elite_probability": 0.6,
    "stop_threshold": 0.10,
    "timeout": None,
    "pool_size": 4,
    "dominance_func": preferred_dominates,
}

_GA_OPERATOR_PARAMS = {
    "load_chunk_distribution": None,
    "objective_aggregator": sum,
}


class GlobalLLGAOptimizer(GlobalOptimizer):
    """Global Limited Lookahead GA control Optimizer

    Attributes:
        prediction_window (int): prediction window size
        ga_params (dict): GA parameters
        ga_operator_class: GA operator class
        ga_operator_params (dict): GA operator initialization parameters
        environment_predictor (GlobalEnvironmentPredictor): global environment input predictor
        objective (Union[function, list(function)]): list of optimization functions
    """

    def __init__(self):
        """Initialization
        """
        GlobalOptimizer.__init__(self)

        self.prediction_window = 1
        self.ga_params = {}
        self.ga_operator_class = None
        self.ga_operator_params = {}

        self.objective = None
        self.environment_predictor = None

        self._system_estimator = GlobalSystemEstimator()
        self._last_population = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.objective is None:
            self.objective = [metric.deadline.weighted_avg_deadline_violation,
                              metric.cost.overall_cost,
                              metric.migration.weighted_migration_rate]
        if not isinstance(self.objective, list):
            self.objective = [self.objective]

        if self.environment_predictor is None:
            self.environment_predictor = GlobalEnvironmentPredictor()
            # TODO: implement env predictor that is shared between scheduler and optimizer
            self.environment_predictor.init_params()

        if self.ga_operator_class is None:
            self.ga_operator_class = GeneralGlobalLLGAOperator

    def clear_params(self):
        """Clear parameters of a simulation
        """
        self._last_population = None

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (GlobalSystem): current global system's state
            environment_input (GlobalEnvironmentInput): global environment input
        Returns:
            GlobalControlInput: control input
        Raises:
            OptimizerError: error found while solving the problem
        """
        environment_inputs = [environment_input]
        environment_inputs += self.environment_predictor.predict(self.prediction_window)

        ga_params = copy.copy(_GA_PARAMS)
        if isinstance(self.ga_params, dict):
            ga_params.update(self.ga_params)

        ga_operator_params = copy.copy(_GA_OPERATOR_PARAMS)
        if isinstance(self.ga_operator_params, dict):
            ga_operator_params.update(self.ga_operator_params)

        ga_operator = self.ga_operator_class(system=system,
                                             environment_inputs=environment_inputs,
                                             objective=self.objective,
                                             system_estimator=self._system_estimator,
                                             extra_first_population=self._last_population,
                                             **ga_operator_params)

        mo_ga = NSGAII(operator=ga_operator, **ga_params)
        population = mo_ga.solve()

        last_pop_size = int(round(mo_ga.elite_proportion * len(population)))
        if last_pop_size > 0:
            self._last_population = population[:last_pop_size]
        else:
            self._last_population = population

        best_individual = population[0]
        encoded_control_input = ga_operator.get_encoded_control_input(best_individual, step=0)
        solution = ga_operator.decode_control_input(system, encoded_control_input, environment_input)
        return solution
