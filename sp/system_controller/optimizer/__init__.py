from abc import ABC, abstractmethod


class Optimizer(ABC):
    @abstractmethod
    def solve(self, system, environment_input):
        return None


class OptimizerError(Exception):
    pass

