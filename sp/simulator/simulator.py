from sp.physical_system import PhysicalSystem, EnvironmentController
from sp.system_controller import SystemController
import time


class Simulator:
    def __init__(self, scenario=None):
        self.start_time = 0
        self.stop_time = 0
        self.step_time = 1

        self.scenario = scenario
        self.system_controller = SystemController()
        self.physical_system = PhysicalSystem()
        self.environment_controller = EnvironmentController()

    def set_time(self, stop, start=0, step=1):
        self.start_time = start
        self.stop_time = stop
        self.step_time = step
        return self

    def set_optimizer(self, optimizer):
        self.system_controller.optimizer = optimizer

    def set_scheduler(self, scheduler):
        self.system_controller.scheduler = scheduler

    def _start_sim(self):
        if self.scenario is None:
            raise ValueError("Scenario not defined")

        self.physical_system.start(self.scenario)
        self.environment_controller.start()
        self.system_controller.start()

    def _stop_sim(self):
        self.physical_system.stop()
        self.system_controller.stop()

    def run(self):
        self._start_sim()

        current_time = self.start_time
        while current_time < self.stop_time:
            system_state = self.physical_system.update(current_time)

            env_input = self.environment_controller.update(system_state)

            start_time = time.time()
            control_input = self.system_controller.update(system_state, env_input)
            elapsed_time = time.time() - start_time
            print(current_time, elapsed_time)

            system_state = self.physical_system.apply_inputs(control_input, env_input)

            current_time += self.step_time

        self._stop_sim()
