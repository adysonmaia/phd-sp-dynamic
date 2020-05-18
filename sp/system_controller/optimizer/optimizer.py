from abc import ABC, abstractmethod


class Optimizer(ABC):
    """Service Placement Optimizer Abstract Class
    """

    @abstractmethod
    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (sp.core.model.system.System): current system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            sp.system_controller.model.opt_solution.OptSolution: problem solution
        Raises:
            OptimizerError: error found while solving the problem
        """
        return None

    def init_params(self):
        """Initialize parameters for a simulation
        """
        pass

    def clear_params(self):
        """Clear parameters of a simulation
        """
        pass


class OptimizerError(Exception):
    """Optimizer Error
    """
    pass

