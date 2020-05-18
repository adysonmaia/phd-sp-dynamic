from abc import ABC, abstractmethod


class Coverage(ABC):
    """Coverage Abstract Class
    """

    @abstractmethod
    def update(self, system, environment_input, time_tolerance=None, distance_tolerance=None):
        """Update attachment of users in a system's state and environment input

        Args:
            system (sp.core.model.system.System): system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
            time_tolerance (float): time tolerance (in seconds)
            distance_tolerance (float): distance tolerance. In meters if the GPS coordination system is used

        Returns:
            dict: attached users indexed by their ids
        """
        pass

