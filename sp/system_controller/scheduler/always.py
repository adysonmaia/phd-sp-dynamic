from .scheduler import Scheduler


class AlwaysScheduler(Scheduler):
    """Always Scheduler

    It schedules the execution of the optimizer at every time steps of the simulation

    """

    def init_params(self):
        """Initialize simulation parameters
        """
        pass

    def clear_params(self):
        """Clear simulation parameters
        """
        pass

    def needs_update(self, system, environment_input):
        """Check if the optimization should be executed at a simulation time

        Args:
            system (System): system
            environment_input (EnvironmentInput): environment input
        Returns:
            bool: True if the optimization will be executed in the current time, False otherwise
        """
        return True

    def update(self, system, environment_input):
        """Update scheduler at a simulation time with a system's state and environment input

        Args:
            system (System): system
            environment_input (EnvironmentInput): environment input
        Returns:
            (System, EnvironmentInput): system and environment input that will be send to the optimizer
        """
        return system, environment_input
