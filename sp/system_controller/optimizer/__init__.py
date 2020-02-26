from abc import ABC, abstractmethod


class Optimizer(ABC):
    @abstractmethod
    def solve(self, system):
        return None


class OptimizerError(Exception):
    pass

