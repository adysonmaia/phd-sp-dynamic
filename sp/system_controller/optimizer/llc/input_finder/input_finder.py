from abc import ABC, abstractmethod


class InputFinder(ABC):
    def __init__(self,
                 system,
                 environment_inputs,
                 objective,
                 objective_aggregator,
                 system_estimator,
                 dominance_func,
                 pool_size=0,
                 last_inputs=None,
                 **kwargs):

        self.system = system
        self.environment_inputs = environment_inputs
        self.objective = objective
        self.objective_aggregator = objective_aggregator
        self.system_estimator = system_estimator
        self.dominance_func = dominance_func
        self.pool_size = pool_size
        self.last_inputs = last_inputs

    @property
    def nb_slots(self):
        return len(self.environment_inputs)

    def clear_params(self):
        pass

    @abstractmethod
    def solve(self):
        pass
