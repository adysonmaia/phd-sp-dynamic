from sp.core.model import System, EnvironmentInput
from sp.system_controller.optimizer import Optimizer, OptimizerError
from sp.hierarchical_controller.cluster_ctrl.model import ClusterControlInput
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario, GlobalControlInput
from abc import abstractmethod


class ClusterOptimizer(Optimizer):
    """Cluster Optimizer

    """

    def __init__(self):
        """Initialization
        """
        Optimizer.__init__(self)

    @abstractmethod
    def solve(self, system, environment_input, global_scenario=None, global_control_input=None):
        """Solve the service placement problem

        Args:
            system (System): current real system's state
            environment_input (EnvironmentInput): real environment input
            global_scenario (GlobalScenario): global scenario
            global_control_input (GlobalControlInput): global control input
        Returns:
            ClusterControlInput: control input
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
