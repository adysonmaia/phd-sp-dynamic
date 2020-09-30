from sp.core.model import System, EnvironmentInput
from sp.system_controller.predictor.environment import EnvironmentPredictor, DefaultEnvironmentPredictor
from sp.hierarchical_controller.global_ctrl.model import GlobalEnvironmentInput, GlobalScenario


class GlobalEnvironmentPredictor(EnvironmentPredictor):
    """Global Environment Predictor

    Attributes:
        real_environment_predictor (EnvironmentPredictor): predictor for real environment inputs
        global_scenario (GlobalScenario): global scenario
        global_period (int): global controller scheduling period
    """

    def __init__(self):
        """Initialization
        """
        EnvironmentPredictor.__init__(self)
        self.real_environment_predictor = None
        self.global_period = 1
        self.global_scenario = None
        self._real_system = None
        self._real_env_input = None

    def init_params(self):
        """Initialize parameters for the simulation
        """
        if self.real_environment_predictor is None:
            self.real_environment_predictor = DefaultEnvironmentPredictor()
        self.real_environment_predictor.init_params()

    def update(self, system, environment_input):
        """Update predictor at a simulation time with a system's state and environment input

        Args:
            system (System): real system's state
            environment_input (EnvironmentInput): real environment input
        """
        self._real_system = system
        self._real_env_input = environment_input
        self.real_environment_predictor.update(system, environment_input)

    def predict(self, steps=1):
        """Predict next environment inputs.

        Args:
            steps (int): number of values to predict
        Returns:
            list(GlobalEnvironmentInput): predicted data
        """
        # Remaining real inputs to create current global input + real inputs for future global inputs
        real_steps = (self.global_period - 1) + (steps * self.global_period)

        real_env_inputs = [self._real_env_input]
        if real_steps > 0:
            real_env_inputs += self.real_environment_predictor.predict(real_steps)

        global_env_inputs = []
        for step in range(steps + 1):
            start = step * self.global_period
            end = start + self.global_period
            env_inputs = real_env_inputs[start:end]
            global_env_input = GlobalEnvironmentInput.from_real_environment_inputs(env_inputs, self.global_scenario)
            global_env_inputs.append(global_env_input)

        if steps > 0:
            global_env_inputs = global_env_inputs[1:]

        return global_env_inputs

    def clear(self):
        """Clear forecasting information
        """
        self.real_environment_predictor.clear()
