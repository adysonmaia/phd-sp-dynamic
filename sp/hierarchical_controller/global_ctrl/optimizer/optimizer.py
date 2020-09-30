from sp.system_controller.optimizer import Optimizer, OptimizerError
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalEnvironmentInput, GlobalControlInput
from abc import abstractmethod


class GlobalOptimizer(Optimizer):
    """Global Optimizer

    """

    def __init__(self):
        """Initialization
        """
        Optimizer.__init__(self)

    @abstractmethod
    def solve(self, system, environment_input):
        """Solve the service placement problem

        Args:
            system (GlobalSystem): current global system's state
            environment_input (GlobalEnvironmentInput): global environment input
        Returns:
            GlobalControlInput: control input
        Raises:
            OptimizerError: error found while solving the problem
        """
        pass

    def init_params(self):
        """Initialize parameters for a simulation
        """
        pass

    def clear_params(self):
        """Clear parameters of a simulation
        """
        pass

