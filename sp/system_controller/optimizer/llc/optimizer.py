from sp.system_controller.optimizer import Optimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
from sp.system_controller.metric import deadline, cost, availability, migration
from .two_step import TwoStep


class LLCOptimizer(Optimizer):
    def __init__(self):
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
        if self.environment_predictor is None:
            self.environment_predictor = DefaultEnvironmentPredictor()

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
        self.environment_predictor.clear()
        self._last_population = None

    def solve(self, system, environment_input):
        self.init_params()
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
