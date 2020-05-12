from sp.physical_system import PhysicalSystem, EnvironmentController
from sp.system_controller import SystemController
from sp.simulator.monitor import Monitor, DefaultMonitor


class Simulator:
    """Service Placement Simulator

    Attributes:
        start_time (float): simulation's start time (in seconds)
        stop_time (float): simulation's stop time (in seconds)
        step_time (float): duration of each simulation time step (in seconds)
        scenario (sp.core.model.scenario.Scenario): simulation's scenario
        physical_system (PhysicalSystem): simulation's physical system.
            It emulates a (physical) system, such as an Edge Computing infrastructure
        system_controller (SystemController): simulation's system controller.
            It is responsible to manage the system through control inputs
        environment_controller (EnvironmentController): simulation's environment controller.
            It controls system's inputs that are directly controlled by the SystemController
        monitor (Monitor): simulation's monitor.
    """

    def __init__(self, scenario=None):
        """Initialization

        Args:
            scenario (sp.core.model.scenario.Scenario): simulation's scenario
        """

        self.start_time = 0
        self.stop_time = 0
        self.step_time = 1

        self.scenario = scenario
        self.system_controller = SystemController()
        self.physical_system = PhysicalSystem()
        self.environment_controller = EnvironmentController()
        self.monitor = DefaultMonitor()

    def set_time(self, stop, start=0, step=1):
        """Set simulation time

        Args:
            stop (float): start time (in seconds)
            start (float): stop time (in seconds)
            step (float):  time-slot duration (in seconds)
        """
        self.start_time = start
        self.stop_time = stop
        self.step_time = step
        return self

    @property
    def optimizer(self):
        """Get System Controller Optimizer

        Returns:
            sp.system_controller.optimizer.optimizer.Optimizer: controller optimizer
        """
        return self.system_controller.optimizer

    @optimizer.setter
    def optimizer(self, value):
        """Set System Controller Optimizer

        Args:
            value (sp.system_controller.optimizer.optimizer.Optimizer): controller optimizer
        """
        self.system_controller.optimizer = value

    @property
    def scheduler(self):
        """Get System Controller Scheduler

        Returns:
            sp.system_controller.scheduler.scheduler.Scheduler: controller scheduler
        """
        return self.system_controller.scheduler

    @scheduler.setter
    def scheduler(self, value):
        """Set System Controller Scheduler

        Args:
            value (sp.system_controller.scheduler.scheduler.Scheduler): controller scheduler
        """
        self.system_controller.scheduler = value

    def _init_params(self):
        """Initialize parameters before starting the simulation
        """
        if self.scenario is None:
            raise ValueError("Scenario not defined")

        self.physical_system.init_params(self.scenario, self.step_time)
        self.environment_controller.init_params()
        self.system_controller.init_params()
        self.monitor.start(self)

    def _clear_params(self):
        """Clear parameters after simulation stopped
        """
        self.physical_system.clear_params()
        self.system_controller.clear_params()

    def run(self):
        """Start simulation
        """
        self._init_params()
        self.monitor(Monitor.events.SIM_STARTED, self.start_time)

        current_time = self.start_time
        while current_time <= self.stop_time:
            system_state = self.physical_system.update(current_time)
            self.monitor(Monitor.events.TIME_SLOT_STARTED, current_time, system=system_state)

            self.monitor(Monitor.events.ENV_CTRL_STARTED, current_time, system=system_state)
            env_input = self.environment_controller.update(system_state)
            self.monitor(Monitor.events.ENV_CTRL_ENDED, current_time,
                         system=system_state, environment_input=env_input)

            self.monitor(Monitor.events.SYS_CTRL_STARTED, current_time,
                         system=system_state, environment_input=env_input)
            control_input = self.system_controller.update(system_state, env_input)
            self.monitor(Monitor.events.SYS_CTRL_ENDED, current_time,
                         system=system_state, environment_input=env_input, control_input=control_input)

            system_state = self.physical_system.apply_inputs(control_input, env_input)

            self.monitor(Monitor.events.TIME_SLOT_ENDED, current_time)
            current_time += self.step_time

        self.monitor(Monitor.events.SIM_ENDED, self.stop_time)
        self._clear_params()
