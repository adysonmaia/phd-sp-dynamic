from . import Controller
from sp.solver import SolverError
from sp.solver.static.cloud import CloudSolver
from abc import abstractmethod


class AllocationController(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.solver = None

    def init_params(self, system):
        Controller.init_params(self, system)
        if self.solver is None:
            self.solver = CloudSolver()

    @abstractmethod
    def update(self, system):
        pass


class PeriodicAllocationController(AllocationController):
    def __init__(self, period=1):
        AllocationController.__init__(self)
        self.period = period
        self.next_update = 0

    def init_params(self, system):
        AllocationController.init_params(self, system)
        self.next_update = system.time

    def update(self, system):
        current_time = system.time
        alloc = None
        if current_time == self.next_update:
            try:
                alloc = self.solver.solve(self.system)
            except SolverError:
                alloc = None
            self.next_update = current_time + self.period
        return alloc

