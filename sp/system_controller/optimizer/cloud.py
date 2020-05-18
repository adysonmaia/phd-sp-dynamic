from .optimizer import Optimizer
from sp.system_controller.model import OptSolution
from sp.system_controller.util import alloc_demanded_resources

ALL_LOAD = 1.0


class CloudOptimizer(Optimizer):
    """Cloud Optimizer

    It places every application in the cloud
    """

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            OptSolution: problem solution
        """
        solution = OptSolution.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            solution.app_placement[app.id][cloud_node.id] = True
            for src_node in system.nodes:
                solution.load_distribution[app.id][src_node.id][cloud_node.id] = ALL_LOAD

        return alloc_demanded_resources(system, solution, environment_input)
