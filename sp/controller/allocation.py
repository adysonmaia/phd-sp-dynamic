from . import Controller
from sp.solver import SolverError
from sp.solver.cloud import CloudSolver


class AllocationController(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.solver = None

    def start(self, system):
        Controller.start(self, system)
        if self.solver is None:
            self.solver = CloudSolver()


class PeriodicAllocationController(AllocationController):
    def __init__(self):
        AllocationController.__init__(self)
        self.period = 1
        self._next_update = 0

    def start(self, system):
        AllocationController.start(self, system)
        self._next_update = system.time

    def update(self, time):
        if time != self._next_update:
            return

        alloc = None
        try:
            alloc = self.solver.solve(self.system, time)
        except SolverError:
            alloc = None

        if alloc is not None:
            self.system.allocation = alloc
        self._next_update = time + self.period

