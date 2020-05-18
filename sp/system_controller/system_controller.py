from sp.system_controller.scheduler.always import Scheduler, AlwaysScheduler
from sp.system_controller.optimizer.cloud import CloudOptimizer
from sp.system_controller.optimizer import Optimizer, OptimizerError


class SystemController:
    """System Controller

    Attributes:
        scheduler (Scheduler): optimization scheduler
        optimizer (Optimizer): optimizer
    """

    def __init__(self):
        """Initialization
        """
        self.scheduler = None
        self.optimizer = None

    def init_params(self):
        """Initialize simulation parameters
        """
        if self.scheduler is None:
            self.scheduler = AlwaysScheduler()
        if self.optimizer is None:
            self.optimizer = CloudOptimizer()

        self.scheduler.init_params()
        self.optimizer.init_params()

    def clear_params(self):
        """Clear simulation parameters
        """
        self.scheduler.clear_params()
        self.optimizer.clear_params()

    def update(self, system, environment_input):
        """Update controller at a simulation time with a system's state and environment input

        Args:
            system (sp.core.model.system.System): system's state
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        """
        control_input = None

        if self.scheduler.needs_update(system, environment_input):
            estimated_system, estimated_env_input = self.scheduler.update(system, environment_input)
            try:
                control_input = self.optimizer.solve(estimated_system, estimated_env_input)
            except OptimizerError:
                pass

        return control_input
