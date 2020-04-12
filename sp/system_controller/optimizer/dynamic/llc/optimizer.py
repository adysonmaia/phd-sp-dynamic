from sp.system_controller.optimizer import Optimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
from sp.system_controller.metric import deadline, cost, availability, migration
from .multi_stage import MultiStage, preferred_dominates


class LLCOptimizer(Optimizer):
    def __init__(self):
        Optimizer.__init__(self)
        self.objective = None
        self.objective_aggregator = None
        self.use_heuristic = True
        self.prediction_window = 1
        self.environment_predictor = None
        self.system_estimator = None
        self.dominance_func = preferred_dominates
        self.pool_size = 4

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

    def solve(self, system, environment_input):
        self.init_params()
        self.environment_predictor.update(system, environment_input)
        ms_heuristic = MultiStage(system=system,
                                  environment_input=environment_input,
                                  objective=self.objective,
                                  use_heuristic=self.use_heuristic,
                                  prediction_window=self.prediction_window,
                                  environment_predictor=self.environment_predictor,
                                  objective_aggregator=self.objective_aggregator,
                                  dominance_func=self.dominance_func,
                                  pool_size=self.pool_size)

        return ms_heuristic.solve()
