from sp.system_controller.optimizer import Optimizer
from sp.system_controller.estimator import SystemEstimator, DefaultSystemEstimator
from sp.system_controller.predictor import EnvironmentPredictor, DefaultEnvironmentPredictor
from sp.system_controller.metric import deadline, cost, availability, migration
from .two_step import TwoStep


class LLCOptimizer(Optimizer):
    """Limited Lookahead Control Optimizer

    See Also: https://ieeexplore.ieee.org/abstract/document/1317283

    Attributes:
        objective (list(function)): list of optimization functions.
            It can be any function in the :py:mod:`sp.system_controller.metric` module
        objective_aggregator (function): objective aggregator function.
            It aggregates a list of values into a single value. Default value is the :py:func:`sum` function
        use_heuristic (bool): whether local search heuristic is used or not
        prediction_window (int): horizon prediction window size
        environment_predictor (EnvironmentPredictor): environment predictor. It uses
            :py:class:`~sp.system_controller.predictor.environment.default.DefaultEnvironmentPredictor` by default
        system_estimator (SystemEstimator): system estimator. It uses
            py:class:`~sp.system_controller.estimator.system.DefaultSystemEstimator` by default
        plan_finder_class (class): plan finder class.
            See py:mod:`sp.system_controller.optimizer.llga.plan_finder` module
        plan_finder_params (dict): initialization parameters of the plan finder class
        input_finder_class (class): input finder class.
            See py:mod:`sp.system_controller.optimizer.llga.input_finder` module
        input_finder_params (dict): initialization parameters of the input finder class
        dominance_func (function): multi-objective dominance function.
            It can be either :py:func:`~sp.system_controller.optimizer.moga.ga_operator.preferred_dominates` or
            :py:func:`~sp.core.heuristic.nsgaii.pareto_dominates`
        pool_size (int): multi-processing pool size. If zero, the optimizer doesn't use multi-processing
    """

    def __init__(self):
        """Initialization
        """

        Optimizer.__init__(self)
        self.objective = None
        self.objective_aggregator = None
        self.use_heuristic = True
        self.prediction_window = 1
        self.environment_predictor = None
        self.system_estimator = None
        self.plan_finder_class = None
        self.plan_finder_params = None
        self.input_finder_class = None
        self.input_finder_params = None
        self.dominance_func = None
        self.pool_size = 4

        self._last_population = None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        if self.environment_predictor is None:
            self.environment_predictor = DefaultEnvironmentPredictor()
        self.environment_predictor.init_params()

        if self.objective is None:
            self.objective = [
                deadline.max_deadline_violation,
                cost.overall_cost,
                availability.avg_unavailability,
                migration.overall_migration_cost
            ]

        if not isinstance(self.objective, list):
            self.objective = [self.objective]

    def clear_params(self):
        """Clear parameters of a simulation
        """
        self.environment_predictor.clear()
        self._last_population = None

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        """
        self.environment_predictor.update(system, environment_input)

        two_step = TwoStep(system=system,
                           environment_input=environment_input,
                           objective=self.objective,
                           prediction_window=self.prediction_window,
                           use_heuristic=self.use_heuristic,
                           system_estimator=self.system_estimator,
                           environment_predictor=self.environment_predictor,
                           objective_aggregator=self.objective_aggregator,
                           plan_finder_class=self.plan_finder_class,
                           plan_finder_params=self.plan_finder_params,
                           input_finder_class=self.input_finder_class,
                           input_finder_params=self.input_finder_params,
                           dominance_func=self.dominance_func,
                           pool_size=self.pool_size,
                           last_population=self._last_population)

        population = two_step.solve()
        self._last_population = population
        solution = two_step.decode_control_input(population[0])

        return solution
