from sp.system_controller.scheduler.always import AlwaysScheduler
from sp.system_controller.optimizer.cloud import CloudOptimizer
from sp.system_controller.optimizer import OptimizerError


class SystemController:
    def __init__(self):
        self.scheduler = None
        self.optimizer = None

    def init_params(self):
        if self.scheduler is None:
            self.scheduler = AlwaysScheduler()
        if self.optimizer is None:
            self.optimizer = CloudOptimizer()

        self.scheduler.init_params()
        self.optimizer.init_params()

    def clear_params(self):
        self.scheduler.clear_params()
        self.optimizer.clear_params()

    def update(self, system, environment_input):
        control_input = None

        if self.scheduler.needs_update(system, environment_input):
            estimated_system, estimated_env_input = self.scheduler.update(system, environment_input)
            try:
                control_input = self.optimizer.solve(estimated_system, estimated_env_input)
            except OptimizerError:
                pass

        return control_input
