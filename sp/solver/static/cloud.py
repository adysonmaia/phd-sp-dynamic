from sp.solver import Solver, utils
from sp.model.allocation import Allocation


ALL_LOAD = 1.0


class CloudSolver(Solver):
    def solve(self, system):
        alloc = Allocation.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            alloc.set_app_placement(app.id, cloud_node.id, True)
            for src_node in system.nodes:
                alloc.set_load_distribution(app.id, src_node.id, cloud_node.id, ALL_LOAD)

        utils.alloc_demanded_resources(system, alloc)

        return alloc
