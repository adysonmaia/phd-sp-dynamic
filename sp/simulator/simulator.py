from sp.physical_system import PhysicalSystem, EnvironmentController
from sp.system_controller import SystemController


class Simulator:
    def __init__(self):
        self._start_time = 0
        self._stop_time = 0
        self._step_time = 1

        self._scenario = None
        self._physical_system = None
        self._system_controller = None
        self._environment_controller = None

    def set_time(self, stop, start=0, step=1):
        self._start_time = start
        self._stop_time = stop
        self._step_time = step
        return self

    def set_scenario(self, scenario):
        self._scenario = scenario
        return self

    def _start_sim(self):
        if self._scenario is None:
            raise ValueError("Scenario not defined")

        self._physical_system = PhysicalSystem(self._scenario)
        self._environment_controller = EnvironmentController()
        self._system_controller = SystemController()

        self._physical_system.start()
        self._environment_controller.start()
        self._system_controller.start()

    def _stop_sim(self):
        self._physical_system.stop()
        self._system_controller.stop()

    def run(self):
        self._start_sim()

        current_time = self._start_time
        while current_time < self._stop_time:
            system_state = self._physical_system.update(current_time)

            env_input = self._environment_controller.update(system_state)
            control_input = self._system_controller.update(system_state, env_input)
            system_state = self._physical_system.apply_inputs(control_input, env_input)

            current_time += self._step_time

        self._stop_sim()
