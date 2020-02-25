from . import Controller
from sp.solver import SolverError
from sp.solver.static.cloud import CloudSolver


class AllocationController(Controller):
    def __init__(self):
        Controller.__init__(self)
        self.solver = None

    def start(self, system):
        Controller.start(self, system)
        if self.solver is None:
            self.solver = CloudSolver()

    def update(self, time):
        pass

    def stop(self):
        pass


class PeriodicAllocationController(AllocationController):
    def __init__(self):
        AllocationController.__init__(self)
        self.period = 1
        self.next_update = 0

    def start(self, system):
        AllocationController.start(self, system)
        self.next_update = system.time

    def update(self, time):
        if time != self.next_update:
            return

        alloc = None
        try:
            alloc = self.solver.solve(self.system, time)
        except SolverError:
            alloc = None

        if alloc is not None:
            self.system.allocation = alloc
        self.next_update = time + self.period

