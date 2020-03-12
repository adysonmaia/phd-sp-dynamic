from sp.system_controller.optimizer import Optimizer
from sp.system_controller.model import OptSolution
from sp.system_controller.utils import alloc_demanded_resources


ALL_LOAD = 1.0


class CloudOptimizer(Optimizer):
    def solve(self, system, environment_input):
        solution = OptSolution.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            solution.app_placement[app.id][cloud_node.id] = True
            for src_node in system.nodes:
                solution.load_distribution[app.id][src_node.id][cloud_node.id] = ALL_LOAD

        return alloc_demanded_resources(system, solution, environment_input)
