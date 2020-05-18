from abc import ABC, abstractmethod
from sp.core.model import System, EnvironmentInput


class Scheduler(ABC):
    """Scheduler Abstract Class

    It defines when a optimization will be executed
    """

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
            system (System): system
            environment_input (EnvironmentInput): environment input

        Returns:
            bool: True if the optimization will be executed in the current time, False otherwise
        """
        pass

    @abstractmethod
    def update(self, system, environment_input):
        """Update scheduler at a simulation time with a system's state and environment input

        Args:
            system (System): system
            environment_input (EnvironmentInput): environment input

        Returns:
            (System, EnvironmentInput): system and environment input that will be send to the optimizer
        """
        pass
