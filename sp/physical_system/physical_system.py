from sp.core.model import System
from sp.system_controller.estimator.system import SystemEstimator, DefaultSystemEstimator


class PhysicalSystem:
    """Physical System.
    It emulates a system by estimating its state along a simulation

    Attributes:
        system_estimator (SystemEstimator): estimator of the system's state.
            It uses :py:class:`sp.system_controller.estimator.system.DefaultSystemEstimator` class by default
    """

    def __init__(self):
        """Initialization
        """

        self.system_estimator = None
        self._scenario = None
        self._system = None
        self._sampling_time = 1
        self._last_update = None

    @property
    def state(self):
        """Get current system's state

        Returns:
            System: state
        """

        return self._system

    def init_params(self, scenario, sampling_time):
        """Set system's parameters used in the simulation

        Args:
            scenario (sp.core.model.scenario.Scenario): simulation's scenario
            sampling_time (float): simulation time-slot duration
        """

        if self.system_estimator is None:
            self.system_estimator = DefaultSystemEstimator()

        self._scenario = scenario
        self._sampling_time = sampling_time
        self._last_update = None
        self._system = System()
        self._system.scenario = self._scenario

    def clear_params(self):
        """Clear system's parameters
        """
        pass

    def update(self, time):
        """Update system to a specified time

        Args:
            time (float): simulation time
        """
        sampling_time = (time - self._last_update) if self._last_update is not None else self._sampling_time
        self._system.time = time
        self._system.sampling_time = sampling_time
        self._last_update = time
        return self._system

    def apply_inputs(self, control_input=None, environment_input=None):
        """Change the system's by applying control and environment inputs

        Args:
            control_input (sp.core.model.control_input.ControlInput): control input
            environment_input (sp.core.model.environment_input.EnvironmentInput): environment input
        Returns:
            System: new system's state
        """
        # TODO: implement the None cases
        if control_input is None or environment_input is None:
            return self._system

        self._system = self.system_estimator(self._system, control_input, environment_input)
        self._system.time = self._last_update
        return self._system
