from sp.system_controller.optimizer.moga import MOGAOptimizer
import copy


class OmittedMigrationOptimizer(MOGAOptimizer):
    """Omitted Migration Optimizer
    """

    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        """
        system = copy.copy(system)
        system.control_input = None
        system.environment_input = None
        return MOGAOptimizer.solve(self, system, environment_input)
