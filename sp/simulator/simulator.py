from sp.physical_system import PhysicalSystem, EnvironmentController
from sp.system_controller import SystemController
from sp.simulator.monitor import Monitor, DefaultMonitor


class Simulator:
    def __init__(self, scenario=None):
        self.start_time = 0
        self.stop_time = 0
        self.step_time = 1

        self.scenario = scenario
        self.system_controller = SystemController()
        self.physical_system = PhysicalSystem()
        self.environment_controller = EnvironmentController()
        self.monitor = DefaultMonitor()

    def set_time(self, stop, start=0, step=1):
        self.start_time = start
        self.stop_time = stop
        self.step_time = step
        return self

    @property
    def optimizer(self):
        return self.system_controller.optimizer

    @optimizer.setter
    def optimizer(self, value):
        self.system_controller.optimizer = value

    @property
    def scheduler(self):
        return self.system_controller.scheduler

    @scheduler.setter
    def scheduler(self, value):
        self.system_controller.scheduler = value

    def _init_params(self):
        if self.scenario is None:
            raise ValueError("Scenario not defined")

        self.physical_system.init_params(self.scenario, self.step_time)
        self.environment_controller.init_params()
        self.system_controller.init_params()
        self.monitor.start(self)

    def _clear_params(self):
        self.physical_system.clear_params()
        self.system_controller.clear_params()

    def run(self):
        self._init_params()
        self.monitor(Monitor.actions.SIM_STARTED, self.start_time)

        current_time = self.start_time
        while current_time < self.stop_time:
            system_state = self.physical_system.update(current_time)
            self.monitor(Monitor.actions.TIME_SLOT_STARTED, current_time, system=system_state)

            self.monitor(Monitor.actions.ENV_CTRL_STARTED, current_time, system=system_state)
            env_input = self.environment_controller.update(system_state)
            self.monitor(Monitor.actions.ENV_CTRL_ENDED, current_time,
                         system=system_state, environment_input=env_input)

            self.monitor(Monitor.actions.SYS_CTRL_STARTED, current_time,
                         system=system_state, environment_input=env_input)
            control_input = self.system_controller.update(system_state, env_input)
            self.monitor(Monitor.actions.SYS_CTRL_ENDED, current_time,
                         system=system_state, environment_input=env_input, control_input=control_input)

            system_state = self.physical_system.apply_inputs(control_input, env_input)

            self.monitor(Monitor.actions.TIME_SLOT_ENDED, current_time)
            current_time += self.step_time

        self.monitor(Monitor.actions.SIM_ENDED, self.stop_time)
        self._clear_params()
