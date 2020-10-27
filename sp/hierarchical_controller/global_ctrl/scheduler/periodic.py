from .scheduler import GlobalScheduler
from sp.system_controller.predictor.environment import EnvironmentPredictor, DefaultEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl.predictor import GlobalEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl.model import GlobalSystem, GlobalEnvironmentInput, GlobalScenario


class GlobalPeriodicScheduler(GlobalScheduler):
    """Global Periodic Scheduler

    Attributes:
        period (int): scheduling period
        environment_predictor (GlobalEnvironmentPredictor): global environment predictor
    """

    def __init__(self):
        """Initialization
        """
        GlobalScheduler.__init__(self)
        self.period = 1
        self.environment_predictor = None
        self._update_count = 0

    def init_params(self):
        """Initialize simulation parameters
        """
        if self.environment_predictor is None:
            self.environment_predictor = GlobalEnvironmentPredictor()

        self.environment_predictor.global_scenario = self.global_scenario
        self.environment_predictor.global_period = self.period
        self.environment_predictor.init_params()
        self._update_count = self.period

    def clear_params(self):
        """Clear simulation parameters
        """
        self.environment_predictor.clear()
        self._update_count = 0

    def needs_update(self, system, environment_input):
        """Check if the optimization should be executed at a simulation time

        Args:
            system (System): real system
            environment_input (EnvironmentInput): real environment input
        Returns:
            bool: True if the optimization will be executed in the current time, False otherwise
        """
        # TODO: update in the first step
        self.environment_predictor.update(system, environment_input)
        self._update_count += 1
        if self._update_count >= self.period:
            self._update_count = 0
            return True
        else:
            return False

    def update(self, system, environment_input):
        """Update scheduler at a simulation time with a real system's state and environment input

        Args:
            system (System): real system
            environment_input (EnvironmentInput): real environment input
        Returns:
            (GlobalSystem, GlobalEnvironmentInput): global system and environment input
                that will be send to the optimizer
        """
        global_system = GlobalSystem.from_real_systems(system, self.global_scenario)
        global_system.sampling_time = self.period * system.sampling_time

        env_inputs = self.environment_predictor.predict(0)
        global_env_input = env_inputs[0]

        return global_system, global_env_input

