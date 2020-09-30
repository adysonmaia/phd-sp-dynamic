from .optimizer import GlobalOptimizer
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalControlInput, GlobalEnvironmentInput
from sp.hierarchical_controller.global_ctrl.util.calc import calc_received_load


ALL_LOAD = 1.0
NB_INSTANCES = 1


class GlobalCloudOptimizer(GlobalOptimizer):
    """Global Cloud Optimizer

    It places every application in the cloud
    """

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (GlobalSystem): current system's state
            environment_input (GlobalEnvironmentInput): environment input
        Returns:
            GlobalControlInput: problem solution
        """
        solution = GlobalControlInput.create_empty(system)
        cloud_node = system.cloud_node

        for app in system.apps:
            solution.app_placement[app.id][cloud_node.id] = NB_INSTANCES
            for src_node in system.nodes:
                solution.load_distribution[app.id][src_node.id][cloud_node.id] = ALL_LOAD

            load = calc_received_load(app.id, cloud_node.id, system, solution, environment_input, use_cache=False)
            solution.received_load[app.id][cloud_node.id] = load

            for resource in system.resources:
                demand = app.demand[resource.name](load)
                solution.allocated_resource[app.id][cloud_node.id][resource.name] = demand

        return solution
