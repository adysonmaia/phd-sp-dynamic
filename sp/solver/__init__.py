from sp.utils import resource_allocation
from abc import ABC, abstractmethod


class Solver(ABC):
    def __init__(self):
        ABC.__init__(self)

    @abstractmethod
    def solve(self, system, time=0):
        return None


class SolverError(Exception):
    pass


utils = resource_allocation
