from abc import ABC, abstractmethod


class Solver(ABC):
    def __init__(self):
        ABC.__init__(self)

    @abstractmethod
    def solve(self, system):
        return None


class SolverError(Exception):
    pass

