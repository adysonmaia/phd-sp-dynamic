from sp.system_controller.scheduler.scheduler import Scheduler
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalEnvironmentInput, GlobalScenario
from abc import abstractmethod


class GlobalScheduler(Scheduler):
    """Global Scheduler Abstract Class

    Attributes:
        global_scenario (GlobalScenario): global scenario
    """

    def __init__(self):
        """Initialization
        """
        Scheduler.__init__(self)
        self.global_scenario = None

    @abstractmethod
    def init_params(self):
        """Initialize simulation parameters
        """
        pass

    @abstractmethod
    def clear_params(self):
        """Clear simulation parameters
        """
        pass

    @abstractmethod
    def needs_update(self, system, environment_input):
        """Check if the optimization should be executed at a simulation time

        Args:
            system (System): real system
            environment_input (EnvironmentInput): real environment input
        Returns:
            bool: True if the optimization will be executed in the current time, False otherwise
        """
        pass

    @abstractmethod
    def update(self, system, environment_input):
        """Update scheduler at a simulation time with a real system's state and environment input

        Args:
            system (System): real system
            environment_input (EnvironmentInput): real environment input
        Returns:
            (GlobalSystem, GlobalEnvironmentInput): global system and environment input
                that will be send to the optimizer
        """
        pass

