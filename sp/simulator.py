from sp.model.system import System
from sp.controller.environment import DefaultEnvironmentController
from sp.controller.allocation import PeriodicAllocationController


class Simulator:
    def __init__(self):
        self._start_time = 0
        self._stop_time = 0
        self._step_time = 1
        self._scenario = None
        self._env_control = None
        self._alloc_control = None

        self._system = None
        self._current_time = 0

    def set_time(self, stop, start=0, step=1):
        self._start_time = start
        self._stop_time = stop
        self._step_time = step
        return self

    def set_scenario(self, scenario):
        self._scenario = scenario
        return self

    def set_environment_controller(self, controller):
        self._env_control = controller
        return self

    def set_allocation_controller(self, controller):
        self._alloc_control = controller

    def _start_sim(self):
        if self._scenario is None:
            raise ValueError("Scenario not defined")

        self._current_time = self._start_time
        self._system = System()
        self._system.time = self._current_time
        self._system.scenario = self._scenario

        if self._env_control is None:
            self._env_control = DefaultEnvironmentController()
        self._env_control.start(self._system)

        if self._alloc_control is None:
            self._alloc_control = PeriodicAllocationController()
        self._alloc_control.start(self._system)

    def _stop_sim(self):
        self._env_control.stop()
        self._alloc_control.stop()

    def run(self):
        self._start_sim()

        while self._current_time < self._stop_time:
            self._system.time = self._current_time

            self._env_control.update(self._current_time)
            self._alloc_control.update(self._current_time)

            self._current_time += self._step_time

        self._stop_sim()
