from abc import ABC, abstractmethod


class Optimizer(ABC):
    @abstractmethod
    def solve(self, system, environment_input):
        return None

    def init_params(self):
        pass

    def clear_params(self):
        pass


class OptimizerError(Exception):
    pass

