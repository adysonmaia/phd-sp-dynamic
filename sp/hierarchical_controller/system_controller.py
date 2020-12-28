from sp.core.model import System, EnvironmentInput
from sp.system_controller.system_controller import SystemController
from sp.system_controller.optimizer import OptimizerError
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.global_ctrl.scheduler import GlobalScheduler, GlobalPeriodicScheduler
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalCloudOptimizer
from sp.hierarchical_controller.global_ctrl.util.make import make_global_limits


class HierarchicalSystemController(SystemController):
    """Hierarchical System Controller

    Attributes:
        global_scenario (GlobalScenario): global scenario
        global_scheduler (GlobalScheduler): global scheduler
        monitor (sp.simulator.monitor.monitor.Monitor): simulator's monitor
    """

    def __init__(self):
        """Initialization
        """
        SystemController.__init__(self)
        self.global_scenario = None
        self.global_optimizer = None
        self.global_scheduler = None
        self.monitor = None

        self._global_control_input = None

    def init_params(self):
        """Initialize simulation parameters
        """
        SystemController.init_params(self)

        if self.global_scheduler is None:
            self.global_scheduler = GlobalPeriodicScheduler()
        self.global_scheduler.global_scenario = self.global_scenario
        self.global_scheduler.init_params()

        if self.global_optimizer is None:
            self.global_optimizer = GlobalCloudOptimizer()
        self.global_optimizer.init_params()

    def clear_params(self):
        """Clear simulation parameters
        """
        SystemController.clear_params(self)
        self._global_control_input = None

        self.global_scheduler.clear_params()
        self.global_optimizer.clear_params()

    def update(self, system, environment_input):
        """Update controller at a simulation time with a system's state and environment input

        Args:
            system (System): system's state
            environment_input (EnvironmentInput): environment input
        """
        control_input = None

        if self.global_scheduler.needs_update(system, environment_input):
            global_system, global_env_input = self.global_scheduler.update(system, environment_input)
            try:
                if self.monitor is not None:
                    self.monitor("on_global_ctrl_started", system.time)

                global_solution = self.global_optimizer.solve(global_system, global_env_input)
                self._global_control_input = make_global_limits(global_system, global_solution, global_env_input)

                if self.monitor is not None:
                    self.monitor("on_global_ctrl_ended", system.time,
                                 system=global_system, environment_input=global_env_input,
                                 control_input=self._global_control_input)
            except OptimizerError:
                pass

        if self.scheduler.needs_update(system, environment_input):
            estimated_system, estimated_env_input = self.scheduler.update(system, environment_input)
            try:
                if self.monitor is not None:
                    self.monitor("on_all_cluster_ctrls_started", system.time)

                control_input = self.optimizer.solve(estimated_system, estimated_env_input,
                                                     self.global_scenario, self._global_control_input)

                if self.monitor is not None:
                    self.monitor("on_all_cluster_ctrls_ended", system.time,
                                 system=estimated_system, environment_input=estimated_env_input,
                                 control_input=control_input)
            except OptimizerError:
                pass

        return control_input
