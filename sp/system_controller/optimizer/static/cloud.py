from sp.system_controller.optimizer import Optimizer
from sp.system_controller.model.allocation import Allocation
from sp.system_controller.utils.alloc_util import alloc_demanded_resources


ALL_LOAD = 1.0


class CloudOptimizer(Optimizer):
    def solve(self, system):
        alloc = Allocation.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            alloc.set_app_placement(app.id, cloud_node.id, True)
            for src_node in system.nodes:
                alloc.set_load_distribution(app.id, src_node.id, cloud_node.id, ALL_LOAD)

        return alloc_demanded_resources(system, alloc)
