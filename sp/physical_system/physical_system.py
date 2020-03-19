from sp.core.model import System
from sp.system_controller.estimator.system import DefaultSystemEstimator


class PhysicalSystem:
    def __init__(self):
        self.system_estimator = None
        self._scenario = None
        self._system = None
        self._last_update = 0

    @property
    def state(self):
        return self._system

    def start(self, scenario):
        if self.system_estimator is None:
            self.system_estimator = DefaultSystemEstimator()

        self._scenario = scenario
        self._last_update = 0
        self._system = System()
        self._system.scenario = self._scenario

    def stop(self):
        pass

    def update(self, time):
        self._system.time = time
        self._system.sampling_time = time - self._last_update
        self._last_update = time
        return self._system

    def apply_inputs(self, control_input=None, environment_input=None):
        # TODO: implement the None cases
        if control_input is None or environment_input is None:
            return self._system

        self._system = self.system_estimator(self._system, control_input, environment_input)
        self._system.time = self._last_update
        return self._system
