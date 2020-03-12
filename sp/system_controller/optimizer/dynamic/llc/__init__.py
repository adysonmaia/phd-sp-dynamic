from sp.system_controller.optimizer import Optimizer
from sp.system_controller.predictor import DefaultEnvironmentPredictor
from sp.system_controller.metric.static import deadline, cost, availability
from sp.system_controller.metric.dynamic import migration
from .multi_stage import MultiStage


class LLCOptimizer(Optimizer):
    def __init__(self):
        Optimizer.__init__(self)
        self.objective = None
        self.objective_aggregator = None
        self.prediction_window = 1
        self.max_iterations = 100
        self.environment_predictor = None
        self.system_estimator = None

    def solve(self, system, environment_input):
        if self.environment_predictor is None:
            self.environment_predictor = DefaultEnvironmentPredictor()
        self.environment_predictor.update(system, environment_input)

        if self.objective is None:
            self.objective = [
                deadline.max_deadline_violation,
                cost.overall_cost,
                availability.avg_unavailability,
                migration.overall_migration_cost
            ]
        if not isinstance(self.objective, list):
            self.objective = [self.objective]

        ms_heuristic = MultiStage(system=system,
                                  environment_input=environment_input,
                                  objective=self.objective,
                                  nb_stages=self.prediction_window,
                                  max_iterations=self.max_iterations,
                                  environment_predictor=self.environment_predictor,
                                  objective_aggregator=self.objective_aggregator)

        return ms_heuristic.solve()
