from sp.core.model import System, EnvironmentInput
from sp.system_controller.system_controller import SystemController
from sp.system_controller.optimizer import OptimizerError
from sp.hierarchical_controller.global_ctrl.model import GlobalScenario
from sp.hierarchical_controller.global_ctrl.scheduler import GlobalScheduler, GlobalPeriodicScheduler
from sp.hierarchical_controller.global_ctrl.optimizer import GlobalCloudOptimizer
from sp.hierarchical_controller.global_ctrl.util.make import make_global_limits
from sp.hierarchical_controller.global_ctrl import metric as global_metric
import sys


class HierarchicalSystemController(SystemController):
    """Hierarchical System Controller

    Attributes:
        global_scenario (GlobalScenario): global scenario
        global_scheduler (GlobalScheduler): global scheduler
    """

    def __init__(self):
        """Initialization
        """
        SystemController.__init__(self)
        self.global_scenario = None
        self.global_optimizer = None
        self.global_scheduler = None

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
                global_solution = self.global_optimizer.solve(global_system, global_env_input)
                self._global_control_input = make_global_limits(global_system, global_solution, global_env_input)

                # print(" -- ")
                # for app in global_system.apps:
                #     total_nb_instances = 0
                #     total_load = 0.0
                #     for node in global_system.nodes:
                #         nb_instances = global_solution.get_max_app_placement(app.id, node.id)
                #         load = global_env_input.get_generated_load(app.id, node.id)
                #         total_nb_instances += nb_instances
                #         total_load += load
                #         print(app.id, node.id, nb_instances, load)
                #     print(app.id, app.type, round(app.deadline, 5), app.max_instances, total_nb_instances, total_load)
                #     # print(app.id, global_solution.load_distribution[app.id])
                #
                # rt = global_metric.response_time.weighted_avg_response_time(global_system, global_solution,
                #                                                             global_env_input)
                # dv = global_metric.deadline.weighted_avg_deadline_violation(global_system, global_solution,
                #                                                             global_env_input)
                # print("rt", rt, "dv", dv)
            except OptimizerError:
                pass

        # sys.exit()

        if self.scheduler.needs_update(system, environment_input):
            estimated_system, estimated_env_input = self.scheduler.update(system, environment_input)
            try:
                control_input = self.optimizer.solve(estimated_system, estimated_env_input,
                                                     self.global_scenario, self._global_control_input)
            except OptimizerError:
                pass

        return control_input
