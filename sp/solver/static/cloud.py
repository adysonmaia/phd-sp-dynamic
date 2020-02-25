from sp.solver import Solver, utils
from sp.model.allocation import Allocation


ALL_LOAD = 1.0


class CloudSolver(Solver):
    def __init__(self):
        Solver.__init__(self)

    def solve(self, system, time=0):
        alloc = Allocation.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            alloc.set_app_placement(app.id, cloud_node.id, True)
            for src_node in system.nodes:
                alloc.set_load_distribution(app.id, src_node.id, cloud_node.id, ALL_LOAD)

        utils.alloc_demanded_resources(system, alloc)

        return alloc
