from sp.physical_system.model import SystemState


class PhysicalSystem:
    def __init__(self, scenario):
        self._scenario = scenario
        self._state = None

    @property
    def state(self):
        return self._state

    def start(self):
        self._state = SystemState()
        self._state.scenario = self._scenario

    def stop(self):
        pass

    def update(self, time):
        self._state.time = time
        return self._state

    def apply_control_input(self, control_input):
        pass

    def apply_environment_input(self, env_input):
        self._state.environment = env_input
